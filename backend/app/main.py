from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import secrets
import time
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from alembic import command
from alembic.config import Config
from sqlalchemy import select, or_, and_, delete, update, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .config import settings, validate_access_token_settings, validate_bootstrap_codes, validate_correction_throttle_settings, validate_database_url, validate_upload_encryption, validate_upload_size, validate_upload_storage, validate_web_origin
from .vacancy_verification import check_vacancy, configured_boards
from .posting_model import load_model
from .db import get_db, SessionLocal
from .models import User, Case, Entity, Evidence, AuditEvent, CaseLink, ProcessingJob, SourceRecord, CorrectionRequest, HumanDisposition, SystemFinding, LoginThrottle, GraphProjectionOutbox, PasswordResetToken, AccountProvisioningGate
from .schemas import RegisterRequest, LoginRequest, AccountStatusRequest, PasswordResetIssueRequest, PasswordResetConsumeRequest, CaseCreate, ReviewRequest, EvidenceReviewRequest, DispositionRequest, DispositionReviewRequest, SourceRecordCreate, SourceRecordRetire, CorrectionCreate, CorrectionReview, CorrectionStatusRequest, CorrectionApply
from .security import hash_password, verify_password, verify_unknown_account_password, create_token, current_user, require_investigator, require_reviewer, set_session_cookie, clear_session_cookie, session_csrf_token
from .extract import extract, normalize
from .campaign_rules import MATCHABLE_TYPES, SIGNAL_WEIGHTS, link_state, redact_link_reason, rule_version, score_matches
from .findings import RULE_NAME as FINDING_RULE_NAME, RULE_VERSION as FINDING_RULE_VERSION, evidence_for_entity, rebuild_system_findings
from .file_validation import content_matches_type
from .graph_outbox import enqueue_graph_sync
from . import graph_store
from .middleware import ApiNoStoreMiddleware, RequestBodyLimitMiddleware
from .private_storage import decode_upload_encryption_key
from .upload_storage import delete_upload, ensure_upload_storage, store_upload
from .privacy import mask_identifier, redact_data, redact_source_ref, redact_text
from .public_status import public_correction_status
from .reporting import render_markdown_report
from .worker_runtime import InlineWorkerRuntime

upload_log = logging.getLogger("casework.upload")

CONSENT_VERSION = "consent-v2"
RDAP_CONSENT_VERSION = "consent-v3-rdap"

def current_consent_version() -> str:
    return RDAP_CONSENT_VERSION if settings.rdap_enabled else CONSENT_VERSION

def validate_external_source_consent(consent_version: str, rdap_consent: bool) -> None:
    if consent_version != current_consent_version():
        raise HTTPException(400, "Consent notice changed. Review and accept the current notice before submitting.")
    if settings.rdap_enabled and not rdap_consent:
        raise HTTPException(400, "Separate consent is required before extracted domain names are sent to public RDAP services")
    if not settings.rdap_enabled and rdap_consent:
        raise HTTPException(400, "RDAP consent cannot be recorded while external RDAP checks are disabled")

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_database_url(settings)
    if len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith("replace-"):
        raise RuntimeError("Set JWT_SECRET to a random value of at least 32 characters before starting the API")
    validate_access_token_settings(settings)
    validate_web_origin(settings)
    validate_bootstrap_codes(settings)
    if "change-this-local-password" in settings.database_url:
        raise RuntimeError("Set a non-default PostgreSQL password in DATABASE_URL before starting the API")
    if settings.effective_neo4j_uri and (not settings.effective_neo4j_password or settings.effective_neo4j_password.startswith("change-this")):
        raise RuntimeError("Set a non-default NEO4J_PASSWORD before connecting to Neo4j")
    if settings.retention_days < 1:
        raise RuntimeError("DATA_RETENTION_DAYS must be a positive integer")
    validate_upload_size(settings)
    validate_upload_encryption(settings)
    validate_upload_storage(settings)
    if not 1 <= settings.campaign_link_threshold <= 100:
        raise RuntimeError("CAMPAIGN_LINK_THRESHOLD must be between 1 and 100")
    if settings.login_max_attempts < 1 or settings.login_window_seconds < 1 or settings.login_lockout_seconds < 1:
        raise RuntimeError("Login throttling limits and durations must be positive integers")
    if settings.register_max_requests < 1 or settings.register_window_seconds < 1 or settings.register_lockout_seconds < 1:
        raise RuntimeError("Registration throttling limits and durations must be positive integers")
    validate_correction_throttle_settings(settings)
    if settings.password_reset_token_minutes < 1:
        raise RuntimeError("PASSWORD_RESET_TOKEN_MINUTES must be a positive integer")
    if settings.rdap_timeout_seconds <= 0 or settings.rdap_max_response_bytes < 1024:
        raise RuntimeError("RDAP timeout must be positive and RDAP response limit must be at least 1024 bytes")
    configured_boards()
    load_model()
    ensure_upload_storage()
    migration_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(migration_config, "head")
    inline_worker = None
    if settings.run_inline_worker:
        from .worker import run_worker
        inline_worker = InlineWorkerRuntime(run_worker)
        inline_worker.start()
    try:
        yield
    finally:
        if inline_worker is not None:
            inline_worker.stop()

app = FastAPI(title="Recruitment Scam Investigation Platform API", version="0.1.0", lifespan=lifespan)

_VALIDATION_FIELDS = {
    "email", "password", "setup_code", "active", "rationale", "token", "new_password",
    "title", "input_kind", "submitted_text", "consent_version", "consent", "rdap_consent",
    "status", "disposition", "evidence_ids", "entity_type", "value", "source_name",
    "source_type", "source_ref", "claim", "outcome", "excerpt", "authority", "case_ref",
    "requester_email", "description", "status_token", "resolution", "entity_id", "entity_action",
    "corrected_value", "evidence_id", "evidence_action", "case_id", "record_id", "format",
}
_VALIDATION_MESSAGES = {
    "missing": "This field is required.",
    "string_too_short": "Text is shorter than the allowed minimum.",
    "string_too_long": "Text exceeds the allowed maximum.",
    "string_pattern_mismatch": "Value has an invalid format.",
    "string_type": "Enter text for this field.",
    "int_type": "Enter a whole number.",
    "int_parsing": "Enter a whole number.",
    "bool_type": "Choose a valid true or false value.",
    "bool_parsing": "Choose a valid true or false value.",
    "value_error": "Value is invalid.",
    "json_invalid": "Request body is not valid JSON.",
}


def safe_validation_details(errors: list[dict]) -> list[dict]:
    """Return actionable validation locations without echoing submitted values."""
    safe = []
    for error in errors[:50]:
        location = []
        for part in error.get("loc", ()):
            if isinstance(part, int) and 0 <= part < 1000:
                location.append(part)
            elif isinstance(part, str) and part in {"body", "query", "path", "header", "form"}:
                location.append(part)
            elif isinstance(part, str) and part in _VALIDATION_FIELDS:
                location.append(part)
        error_type = error.get("type")
        safe_type = error_type if isinstance(error_type, str) and error_type in _VALIDATION_MESSAGES else "invalid_value"
        safe.append({
            "loc": location,
            "msg": _VALIDATION_MESSAGES.get(safe_type, "Value is invalid."),
            "type": safe_type,
        })
    return safe


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    # Pydantic errors include the rejected `input` and may include context values.
    # Keep only allowlisted field locations and fixed messages in API responses.
    return JSONResponse(status_code=422, content={"detail": safe_validation_details(exc.errors())})

app.add_middleware(
    RequestBodyLimitMiddleware,
    default_api_write_limit=128 * 1024,
    limits={
        # File bytes plus bounded multipart metadata/consent fields. The endpoint still checks the file itself.
        ("POST", "/api/cases/upload"): settings.max_upload_bytes + 64 * 1024,
        # Supports the schema's 100,000-character UTF-8 text field plus JSON/title/consent encoding overhead.
        ("POST", "/api/cases"): 512 * 1024,
    },
)
app.add_middleware(ApiNoStoreMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=[settings.web_origin], allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"])

def record_audit(db: Session, actor_id: int | None, action: str, case_id: int | None = None, detail: dict | None = None):
    db.add(AuditEvent(actor_id=actor_id, action=action, case_id=case_id, detail=detail or {}))


def auth_response(response: Response | None, user: User, session_mode: str) -> dict:
    user_data = {"id": user.id, "email": user.email, "role": user.role}
    if session_mode == "cookie":
        if response is None:
            raise RuntimeError("Cookie sessions require an HTTP response context")
        csrf_token = set_session_cookie(response, user)
        return {"token_type": "cookie", "csrf_token": csrf_token, "user": user_data}
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_data}

def serialize_entity(entity: Entity, redact: bool = False):
    return {"id": entity.id, "type": entity.entity_type, "value": mask_identifier(entity.entity_type, entity.raw_value) if redact else entity.raw_value, "normalized": "[redacted]" if redact else entity.normalized_value, "excerpt": "[source excerpt restricted for privacy]" if redact else entity.source_excerpt, "source_location": entity.source_location, "source_start_char": entity.source_start_char, "source_end_char": entity.source_end_char, "method": entity.extraction_method, "extraction_confidence": entity.extraction_confidence, "extraction_uncertainty": entity.extraction_uncertainty, "review_status": entity.review_status, "created_at": entity.created_at.isoformat()}

