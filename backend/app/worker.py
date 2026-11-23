"""Durable PostgreSQL-backed processor. Jobs are claimed transactionally by one worker."""
import logging
import hashlib
import hmac
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Event
from sqlalchemy import select, or_, and_, delete
from sqlalchemy.orm import Session
from .db import SessionLocal
from .config import settings
from .config import validate_database_url, validate_upload_encryption, validate_upload_storage
from .models import Case, Entity, Evidence, ProcessingJob, AuditEvent, SourceRecord, CorrectionRequest, LoginThrottle, GraphProjectionOutbox, PasswordResetToken
from .extract import extract
from .vacancy_verification import check_vacancy
from .classify_cases import classify
from .posting_model import load_model
from .source_adapters import LocalEvidenceCorpusAdapter, RdapDomainAdapter
from .findings import RULE_VERSION as FINDING_RULE_VERSION, rebuild_system_findings
from .graph_outbox import enqueue_graph_sync, process_graph_projection_once
from .private_storage import decode_upload_encryption_key, is_private_upload_name
from .upload_storage import delete_upload, ensure_upload_storage, list_uploads, load_upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("case-worker")


@dataclass(frozen=True)
class TextSegment:
    source_location: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    segments: tuple[TextSegment, ...]
    regions: tuple["OCRRegion", ...] = ()


@dataclass(frozen=True)
class OCRRegion:
    start_char: int
    end_char: int
    left: int
    top: int
    width: int
    height: int


def ocr_image(image, location_prefix: str) -> tuple[str, tuple[OCRRegion, ...]]:
    """Return OCR text and word boxes mapped to offsets in that text."""
    import pytesseract
    from pytesseract import Output
    data = pytesseract.image_to_data(image, output_type=Output.DICT, timeout=30)
    words: list[str] = []
    regions: list[OCRRegion] = []
    offset = 0
    for index, raw_word in enumerate(data.get("text", [])):
        word = str(raw_word).strip()
        if not word:
            continue
        if words:
            offset += 1
        start = offset
        words.append(word)
        offset += len(word)
        regions.append(OCRRegion(
            start_char=start,
            end_char=offset,
            left=int(data["left"][index]),
            top=int(data["top"][index]),
            width=int(data["width"][index]),
            height=int(data["height"][index]),
        ))
    return " ".join(words), tuple(regions)


def region_location(regions: tuple[OCRRegion, ...], start_char: int, end_char: int, prefix: str) -> str | None:
    matched = [region for region in regions if region.start_char < end_char and region.end_char > start_char]
    if not matched:
        return None
    left = min(region.left for region in matched)
    top = min(region.top for region in matched)
    right = max(region.left + region.width for region in matched)
    bottom = max(region.top + region.height for region in matched)
    # source_location is currently VARCHAR(80); keep the encoded box compact.
    return f"{prefix}_ocrpx_{left}_{top}_{right-left}_{bottom-top}"[:80]


def read_uploaded_text(evidence: Evidence) -> ExtractedDocument:
    details = evidence.details or {}
    stored_name = details.get("stored_name")
    if not is_private_upload_name(stored_name):
        raise ValueError("Upload reference is invalid")
    expected_sha256 = details.get("sha256")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("Private upload integrity reference is invalid")
    upload_bytes = load_upload(stored_name, settings.max_upload_bytes, decode_upload_encryption_key(settings.upload_encryption_key))
    actual_sha256 = hashlib.sha256(upload_bytes).hexdigest()
    if not hmac.compare_digest(actual_sha256, expected_sha256):
        raise ValueError("Private upload integrity check failed")
    media_type = details.get("media_type")
    if media_type == "application/pdf":
        import fitz
        import io
        with fitz.open(stream=upload_bytes, filetype="pdf") as document:
            if document.page_count > 20:
                raise ValueError("PDF exceeds the 20-page processing limit")
            pages: list[str] = []
            page_regions: list[tuple[OCRRegion, ...]] = []
            for page_number, page in enumerate(document, start=1):
                content = page.get_text("text").strip()
                regions: tuple[OCRRegion, ...] = ()
                if not content:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    from PIL import Image
                    with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
                        content, regions = ocr_image(image, f"pdf_page_{page_number}")
                pages.append(content)
                page_regions.append(regions)
            text_parts: list[str] = []
            segments: list[TextSegment] = []
            all_regions: list[OCRRegion] = []
            offset = 0
            for page_number, content in enumerate(pages, start=1):
                if page_number > 1:
                    text_parts.append("\n\n")
                    offset += 2
                start = offset
                text_parts.append(content)
                offset += len(content)
                if content:
                    segments.append(TextSegment(f"pdf_page_{page_number}", start, offset))
                    all_regions.extend(OCRRegion(r.start_char + start, r.end_char + start, r.left, r.top, r.width, r.height) for r in page_regions[page_number - 1])
            return ExtractedDocument("".join(text_parts), tuple(segments), tuple(all_regions))
    if media_type in {"image/png", "image/jpeg", "image/webp"}:
        import io
        from PIL import Image
        with Image.open(io.BytesIO(upload_bytes)) as image:
            if image.width * image.height > 30_000_000:
                raise ValueError("Image exceeds the 30-megapixel processing limit")
            text, regions = ocr_image(image, "image")
            return ExtractedDocument(text, (TextSegment("image_ocr_text", 0, len(text)),), regions)
    raise ValueError("Unsupported stored upload type")


