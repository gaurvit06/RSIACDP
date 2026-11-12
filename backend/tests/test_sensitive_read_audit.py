"""Persisted audit checks for sensitive investigator and reviewer reads."""
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.main import pending_dispositions
from app.models import AuditEvent, Case, Evidence, HumanDisposition, User


class SensitiveReadAuditTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_review_queue_access_persists_a_minimized_audit_event(self):
        with Session(self.engine) as db:
            reviewer = User(email="reviewer@example.invalid", password_hash="synthetic-hash", role="reviewer")
            db.add(reviewer)
            db.commit()
            db.refresh(reviewer)

            self.assertEqual(pending_dispositions(db, reviewer), [])
            event = db.scalar(select(AuditEvent).where(AuditEvent.action == "pending_dispositions_accessed"))
            self.assertIsNotNone(event)
            self.assertEqual(event.actor_id, reviewer.id)
            self.assertEqual(event.detail, {"disposition_count": 0})
            self.assertIsNone(event.case_id)

    def test_reviewer_queue_exposes_cited_source_and_rationale_for_inspection(self):
        with Session(self.engine) as db:
            investigator = User(email="investigator@example.invalid", password_hash="synthetic-hash", role="investigator")
            reviewer = User(email="reviewer@example.invalid", password_hash="synthetic-hash", role="reviewer")
            db.add_all([investigator, reviewer])
            db.flush()
            case = Case(
                case_ref="RC-ABCDEF98",
                title="Synthetic reviewer inspection case",
                input_kind="message",
                submitted_text="Synthetic case text.",
                consent_version="consent-test-v1",
                created_by=investigator.id,
            )
            db.add(case)
            db.flush()
            evidence = Evidence(
                case_id=case.id,
                source_name="Synthetic reviewed source",
                source_type="curated_local_corpus",
                source_ref="LOCAL-REVIEW-1",
                claim="Synthetic source claim for reviewer inspection.",
                outcome="result",
                excerpt="Synthetic source excerpt that the second reviewer must inspect.",
                authority="government",
                details={"source_record_ref": "https://records.example.invalid/item/1"},
                review_status="relevant",
            )
            disposition = HumanDisposition(
                case_id=case.id,
                disposition="confirmed_authoritative",
                rationale="Synthetic investigator explanation for this source claim.",
                evidence_ids=[],
                status="pending_review",
                proposed_by=investigator.id,
            )
            db.add_all([evidence, disposition])
            db.flush()
            disposition.evidence_ids = [evidence.id]
            db.commit()

            pending = pending_dispositions(db, reviewer)

            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["rationale"], "Synthetic investigator explanation for this source claim.")
            self.assertEqual(pending[0]["evidence"][0]["claim"], evidence.claim)
            self.assertEqual(pending[0]["evidence"][0]["excerpt"], evidence.excerpt)
            self.assertEqual(pending[0]["evidence"][0]["details"]["source_record_ref"], "https://records.example.invalid/item/1")
            self.assertNotEqual(pending[0]["evidence"][0]["excerpt"], "[source excerpt restricted for privacy]")


if __name__ == "__main__":
    unittest.main()