def serialize_evidence(item: Evidence, redact: bool = False):
    details = item.details or {}
    if redact:
        details = {}
    return {"id": item.id, "source_name": "[source name restricted for privacy]" if redact else item.source_name, "source_type": item.source_type, "source_ref": redact_source_ref(item.source_ref, item.source_type) if redact else item.source_ref, "claim": "[source claim restricted for privacy]" if redact else item.claim, "outcome": item.outcome, "excerpt": "[source excerpt restricted for privacy]" if redact else item.excerpt, "authority": item.authority, "retrieved_at": item.retrieved_at.isoformat(), "details": details, "review_status": item.review_status, "review_reason": "[review rationale restricted for privacy]" if redact and item.review_reason else (redact_text(item.review_reason) if redact else item.review_reason), "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}

def serialize_case(case: Case, include_text: bool = False, redact_personal: bool = False):
    result = {"id": case.id, "case_ref": case.case_ref, "title": "[case title restricted for privacy]" if redact_personal else case.title, "input_kind": case.input_kind, "status": case.status, "posting_prediction": case.posting_prediction, "assessment": case.assessment, "consent_version": case.consent_version, "external_source_consent": case.external_source_consent, "created_at": case.created_at.isoformat(), "updated_at": case.updated_at.isoformat(), "entities": [serialize_entity(x, redact_personal) for x in case.entities], "evidence": [serialize_evidence(x, redact_personal) for x in case.evidence]}
    if include_text:
        result["submitted_text"] = case.submitted_text
    return result

def serialize_disposition(item: HumanDisposition, redact: bool = True):
    display_labels = {"confirmed_authoritative": "Confirmed by an authoritative source", "evidence_supports_concern": "Evidence supports concern", "insufficient_evidence": "Insufficient evidence", "no_adverse_evidence": "No adverse evidence found"}
    return {"id": item.id, "case_id": item.case_id, "disposition": item.disposition, "display_label": display_labels.get(item.disposition, "Human disposition"), "rationale": "[review rationale restricted for privacy]" if redact else item.rationale, "evidence_ids": item.evidence_ids, "status": item.status, "review_rationale": "[review rationale restricted for privacy]" if redact and item.review_rationale else (redact_text(item.review_rationale) if redact else item.review_rationale), "created_at": item.created_at.isoformat(), "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}

def serialize_finding(item: SystemFinding, redact: bool = False):
    snapshot = []
    for evidence in item.evidence_snapshot or []:
        snapshot.append({
            "evidence_id": evidence.get("evidence_id"),
            "source_name": "[source name restricted for privacy]" if redact else evidence.get("source_name", ""),
            "source_type": evidence.get("source_type", "unknown"),
            "source_ref": redact_source_ref(evidence.get("source_ref", ""), evidence.get("source_type", "")) if redact else evidence.get("source_ref", ""),
            "claim": "[source claim restricted for privacy]" if redact else evidence.get("claim", ""),
            "outcome": evidence.get("outcome", "unknown"),
            "authority": evidence.get("authority", "unknown"),
            "retrieved_at": evidence.get("retrieved_at", "not recorded"),
        })
    return {"id": item.id, "entity_id": item.entity_id, "scope": item.scope, "claim": redact_text(item.claim) if redact else item.claim, "assessment": item.assessment, "observation": redact_text(item.observation) if redact else item.observation, "evidence_ids": item.evidence_ids, "supporting_evidence_ids": item.supporting_evidence_ids, "evidence_snapshot": snapshot, "conflict_evidence_ids": item.conflict_evidence_ids, "unreviewed_evidence_ids": item.unreviewed_evidence_ids, "rule_name": item.rule_name, "rule_version": item.rule_version, "limitations": item.limitations, "created_at": item.created_at.isoformat()}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    return health_ready(db)

@app.get("/health/live")
def health_live():
    return {"status": "ok", "service": "api"}

@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "service": "api", "dependencies": {"postgres": "unavailable"}},
        )
    return {"status": "ready", "service": "api", "dependencies": {"postgres": "ready"}}

@app.get("/api/policy")
def policy():
    employers = sorted(configured_boards())
    board_notice = (f" Automatic vacancy verification covers {', '.join(employers)}. The worker downloads their public job listings and compares the wording locally. It sends no submitted text or identifiers to these boards." if employers else "")
    return {"official_board_employers": employers, "consent_version": current_consent_version(), "retention_days": settings.retention_days, "max_upload_bytes": settings.max_upload_bytes, "allowed_upload_media_types": ["image/png", "image/jpeg", "image/webp", "application/pdf"], "rdap_enabled": settings.rdap_enabled, "rdap_disclosure": ("When enabled, only extracted domain names are sent to the domain's public RDAP registry discovered through the IANA bootstrap registry. Submitted text, complete URLs, and other identifiers are not sent. The registry operator and network providers may log domain queries. RDAP provides registration metadata, not a determination of fraud or legitimacy." if settings.rdap_enabled else "External RDAP lookups are disabled.") + board_notice, "campaign_rule_version": rule_version(settings.campaign_link_threshold), "campaign_link_threshold": settings.campaign_link_threshold, "campaign_signal_weights": SIGNAL_WEIGHTS, "campaign_score_note": "Campaign link strength is a deterministic signal score from 0 to 100, not a probability or finding of wrongdoing. Links below the configured threshold remain low-signal leads.", "stored_data": ["submitted text or uploaded file", "extracted identifiers", "source results", "investigator review and audit records", "correction request contact details and explanation"], "access": "Signed-in workspace users; analyst views withhold free-text evidence, titles, review rationales, and direct identifiers. Authorized investigators and reviewers can inspect case source content. Downloadable reports restrict free-text source content and mask contact identifiers. Correction request details are limited to investigators.", "deletion": "Case records, original uploads, local evidence corpus entries, and correction requests are automatically deleted after the configured retention period."}

@app.post("/api/corrections", status_code=202)
def create_correction(body: CorrectionCreate, request: Request, db: Session = Depends(get_db)):
    remote_address = request.client.host if request.client else "unknown"
    enforce_public_correction_rate_limit(remote_address, db)
    status_token = secrets.token_urlsafe(32)
    request = CorrectionRequest(request_ref=f"CR-{secrets.token_hex(6).upper()}", case_ref=body.case_ref, requester_email=body.requester_email.lower(), description=body.description, status="received", status_token_hash=hashlib.sha256(status_token.encode()).hexdigest())
    db.add(request)
    db.commit()
    # Do not reveal whether a supplied case reference exists.
    return {"received": True, "request_ref": request.request_ref, "status_token": status_token, "message": "Your correction request was received for review. Save the status token; it is shown only once."}

@app.post("/api/corrections/{request_ref}/status")
def correction_status(request_ref: str, body: CorrectionStatusRequest, db: Session = Depends(get_db)):
    request = db.scalar(select(CorrectionRequest).where(CorrectionRequest.request_ref == request_ref))
    supplied = hashlib.sha256(body.status_token.encode()).hexdigest()
    if not request or not secrets.compare_digest(supplied, request.status_token_hash):
        raise HTTPException(404, "Correction request not found")
    # Investigator-written resolution text can contain names or copied source
    # material that pattern-based redaction cannot reliably identify. Expose
    # only a fixed status message to the public token holder.
    return public_correction_status(request)