def process_job(db: Session, job: ProcessingJob) -> None:
    case = db.get(Case, job.case_id)
    if not case:
        job.status = "failed"
        job.last_error = "Case record is missing"
        return
    job.status = "processing"
    job.processing_ms = None
    case.status = "processing"
    db.commit()
    processing_started = time.perf_counter()
    try:
        uploads = [e for e in case.evidence if e.source_type == "uploaded_file"]
        source_segments: tuple[TextSegment, ...] = ()
        if uploads:
            extracted_document = read_uploaded_text(uploads[0])
            text = extracted_document.text
            source_segments = extracted_document.segments
            case.submitted_text = text
            uploads[0].claim = "Uploaded content extracted locally using PDF text parsing or OCR"
            uploads[0].outcome = "result" if text.strip() else "no_result"
            uploads[0].excerpt = text[:2000] if text.strip() else "No readable text was detected in the uploaded material."
            uploads[0].details = {**(uploads[0].details or {}), "extraction_method": "local_ocr_or_pdf_text", "character_count": len(text)}
        material = case.submitted_text or ""
        entities = extract(material)
        for found in entities:
            exists = any(e.entity_type == found.kind and e.normalized_value == found.normalized for e in case.entities)
            if not exists:
                location = "submitted_text"
                start_char, end_char = found.start_char, found.end_char
                if uploads:
                    segment = next((part for part in source_segments if part.start_char <= found.start_char < part.end_char and found.end_char <= part.end_char), None)
                    if segment:
                        location = segment.source_location
                        start_char -= segment.start_char
                        end_char -= segment.start_char
                        if source_segments and extracted_document.regions:
                            region = region_location(extracted_document.regions, found.start_char, found.end_char, location)
                            if region:
                                location = region
                    else:
                        location = "extracted_upload_text"
                case.entities.append(Entity(entity_type=found.kind, raw_value=found.raw, normalized_value=found.normalized, source_excerpt=found.excerpt, source_location=location, source_start_char=start_char, source_end_char=end_char, extraction_method="deterministic_regex", extraction_confidence=found.confidence, extraction_uncertainty=found.uncertainty))
        db.flush()
        current_entities = list(case.entities)
        source_adapters = [LocalEvidenceCorpusAdapter(db)]
        if settings.rdap_enabled and case.external_source_consent:
            source_adapters.append(RdapDomainAdapter(settings.rdap_timeout_seconds, settings.rdap_max_response_bytes))
        source_checks = 0
        matched_source_records = 0
        for entity in current_entities:
            for source_adapter in source_adapters:
                for observation in source_adapter.check(entity):
                    source_checks += 1
                    matched_source_records += int(observation.outcome == "result")
                    already = any(e.source_ref == observation.source_ref and e.source_type == observation.source_type for e in case.evidence)
                    if already:
                        continue
                    db.add(Evidence(case_id=case.id, source_name=observation.source_name, source_type=observation.source_type, source_ref=observation.source_ref, claim=observation.claim, outcome=observation.outcome, excerpt=observation.excerpt, authority=observation.authority, retrieved_at=observation.retrieved_at, details=observation.details))
        db.flush()
        check_vacancy(db, case)
        rebuild_system_findings(db, case)
        classify(db, case)
        db.add(AuditEvent(case_id=case.id, actor_id=None, action="system_findings_recomputed", detail={"rule_version": FINDING_RULE_VERSION, "trigger": "processing_completed"}))
        case.status = "completed"
        job.status = "completed"
        job.last_error = ""
        # Measure worker execution after the durable processing transition and
        # before the completion commit. Queue wait time is intentionally excluded.
        job.processing_ms = round((time.perf_counter() - processing_started) * 1000, 3)
        db.add(AuditEvent(case_id=case.id, actor_id=None, action="processing_completed", detail={"entity_count": len(entities), "source_checks": source_checks, "matched_source_records": matched_source_records, "external_source_checks_enabled": bool(settings.rdap_enabled and case.external_source_consent)}))
        enqueue_graph_sync(db, case.id)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ProcessingJob, job.id)
        case = db.get(Case, job.case_id) if job else None
        if job:
            # Exception messages can contain submitted values, paths or provider details.
            # Keep only the class for operator diagnostics; the API returns safe guidance.
            job.last_error = type(exc).__name__[:80]
            job.status = "queued" if job.attempts < 3 else "failed"
        if case:
            case.status = "queued" if job and job.status == "queued" else "failed"
            db.add(AuditEvent(case_id=case.id, actor_id=None, action="processing_failed", detail={"attempt": job.attempts if job else 0, "error_type": type(exc).__name__}))
            enqueue_graph_sync(db, case.id)
        db.commit()
        log.error("Case processing failed for case id %s on attempt %s (%s)", job.case_id, job.attempts, type(exc).__name__)


