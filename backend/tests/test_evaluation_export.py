"""Synthetic database tests for privacy-safe evaluation joins."""
import json
import io
import unittest
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.findings import entity_fingerprint, rebuild_system_findings
from app.models import AuditEvent, Case, CaseLink, Entity, Evidence, ProcessingJob, User
from evaluation.evaluate import load as load_scored_rows, score
from evaluation.export_pipeline import _outside_workspace, export_rows, load_annotations, main as export_main


def annotation(case_ref: str, case_id: str, *, campaign_id="gold-group-1") -> dict:
    return {
        "case_ref": case_ref,
        "case_id": case_id,
        "split": "test",
        "campaign_id": campaign_id,
        "gold_entities": [{"type": "phone", "value": "+91 98765 43210"}],
        "gold_supported_entities": [{"type": "phone", "value": "+91 98765 43210"}],
        "gold_adverse_verdict": False,
    }


class EvaluationExportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        investigator = User(email="evaluation-investigator@example.invalid", password_hash="synthetic", role="investigator")
        self.db.add(investigator)
        self.db.flush()
        self.refs = ("RC-11111111", "RC-22222222")
        self.cases = []
        for index, ref in enumerate(self.refs, start=1):
            case = Case(
                case_ref=ref,
                title=f"Synthetic private title {index}",
                input_kind="message",
                submitted_text=f"Synthetic private submitted text {index}",
                status="completed",
                assessment="Insufficient evidence",
                consent_version="synthetic-test",
                created_by=investigator.id,
                created_at=datetime(2026, index, 1, tzinfo=timezone.utc),
            )
            self.db.add(case)
            self.db.flush()
            entity = Entity(
                case_id=case.id,
                entity_type="phone",
                raw_value="+91 98765 43210",
                normalized_value="9876543210",
                source_excerpt="Phone: +91 98765 43210",
                source_location="submitted_text",
                source_start_char=7,
                source_end_char=24,
                extraction_method="deterministic_regex",
                review_status="confirmed",
            )
            self.db.add(entity)
            self.db.flush()
            self.db.add(ProcessingJob(case_id=case.id, status="completed", attempts=1, processing_ms=31.25, created_at=case.created_at, updated_at=case.created_at))
            self.db.add(AuditEvent(
                case_id=case.id,
                actor_id=investigator.id,
                action="campaign_links_recomputed",
                detail={"matched_case_count": 1, "rule_version": "campaign-signals-v3-threshold-40", "threshold": 40, "campaign_linking_ms": 4.75},
                created_at=case.created_at + timedelta(seconds=2),
            ))
            self.cases.append((case, entity))

        case, entity = self.cases[0]
        evidence = Evidence(
            case_id=case.id,
            source_name="Synthetic reviewed source",
            source_type="curated_local_corpus",
            source_ref="local:synthetic-1",
            claim="Synthetic exact identifier record",
            outcome="result",
            excerpt="Synthetic source excerpt",
            authority="unverified_public_report",
            review_status="relevant",
            details={"entity_fingerprint": entity_fingerprint(entity)},
        )
        self.db.add(evidence)
        self.db.flush()
        self.db.add(AuditEvent(case_id=case.id, actor_id=investigator.id, action="entity_reviewed", detail={"entity_id": entity.id, "status": "confirmed"}))
        self.db.add(AuditEvent(case_id=case.id, actor_id=investigator.id, action="evidence_reviewed", detail={"evidence_id": evidence.id, "status": "relevant"}))
        rebuild_system_findings(self.db, case)

        first_id, second_id = sorted(item[0].id for item in self.cases)
        self.db.add(CaseLink(
            left_case_id=first_id,
            right_case_id=second_id,
            rule_version="campaign-signals-v3-threshold-40",
            strength=40,
            reasons=["Synthetic exact phone reuse"],
            review_status="proposed",
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_export_joins_real_persisted_outputs_without_private_case_fields(self):
        rows, metadata = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001"), annotation(self.refs[1], "pseudo-case-0002")],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
        )

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            score_input = Path(directory) / "scorer-input.jsonl"
            score_input.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            scored_rows = load_scored_rows(score_input)
        metrics = score(scored_rows)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["gold_entities"], [{"type": "phone", "value": "9876543210"}])
        self.assertEqual(rows[0]["predicted_entities"], [{"type": "phone", "value": "9876543210"}])
        self.assertEqual(rows[0]["predicted_supported_entities"], [{"type": "phone", "value": "9876543210"}])
        self.assertEqual(self.cases[0][0].assessment, "Evidence supports concern")
        self.assertTrue(rows[0]["predicted_adverse_verdict"])
        self.assertEqual(rows[0]["predicted_campaign_id"], rows[1]["predicted_campaign_id"])
        self.assertAlmostEqual(rows[0]["processing_ms"], 36.0)
        self.assertEqual(metadata["campaign_linking_mode"], "enabled")
        self.assertEqual(metrics["test_cases"], 2)
        self.assertIn("gold-label annotator", metadata["evidence_support_definition"])
        self.assertRegex(metadata["case_evidence_snapshot_hmac_sha256"], r"^[a-f0-9]{64}$")
        self.assertRegex(metadata["evidence_corpus_snapshot_hmac_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("synthetic-evaluation-hmac-key-0001", json.dumps(metadata))
        encoded = json.dumps(rows)
        for private in (*self.refs, "Synthetic private title", "Synthetic private submitted text", "Synthetic source excerpt"):
            self.assertNotIn(private, encoded)

    def test_export_rejects_corrected_or_retried_cases(self):
        case, _ = self.cases[0]
        self.db.add(AuditEvent(case_id=case.id, actor_id=None, action="correction_applied", detail={}))
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "human changes"):
            export_rows(self.db, [annotation(self.refs[0], "pseudo-case-0001")], snapshot_key=b"synthetic-evaluation-hmac-key-0001")

        case, _ = self.cases[1]
        job = self.db.query(ProcessingJob).filter_by(case_id=case.id).one()
        job.attempts = 2
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "retried job"):
            export_rows(self.db, [annotation(self.refs[1], "pseudo-case-0002")], snapshot_key=b"synthetic-evaluation-hmac-key-0001")

    def test_export_ignores_links_from_historical_campaign_rule_versions(self):
        link = self.db.query(CaseLink).one()
        link.rule_version = "campaign-signals-v2-threshold-25"
        self.db.commit()

        rows, metadata = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001"), annotation(self.refs[1], "pseudo-case-0002")],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
        )

        self.assertIsNone(rows[0]["predicted_campaign_id"])
        self.assertIsNone(rows[1]["predicted_campaign_id"])
        self.assertEqual(metadata["campaign_rule_versions"], [])

    def test_export_includes_current_rule_low_signal_lead_groups(self):
        link = self.db.query(CaseLink).one()
        link.review_status = "low_signal"
        self.db.commit()

        rows, metadata = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001"), annotation(self.refs[1], "pseudo-case-0002")],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
        )

        self.assertEqual(rows[0]["predicted_campaign_id"], rows[1]["predicted_campaign_id"])
        self.assertIn("low_signal", metadata["campaign_cluster_definition"])
        self.assertIn("investigative leads", metadata["campaign_cluster_definition"])

    def test_graph_ablation_exports_matched_worker_timing_and_omits_campaign_predictions(self):
        self.db.query(CaseLink).delete()
        self.db.query(AuditEvent).filter(AuditEvent.action == "campaign_links_recomputed").delete()
        self.db.commit()

        rows, metadata = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001"), annotation(self.refs[1], "pseudo-case-0002")],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
            graph_linking_enabled=False,
        )

        self.assertEqual([row["processing_ms"] for row in rows], [31.25, 31.25])
        self.assertEqual([row["predicted_campaign_id"] for row in rows], [None, None])
        self.assertEqual(metadata["campaign_linking_mode"], "disabled")

    def test_graph_ablation_rejects_any_persisted_linking_history(self):
        with self.assertRaisesRegex(ValueError, "campaign-linking history"):
            export_rows(
                self.db,
                [annotation(self.refs[0], "pseudo-case-0001")],
                snapshot_key=b"synthetic-evaluation-hmac-key-0001",
                graph_linking_enabled=False,
            )

    def test_full_export_requires_link_recomputation_after_worker_completion(self):
        case, _ = self.cases[0]
        self.db.query(AuditEvent).filter(
            AuditEvent.case_id == case.id,
            AuditEvent.action == "campaign_links_recomputed",
        ).delete()
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "campaign-link recomputation"):
            export_rows(self.db, [annotation(self.refs[0], "pseudo-case-0001")], snapshot_key=b"synthetic-evaluation-hmac-key-0001")

    def test_full_export_rejects_stale_rule_version_link_timing(self):
        case, _ = self.cases[0]
        run = self.db.query(AuditEvent).filter_by(case_id=case.id, action="campaign_links_recomputed").one()
        run.detail = {**run.detail, "rule_version": "campaign-signals-v3-threshold-35"}
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "configured current rule version"):
            export_rows(self.db, [annotation(self.refs[0], "pseudo-case-0001")], snapshot_key=b"synthetic-evaluation-hmac-key-0001")

    def test_full_export_compares_link_and_worker_timestamps_as_datetimes(self):
        case, _ = self.cases[0]
        run = self.db.query(AuditEvent).filter_by(case_id=case.id, action="campaign_links_recomputed").one()
        run.created_at = case.created_at + timedelta(milliseconds=1)
        self.db.commit()

        rows, _ = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001")],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
        )

        self.assertAlmostEqual(rows[0]["processing_ms"], 36.0)

    def test_claim_level_concern_is_not_hidden_by_overall_authoritative_status(self):
        case, _ = self.cases[0]
        case.assessment = "Confirmed by an authoritative source"
        self.db.commit()

        rows, _ = export_rows(
            self.db,
            [annotation(self.refs[0], "pseudo-case-0001", campaign_id=None)],
            snapshot_key=b"synthetic-evaluation-hmac-key-0001",
        )

        self.assertTrue(rows[0]["predicted_adverse_verdict"])

    def test_annotation_loader_rejects_identifying_ids_and_extra_text(self):
        import tempfile
        from pathlib import Path

        bad_rows = [
            {**annotation("RC-33333333", "person@example.invalid"), "case_ref": "RC-33333333"},
            {**annotation("RC-44444444", "pseudo-case-0004"), "submitted_text": "private input"},
        ]
        for row in bad_rows:
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "annotations.jsonl"
                source.write_text(json.dumps(row) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_annotations(source)

    def test_annotation_loader_rejects_case_reference_duplicates_after_case_normalization(self):
        import tempfile
        from pathlib import Path

        rows = [
            annotation("RC-ABCDEF01", "pseudo-case-1001"),
            annotation("rc-abcdef01", "pseudo-case-1002"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "annotations.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be unique"):
                load_annotations(source)

    def test_annotation_loader_applies_application_entity_normalization(self):
        import tempfile
        from pathlib import Path

        row = annotation("RC-ABCDEF02", "pseudo-case-1003")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "annotations.jsonl"
            source.write_text(json.dumps(row) + "\n", encoding="utf-8")
            loaded = load_annotations(source)
        self.assertEqual(loaded[0]["case_ref"], "RC-ABCDEF02")
        self.assertEqual(loaded[0]["gold_entities"], [{"type": "phone", "value": "9876543210"}])

    def test_export_requires_a_protected_snapshot_key(self):
        with self.assertRaisesRegex(ValueError, "EVALUATION_SNAPSHOT_HMAC_KEY"):
            export_rows(self.db, [annotation(self.refs[0], "pseudo-case-0001")], snapshot_key=b"short")

    def test_cli_writes_outputs_exclusively_without_join_keys_or_hmac_secret(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            annotation_path = root / "private-map.jsonl"
            output_path = root / "result.jsonl"
            annotation_path.write_text(json.dumps(annotation(self.refs[0], "pseudo-case-0001")) + "\n", encoding="utf-8")
            expected_rows = [{
                "case_id": "pseudo-case-0001",
                "submitted_at": "2026-01-01T00:00:00Z",
                "split": "test",
                "campaign_id": None,
                "gold_entities": [],
                "predicted_entities": [],
                "predicted_campaign_id": None,
                "gold_supported_entities": [],
                "predicted_supported_entities": [],
                "gold_adverse_verdict": False,
                "predicted_adverse_verdict": False,
                "processing_ms": 4.0,
            }]
            with patch.dict("os.environ", {"EVALUATION_SNAPSHOT_HMAC_KEY": "synthetic-key-that-is-at-least-32-bytes"}):
                with patch("evaluation.export_pipeline._outside_workspace", side_effect=lambda path: Path(path).resolve()), patch(
                    "app.db.SessionLocal"
                ) as session_factory, patch(
                    "evaluation.export_pipeline.export_rows",
                    return_value=(expected_rows, {"format": "test", "privacy": "synthetic"}),
                ):
                    session_factory.return_value.__enter__.return_value = self.db
                    self.assertEqual(export_main([str(annotation_path), str(output_path)]), 0)
                    exported = output_path.read_text(encoding="utf-8")
                    metadata_path = output_path.with_suffix(".jsonl.metadata.json")
                    metadata = metadata_path.read_text(encoding="utf-8")
                    self.assertNotIn(self.refs[0], exported)
                    self.assertNotIn("submitted_text", exported)
                    self.assertNotIn("synthetic-key", metadata)
                    self.assertTrue(session_factory.return_value.__enter__.called)
                    before = output_path.read_bytes()
                    errors = io.StringIO()
                    with redirect_stderr(errors):
                        self.assertEqual(export_main([str(annotation_path), str(output_path)]), 1)
                    self.assertEqual(output_path.read_bytes(), before)

    def test_cli_graph_ablation_flag_selects_link_free_export(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            annotation_path = root / "private-map.jsonl"
            output_path = root / "no-graph.jsonl"
            annotation_path.write_text(json.dumps(annotation(self.refs[0], "pseudo-case-0001")) + "\n", encoding="utf-8")
            with patch.dict("os.environ", {"EVALUATION_SNAPSHOT_HMAC_KEY": "synthetic-key-that-is-at-least-32-bytes"}), patch(
                "evaluation.export_pipeline._outside_workspace", side_effect=lambda path: Path(path).resolve()
            ), patch("app.db.SessionLocal") as session_factory, patch(
                "evaluation.export_pipeline.export_rows", return_value=([], {"format": "test"})
            ) as exporter:
                session_factory.return_value.__enter__.return_value = self.db
                self.assertEqual(export_main(["--without-graph-linking", str(annotation_path), str(output_path)]), 0)
                self.assertFalse(exporter.call_args.kwargs["graph_linking_enabled"])

    def test_export_path_guard_rejects_repository_files(self):
        repository_file = Path(__file__).resolve().parents[1] / "evaluation" / "not-an-artifact.jsonl"
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            _outside_workspace(repository_file)


if __name__ == "__main__":
    unittest.main()