@app.get("/api/corrections")
def list_corrections(db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    requests = db.scalars(select(CorrectionRequest).order_by(CorrectionRequest.created_at.desc()).limit(500)).all()
    record_audit(db, user.id, "correction_queue_accessed", None, {"request_count": len(requests)})
    db.commit()
    return [{"request_ref": r.request_ref, "case_ref": r.case_ref, "requester_email": r.requester_email, "description": r.description, "status": r.status, "resolution": r.resolution, "created_at": r.created_at.isoformat(), "updated_at": r.updated_at.isoformat()} for r in requests]

@app.patch("/api/corrections/{request_ref}")
def review_correction(request_ref: str, body: CorrectionReview, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    request = db.scalar(select(CorrectionRequest).where(CorrectionRequest.request_ref == request_ref))
    if not request:
        raise HTTPException(404, "Correction request not found")
    request.status = body.status
    request.resolution = body.resolution
    request.reviewed_by = user.id
    record_audit(db, user.id, "correction_request_reviewed", None, {"request_ref": request_ref, "status": body.status, "resolution": body.resolution})
    db.commit()
    return {"request_ref": request.request_ref, "status": request.status, "resolution": request.resolution}

@app.post("/api/corrections/{request_ref}/apply")
def apply_correction(request_ref: str, body: CorrectionApply, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    request = db.scalar(select(CorrectionRequest).where(CorrectionRequest.request_ref == request_ref).with_for_update())
    if not request:
        raise HTTPException(404, "Correction request not found")
    if request.status not in {"received", "investigating"}:
        raise HTTPException(409, "This correction request is no longer open for case changes")
    previously_applied = db.scalar(
        select(AuditEvent.id)
        .where(
            AuditEvent.action == "correction_applied",
            AuditEvent.detail["request_ref"].as_string() == request_ref,
        )
        .limit(1)
    )
    if previously_applied is not None:
        raise HTTPException(409, "This correction request has already been applied")
    case = db.scalar(select(Case).where(Case.case_ref == request.case_ref))
    if not case:
        raise HTTPException(409, "The referenced case is unavailable; record the request outcome without applying a record change")
    if (body.entity_id is None) != (body.entity_action is None) or (body.evidence_id is None) != (body.evidence_action is None):
        raise HTTPException(400, "Each correction target requires exactly one corresponding action")
    if (body.entity_id is None) == (body.evidence_id is None):
        raise HTTPException(400, "Select exactly one entity or evidence record to correct")
    changed = []
    if body.entity_id is not None:
        entity = db.get(Entity, body.entity_id)
        if not entity or entity.case_id != case.id:
            raise HTTPException(404, "Correction entity is not part of the referenced case")
        prior_entity_evidence_ids = {
            item.id for item in evidence_for_entity(
                entity,
                db.scalars(select(Evidence).where(Evidence.case_id == case.id)).all(),
            )
        }
        prior = {"entity_id": entity.id, "review_status": entity.review_status, "raw_value": entity.raw_value}
        if body.entity_action == "reject":
            entity.review_status = "rejected"
        elif body.entity_action == "confirm":
            entity.review_status = "confirmed"
        else:
            if not body.corrected_value:
                raise HTTPException(400, "A corrected value is required for the correct action")
            normalized = normalize(entity.entity_type, body.corrected_value)
            if not normalized:
                raise HTTPException(400, "The corrected value is not valid for this entity type")
            entity.raw_value = body.corrected_value.strip()
            entity.normalized_value = normalized
            entity.review_status = "confirmed"
        changed.append({"kind": "entity", "before": prior, "after": {"entity_id": entity.id, "review_status": entity.review_status, "raw_value": entity.raw_value}})
        if body.entity_action in {"correct", "reject"} and prior_entity_evidence_ids:
            reopen_dispositions_for_evidence_ids(
                db, case.id, prior_entity_evidence_ids, request_ref, user.id,
                trigger="entity_claim_changed",
            )
    if body.evidence_id is not None:
        item = db.get(Evidence, body.evidence_id)
        if not item or item.case_id != case.id:
            raise HTTPException(404, "Correction evidence is not part of the referenced case")
        if (item.details or {}).get("source_record_withdrawn") is True and body.evidence_action in {"relevant", "contradicts"}:
            raise HTTPException(409, "The source record was withdrawn. Add and review a current source record before treating this evidence as relevant or contradictory.")
        prior = {"evidence_id": item.id, "review_status": item.review_status}
        item.review_status = body.evidence_action
        item.review_reason = body.resolution
        item.reviewed_by = user.id
        item.reviewed_at = datetime.now(timezone.utc)
        changed.append({"kind": "evidence", "before": prior, "after": {"evidence_id": item.id, "review_status": item.review_status}})
        if item.review_status != "relevant" or item.outcome != "result":
            reopen_dispositions_for_evidence_ids(
                db, case.id, {item.id}, request_ref, user.id,
                trigger="evidence_support_changed",
            )
    request.status = "resolved"
    request.resolution = body.resolution
    request.reviewed_by = user.id
    request.updated_at = datetime.now(timezone.utc)
    record_audit(db, user.id, "correction_applied", case.id, {"request_ref": request_ref, "changes": changed, "rationale": body.resolution})
    # SessionLocal disables autoflush, so make entity/evidence changes visible to
    # the relational checks that decide whether an existing campaign link survives.
    db.flush()
    if body.entity_id is not None:
        links = db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))).all()
        for link in links:
            if link.review_status in {"rejected", "stale"}:
                continue
            if not shared_case_identifiers(db, link.left_case_id, link.right_case_id):
                link.review_status = "stale"
                record_audit(db, user.id, "case_link_withdrawn_after_correction", case.id, {"link_id": link.id, "request_ref": request_ref, "rule_version": link.rule_version})
    if body.entity_id is not None and entity.entity_type in {"company_claim", "job_title_claim"}:
        check_vacancy(db, case)
    rebuild_system_findings(db, case)
    record_audit(db, user.id, "system_findings_recomputed", case.id, {"rule_version": FINDING_RULE_VERSION, "trigger": "correction_applied"})
    # Recompute campaign links in the same transaction so corrections both
    # withdraw obsolete links and discover newly supported exact matches.
    links = refresh_links(case.id, db, user)["links"]
    return {"request_ref": request.request_ref, "status": request.status, "changes": changed, "links": links}


def reopen_dispositions_for_evidence_ids(
    db: Session, case_id: int, evidence_ids: set[int], request_ref: str, actor_id: int, *, trigger: str
) -> None:
    """Reopen approved strong human dispositions if a correction invalidates cited evidence/claims."""
    if not evidence_ids:
        return
    affected = db.scalars(select(HumanDisposition).where(
        HumanDisposition.case_id == case_id,
        HumanDisposition.status == "approved",
        HumanDisposition.disposition.in_({"confirmed_authoritative", "evidence_supports_concern"}),
    )).all()
    for disposition in affected:
        matching_ids = evidence_ids.intersection(disposition.evidence_ids or [])
        if not matching_ids:
            continue
        previous = {
            "disposition_id": disposition.id,
            "status": disposition.status,
            "reviewed_by": disposition.reviewed_by,
            "reviewed_at": disposition.reviewed_at.isoformat() if disposition.reviewed_at else None,
        }
        disposition.status = "pending_review"
        disposition.reviewed_by = None
        disposition.reviewed_at = None
        disposition.review_rationale = ""
        action = "human_disposition_reopened_after_source_record_retirement" if trigger == "source_record_retirement" else "human_disposition_reopened_after_correction"
        record_audit(db, actor_id, action, case_id, {
            "request_ref": request_ref,
            "disposition_id": disposition.id,
            "previous_review": previous,
            "changed_evidence_ids": sorted(matching_ids),
            "trigger": trigger,
        })