def purge_expired_records(now: datetime | None = None) -> int:
    """Purge expired cases/corpus entries, then remove their private files by opaque name."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=settings.retention_days)
    ensure_upload_storage()
    expired_uploads: set[str] = set()
    active_uploads: set[str] = set()
    deleted_cases = 0
    with SessionLocal() as db:
        with db.begin():
            expired_cases = db.scalars(select(Case).where(Case.created_at < cutoff)).all()
            for case in expired_cases:
                enqueue_graph_sync(db, case.id, operation="delete")
                for evidence in case.evidence:
                    stored_name = (evidence.details or {}).get("stored_name")
                    if is_private_upload_name(stored_name):
                        expired_uploads.add(stored_name)
                db.execute(delete(AuditEvent).where(AuditEvent.case_id == case.id))
                db.delete(case)
                deleted_cases += 1
            db.execute(delete(GraphProjectionOutbox).where(GraphProjectionOutbox.status == "completed", GraphProjectionOutbox.updated_at < cutoff))
            db.execute(delete(SourceRecord).where(SourceRecord.created_at < cutoff))
            db.execute(delete(CorrectionRequest).where(CorrectionRequest.created_at < cutoff))
            db.execute(delete(PasswordResetToken).where(PasswordResetToken.created_at < cutoff))
            db.execute(delete(AuditEvent).where(AuditEvent.case_id.is_(None), AuditEvent.created_at < cutoff))
            throttle_cutoff = now - timedelta(seconds=settings.login_window_seconds + settings.login_lockout_seconds)
            db.execute(delete(LoginThrottle).where(LoginThrottle.updated_at < throttle_cutoff))
            # Ensure queued case deletions and their cascaded evidence are gone
            # before computing references that protect uploads from cleanup.
            db.flush()
            for details in db.scalars(select(Evidence.details).where(Evidence.source_type == "uploaded_file")):
                stored_name = (details or {}).get("stored_name")
                if is_private_upload_name(stored_name):
                    active_uploads.add(stored_name)
    # Recover remote objects left behind if a prior database delete committed
    # before storage cleanup, and apply the same age-based retention rule.
    for stored_name, created_at in list_uploads():
        if stored_name not in active_uploads and (stored_name in expired_uploads or created_at < cutoff):
            try:
                delete_upload(stored_name)
            except Exception as exc:
                # Storage errors may contain service URLs or object paths.
                log.warning("Could not remove expired private upload (error=%s)", type(exc).__name__)
    return deleted_cases


def run_worker(stop_event: Event | None = None) -> None:
    """Poll the durable PostgreSQL queue until asked to stop, if stoppable."""
    validate_database_url(settings)
    load_model()
    validate_upload_encryption(settings)
    validate_upload_storage(settings)
    log.info("Case processing worker started")
    last_retention = 0.0
    retention_interval = 24 * 60 * 60
    retention_failure_retry = 60 * 60
    retry_delay = 2.0
    while stop_event is None or not stop_event.is_set():
        now_monotonic = time.monotonic()
        if now_monotonic - last_retention >= retention_interval:
            try:
                removed = purge_expired_records()
                log.info("Retention sweep removed %d expired cases", removed)
            except Exception as exc:
                # Do not emit tracebacks or exception text from privacy-sensitive
                # retention work; both may include paths or database details.
                log.error("Retention sweep failed (error=%s)", type(exc).__name__)
                # Retry transient database/filesystem failures in an hour instead
                # of silently postponing retention cleanup for another full day.
                last_retention = time.monotonic() - retention_interval + retention_failure_retry
            else:
                last_retention = time.monotonic()
        try:
            with SessionLocal() as db:
                # SKIP LOCKED allows multiple worker replicas without double processing.
                with db.begin():
                    retry_before = datetime.now(timezone.utc) - timedelta(minutes=10)
                    job = db.scalar(select(ProcessingJob).where(or_(ProcessingJob.status == "queued", and_(ProcessingJob.status == "processing", ProcessingJob.updated_at < retry_before, ProcessingJob.attempts < 3))).order_by(ProcessingJob.created_at).with_for_update(skip_locked=True).limit(1))
                    if job:
                        job_id = job.id
                        job.status = "processing"
                        job.attempts += 1
                    else:
                        job_id = None
                if job_id:
                    current = db.get(ProcessingJob, job_id)
                    if current:
                        process_job(db, current)
            projection_work = process_graph_projection_once()
        except Exception as exc:
            # Database/network failures must not silently kill an in-process
            # worker. Keep exception contents out of logs and back off retries.
            log.error("Worker iteration failed (%s)", type(exc).__name__)
            if stop_event is None:
                time.sleep(retry_delay)
            else:
                stop_event.wait(retry_delay)
            retry_delay = min(retry_delay * 2, 60.0)
            continue
        retry_delay = 2.0
        if not job_id and not projection_work:
            if stop_event is None:
                time.sleep(2)
            else:
                stop_event.wait(2)


def main() -> None:
    run_worker()


if __name__ == "__main__":
    main()
