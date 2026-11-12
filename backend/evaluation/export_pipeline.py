"""Export eligible persisted application results for an authorized evaluation set.

The input mapping contains private case references and gold labels. The output
contains only pseudonymous case IDs, labels, normalized extracted identifiers,
system outcomes, and measured pipeline durations. Both files belong in protected
storage outside the repository.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.campaign_rules import rule_version
from app.config import settings
from app.extract import normalize
from app.findings import RULE_VERSION as FINDING_RULE_VERSION
from app.models import AuditEvent, Case, CaseLink, Evidence, ProcessingJob, SourceRecord, SystemFinding
from app.source_adapters import LocalEvidenceCorpusAdapter
from evaluation.evaluate import score as score_rows


INPUT_FIELDS = {
    "case_ref",
    "case_id",
    "split",
    "campaign_id",
    "gold_entities",
    "gold_supported_entities",
    "gold_adverse_verdict",
}
HUMAN_MUTATION_ACTIONS = {
    "correction_applied",
    "case_link_reviewed",
    "processing_retried",
}
ENTITY_REVIEW_STATES = {"needs_review", "unreviewed", "confirmed", "rejected"}


def _pseudonymous_id(value: object, *, min_length: int = 8) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{%d,64}" % min_length, value):
        return False
    digits = sum(character.isdigit() for character in value)
    return (
        "@" not in value
        and not value.isdecimal()
        and (digits < 10 or digits / len(value) <= 0.75)
        and re.fullmatch(r"RC-[A-Fa-f0-9]{8}", value) is None
    )


def load_annotations(path: Path) -> list[dict]:
    rows: list[dict] = []
    seen_case_refs: set[str] = set()
    seen_case_ids: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"annotation line {line_no}: invalid JSON") from exc
        if not isinstance(row, dict) or set(row) != INPUT_FIELDS:
            raise ValueError(f"annotation line {line_no}: fields must be exactly {sorted(INPUT_FIELDS)}")
        case_ref = row["case_ref"]
        case_id = row["case_id"]
        if not isinstance(case_ref, str) or not re.fullmatch(r"RC-[A-Fa-f0-9]{8}", case_ref, re.IGNORECASE):
            raise ValueError(f"annotation line {line_no}: case_ref is invalid")
        case_ref = case_ref.upper()
        if not _pseudonymous_id(case_id) or case_id == case_ref:
            raise ValueError(f"annotation line {line_no}: case_id must be a pseudonymous non-contact identifier")
        if case_ref in seen_case_refs or case_id in seen_case_ids:
            raise ValueError(f"annotation line {line_no}: case references and pseudonymous IDs must be unique")
        if row["split"] not in {"train", "dev", "test"}:
            raise ValueError(f"annotation line {line_no}: split must be train, dev, or test")
        campaign_id = row["campaign_id"]
        if campaign_id is not None and not _pseudonymous_id(campaign_id, min_length=6):
            raise ValueError(f"annotation line {line_no}: campaign_id must be null or pseudonymous")
        if not isinstance(row["gold_adverse_verdict"], bool):
            raise ValueError(f"annotation line {line_no}: gold_adverse_verdict must be a JSON boolean")
        entities = row["gold_entities"]
        supported_entities = row["gold_supported_entities"]
        if not isinstance(entities, list) or any(
            not isinstance(entity, dict)
            or set(entity) != {"type", "value"}
            or not isinstance(entity["type"], str)
            or not entity["type"].strip()
            or not isinstance(entity["value"], str)
            or not entity["value"].strip()
            for entity in entities
        ):
            raise ValueError(f"annotation line {line_no}: gold_entities must contain only non-empty type/value strings")
        if not isinstance(supported_entities, list) or any(
            not isinstance(entity, dict)
            or set(entity) != {"type", "value"}
            or not isinstance(entity["type"], str)
            or not entity["type"].strip()
            or not isinstance(entity["value"], str)
            or not entity["value"].strip()
            for entity in supported_entities
        ):
            raise ValueError(f"annotation line {line_no}: gold_supported_entities must contain only non-empty type/value strings")
        row["gold_entities"] = [
            {"type": entity["type"], "value": normalize(entity["type"], entity["value"])}
            for entity in entities
        ]
        if any(not entity["value"] for entity in row["gold_entities"]):
            raise ValueError(f"annotation line {line_no}: gold entity values must normalize to non-empty strings")
        row["gold_supported_entities"] = [
            {"type": entity["type"], "value": normalize(entity["type"], entity["value"])}
            for entity in supported_entities
        ]
        gold_keys = {(entity["type"], entity["value"]) for entity in row["gold_entities"]}
        support_keys = [(entity["type"], entity["value"]) for entity in row["gold_supported_entities"]]
        if any(not value for _kind, value in support_keys) or len(set(support_keys)) != len(support_keys):
            raise ValueError(f"annotation line {line_no}: gold_supported_entities must normalize to unique non-empty claims")
        if not set(support_keys).issubset(gold_keys):
            raise ValueError(f"annotation line {line_no}: supported claims must also appear in gold_entities")
        seen_case_refs.add(case_ref)
        seen_case_ids.add(case_id)
        row["case_ref"] = case_ref
        rows.append(row)
    if not rows:
        raise ValueError("annotation mapping contains no records")
    return rows


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_utc(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _ensure_eligible(db: Session, case: Case) -> None:
    if any(entity.review_status not in ENTITY_REVIEW_STATES for entity in case.entities):
        raise ValueError("evaluation export rejected a case with an unsupported entity review state")
    if db.scalar(select(AuditEvent.id).where(
        AuditEvent.case_id == case.id,
        AuditEvent.action.in_(HUMAN_MUTATION_ACTIONS),
    ).limit(1)) is not None:
        raise ValueError("evaluation export rejected a case with human changes to pipeline inputs")


def _snapshot_key(value: bytes | None = None) -> bytes:
    key = value if value is not None else os.getenv("EVALUATION_SNAPSHOT_HMAC_KEY", "").encode("utf-8")
    if len(key) < 32:
        raise ValueError("set EVALUATION_SNAPSHOT_HMAC_KEY to a protected value of at least 32 bytes")
    return key


def _corpus_snapshot_hmac(db: Session, key: bytes) -> str:
    static_path = Path(__file__).parents[1] / "app" / "evidence_corpus.json"
    static_bytes = static_path.read_bytes() if static_path.exists() else b""
    persisted = db.scalars(select(SourceRecord).order_by(SourceRecord.record_id)).all()
    snapshot_rows = [{
        "record_id": item.record_id,
        "entity_type": item.entity_type,
        "normalized_value": item.normalized_value,
        "source_name": item.source_name,
        "source_type": item.source_type,
        "source_ref": item.source_ref,
        "claim": item.claim,
        "outcome": item.outcome,
        "authority": item.authority,
        "retrieved_at": _is_utc(item.retrieved_at),
    } for item in persisted]
    material = static_bytes + b"\n--persisted-local-corpus-v1--\n" + json.dumps(
        snapshot_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def export_rows(
    db: Session,
    annotations: list[dict],
    snapshot_key: bytes | None = None,
    *,
    graph_linking_enabled: bool = True,
) -> tuple[list[dict], dict]:
    """Join authorized gold labels to unchanged persisted pipeline outputs."""
    key = _snapshot_key(snapshot_key)
    if db.get_bind().dialect.name == "postgresql":
        if db.in_transaction():
            raise ValueError("evaluation export requires a fresh database session for a consistent read snapshot")
        db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    cases: dict[str, Case] = {}
    jobs: dict[str, ProcessingJob] = {}
    campaign_linking_ms: dict[int, float] = {}
    for row in annotations:
        case = db.scalar(select(Case).where(Case.case_ref == row["case_ref"]))
        if case is None or case.status != "completed":
            raise ValueError("evaluation export rejected a missing or incomplete case")
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case.id))
        if job is None or job.status != "completed" or job.processing_ms is None:
            raise ValueError("evaluation export rejected a case without a successful measured worker run")
        if job.attempts != 1:
            raise ValueError("evaluation export rejected a retried job because only latest-attempt timing is persisted")
        if isinstance(job.processing_ms, bool) or not math.isfinite(job.processing_ms) or job.processing_ms < 0:
            raise ValueError("evaluation export rejected an invalid worker duration")
        latest_link_run = db.scalar(
            select(AuditEvent)
            .where(AuditEvent.case_id == case.id, AuditEvent.action == "campaign_links_recomputed")
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(1)
        )
        if graph_linking_enabled:
            if latest_link_run is None or _as_utc(latest_link_run.created_at) <= _as_utc(job.updated_at):
                raise ValueError("evaluation export requires a campaign-link recomputation after the successful worker run")
            run_detail = latest_link_run.detail if isinstance(latest_link_run.detail, dict) else {}
            if run_detail.get("rule_version") != rule_version(settings.campaign_link_threshold):
                raise ValueError("evaluation export requires a campaign-link run using the configured current rule version")
            link_duration = run_detail.get("campaign_linking_ms")
            if isinstance(link_duration, bool) or not isinstance(link_duration, (int, float)) or not math.isfinite(link_duration) or link_duration < 0:
                raise ValueError("evaluation export rejected a campaign-link run without a valid measured duration")
            campaign_linking_ms[case.id] = float(link_duration)
        else:
            if latest_link_run is not None:
                raise ValueError("no-graph export rejected a case with campaign-linking history")
            linked_case = db.scalar(
                select(CaseLink.id)
                .where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))
                .limit(1)
            )
            if linked_case is not None:
                raise ValueError("no-graph export rejected a case with persisted campaign links")
            campaign_linking_ms[case.id] = 0.0
        _ensure_eligible(db, case)
        cases[row["case_ref"]] = case
        jobs[row["case_ref"]] = job

    mapped_case_id = {cases[row["case_ref"]].id: row["case_id"] for row in annotations}
    current_campaign_rule = rule_version(settings.campaign_link_threshold)
    links = db.scalars(select(CaseLink).where(
        CaseLink.left_case_id.in_(mapped_case_id),
        CaseLink.right_case_id.in_(mapped_case_id),
        CaseLink.rule_version == current_campaign_rule,
        CaseLink.review_status.in_({"proposed", "low_signal"}),
    )).all() if mapped_case_id and graph_linking_enabled else []
    adjacency: dict[int, set[int]] = {case_id: set() for case_id in mapped_case_id}
    rule_versions: set[str] = set()
    for link in links:
        adjacency[link.left_case_id].add(link.right_case_id)
        adjacency[link.right_case_id].add(link.left_case_id)
        rule_versions.add(link.rule_version)

    predicted_campaign: dict[int, str] = {}
    visited: set[int] = set()
    for start in sorted(adjacency):
        if start in visited:
            continue
        stack = [start]
        component: list[int] = []
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            stack.extend(adjacency[node] - visited)
        if len(component) < 2:
            continue
        pseudonyms = sorted(mapped_case_id[item] for item in component)
        cluster = hashlib.sha256(("evaluation-campaign-v1:" + "|".join(pseudonyms)).encode("utf-8")).hexdigest()[:24]
        for case_id in component:
            predicted_campaign[case_id] = cluster

    output: list[dict] = []
    finding_rule_versions: set[str] = set()
    source_adapter_versions = {LocalEvidenceCorpusAdapter.adapter_version}
    for row in annotations:
        case = cases[row["case_ref"]]
        # Preserve all extracted candidates for entity-extraction scoring,
        # including investigator-rejected candidates. Value corrections are
        # excluded above because they overwrite the original extraction.
        entities = list(case.entities)
        findings = db.scalars(select(SystemFinding).where(
            SystemFinding.case_id == case.id,
            SystemFinding.active.is_(True),
        )).all()
        finding_rule_versions.update(finding.rule_version for finding in findings)
        evidence_by_id: dict[int, Evidence] = {item.id: item for item in case.evidence}
        for item in case.evidence:
            details = item.details or {}
            adapter_version = details.get("adapter_version") or details.get("corpus_version")
            if isinstance(adapter_version, str) and adapter_version:
                source_adapter_versions.add(adapter_version)
        # Only a persisted rule finding that cites a relevant result-bearing
        # source counts. Human relevance review is part of this workflow; the
        # gold-label annotators must remain independent of those investigators.
        entity_by_id = {entity.id: entity for entity in entities}
        predicted_supported = set()
        for finding in findings:
            entity = entity_by_id.get(finding.entity_id)
            if entity is None:
                continue
            if any(
                evidence_id in evidence_by_id
                and evidence_by_id[evidence_id].outcome == "result"
                and evidence_by_id[evidence_id].review_status == "relevant"
                for evidence_id in finding.supporting_evidence_ids
            ):
                predicted_supported.add((entity.entity_type, normalize(entity.entity_type, entity.normalized_value)))
        output.append({
            "case_id": row["case_id"],
            "submitted_at": _is_utc(case.created_at),
            "split": row["split"],
            "campaign_id": row["campaign_id"],
            "gold_entities": [
                {"type": entity["type"], "value": normalize(entity["type"], entity["value"])}
                for entity in row["gold_entities"]
            ],
            "predicted_entities": [
                {"type": entity.entity_type, "value": entity.normalized_value}
                for entity in entities
            ],
            "predicted_campaign_id": predicted_campaign.get(case.id),
            "gold_supported_entities": [
                {"type": entity["type"], "value": normalize(entity["type"], entity["value"])}
                for entity in row["gold_supported_entities"]
            ],
            "predicted_supported_entities": [
                {"type": entity_type, "value": value}
                for entity_type, value in sorted(predicted_supported)
            ],
            "gold_adverse_verdict": row["gold_adverse_verdict"],
            # Count a concern at either the case or claim level so another
            # positive finding cannot hide a claim-level false positive.
            # This evaluation field is never a guilt determination.
            "predicted_adverse_verdict": (
                case.assessment == "Evidence supports concern"
                or any(finding.assessment == "Evidence supports concern" for finding in findings)
            ),
            "processing_ms": float(jobs[row["case_ref"]].processing_ms) + campaign_linking_ms[case.id],
        })
    # Reject time overlap, campaign leakage and missing held-out test rows before
    # creating any external evaluation artifacts.
    score_rows(output)
    metadata = {
        "format": "rsaicdp-pipeline-evaluation-v3",
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "records": len(output),
        "database_read_snapshot": "PostgreSQL repeatable-read, read-only transaction",
        "campaign_rule_versions": sorted(rule_versions),
        "campaign_linking_mode": "enabled" if graph_linking_enabled else "disabled",
        "campaign_cluster_definition": "connected components of current-rule proposed and low_signal links among mapped cases; both are investigative leads and neither proves wrongdoing" if graph_linking_enabled else "campaign predictions intentionally omitted in the graph-linking ablation",
        "campaign_rule_version_configured": current_campaign_rule,
        "finding_rule_versions": sorted(finding_rule_versions or {FINDING_RULE_VERSION}),
        "source_adapter_versions": sorted(source_adapter_versions),
        "evidence_corpus_snapshot_hmac_sha256": _corpus_snapshot_hmac(db, key),
        "case_evidence_snapshot_hmac_sha256": hmac.new(
            key,
            json.dumps([
                {
                    "case_id": row["case_id"],
                    "evidence": sorted(
                        [{
                            "source_name": item.source_name,
                            "source_type": item.source_type,
                            "source_ref": item.source_ref,
                            "claim": item.claim,
                            "outcome": item.outcome,
                            "excerpt": item.excerpt,
                            "authority": item.authority,
                            "retrieved_at": _is_utc(item.retrieved_at),
                            "details": item.details or {},
                            "review_status": item.review_status,
                        } for item in cases[row["case_ref"]].evidence],
                        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    ),
                }
                for row in sorted(annotations, key=lambda item: item["case_id"])
            ], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest(),
        "processing_boundary": "worker processing duration plus measured deterministic campaign-link recomputation duration when enabled; excludes queue wait, worker and link final commits, and asynchronous Neo4j projection; the no-graph ablation requires no link audit history or persisted case links",
        "evidence_support_definition": "claim-level precision and recall over (case_id, entity type, normalized value); a prediction requires an active entity finding citing a result-bearing source record an investigator marked relevant; reviewers must be independent from gold-label annotators, and relevance does not establish wrongdoing",
        "adverse_flag_definition": "true when the case assessment or any active claim-level finding is Evidence supports concern; authoritative-source confirmation alone is not adverse",
        "review_scope": "entity confirmation/rejection and evidence relevance review are part of the end-to-end workflow; corrected entity values and investigator link decisions are excluded; investigators must not see or author gold labels",
        "privacy": "case_ref and submitted text are not written to the export; case_id must be pseudonymous; entity values may still be personal data and require protected storage",
    }
    return output, metadata


def _outside_workspace(path: Path) -> Path:
    resolved = path.resolve()
    workspace_root = Path(__file__).resolve().parents[2]
    if resolved == workspace_root or workspace_root in resolved.parents:
        raise ValueError("evaluation input and output files must be stored outside the repository")
    return resolved


def _write_new_private(path: Path, content: str) -> None:
    """Create a new export without overwriting an existing evaluation artifact."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def main(args: list[str]) -> int:
    without_graph_linking = bool(args and args[0] == "--without-graph-linking")
    positional = args[1:] if without_graph_linking else args
    if len(positional) != 2:
        print(f"usage: {Path(sys.argv[0]).name} [--without-graph-linking] ANNOTATIONS.jsonl OUTPUT.jsonl", file=sys.stderr)
        return 2
    try:
        annotation_path = _outside_workspace(Path(positional[0]))
        output_path = _outside_workspace(Path(positional[1]))
        annotations = load_annotations(annotation_path)
        from app.db import SessionLocal

        key = _snapshot_key()
        with SessionLocal() as db:
            rows, metadata = export_rows(db, annotations, key, graph_linking_enabled=not without_graph_linking)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        metadata["annotations_hmac_sha256"] = hmac.new(key, annotation_path.read_bytes(), hashlib.sha256).hexdigest()
        metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
        _write_new_private(output_path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        try:
            _write_new_private(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        print(json.dumps({"records": len(rows), "metadata_file": metadata_path.name}, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"pipeline evaluation export error: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError as exc:
        print(f"pipeline evaluation export database error: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