@app.post("/api/auth/register")
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db), response: Response = None):
    remote_address = request.client.host if request.client else "unknown"
    fingerprint = registration_throttle_fingerprint(remote_address)
    now = datetime.now(timezone.utc).timestamp()
    throttle = get_or_create_login_throttle(db, fingerprint, now)
    if throttle.locked_until > now:
        retry_after = max(1, int(throttle.locked_until - now))
        db.commit()
        raise HTTPException(429, "Too many account creation requests. Try again later.", headers={"Retry-After": str(retry_after)})
    if now - throttle.window_started_at >= settings.register_window_seconds:
        throttle.attempts = 0
        throttle.window_started_at = now
        throttle.locked_until = 0
    # Count every registration request, including successful ones, so repeated
    # account creation and one-time setup-code probing share the same limit.
    throttle.attempts += 1
    throttle.updated_at = datetime.now(timezone.utc)
    if throttle.attempts > settings.register_max_requests:
        throttle.locked_until = now + settings.register_lockout_seconds
    db.commit()
    if throttle.locked_until > now:
        retry_after = max(1, int(throttle.locked_until - now))
        raise HTTPException(429, "Too many account creation requests. Try again later.", headers={"Retry-After": str(retry_after)})
    email = body.email.lower()
    gate_update = db.execute(
        update(AccountProvisioningGate)
        .where(AccountProvisioningGate.id == 1)
        .values(generation=AccountProvisioningGate.generation + 1)
    )
    if gate_update.rowcount != 1:
        db.rollback()
        raise HTTPException(503, "Account provisioning is temporarily unavailable")
    # The singleton UPDATE is held until this registration commits. PostgreSQL
    # serializes simultaneous first/reviewer registrations; SQLite also obtains
    # a write lock. Re-check duplicate emails after acquiring the gate.
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    # Investigator privileges require an operator-provisioned one-time setup secret.
    if body.account_kind == "personal":
        if body.setup_code:
            raise HTTPException(400, "Personal accounts do not use a workspace setup code")
        role = "personal"
    else:
        is_first = db.scalar(select(User.id).where(User.role != "personal").limit(1)) is None
        if is_first and (not settings.initial_investigator_code or not secrets.compare_digest(body.setup_code, settings.initial_investigator_code)):
            raise HTTPException(403, "Initial investigator setup code is required")
        if is_first:
            role = "investigator"
        elif settings.initial_reviewer_code and secrets.compare_digest(body.setup_code, settings.initial_reviewer_code):
            if db.scalar(select(User.id).where(User.role == "reviewer").limit(1)):
                raise HTTPException(409, "An authorized reviewer account has already been provisioned")
            role = "reviewer"
        elif body.setup_code:
            raise HTTPException(403, "The supplied account setup code is not valid")
        elif not settings.allow_analyst_self_registration:
            raise HTTPException(403, "Public registration is closed for this workspace")
        else:
            role = "analyst"
    user = User(email=email, password_hash=hash_password(body.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return auth_response(response, user, body.session_mode)

def login_throttle_fingerprint(email: str, remote_address: str) -> str:
    return _throttle_fingerprint("login", email.casefold(), remote_address)


def registration_throttle_fingerprint(remote_address: str) -> str:
    return _throttle_fingerprint("registration", remote_address)


def _throttle_fingerprint(scope: str, *parts: str) -> str:
    material = (scope + "|" + "|".join(parts)).encode("utf-8")
    return hmac.new(settings.jwt_secret.encode("utf-8"), material, hashlib.sha256).hexdigest()


def get_or_create_login_throttle(db: Session, fingerprint: str, now: float) -> LoginThrottle:
    values = {"fingerprint": fingerprint, "attempts": 0, "window_started_at": now, "locked_until": 0}
    if db.bind.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
    elif db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        existing = db.get(LoginThrottle, fingerprint)
        if existing:
            return existing
        existing = LoginThrottle(**values)
        db.add(existing)
        db.flush()
        return existing
    db.execute(dialect_insert(LoginThrottle).values(**values).on_conflict_do_nothing(index_elements=[LoginThrottle.fingerprint]))
    return db.scalar(select(LoginThrottle).where(LoginThrottle.fingerprint == fingerprint).with_for_update())


def enforce_public_correction_rate_limit(remote_address: str, db: Session, now: float | None = None) -> None:
    """Persist a per-client limit without storing the raw network address."""
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    fingerprint = _throttle_fingerprint("correction_request", remote_address)
    throttle = get_or_create_login_throttle(db, fingerprint, now)
    if throttle.locked_until > now:
        retry_after = max(1, int(throttle.locked_until - now))
        db.commit()
        raise HTTPException(429, "Too many correction requests. Try again later.", headers={"Retry-After": str(retry_after)})
    if now - throttle.window_started_at >= settings.correction_window_seconds:
        throttle.attempts = 0
        throttle.window_started_at = now
        throttle.locked_until = 0
    throttle.attempts += 1
    throttle.updated_at = datetime.now(timezone.utc)
    if throttle.attempts > settings.correction_max_requests:
        throttle.locked_until = now + settings.correction_lockout_seconds
    db.commit()
    if throttle.locked_until > now:
        retry_after = max(1, int(throttle.locked_until - now))
        raise HTTPException(429, "Too many correction requests. Try again later.", headers={"Retry-After": str(retry_after)})


@app.post("/api/auth/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db), response: Response = None):
    normalized_email = body.email.lower()
    remote_address = request.client.host if request.client else "unknown"
    fingerprint = login_throttle_fingerprint(normalized_email, remote_address)
    now = datetime.now(timezone.utc).timestamp()
    throttle = get_or_create_login_throttle(db, fingerprint, now)
    if throttle.locked_until > now:
        retry_after = max(1, int(throttle.locked_until - now))
        record_audit(db, None, "login_throttled", None, {"retry_after_seconds": retry_after})
        db.commit()
        raise HTTPException(429, "Too many sign-in attempts. Try again later.", headers={"Retry-After": str(retry_after)})
    if now - throttle.window_started_at >= settings.login_window_seconds:
        throttle.attempts = 0
        throttle.window_started_at = now
        throttle.locked_until = 0
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user:
        valid_password = verify_password(body.password, user.password_hash)
    else:
        verify_unknown_account_password(body.password)
        valid_password = False
    if not user or not user.active or not valid_password:
        throttle.attempts += 1
        throttle.updated_at = datetime.now(timezone.utc)
        if throttle.attempts >= settings.login_max_attempts:
            throttle.locked_until = now + settings.login_lockout_seconds
        record_audit(db, None, "login_failed", None, {"attempt_count": throttle.attempts, "locked": throttle.locked_until > now})
        db.commit()
        raise HTTPException(401, "Incorrect email or password")
    db.delete(throttle)
    record_audit(db, user.id, "user_signed_in")
    db.commit()
    return auth_response(response, user, body.session_mode)

@app.get("/api/auth/me")
def me(request: Request, user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "csrf_token": session_csrf_token(request)}

@app.post("/api/auth/logout")
def logout(response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)):
    user.token_version += 1
    record_audit(db, user.id, "user_signed_out")
    db.commit()
    clear_session_cookie(response)
    return {"status": "signed_out"}

@app.get("/api/accounts")
def list_accounts(db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    accounts = db.scalars(select(User).order_by(User.created_at, User.id)).all()
    record_audit(db, user.id, "account_list_accessed", None, {"account_count": len(accounts)})
    db.commit()
    return [{"id": account.id, "email": account.email, "role": account.role, "active": account.active, "created_at": account.created_at.isoformat()} for account in accounts]

@app.patch("/api/accounts/{account_id}/status")
def update_account_status(account_id: int, body: AccountStatusRequest, db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    account = db.get(User, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    if account.id == user.id and not body.active:
        raise HTTPException(409, "You cannot suspend your own account")
    if account.active == body.active:
        raise HTTPException(409, "Account already has the requested status")
    if account.role == "reviewer" and account.active and not body.active:
        # Lock active reviewer rows so concurrent status changes cannot both
        # conclude they are leaving at least one active reviewer behind.
        active_reviewers = db.scalars(
            select(User).where(User.role == "reviewer", User.active.is_(True)).order_by(User.id).with_for_update()
        ).all()
        if len(active_reviewers) <= 1:
            raise HTTPException(409, "At least one active reviewer account must remain")
    previous_active = account.active
    account.active = body.active
    account.token_version += 1
    record_audit(db, user.id, "account_status_changed", None, {
        "account_id": account.id,
        "role": account.role,
        "previous_active": previous_active,
        "active": body.active,
        "rationale": body.rationale,
    })
    db.commit()
    return {"id": account.id, "email": account.email, "role": account.role, "active": account.active, "created_at": account.created_at.isoformat()}

@app.post("/api/accounts/{account_id}/password-reset")
def issue_password_reset(account_id: int, body: PasswordResetIssueRequest, db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    # Serialize reset issuance per account. Redemption acquires the same locks
    # in account-then-token order so replacement cannot race with token use.
    account = db.scalar(select(User).where(User.id == account_id).with_for_update())
    if not account:
        raise HTTPException(404, "Account not found")
    now = datetime.now(timezone.utc)
    db.execute(
        update(PasswordResetToken).where(
            PasswordResetToken.user_id == account.id,
            PasswordResetToken.consumed_at.is_(None),
        ).values(consumed_at=now)
    )
    raw_token = secrets.token_urlsafe(32)
    token_hash = hmac.new(settings.jwt_secret.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256).hexdigest()
    expires_at = now + timedelta(minutes=settings.password_reset_token_minutes)
    reset = PasswordResetToken(user_id=account.id, token_hash=token_hash, created_by=user.id, expires_at=expires_at)
    db.add(reset)
    record_audit(db, user.id, "password_reset_token_issued", None, {"account_id": account.id, "expires_at": expires_at.isoformat(), "rationale": body.rationale})
    db.commit()
    return JSONResponse(
        {"account_id": account.id, "reset_token": raw_token, "expires_at": expires_at.isoformat(), "delivery": "Deliver this one-time token to the account holder through a separately verified secure channel."},
        headers={"Cache-Control": "no-store, private"},
    )

@app.post("/api/auth/reset-password")
def consume_password_reset(body: PasswordResetConsumeRequest, request: Request, db: Session = Depends(get_db)):
    remote_address = request.client.host if request.client else "unknown"
    fingerprint = _throttle_fingerprint("password_reset", remote_address)
    now_epoch = datetime.now(timezone.utc).timestamp()
    throttle = get_or_create_login_throttle(db, fingerprint, now_epoch)
    if throttle.locked_until > now_epoch:
        retry_after = max(1, int(throttle.locked_until - now_epoch))
        db.commit()
        raise HTTPException(429, "Too many password reset attempts. Try again later.", headers={"Retry-After": str(retry_after)})
    if now_epoch - throttle.window_started_at >= settings.login_window_seconds:
        throttle.attempts = 0
        throttle.window_started_at = now_epoch
        throttle.locked_until = 0
    token_hash = hmac.new(settings.jwt_secret.encode("utf-8"), body.token.encode("utf-8"), hashlib.sha256).hexdigest()
    reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    expires_at = reset.expires_at if reset else None
    if expires_at is not None and expires_at.tzinfo is None:
        # SQLite drops timezone metadata on round-trip; persisted values are UTC.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not reset or reset.consumed_at is not None or expires_at <= now:
        throttle.attempts += 1
        throttle.updated_at = now
        if throttle.attempts >= settings.login_max_attempts:
            throttle.locked_until = now_epoch + settings.login_lockout_seconds
        db.commit()
        raise HTTPException(400, "Reset token is invalid, expired, or already used")
    account = db.scalar(select(User).where(User.id == reset.user_id).with_for_update())
    if not account:
        db.commit()
        raise HTTPException(400, "Reset token is invalid, expired, or already used")
    reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash).with_for_update())
    expires_at = reset.expires_at if reset else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not reset or reset.user_id != account.id or reset.consumed_at is not None or expires_at <= now:
        throttle.attempts += 1
        throttle.updated_at = now
        if throttle.attempts >= settings.login_max_attempts:
            throttle.locked_until = now_epoch + settings.login_lockout_seconds
        db.commit()
        raise HTTPException(400, "Reset token is invalid, expired, or already used")
    reset.consumed_at = now
    account.password_hash = hash_password(body.new_password)
    account.token_version += 1
    db.delete(throttle)
    record_audit(db, None, "password_reset_completed", None, {"account_id": account.id, "reset_token_id": reset.id})
    db.commit()
    return {"status": "password_updated", "sign_in_message": "Password updated. Sign in with the new password. Suspended accounts still require reviewer reactivation."}

@app.post("/api/cases")
def create_case(body: CaseCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not body.consent:
        raise HTTPException(400, "Consent is required before case processing")
    validate_external_source_consent(body.consent_version, body.rdap_consent)
    title = body.title.strip()
    if len(title) < 3:
        raise HTTPException(400, "Case title must contain at least 3 non-space characters")
    case = Case(case_ref=f"RC-{secrets.token_hex(4).upper()}", title=title, input_kind=body.input_kind, submitted_text=body.submitted_text, status="queued", consent_version=current_consent_version(), external_source_consent=body.rdap_consent, consented_at=datetime.now(timezone.utc), created_by=user.id)
    db.add(case)
    db.flush()
    digest = hashlib.sha256(body.submitted_text.encode("utf-8")).hexdigest()
    db.add(Evidence(case_id=case.id, source_name="User submission", source_type="submitted_material", source_ref=f"sha256:{digest}", claim="Submitted material received for investigation", outcome="result", excerpt="Original submitted material is access controlled and retained according to policy.", authority="user_submitted", details={"sha256": digest, "input_kind": body.input_kind}))
    db.add(ProcessingJob(case_id=case.id))
    record_audit(db, user.id, "case_created", case.id, {"consent_version": body.consent_version, "input_kind": body.input_kind, "external_source_consent": body.rdap_consent})
    db.commit()
    db.refresh(case)
    return serialize_case(case, redact_personal=user.role not in {"investigator", "reviewer", "admin"})


def persist_uploaded_case(
    db: Session,
    user: User,
    title: str,
    consent_version: str,
    rdap_consent: bool,
    content: bytes,
    media_type: str,
) -> Case:
    """Store a private upload and commit its case atomically with compensation on failure."""
    suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "application/pdf": ".pdf"}[media_type]
    stored_name = secrets.token_hex(24) + suffix
    ensure_upload_storage()
    encryption_key = decode_upload_encryption_key(settings.upload_encryption_key)
    if encryption_key is None and settings.app_environment != "testing":
        raise RuntimeError("Set UPLOAD_ENCRYPTION_KEY before storing uploaded files")
    store_upload(stored_name, content, encryption_key)
    digest = hashlib.sha256(content).hexdigest()
    case = Case(case_ref=f"RC-{secrets.token_hex(4).upper()}", title=title, input_kind="file", submitted_text=None, status="queued", consent_version=current_consent_version(), external_source_consent=rdap_consent, consented_at=datetime.now(timezone.utc), created_by=user.id)
    try:
        db.add(case)
        db.flush()
        storage_excerpt = (
            "File contents are application-encrypted in private storage and are not served through a public URL."
            if encryption_key is not None
            else "Test-only mode permits unencrypted synthetic fixtures; this file remains in private storage and is not served through a public URL."
        )
        db.add(Evidence(case_id=case.id, source_name="Private upload", source_type="uploaded_file", source_ref=f"sha256:{digest}", claim="Uploaded file received; OCR/text extraction is pending", outcome="not_checked", excerpt=storage_excerpt, authority="user_submitted", details={"sha256": digest, "stored_name": stored_name, "media_type": media_type, "size": len(content)}))
        db.add(ProcessingJob(case_id=case.id))
        record_audit(db, user.id, "file_uploaded", case.id, {"media_type": media_type, "sha256": digest, "consent_version": consent_version, "external_source_consent": rdap_consent})
        db.commit()
    except Exception:
        db.rollback()
        try:
            delete_upload(stored_name)
        except Exception as cleanup_error:
            upload_log.warning("Could not remove uncommitted private upload (error=%s)", type(cleanup_error).__name__)
        raise
    db.refresh(case)
    return case

@app.post("/api/cases/upload")
async def upload_case(title: str = Form(min_length=3, max_length=240), consent_version: str = Form(min_length=1, max_length=40), consent: bool = Form(...), rdap_consent: bool = Form(False), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not consent:
        raise HTTPException(400, "Consent is required before case processing")
    validate_external_source_consent(consent_version, rdap_consent)
    title = title.strip()
    if len(title) < 3:
        raise HTTPException(400, "Case title must contain at least 3 non-space characters")
    allowed = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(415, "Only PNG, JPEG, WEBP, and PDF files are accepted")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "File exceeds configured upload size limit")
    if not content:
        raise HTTPException(400, "Uploaded file is empty")
    if not content_matches_type(content, file.content_type):
        raise HTTPException(415, "File contents do not match the declared file type")
    case = persist_uploaded_case(db, user, title, consent_version, rdap_consent, content, file.content_type)
    return serialize_case(case, redact_personal=user.role not in {"investigator", "reviewer", "admin"})

@app.get("/api/cases")
def list_cases(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Case)
    if user.role == "personal":
        query = query.where(Case.created_by == user.id)
    cases = db.scalars(query.order_by(Case.created_at.desc()).limit(200)).all()
    result = []
    for case in cases:
        data = serialize_case(case, redact_personal=user.role not in {"investigator", "reviewer", "admin"})
        if user.role == "personal":
            data["title"] = case.title
        data["links"] = [] if user.role == "personal" else [serialize_link(link, redact=user.role not in {"investigator", "reviewer", "admin"}) for link in db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))).all()]
        result.append(data)
    record_audit(db, user.id, "case_list_accessed", None, {"case_count": len(cases)})
    db.commit()
    return result

@app.get("/api/processing-status")
def processing_status(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Small polling payload; avoids repeated full-case reads and audit events."""
    rows = db.execute(
        select(
            ProcessingJob.case_id.label("case_id"),
            Case.status.label("case_status"),
            ProcessingJob.status.label("job_status"),
            ProcessingJob.attempts.label("attempts"),
            ProcessingJob.last_error.label("last_error"),
        )
        .join(Case, Case.id == ProcessingJob.case_id)
        .where(Case.created_by == user.id if user.role == "personal" else True)
        .order_by(Case.created_at.desc())
        .limit(200)
    ).mappings().all()
    safe_error = (
        "Processing could not complete. Check that the file is valid and within the stated limits. "
        "An investigator can retry processing; if it fails again, provide the case reference to the operator."
    )
    return {"items": [
        {
            "case_id": row["case_id"],
            "case_status": row["case_status"],
            "status": row["job_status"],
            "attempts": row["attempts"],
            "error": safe_error if row["last_error"] else None,
        }
        for row in rows
    ]}

@app.get("/api/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    case = db.get(Case, case_id)
    if not case or (user.role == "personal" and case.created_by != user.id):
        raise HTTPException(404, "Case not found")
    record_audit(db, user.id, "case_accessed", case.id)
    db.commit()
    db.refresh(case)
    result = serialize_case(case, include_text=user.role in {"investigator", "reviewer", "admin"}, redact_personal=user.role not in {"investigator", "reviewer", "admin"})
    if user.role == "personal":
        result.update(title=case.title, submitted_text=case.submitted_text)
    result["timeline"] = [{"action": a.action, "actor_id": None if user.role == "personal" else a.actor_id, "detail": {} if user.role == "personal" else redact_data(a.detail) if user.role not in {"investigator", "reviewer", "admin"} else a.detail, "created_at": a.created_at.isoformat()} for a in db.scalars(select(AuditEvent).where(AuditEvent.case_id == case.id).order_by(AuditEvent.created_at)).all()]
    result["links"] = [] if user.role == "personal" else [serialize_link(link, redact=user.role not in {"investigator", "reviewer", "admin"}) for link in db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))).all()]
    result["human_dispositions"] = [serialize_disposition(item, redact=user.role not in {"investigator", "reviewer", "admin"}) for item in db.scalars(select(HumanDisposition).where(HumanDisposition.case_id == case.id).order_by(HumanDisposition.created_at)).all()]
    redact = user.role not in {"investigator", "reviewer", "admin"}
    result["findings"] = [serialize_finding(item, redact=redact) for item in db.scalars(select(SystemFinding).where(SystemFinding.case_id == case.id, SystemFinding.active.is_(True)).order_by(SystemFinding.created_at, SystemFinding.id)).all()]
    job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case.id))
    result["processing"] = {
        "status": job.status,
        "attempts": job.attempts,
        # Worker exception text may include machine paths or input-derived data.
        # Keep diagnostics in protected service logs; expose only safe next steps.
        "error": (
            "Processing could not complete. Check that the file is valid and within the stated limits. "
            "An investigator can retry processing; if it fails again, provide the case reference to the operator."
            if job.last_error
            else None
        ),
    } if job else None
    return result

@app.post("/api/cases/{case_id}/retry-processing")
def retry_processing(case_id: int, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case.id))
    if not job:
        raise HTTPException(409, "No processing job exists for this case")
    if job.status == "processing":
        raise HTTPException(409, "Case processing is already in progress")
    job.status = "queued"
    job.last_error = ""
    case.status = "queued"
    record_audit(db, user.id, "processing_retried", case.id, {})
    db.commit()
    return {"status": "queued"}

def serialize_link(link: CaseLink, redact: bool = False):
    reasons = [redact_link_reason(reason) for reason in link.reasons] if redact else link.reasons
    return {"id": link.id, "left_case_id": link.left_case_id, "right_case_id": link.right_case_id, "rule_version": link.rule_version, "strength": link.strength, "reasons": reasons, "review_status": link.review_status, "created_at": link.created_at.isoformat()}

def shared_case_identifiers(db: Session, left_case_id: int, right_case_id: int) -> set[tuple[str, str]]:
    left = db.scalars(select(Entity).where(Entity.case_id == left_case_id, Entity.review_status != "rejected")).all()
    right = db.scalars(select(Entity).where(Entity.case_id == right_case_id, Entity.review_status != "rejected")).all()
    left_keys = {(item.entity_type, item.normalized_value) for item in left if item.entity_type in MATCHABLE_TYPES}
    right_keys = {(item.entity_type, item.normalized_value) for item in right if item.entity_type in MATCHABLE_TYPES}
    return left_keys & right_keys

@app.post("/api/cases/{case_id}/entities/{entity_id}/review")
def review_entity(case_id: int, entity_id: int, body: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    entity = db.get(Entity, entity_id)
    if not entity or entity.case_id != case_id:
        raise HTTPException(404, "Entity not found")
    entity.review_status = body.status
    db.flush()
    record_audit(db, user.id, "entity_reviewed", case_id, {"entity_id": entity_id, "status": body.status, "rationale": body.rationale})
    if body.status == "rejected":
        links = db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case_id, CaseLink.right_case_id == case_id))).all()
        for link in links:
            if link.review_status in {"rejected", "stale"}:
                continue
            if not shared_case_identifiers(db, link.left_case_id, link.right_case_id):
                previous_status = link.review_status
                link.review_status = "stale"
                record_audit(db, user.id, "case_link_withdrawn_after_entity_rejection", case_id, {"link_id": link.id, "previous_status": previous_status, "rule_version": link.rule_version})
    if entity.entity_type in {"company_claim", "job_title_claim"}:
        check_vacancy(db, entity.case)
    rebuild_system_findings(db, entity.case)
    record_audit(db, user.id, "system_findings_recomputed", case_id, {"rule_version": FINDING_RULE_VERSION, "trigger": "entity_review"})
    enqueue_graph_sync(db, case_id)
    db.commit()
    return serialize_entity(entity)

@app.post("/api/cases/{case_id}/evidence/{evidence_id}/review")
def review_evidence(case_id: int, evidence_id: int, body: EvidenceReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    item = db.get(Evidence, evidence_id)
    if not item or item.case_id != case_id:
        raise HTTPException(404, "Evidence item not found")
    if (item.details or {}).get("source_record_withdrawn") is True and body.status in {"relevant", "contradicts"}:
        raise HTTPException(409, "The source record was withdrawn. Add and review a current source record before treating this evidence as relevant or contradictory.")
    item.review_status = body.status
    item.review_reason = body.rationale
    item.reviewed_by = user.id
    item.reviewed_at = datetime.now(timezone.utc)
    record_audit(db, user.id, "evidence_reviewed", case_id, {"evidence_id": evidence_id, "status": body.status, "rationale": body.rationale})
    case = db.get(Case, case_id)
    rebuild_system_findings(db, case)
    record_audit(db, user.id, "system_findings_recomputed", case_id, {"rule_version": FINDING_RULE_VERSION, "trigger": "evidence_review"})
    enqueue_graph_sync(db, case_id)
    db.commit()
    return serialize_evidence(item, redact=user.role not in {"investigator", "reviewer", "admin"})

@app.post("/api/cases/{case_id}/disposition")
def disposition(case_id: int, body: DispositionRequest, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    selected_ids = sorted(set(body.evidence_ids))
    evidence = db.scalars(select(Evidence).where(Evidence.case_id == case_id, Evidence.id.in_(selected_ids))).all() if selected_ids else []
    if len(evidence) != len(selected_ids):
        raise HTTPException(400, "Every supporting evidence item must belong to this case")
    requires_review = body.disposition in {"confirmed_authoritative", "evidence_supports_concern"}
    if requires_review:
        if any((item.details or {}).get("source_record_withdrawn") is True for item in evidence):
            raise HTTPException(400, "Withdrawn source records cannot support a stronger human disposition")
        supporting = [item for item in evidence if item.review_status == "relevant" and item.outcome == "result"]
        if not supporting:
            raise HTTPException(400, "A stronger disposition requires investigator-reviewed relevant evidence with a result")
        if body.disposition == "confirmed_authoritative" and not any(item.authority in {"government", "platform_action", "authoritative_source"} for item in supporting):
            raise HTTPException(400, "Confirmed by an authoritative source requires relevant, result-bearing evidence from an authoritative source")
    item = HumanDisposition(case_id=case_id, disposition=body.disposition, rationale=body.rationale, evidence_ids=selected_ids, status="pending_review" if requires_review else "recorded", proposed_by=user.id)
    db.add(item)
    db.flush()
    record_audit(db, user.id, "human_disposition_submitted", case_id, {"disposition_id": item.id, "disposition": body.disposition, "status": item.status, "evidence_ids": selected_ids})
    db.commit()
    db.refresh(item)
    return serialize_disposition(item, redact=False)

@app.get("/api/dispositions/pending")
def pending_dispositions(db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    items = db.scalars(select(HumanDisposition).where(HumanDisposition.status == "pending_review").order_by(HumanDisposition.created_at).limit(500)).all()
    result = []
    for item in items:
        case = db.get(Case, item.case_id)
        if case:
            supporting = db.scalars(select(Evidence).where(Evidence.case_id == case.id, Evidence.id.in_(item.evidence_ids or []))).all() if item.evidence_ids else []
            # This endpoint is reviewer-only. Independent review requires the
            # actual rationale and cited source material, not analyst-masked data.
            result.append({**serialize_disposition(item, redact=False), "case_ref": case.case_ref, "case_title": case.title, "proposer_id": item.proposed_by, "evidence": [serialize_evidence(record, redact=False) for record in supporting]})
    record_audit(db, user.id, "pending_dispositions_accessed", None, {"disposition_count": len(result)})
    db.commit()
    return result

@app.patch("/api/dispositions/{disposition_id}/review")
def review_disposition(disposition_id: int, body: DispositionReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    item = db.get(HumanDisposition, disposition_id)
    if not item:
        raise HTTPException(404, "Human disposition not found")
    if item.status != "pending_review":
        raise HTTPException(409, "This disposition is no longer awaiting review")
    if item.proposed_by == user.id:
        raise HTTPException(403, "A separate authorized reviewer must review this disposition")
    if body.status == "approved" and item.disposition in {"confirmed_authoritative", "evidence_supports_concern"}:
        supporting = db.scalars(select(Evidence).where(Evidence.case_id == item.case_id, Evidence.id.in_(item.evidence_ids or []))).all() if item.evidence_ids else []
        if not supporting or any(
            record.review_status != "relevant"
            or record.outcome != "result"
            or (record.details or {}).get("source_record_withdrawn") is True
            for record in supporting
        ):
            raise HTTPException(409, "Supporting evidence changed or no longer meets the relevance and result requirements")
        if item.disposition == "confirmed_authoritative" and not any(record.authority in {"government", "platform_action", "authoritative_source"} for record in supporting):
            raise HTTPException(409, "The cited evidence no longer meets the authoritative-source requirement")
    item.status = body.status
    item.reviewed_by = user.id
    item.review_rationale = body.rationale
    item.reviewed_at = datetime.now(timezone.utc)
    record_audit(db, user.id, "human_disposition_reviewed", item.case_id, {"disposition_id": item.id, "status": body.status, "rationale": body.rationale})
    db.commit()
    return serialize_disposition(item, redact=False)

@app.get("/api/cases/{case_id}/report")
def report(case_id: int, db: Session = Depends(get_db), user: User = Depends(current_user), format: str = "json"):
    if format not in {"json", "markdown"}:
        raise HTTPException(400, "Report format must be json or markdown")
    case = db.get(Case, case_id)
    if not case or (user.role == "personal" and case.created_by != user.id):
        raise HTTPException(404, "Case not found")
    # Default export masks contact identifiers, including the original submission text.
    entities = []
    for entity in case.entities:
        value = mask_identifier(entity.entity_type, entity.raw_value)
        entities.append({"type": entity.entity_type, "value": value, "review_status": entity.review_status, "source_location": entity.source_location, "source_start_char": entity.source_start_char, "source_end_char": entity.source_end_char, "extraction_confidence": entity.extraction_confidence, "extraction_uncertainty": entity.extraction_uncertainty, "excerpt": "[source excerpt restricted for privacy]"})
    evidence = [serialize_evidence(item, redact=True) for item in case.evidence]
    human_dispositions = db.scalars(select(HumanDisposition).where(HumanDisposition.case_id == case.id).order_by(HumanDisposition.created_at)).all()
    audits = db.scalars(select(AuditEvent).where(AuditEvent.case_id == case.id).order_by(AuditEvent.created_at)).all()
    findings = db.scalars(select(SystemFinding).where(SystemFinding.case_id == case.id, SystemFinding.active.is_(True)).order_by(SystemFinding.created_at, SystemFinding.id)).all()
    finding_history = db.scalars(select(SystemFinding).where(SystemFinding.case_id == case.id).order_by(SystemFinding.created_at, SystemFinding.id)).all()
    links = [] if user.role == "personal" else db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))).all()
    document = {
        "case_ref": case.case_ref,
        "title": "[case title restricted for privacy]",
        "posting_prediction": case.posting_prediction,
        "assessment": case.assessment,
        "consent": {"version": case.consent_version, "external_rdap_domain_lookup": case.external_source_consent},
        "created_at": case.created_at.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_summary": {"total": len(evidence), "by_outcome": {outcome: sum(item["outcome"] == outcome for item in evidence) for outcome in sorted({item["outcome"] for item in evidence})}, "by_review_status": {status: sum(item["review_status"] == status for item in evidence) for status in sorted({item["review_status"] for item in evidence})}},
        "limitations": "System findings are investigative leads. They do not establish wrongdoing. No adverse evidence found, empty lookups, unavailable checks, and failed checks are not proof of legitimacy or fraud. Human investigator dispositions are separate from system assessment.",
        "entities": entities,
        "evidence": evidence,
        "machine_findings": [serialize_finding(item, redact=True) for item in findings],
        "finding_history": [dict(serialize_finding(item, redact=True), active=item.active, superseded_at=item.superseded_at.isoformat() if item.superseded_at else None) for item in finding_history],
        "campaign_links": [serialize_link(item, redact=True) for item in links],
        "campaign_link_note": "Campaign connections are investigative leads. Reused identifiers do not establish that a person or organization acted improperly.",
        "human_dispositions": [serialize_disposition(item, redact=True) for item in human_dispositions],
        "timeline": [{"action": event.action, "actor_type": "workspace_user" if event.actor_id is not None else "system", "occurred_at": event.created_at.isoformat(), "details": {} if user.role == "personal" else redact_data(event.detail)} for event in audits],
        "rule_versions": sorted({link.rule_version for link in links}),
    }
    record_audit(db, user.id, "report_exported", case.id, {"format": format, "redacted": True})
    db.commit()
    if format == "markdown":
        return PlainTextResponse(
            render_markdown_report(document),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{case.case_ref}-report.md"'},
        )
    return JSONResponse(document, headers={"Content-Disposition": f'attachment; filename="{case.case_ref}-report.json"'})

@app.post("/api/cases/{case_id}/link/refresh")
def refresh_links(case_id: int, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    linking_started = time.perf_counter()
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    version = rule_version(settings.campaign_link_threshold)
    existing_links = db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id), CaseLink.rule_version == version)).all()
    matchable = {(e.entity_type, e.normalized_value) for e in case.entities if e.entity_type in MATCHABLE_TYPES and e.review_status != "rejected"}
    predicates = [and_(Entity.entity_type == kind, Entity.normalized_value == value) for kind, value in matchable]
    if not predicates:
        for link in existing_links:
            if link.review_status not in {"rejected", "stale"}:
                link.review_status = "stale"
                record_audit(db, user.id, "case_link_withdrawn_after_recompute", case.id, {"link_id": link.id, "rule_version": version})
        link_duration_ms = round((time.perf_counter() - linking_started) * 1000, 3)
        record_audit(db, user.id, "campaign_links_recomputed", case.id, {"matched_case_count": 0, "rule_version": version, "threshold": settings.campaign_link_threshold, "campaign_linking_ms": link_duration_ms})
        enqueue_graph_sync(db, case.id)
        db.commit()
        return {"links": [], "threshold": settings.campaign_link_threshold, "note": "No matchable identifiers remain. Existing links for this rule version were withdrawn; historical review events remain in the audit timeline."}
    matches = db.execute(select(Entity.normalized_value, Entity.entity_type, Entity.case_id).where(Entity.case_id != case.id, Entity.review_status != "rejected", or_(*predicates))).all()
    grouped: dict[int, set[tuple[str, str]]] = {}
    for value, kind, other_id in matches:
        if kind in MATCHABLE_TYPES:
            grouped.setdefault(other_id, set()).add((kind, value))
    links = []
    matched_case_ids = set(grouped)
    for link in existing_links:
        other_case_id = link.right_case_id if link.left_case_id == case.id else link.left_case_id
        if other_case_id not in matched_case_ids and link.review_status not in {"rejected", "stale"}:
            previous_status = link.review_status
            link.review_status = "stale"
            record_audit(db, user.id, "case_link_withdrawn_after_recompute", case.id, {"link_id": link.id, "previous_status": previous_status, "rule_version": version})
    for other_id, matches_for_case in grouped.items():
        left, right = sorted((case.id, other_id))
        strength, reasons = score_matches(matches_for_case)
        state = link_state(strength, settings.campaign_link_threshold)
        link = db.scalar(select(CaseLink).where(CaseLink.left_case_id == left, CaseLink.right_case_id == right, CaseLink.rule_version == version))
        if link is None:
            link = CaseLink(left_case_id=left, right_case_id=right, rule_version=version, strength=strength, reasons=reasons, review_status=state)
            db.add(link)
        else:
            link.strength = strength
            link.reasons = reasons
            if link.review_status in {"proposed", "low_signal", "stale"}:
                previous_status = link.review_status
                link.review_status = state
                if previous_status == "stale":
                    record_audit(db, user.id, "case_link_reactivated_after_recompute", case.id, {"link_id": link.id, "rule_version": version})
        links.append(link)
    link_duration_ms = round((time.perf_counter() - linking_started) * 1000, 3)
    record_audit(db, user.id, "campaign_links_recomputed", case.id, {"matched_case_count": len(links), "rule_version": version, "threshold": settings.campaign_link_threshold, "campaign_linking_ms": link_duration_ms})
    enqueue_graph_sync(db, case.id)
    db.commit()
    return {"links": [serialize_link(x) for x in links], "threshold": settings.campaign_link_threshold, "note": "Links are investigative leads. Repeated identifiers can be misreported, compromised, or reused and do not establish wrongdoing."}

@app.post("/api/cases/{case_id}/links/{link_id}/review")
def review_link(case_id: int, link_id: int, body: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    link = db.get(CaseLink, link_id)
    if not link or case_id not in {link.left_case_id, link.right_case_id}:
        raise HTTPException(404, "Case link not found")
    if link.review_status not in {"proposed", "low_signal", "confirmed", "rejected"}:
        raise HTTPException(409, "This link is stale and must be recomputed before review")
    if body.status not in {"confirmed", "rejected"}:
        raise HTTPException(400, "A link review must confirm or reject the proposed relationship")
    link.review_status = body.status
    record_audit(db, user.id, "case_link_reviewed", case_id, {"link_id": link.id, "status": body.status, "rationale": body.rationale})
    enqueue_graph_sync(db, link.left_case_id)
    enqueue_graph_sync(db, link.right_case_id)
    db.commit()
    return serialize_link(link)

@app.get("/api/campaigns")
def list_campaigns(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == "personal":
        raise HTTPException(403, "Workspace access is required for campaign analysis")
    redact = user.role not in {"investigator", "reviewer", "admin"}
    active_links = db.scalars(select(CaseLink).where(CaseLink.review_status.in_({"proposed", "confirmed", "low_signal"})).order_by(CaseLink.created_at.desc()).limit(2000)).all()
    adjacency: dict[int, set[int]] = {}
    links_by_case: dict[int, list[CaseLink]] = {}
    for link in active_links:
        adjacency.setdefault(link.left_case_id, set()).add(link.right_case_id)
        adjacency.setdefault(link.right_case_id, set()).add(link.left_case_id)
        links_by_case.setdefault(link.left_case_id, []).append(link)
        links_by_case.setdefault(link.right_case_id, []).append(link)

    entity_cache: dict[int, list[Entity]] = {}
    evidence_cache: dict[int, list[Evidence]] = {}
    groups = []
    visited: set[int] = set()
    for start_id in sorted(adjacency):
        if start_id in visited:
            continue
        pending = [start_id]
        member_ids: set[int] = set()
        while pending:
            case_id = pending.pop()
            if case_id in member_ids:
                continue
            member_ids.add(case_id)
            visited.add(case_id)
            pending.extend(adjacency.get(case_id, set()) - member_ids)
        group_links = sorted({link.id: link for case_id in member_ids for link in links_by_case.get(case_id, []) if link.left_case_id in member_ids and link.right_case_id in member_ids}.values(), key=lambda item: item.id)
        cases = db.scalars(select(Case).where(Case.id.in_(member_ids)).order_by(Case.created_at)).all()
        for case in cases:
            entity_cache[case.id] = case.entities
            evidence_cache[case.id] = case.evidence
        pair_details = []
        for link in group_links:
            left_entities = entity_cache[link.left_case_id]
            right_entities = entity_cache[link.right_case_id]
            left_by_key = {(item.entity_type, item.normalized_value): item for item in left_entities if item.review_status != "rejected"}
            right_by_key = {(item.entity_type, item.normalized_value): item for item in right_entities if item.review_status != "rejected"}
            shared_keys = set(left_by_key) & set(right_by_key)
            shared_fingerprints = {hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest() for kind, value in shared_keys}
            matched_entities = [{"case_id": link.left_case_id, **serialize_entity(left_by_key[key], redact)} for key in sorted(shared_keys)]
            matched_entities.extend({"case_id": link.right_case_id, **serialize_entity(right_by_key[key], redact)} for key in sorted(shared_keys))
            related_evidence = []
            failed_checks = []
            for case_id in (link.left_case_id, link.right_case_id):
                for item in evidence_cache[case_id]:
                    details = item.details or {}
                    key = (details.get("matched_entity_type"), details.get("matched_normalized_value"))
                    if key not in shared_keys and details.get("entity_fingerprint") not in shared_fingerprints:
                        continue
                    serialized = serialize_evidence(item, redact)
                    related_evidence.append(serialized)
                    if item.outcome in {"no_result", "unavailable", "error", "not_checked"}:
                        failed_checks.append(serialized)
            pair_details.append({**serialize_link(link, redact), "matched_entities": matched_entities, "related_evidence": related_evidence, "empty_or_failed_checks": failed_checks})
        ref = "CL-" + hashlib.sha256(",".join(map(str, sorted(member_ids))).encode("ascii")).hexdigest()[:10].upper()
        groups.append({
            "campaign_ref": ref,
            "classification": "possible_campaign_lead" if any(link.review_status in {"proposed", "confirmed"} for link in group_links) else "low_signal_lead",
            "case_count": len(cases),
            "cases": [{"id": case.id, "case_ref": case.case_ref, "title": "[case title restricted for privacy]" if redact else case.title, "assessment": case.assessment, "created_at": case.created_at.isoformat()} for case in cases],
            "links": pair_details,
            "rule_versions": sorted({link.rule_version for link in group_links}),
            "strength": max((link.strength for link in group_links), default=0),
            "review_statuses": sorted({link.review_status for link in group_links}),
            "note": "A linked group is an investigative lead. Shared identifiers may be reused, compromised, or misreported; this does not establish wrongdoing.",
        })
    record_audit(db, user.id, "campaign_groups_accessed", None, {"group_count": len(groups)})
    db.commit()
    return sorted(groups, key=lambda group: (-group["strength"], group["campaign_ref"]))

@app.get("/api/graph")
def graph(db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    record_audit(db, user.id, "evidence_graph_accessed")
    db.commit()
    pending_projection = db.scalar(select(GraphProjectionOutbox.id).where(GraphProjectionOutbox.status != "completed").limit(1))
    if graph_store.configured() and not pending_projection:
        try:
            data = graph_store.graph_data(limit=100)
            for node in data.get("nodes", []):
                if node.get("type") == "evidence":
                    node["label"] = f"{node.get('source_type', 'source')} · {node.get('outcome', 'unknown')}"
                    if node.get("source_ref"):
                        node["source_ref"] = redact_source_ref(node["source_ref"])
                elif node.get("type") != "case" and "label" in node:
                    # Re-mask values at read time so old Neo4j projections do not leak
                    # identifiers written before a masking-rule change.
                    node["label"] = mask_identifier(node.get("type", ""), node["label"])
            for edge in data.get("edges", []):
                if "reasons" in edge:
                    edge["reasons"] = [redact_link_reason(reason) for reason in edge["reasons"]]
            return {**data, "projection": "neo4j", "note": "Graph is an investigative aid; links are not proof of wrongdoing."}
        except Exception as exc:
            import logging
            logging.getLogger("casework.graph").error("Neo4j read failed; serving PostgreSQL-derived graph (%s)", type(exc).__name__)
    cases = db.scalars(select(Case).order_by(Case.created_at.desc()).limit(100)).all()
    nodes, edges = [], []
    for case in cases:
        case_node = f"case:{case.id}"
        nodes.append({"id": case_node, "type": "case", "label": case.case_ref, "case_id": case.id, "created_at": case.created_at.isoformat() if case.created_at else None})
        entity_ids = {}
        for entity in case.entities:
            node_id = graph_store.entity_node_id(f"{entity.entity_type}:{entity.normalized_value}")
            entity_ids[f"{entity.entity_type}:{entity.normalized_value}"] = node_id
            if not any(n["id"] == node_id for n in nodes):
                value = mask_identifier(entity.entity_type, entity.raw_value)
                nodes.append({"id": node_id, "type": entity.entity_type, "label": value, "review_status": entity.review_status})
            edges.append({"from": case_node, "to": node_id, "kind": "contains_identifier", "review_status": entity.review_status})
        for item in case.evidence:
            serialized = graph_store.serialize_evidence(item)
            matched_entity_key = serialized.pop("matched_entity_key")
            evidence_id = serialized.pop("evidence_key")
            label = f"{serialized['source_type']} · {serialized['outcome']}"
            nodes.append({"id": evidence_id, "type": "evidence", "label": label, **serialized})
            edges.append({"from": case_node, "to": evidence_id, "kind": "has_evidence", "review_status": item.review_status})
            entity_id = entity_ids.get(matched_entity_key)
            if entity_id:
                edges.append({"from": evidence_id, "to": entity_id, "kind": "checks_identifier", "review_status": item.review_status})
    visible_case_ids = [case.id for case in cases]
    for link in db.scalars(select(CaseLink).where(CaseLink.left_case_id.in_(visible_case_ids), CaseLink.right_case_id.in_(visible_case_ids))).all():
        edges.append({"from": f"case:{link.left_case_id}", "to": f"case:{link.right_case_id}", "kind": "proposed_campaign_link", "review_status": link.review_status, "strength": link.strength, "rule_version": link.rule_version, "reasons": [redact_link_reason(reason) for reason in link.reasons]})
    return {"nodes": nodes, "edges": edges, "projection": "postgresql-derived", "note": "Graph is an investigative aid; links are not proof of wrongdoing."}

@app.get("/api/evidence-corpus")
def list_evidence_corpus(db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    records = db.scalars(select(SourceRecord).order_by(SourceRecord.created_at.desc()).limit(500)).all()
    record_audit(db, user.id, "evidence_corpus_accessed", None, {"record_count": len(records)})
    db.commit()
    return [{"record_id": r.record_id, "entity_type": r.entity_type, "normalized_value": r.normalized_value, "source_name": r.source_name, "source_type": r.source_type, "source_ref": r.source_ref, "claim": r.claim, "outcome": r.outcome, "excerpt": r.excerpt, "authority": r.authority, "retrieved_at": r.retrieved_at.isoformat(), "active": r.active, "retired_at": r.retired_at.isoformat() if r.retired_at else None, "retirement_reason": r.retirement_reason} for r in records]

@app.post("/api/evidence-corpus")
def add_evidence_record(body: SourceRecordCreate, db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    authoritative_types = {"government": {"government"}, "platform_action": {"platform"}, "authoritative_source": {"government", "platform", "company_official"}}
    permitted_types = authoritative_types.get(body.authority)
    if permitted_types and body.source_type not in permitted_types:
        raise HTTPException(400, "The selected authority level does not match the source category")
    if body.authority in authoritative_types and body.outcome == "result" and not body.source_ref.strip():
        raise HTTPException(400, "A traceable source reference is required for authoritative evidence")
    normalized = normalize(body.entity_type, body.value)
    if len(normalized) < 2:
        raise HTTPException(400, "The normalized identifier is too short to index safely")
    duplicate = db.scalar(select(SourceRecord).where(SourceRecord.entity_type == body.entity_type, SourceRecord.normalized_value == normalized, SourceRecord.source_ref == body.source_ref, SourceRecord.claim == body.claim, SourceRecord.active.is_(True)))
    if duplicate:
        raise HTTPException(409, "An equivalent corpus entry already exists")
    record_id = f"LOCAL-{secrets.token_hex(8).upper()}"
    record = SourceRecord(record_id=record_id, entity_type=body.entity_type, normalized_value=normalized, source_name=body.source_name, source_type=body.source_type, source_ref=body.source_ref, claim=body.claim, outcome=body.outcome, excerpt=body.excerpt, authority=body.authority, retrieved_at=datetime.now(timezone.utc), created_by=user.id)
    db.add(record)
    record_audit(db, user.id, "evidence_corpus_record_created", None, {"record_id": record_id, "entity_type": body.entity_type, "outcome": body.outcome, "authority": body.authority})
    db.commit()
    db.refresh(record)
    return {"record_id": record.record_id, "entity_type": record.entity_type, "normalized_value": record.normalized_value, "source_name": record.source_name, "source_type": record.source_type, "source_ref": record.source_ref, "claim": record.claim, "outcome": record.outcome, "excerpt": record.excerpt, "authority": record.authority, "retrieved_at": record.retrieved_at.isoformat()}

@app.post("/api/evidence-corpus/{record_id}/retire")
def retire_evidence_record(record_id: str, body: SourceRecordRetire, db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    record = db.scalar(select(SourceRecord).where(SourceRecord.record_id == record_id).with_for_update())
    if not record:
        raise HTTPException(404, "Evidence corpus record not found")
    if not record.active:
        raise HTTPException(409, "This evidence corpus record has already been retired")

    now = datetime.now(timezone.utc)
    record.active = False
    record.retired_at = now
    record.retired_by = user.id
    record.retirement_reason = body.rationale.strip()
    affected = db.scalars(select(Evidence).where(
        Evidence.source_type == "curated_local_corpus",
        Evidence.source_ref == record.record_id,
    )).all()
    cases: dict[int, Case] = {}
    affected_ids_by_case: dict[int, set[int]] = {}
    for item in affected:
        details = dict(item.details or {})
        details["source_record_withdrawn"] = True
        item.details = details
        previous_review = {
            "evidence_id": item.id,
            "review_status": item.review_status,
            "reviewed_by": item.reviewed_by,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        }
        item.review_status = "needs_review"
        item.review_reason = "The underlying curated source record was withdrawn. Re-check the original source before relying on this result."
        item.reviewed_by = user.id
        item.reviewed_at = now
        record_audit(db, user.id, "evidence_review_invalidated_by_source_retirement", item.case_id, {
            "source_record_id": record.record_id,
            "previous_review": previous_review,
            "new_review_status": "needs_review",
        })
        cases.setdefault(item.case_id, db.get(Case, item.case_id))
        affected_ids_by_case.setdefault(item.case_id, set()).add(item.id)

    db.flush()
    for case_id, evidence_ids in affected_ids_by_case.items():
        reopen_dispositions_for_evidence_ids(db, case_id, evidence_ids, record_id, user.id, trigger="source_record_retirement")
        case = cases[case_id]
        if case:
            rebuild_system_findings(db, case)
            record_audit(db, user.id, "system_findings_recomputed", case_id, {"rule_version": FINDING_RULE_VERSION, "trigger": "source_record_retirement", "source_record_id": record_id})
            enqueue_graph_sync(db, case_id)

    record_audit(db, user.id, "evidence_corpus_record_retired", None, {
        "record_id": record_id,
        "affected_evidence_count": len(affected),
        "affected_case_count": len(affected_ids_by_case),
    })
    db.commit()
    return {"record_id": record.record_id, "active": record.active, "retired_at": record.retired_at.isoformat(), "affected_evidence_count": len(affected), "affected_case_count": len(affected_ids_by_case)}
