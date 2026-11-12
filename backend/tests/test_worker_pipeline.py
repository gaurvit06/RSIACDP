"""Offline worker-to-evidence pipeline check using synthetic SQLite data."""
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.findings import rebuild_system_findings
from app.models import AuditEvent, Case, Entity, Evidence, ProcessingJob, SourceRecord, SystemFinding, User
from app.main import persist_uploaded_case
from app.private_storage import UPLOAD_MAGIC
from app.worker import process_job


class WorkerPipelineTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False, expire_on_commit=False)
        self.user = User(email="pipeline@example.invalid", password_hash="synthetic-only", role="investigator")
        self.db.add(self.user)
        self.db.flush()
        self.case = Case(
            case_ref="RC-ABCDEF56",
            title="Synthetic worker pipeline case",
            input_kind="message",
            submitted_text="For the synthetic vacancy, contact recruiter@example.invalid. The recruiter is based in Pune. A payment was requested to candidate.test@upi.",
            consent_version="consent-test-v1",
            created_by=self.user.id,
        )
        self.db.add(self.case)
        self.db.flush()
        self.job = ProcessingJob(case_id=self.case.id, status="queued", attempts=1)
        self.source = SourceRecord(
            record_id="LOCAL-PIPELINE-0001",
            entity_type="email",
            normalized_value="recruiter@example.invalid",
            source_name="Synthetic reviewed source",
            source_type="government",
            source_ref="https://records.example.invalid/item/1",
            claim="The synthetic source records this email identifier.",
            outcome="result",
            excerpt="Synthetic source excerpt for the worker integration fixture.",
            authority="government",
            created_by=self.user.id,
        )
        self.db.add_all([self.job, self.source])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_worker_persists_extraction_and_traceable_local_evidence(self):
        process_job(self.db, self.job)

        self.db.refresh(self.case)
        self.db.refresh(self.job)
        self.assertEqual(self.job.status, "completed", self.job.last_error)
        entity = self.db.scalar(select(Entity).where(Entity.case_id == self.case.id, Entity.entity_type == "email"))
        location = self.db.scalar(select(Entity).where(Entity.case_id == self.case.id, Entity.entity_type == "location_claim"))
        upi = self.db.scalar(select(Entity).where(Entity.case_id == self.case.id, Entity.entity_type == "upi_id"))
        evidence = self.db.scalar(select(Evidence).where(Evidence.case_id == self.case.id, Evidence.source_ref == self.source.record_id))
        upi_check = self.db.scalar(select(Evidence).where(Evidence.case_id == self.case.id, Evidence.claim == "No curated local corpus record matched this upi_id identifier"))
        self.assertEqual(self.case.status, "completed")
        self.assertEqual(entity.entity_type, "email")
        self.assertEqual(entity.normalized_value, "recruiter@example.invalid")
        self.assertEqual(entity.source_location, "submitted_text")
        self.assertIsNotNone(entity.source_start_char)
        self.assertIsNotNone(entity.source_end_char)
        self.assertEqual(entity.review_status, "needs_review")
        self.assertEqual(location.raw_value, "Pune")
        self.assertEqual(location.normalized_value, "pune")
        self.assertEqual(location.source_location, "submitted_text")
        self.assertEqual(self.case.submitted_text[location.source_start_char:location.source_end_char], "Pune")
        self.assertEqual(location.review_status, "needs_review")
        self.assertEqual(upi.raw_value, "candidate.test@upi")
        self.assertEqual(upi.normalized_value, "candidate.test@upi")
        self.assertEqual(upi.source_location, "submitted_text")
        self.assertEqual(self.case.submitted_text[upi.source_start_char:upi.source_end_char], "candidate.test@upi")
        self.assertEqual(upi.review_status, "needs_review")
        self.assertIsNotNone(upi_check)
        self.assertEqual(upi_check.outcome, "no_result")
        self.assertEqual(evidence.source_ref, self.source.record_id)
        self.assertEqual(evidence.outcome, "result")
        self.assertEqual(evidence.review_status, "unreviewed")
        self.assertTrue(evidence.details["entity_fingerprint"])
        self.assertEqual(evidence.details["source_record_ref"], self.source.source_ref)
        self.assertIsNotNone(evidence.retrieved_at)
        self.assertEqual(
            self.db.scalar(select(AuditEvent).where(AuditEvent.case_id == self.case.id, AuditEvent.action == "processing_completed")).detail["entity_count"],
            4,
        )

        entity.review_status = "confirmed"
        evidence.review_status = "relevant"
        evidence.reviewed_by = self.user.id
        self.db.flush()
        findings = rebuild_system_findings(self.db, self.case)
        finding = next(item for item in findings if item.entity_id == entity.id)
        self.assertEqual(finding.assessment, "Confirmed by an authoritative source")
        self.assertEqual(finding.supporting_evidence_ids, [evidence.id])
        self.assertIn("does not establish wrongdoing", finding.limitations)

    def test_encrypted_file_intake_runs_through_worker_to_provenance_and_neutral_finding(self):
        key = b"i" * 32
        encoded_key = base64.b64encode(key).decode("ascii")
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Contact recruiter@example.invalid for the Recruitment Analyst role; based in Pune.")
        original = pdf.tobytes()
        pdf.close()
        with tempfile.TemporaryDirectory(prefix="rsaicdp-worker-e2e-") as directory:
            upload_dir = Path(directory)
            with patch("app.main.settings.upload_dir", upload_dir), patch(
                "app.main.settings.upload_encryption_key", encoded_key
            ), patch("app.worker.settings.upload_dir", upload_dir), patch(
                "app.worker.settings.upload_encryption_key", encoded_key
            ):
                case = persist_uploaded_case(
                    self.db, self.user, "Synthetic encrypted document", "consent-v2", False,
                    original, "application/pdf",
                )
                upload_evidence = self.db.scalar(select(Evidence).where(
                    Evidence.case_id == case.id, Evidence.source_type == "uploaded_file"
                ))
                upload_path = upload_dir / upload_evidence.details["stored_name"]
                self.assertTrue(upload_path.read_bytes().startswith(UPLOAD_MAGIC))
                self.assertEqual(upload_evidence.details["sha256"], hashlib.sha256(original).hexdigest())
                job = self.db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case.id))
                process_job(self.db, job)

            self.db.refresh(case)
            self.db.refresh(job)
            email = self.db.scalar(select(Entity).where(
                Entity.case_id == case.id, Entity.entity_type == "email"
            ))
            location = self.db.scalar(select(Entity).where(
                Entity.case_id == case.id, Entity.entity_type == "location_claim"
            ))
            matched_evidence = self.db.scalar(select(Evidence).where(
                Evidence.case_id == case.id, Evidence.source_ref == self.source.record_id
            ))
            finding = self.db.scalar(select(SystemFinding).where(
                SystemFinding.case_id == case.id, SystemFinding.entity_id == email.id,
                SystemFinding.active.is_(True),
            ))
            self.assertEqual(case.status, "completed")
            self.assertEqual(job.status, "completed")
            self.assertEqual(email.normalized_value, "recruiter@example.invalid")
            self.assertEqual(email.source_location, "pdf_page_1")
            self.assertEqual(email.extraction_method, "deterministic_regex")
            self.assertEqual(location.raw_value, "Pune")
            self.assertEqual(location.source_location, "pdf_page_1")
            self.assertEqual(location.review_status, "needs_review")
            self.assertEqual(location.extraction_confidence, 0.55)
            self.assertEqual(matched_evidence.outcome, "result")
            self.assertEqual(matched_evidence.review_status, "unreviewed")
            self.assertIsNotNone(matched_evidence.retrieved_at)
            self.assertEqual(finding.assessment, "Insufficient evidence")
            self.assertIn(matched_evidence.id, finding.evidence_ids)
            self.assertEqual(finding.supporting_evidence_ids, [])
            self.assertEqual(finding.rule_version, "exact-source-evidence-v1")


if __name__ == "__main__":
    unittest.main()
