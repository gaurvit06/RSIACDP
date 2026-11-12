"""Run a synthetic-only SQLite smoke comparison through the real worker and exporter.

This exercises product code; it is not a model-accuracy evaluation. All fixture
labels and source records are generated together, so measured scores are
generator-dependent and must not be presented as real-world performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _read_fixture(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != 108 or any(not row.get("submitted_text", "").startswith("SYNTHETIC TEST ONLY.") for row in rows):
        raise ValueError("expected 108 explicitly synthetic v2 fixture rows")
    if {row.get("split") for row in rows} != {"train", "dev", "test"}:
        raise ValueError("fixture must contain train, dev, and test splits")
    split_counts = {split: sum(row.get("split") == split for row in rows) for split in ("train", "dev", "test")}
    if split_counts != {"train": 36, "dev": 36, "test": 36}:
        raise ValueError("fixture split sizes do not match the v2 manifest")
    if len({row.get("case_id") for row in rows}) != len(rows):
        raise ValueError("fixture case IDs must be unique")
    campaign_splits: dict[str, set[str]] = {}
    group_domains: dict[str, set[str]] = {}
    for row in rows:
        campaign_id = row.get("campaign_id")
        campaign_splits.setdefault(campaign_id, set()).add(row["split"])
        entities = row.get("gold_entities", [])
        by_type = {item.get("type"): item.get("value") for item in entities if isinstance(item, dict)}
        email = by_type.get("email", "")
        domain = by_type.get("domain", "")
        if len(entities) != 2 or not email.endswith("@" + domain) or not domain.endswith(".invalid"):
            raise ValueError("each v2 row must label one reserved .invalid email and its derived domain")
        group_domains.setdefault(campaign_id, set()).add(domain)
    if any(len(splits) != 1 for splits in campaign_splits.values()):
        raise ValueError("campaigns must not cross chronological splits")
    if any(len(domains) != 1 for domains in group_domains.values()):
        raise ValueError("every campaign group must reuse exactly one fictional domain")
    return rows, hashlib.sha256(raw).hexdigest()


def _write_jsonl_new(path: Path, records: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records))


def _source_snapshot_sha256() -> str:
    backend_root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for directory in (backend_root / "app", backend_root / "evaluation"):
        for source in sorted(directory.rglob("*.py")):
            relative = source.relative_to(backend_root).as_posix()
            digest.update(relative.encode("utf-8") + b"\0" + source.read_bytes() + b"\0")
    return digest.hexdigest()


def run(input_path: Path, output_dir: Path) -> dict:
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    repository = Path(__file__).resolve().parents[2]
    if repository == input_path or repository in input_path.parents:
        raise ValueError("synthetic input must be stored outside the repository")
    if repository == output_dir or repository in output_dir.parents:
        raise ValueError("evaluation outputs must be stored outside the repository")
    rows, dataset_sha256 = _read_fixture(input_path)
    code_revision = os.getenv("RSAICDP_CODE_REVISION", "").strip()
    if code_revision and re.fullmatch(r"[0-9a-fA-F]{7,40}", code_revision) is None:
        raise ValueError("RSAICDP_CODE_REVISION must be a 7- to 40-character Git commit hash")
    source_snapshot_sha256 = _source_snapshot_sha256()
    output_dir.mkdir(parents=True, exist_ok=False)

    # App imports below must see test mode before constructing the default
    # SQLAlchemy engine. The real smoke databases are separate, explicit SQLite
    # files created only inside a temporary subdirectory of this new output.
    work_area = tempfile.TemporaryDirectory(prefix="work-", dir=output_dir)
    work_dir = Path(work_area.name)
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(work_dir / 'unused-import-engine.sqlite3').as_posix()}"
    os.environ["UPLOAD_DIR"] = str(work_dir / "unused-uploads")
    os.environ["UPLOAD_STORAGE_BACKEND"] = "local"
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
    os.environ["NEO4J_URI"] = ""
    os.environ["NEO4J_HOST"] = ""
    os.environ["NEO4J_PASSWORD"] = ""
    os.environ["RDAP_ENABLED"] = "false"
    os.environ["CAMPAIGN_LINK_THRESHOLD"] = "40"

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.findings import rebuild_system_findings
    from app.main import refresh_links
    from app.models import AuditEvent, Case, ProcessingJob, SourceRecord, User
    from app.worker import process_job
    from evaluation.baseline_tfidf_logreg import run as run_tfidf
    from evaluation.compare_runs import compare
    from evaluation.export_pipeline import export_rows, load_annotations

    seed_db = work_dir / "seed.sqlite3"
    full_db = work_dir / "full.sqlite3"
    no_graph_db = work_dir / "no-graph.sqlite3"
    annotations_path = work_dir / "pipeline-map.jsonl"
    seed_engine = create_engine(f"sqlite+pysqlite:///{seed_db.as_posix()}", connect_args={"timeout": 30})
    Base.metadata.create_all(seed_engine)
    factory = sessionmaker(bind=seed_engine, autoflush=False, expire_on_commit=False)
    annotations: list[dict] = []
    synthetic_user_email = "synthetic-evaluation-investigator@example.invalid"
    source_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with factory() as db:
        investigator = User(email=synthetic_user_email, password_hash="fixture-only-not-a-login-hash", role="investigator")
        db.add(investigator)
        db.flush()
        unique_support: dict[tuple[str, str], dict] = {}
        for row in rows:
            for entity in row["gold_supported_entities"]:
                unique_support[(entity["type"], entity["value"])] = row
        for index, ((entity_type, value), source_row) in enumerate(sorted(unique_support.items()), start=1):
            db.add(SourceRecord(
                record_id=f"synthetic-fixture-v2-{index:04d}",
                entity_type=entity_type,
                normalized_value=value,
                source_name="SYNTHETIC TEST ONLY — generated fixture record",
                source_type="unverified_public_report",
                source_ref=f"synthetic://fixture-v2/{source_row['split']}/{index:04d}",
                claim="SYNTHETIC TEST ONLY: generated record for a fictional identifier; this is not a real source or allegation.",
                outcome="result",
                excerpt="SYNTHETIC TEST ONLY. This generated record exists solely to exercise evidence review and finding rules.",
                authority="unverified_public_report",
                retrieved_at=source_time,
                created_by=investigator.id,
            ))
        db.flush()
        for index, row in enumerate(rows, start=1):
            submitted_at = datetime.fromisoformat(row["submitted_at"].replace("Z", "+00:00"))
            case_id_hash = hashlib.sha256(row["case_id"].encode("utf-8")).hexdigest()[:8].upper()
            case = Case(
                case_ref=f"RC-{case_id_hash}",
                title=f"SYNTHETIC TEST ONLY — evaluation case {index:06d}",
                input_kind="message",
                submitted_text=row["submitted_text"],
                status="queued",
                assessment="Insufficient evidence",
                consent_version="synthetic-evaluation-fixture-v2",
                consented_at=submitted_at,
                external_source_consent=False,
                created_by=investigator.id,
                created_at=submitted_at,
            )
            db.add(case)
            db.flush()
            db.add(ProcessingJob(case_id=case.id, status="queued", attempts=1, created_at=submitted_at, updated_at=submitted_at))
            annotations.append({
                "case_ref": case.case_ref,
                "case_id": row["case_id"],
                "split": row["split"],
                "campaign_id": row["campaign_id"],
                "gold_entities": row["gold_entities"],
                "gold_supported_entities": row["gold_supported_entities"],
                "gold_adverse_verdict": row["gold_adverse_verdict"],
            })
        db.commit()

    with factory() as db:
        job_ids = list(db.scalars(select(ProcessingJob.id).order_by(ProcessingJob.id)))
    for job_id in job_ids:
        with factory() as db:
            job = db.get(ProcessingJob, job_id)
            process_job(db, job)
            if job.status != "completed" or job.attempts != 1 or job.processing_ms is None:
                raise RuntimeError(f"synthetic fixture processing failed for job {job_id}")

    with factory() as db:
        cases = db.scalars(select(Case).order_by(Case.id)).all()
        for case in cases:
            for entity in case.entities:
                entity.review_status = "confirmed"
                db.add(AuditEvent(case_id=case.id, actor_id=case.created_by, action="entity_reviewed", detail={"entity_id": entity.id, "status": "confirmed", "synthetic_fixture": True}))
            for evidence in case.evidence:
                if evidence.outcome == "result":
                    evidence.review_status = "relevant"
                    evidence.review_reason = "Synthetic fixture review only; not a real source assessment."
                    evidence.reviewed_by = case.created_by
                    evidence.reviewed_at = datetime.now(timezone.utc)
                    db.add(AuditEvent(case_id=case.id, actor_id=case.created_by, action="evidence_reviewed", detail={"evidence_id": evidence.id, "status": "relevant", "synthetic_fixture": True}))
            rebuild_system_findings(db, case)
        db.commit()

    with factory() as db:
        cases = db.scalars(select(Case).order_by(Case.id)).all()
        annotations_by_ref = {item["case_ref"]: item for item in annotations}
        for case in cases:
            actual = {(entity.entity_type, entity.normalized_value) for entity in case.entities}
            expected = {(entity["type"], entity["value"].casefold()) for entity in annotations_by_ref[case.case_ref]["gold_entities"]}
            if actual != expected:
                raise RuntimeError(f"deterministic extractor disagreed with the v2 fixture for case {case.case_ref}")
            if any(item.entity_type == "fee_request" for item in case.entities):
                raise RuntimeError("a mere synthetic fee mention was extracted as a payment request")
    seed_engine.dispose()

    shutil.copyfile(seed_db, full_db)
    shutil.copyfile(seed_db, no_graph_db)
    _write_jsonl_new(annotations_path, annotations)
    mapped_annotations = load_annotations(annotations_path)
    hmac_key = os.urandom(32)

    full_engine = create_engine(f"sqlite+pysqlite:///{full_db.as_posix()}", connect_args={"timeout": 30})
    full_factory = sessionmaker(bind=full_engine, autoflush=False, expire_on_commit=False)
    with full_factory() as db:
        investigator = db.scalar(select(User).where(User.email == synthetic_user_email))
        for item in mapped_annotations:
            case = db.scalar(select(Case).where(Case.case_ref == item["case_ref"]))
            refresh_links(case.id, db, investigator)
    with full_factory() as db:
        full_rows, full_meta = export_rows(db, mapped_annotations, hmac_key, graph_linking_enabled=True)
    full_engine.dispose()

    no_graph_engine = create_engine(f"sqlite+pysqlite:///{no_graph_db.as_posix()}", connect_args={"timeout": 30})
    no_graph_factory = sessionmaker(bind=no_graph_engine, autoflush=False, expire_on_commit=False)
    with no_graph_factory() as db:
        no_graph_rows, no_graph_meta = export_rows(db, mapped_annotations, hmac_key, graph_linking_enabled=False)
    no_graph_engine.dispose()
    if full_meta["case_evidence_snapshot_hmac_sha256"] != no_graph_meta["case_evidence_snapshot_hmac_sha256"]:
        raise RuntimeError("full and no-graph runs do not share identical case evidence snapshots")
    if full_meta["evidence_corpus_snapshot_hmac_sha256"] != no_graph_meta["evidence_corpus_snapshot_hmac_sha256"]:
        raise RuntimeError("full and no-graph runs do not share identical evidence corpus snapshots")

    baseline_predictions, baseline_metrics = run_tfidf(rows, dataset_sha256)
    baseline_path = output_dir / "tfidf-logreg.jsonl"
    no_graph_path = output_dir / "evidence-pipeline-no-graph.jsonl"
    full_path = output_dir / "full-evidence-pipeline.jsonl"
    _write_jsonl_new(baseline_path, baseline_predictions)
    _write_jsonl_new(no_graph_path, no_graph_rows)
    _write_jsonl_new(full_path, full_rows)
    (output_dir / "tfidf-logreg-metrics.json").write_text(json.dumps(baseline_metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "full-evidence-pipeline.metadata.json").write_text(json.dumps(full_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "evidence-pipeline-no-graph.metadata.json").write_text(json.dumps(no_graph_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    comparison = compare({
        "tfidf_logreg": baseline_path,
        "evidence_pipeline_no_graph": no_graph_path,
        "full_evidence_pipeline": full_path,
    })
    summary = {
        "synthetic_fixture_only": True,
        "generator_version": "synthetic-fixtures-v2",
        "dataset_sha256": dataset_sha256,
        "git_revision": code_revision or None,
        "source_snapshot_sha256": source_snapshot_sha256,
        "records": len(rows),
        "test_case_count": comparison["test_case_count"],
        "pipeline_snapshot_match": True,
        "rule_versions": {"full": full_meta["campaign_rule_versions"], "no_graph": no_graph_meta["campaign_rule_versions"]},
        "comparison": comparison,
        "limitations": [
            "Gold labels and source records are generated together; these scores are a tautological integration rehearsal, not an independent accuracy evaluation.",
            "Only reserved .invalid email and derived-domain identifiers are exercised; there are no real reports, identities, or authoritative records.",
            "The synthetic evidence review is generated to exercise the finding pipeline; it is not an independent investigator relevance judgment.",
            "The no-graph and full runs use isolated SQLite databases and do not exercise a live Neo4j projection.",
            "LLM with web search was not run because no approved provider and lawful retrieval configuration were supplied.",
            "Worker and linking timings are local smoke measurements, not production latency estimates.",
        ],
    }
    summary_path = output_dir / "synthetic-pipeline-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    work_area.cleanup()
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="v2 synthetic input JSONL stored outside the repository")
    parser.add_argument("output", type=Path, help="new private output directory outside the repository")
    arguments = parser.parse_args()
    result = run(arguments.input, arguments.output)
    print(json.dumps({
        "summary_file": str(arguments.output.resolve() / "synthetic-pipeline-summary.json"),
        "test_case_count": result["test_case_count"],
        "dataset_sha256": result["dataset_sha256"],
        "git_revision": result["git_revision"],
        "source_snapshot_sha256": result["source_snapshot_sha256"],
        "systems": result["comparison"]["systems"],
        "limitations": result["limitations"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
