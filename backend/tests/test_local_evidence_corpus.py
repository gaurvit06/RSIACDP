"""Database-backed checks for the offline curated evidence source."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import ValidationError

from app.db import Base
from app.main import add_evidence_record, list_evidence_corpus, retire_evidence_record, review_evidence
from app.models import AuditEvent, Case, Entity, Evidence, HumanDisposition, SourceRecord, User
from app.schemas import EvidenceReviewRequest, SourceRecordCreate, SourceRecordRetire
from app.source_adapters import LocalEvidenceCorpusAdapter


class LocalEvidenceCorpusTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(email="corpus-operator@example.invalid", password_hash="synthetic-test-hash", role="investigator")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        self.reviewer = User(email="corpus-reviewer@example.invalid", password_hash="synthetic-test-hash", role="reviewer")
        self.db.add(self.reviewer)
        self.db.commit()
        self.db.refresh(self.reviewer)
        self.entity = SimpleNamespace(entity_type="email", normalized_value="hr@example.invalid")

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def write_corpus(self, records):
        temp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        self.addCleanup(Path(temp.name).unlink, missing_ok=True)
        with temp:
            json.dump({"version": "test-corpus-v1", "records": records}, temp)
        return Path(temp.name)

    def test_empty_corpus_returns_neutral_no_result_with_provenance(self):
        adapter = LocalEvidenceCorpusAdapter(self.db, self.write_corpus([]))

        result = adapter.check(self.entity)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source_type, "curated_local_corpus")
        self.assertEqual(result[0].outcome, "no_result")
        self.assertEqual(result[0].authority, "curated")
        self.assertIn("not evidence of fraud or legitimacy", result[0].excerpt)
        self.assertEqual(result[0].details["lookup"], "exact_normalized_identifier")
        self.assertEqual(len(result[0].details["entity_fingerprint"]), 64)
        self.assertIsNotNone(result[0].retrieved_at.tzinfo)

    def test_exact_persisted_source_record_returns_traceable_result(self):
        record = SourceRecord(
            record_id="LOCAL-0123456789ABCDEF",
            entity_type="email",
            normalized_value=self.entity.normalized_value,
            source_name="Synthetic authorized local record",
            source_type="operator_reviewed_record",
            source_ref="https://evidence.example.invalid/records/synthetic-1",
            claim="The synthetic record contains this exact email identifier.",
            outcome="result",
            excerpt="Synthetic record excerpt for an offline adapter test.",
            authority="unverified_public_report",
            created_by=self.user.id,
        )
        self.db.add(record)
        self.db.commit()

        result = LocalEvidenceCorpusAdapter(self.db, self.write_corpus([])).check(self.entity)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source_ref, record.record_id)
        self.assertEqual(result[0].outcome, "result")
        self.assertEqual(result[0].claim, record.claim)
        self.assertEqual(result[0].details["source_record_ref"], record.source_ref)
        self.assertEqual(result[0].details["source_category"], record.source_type)
        self.assertEqual(result[0].details["matched_entity_type"], "email")
        self.assertEqual(result[0].details["matched_normalized_value"], self.entity.normalized_value)
        self.assertTrue(result[0].details["source_record_retrieved_at"])

    def test_bundled_record_requires_stable_record_identifier(self):
        path = self.write_corpus([{
            "entity_type": "email",
            "normalized_value": self.entity.normalized_value,
            "source_name": "Synthetic corpus entry",
            "claim": "Synthetic fixture claim.",
        }])

        with self.assertRaisesRegex(ValueError, "record_id"):
            LocalEvidenceCorpusAdapter(self.db, path).check(self.entity)

    def test_corpus_entry_normalizes_identifier_and_writes_minimal_audit(self):
        body = SourceRecordCreate(
            entity_type="phone",
            value="+91 98765 43210",
            source_name="Synthetic reviewed source",
            source_type="government",
            source_ref="https://records.example.invalid/item/1",
            claim="The synthetic source records this phone identifier.",
            outcome="result",
            excerpt="Synthetic excerpt with no person data.",
            authority="government",
        )

        created = add_evidence_record(body, self.db, self.user)

        self.assertEqual(created["normalized_value"], "9876543210")
        self.assertTrue(created["record_id"].startswith("LOCAL-"))
        self.db.flush()
        audit = self.db.query(AuditEvent).filter_by(action="evidence_corpus_record_created").one()
        self.assertEqual(audit.actor_id, self.user.id)
        self.assertEqual(audit.detail, {
            "record_id": created["record_id"],
            "entity_type": "phone",
            "outcome": "result",
            "authority": "government",
        })
        self.assertNotIn("9876543210", str(audit.detail))

    def test_authoritative_source_requires_matching_category_and_reference(self):
        mismatched = SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="news", source_ref="https://news.example.invalid/item/1",
            claim="A synthetic source claim.", outcome="result", authority="government",
        )
        with self.assertRaises(HTTPException) as mismatch:
            add_evidence_record(mismatched, self.db, self.user)
        self.assertEqual(mismatch.exception.status_code, 400)

        missing_reference = SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="government", claim="A synthetic source claim.", outcome="result", authority="government",
        )
        with self.assertRaises(HTTPException) as no_reference:
            add_evidence_record(missing_reference, self.db, self.user)
        self.assertEqual(no_reference.exception.status_code, 400)
        self.assertEqual(self.db.query(SourceRecord).count(), 0)

    def test_duplicate_normalized_source_claim_is_rejected(self):
        body = SourceRecordCreate(
            entity_type="phone", value="+91 98765 43210", source_name="Synthetic source",
            source_type="government", source_ref="https://records.example.invalid/item/1",
            claim="The synthetic source records this phone identifier.", outcome="result", authority="government",
        )
        add_evidence_record(body, self.db, self.user)
        duplicate_with_formatting_difference = body.model_copy(update={"value": "98765-43210"})

        with self.assertRaises(HTTPException) as duplicate:
            add_evidence_record(duplicate_with_formatting_difference, self.db, self.user)

        self.assertEqual(duplicate.exception.status_code, 409)
        self.assertEqual(self.db.query(SourceRecord).count(), 1)

    def test_corpus_listing_is_audited_and_returns_traceable_fields(self):
        add_evidence_record(SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="other", source_ref="https://source.example.invalid/item/1",
            claim="A synthetic source claim.", outcome="result", authority="curated",
        ), self.db, self.user)

        listed = list_evidence_corpus(self.db, self.user)

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["source_ref"], "https://source.example.invalid/item/1")
        self.assertTrue(listed[0]["retrieved_at"])
        self.assertEqual(self.db.query(AuditEvent).filter_by(action="evidence_corpus_accessed").count(), 1)

    def test_retiring_corpus_record_invalidates_case_support_and_reopens_disposition(self):
        source = add_evidence_record(SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="government", source_ref="https://source.example.invalid/item/1",
            claim="A synthetic source claim.", outcome="result", excerpt="Synthetic source excerpt.", authority="government",
        ), self.db, self.user)
        case = Case(case_ref="RC-ABCDEF12", title="Synthetic case", input_kind="message", consent_version="consent-v2", created_by=self.user.id)
        self.db.add(case)
        self.db.flush()
        entity = Entity(case_id=case.id, entity_type="email", raw_value="hr@example.invalid", normalized_value="hr@example.invalid", review_status="confirmed")
        self.db.add(entity)
        evidence = Evidence(
            case_id=case.id, source_name="Synthetic source", source_type="curated_local_corpus",
            source_ref=source["record_id"], claim="A synthetic source claim.", outcome="result",
            excerpt="Synthetic source excerpt.", authority="government", review_status="relevant",
            details={"matched_entity_type": "email", "matched_normalized_value": "hr@example.invalid", "source_record_ref": "https://source.example.invalid/item/1", "source_category": "government"},
        )
        self.db.add(evidence)
        self.db.flush()
        disposition = HumanDisposition(
            case_id=case.id, disposition="confirmed_authoritative", rationale="Synthetic reviewer disposition.",
            evidence_ids=[evidence.id], status="approved", proposed_by=self.user.id, reviewed_by=self.reviewer.id,
            review_rationale="Synthetic independent review.",
        )
        self.db.add(disposition)
        self.db.commit()

        with patch("app.main.enqueue_graph_sync") as enqueue:
            result = retire_evidence_record(source["record_id"], SourceRecordRetire(rationale="The synthetic source entry was found to be outdated."), self.db, self.reviewer)

        self.db.refresh(case)
        self.db.refresh(evidence)
        self.db.refresh(disposition)
        stored_source = self.db.query(SourceRecord).filter_by(record_id=source["record_id"]).one()
        self.assertFalse(stored_source.active)
        self.assertEqual(stored_source.retired_by, self.reviewer.id)
        self.assertEqual(result["affected_evidence_count"], 1)
        self.assertEqual(result["affected_case_count"], 1)
        self.assertEqual(evidence.review_status, "needs_review")
        self.assertTrue(evidence.details["source_record_withdrawn"])
        invalidation_audit = self.db.query(AuditEvent).filter_by(action="evidence_review_invalidated_by_source_retirement").one()
        self.assertEqual(invalidation_audit.detail["previous_review"]["review_status"], "relevant")
        self.assertEqual(invalidation_audit.detail["new_review_status"], "needs_review")
        self.assertEqual(case.assessment, "Insufficient evidence")
        self.assertEqual(disposition.status, "pending_review")
        self.assertEqual(disposition.reviewed_by, None)
        self.assertEqual(enqueue.call_args_list[0].args, (self.db, case.id))
        self.assertEqual(self.db.query(AuditEvent).filter_by(action="evidence_corpus_record_retired").count(), 1)
        with self.assertRaises(HTTPException) as review_rejected:
            review_evidence(case.id, evidence.id, EvidenceReviewRequest(status="relevant", rationale="The withdrawn evidence cannot be revalidated here."), self.db, self.user)
        self.assertEqual(review_rejected.exception.status_code, 409)
        self.assertEqual(evidence.review_status, "needs_review")
        self.assertEqual(LocalEvidenceCorpusAdapter(self.db, self.write_corpus([])).check(SimpleNamespace(entity_type="email", normalized_value="hr@example.invalid"))[0].outcome, "no_result")

    def test_retirement_rejects_missing_or_already_retired_record(self):
        with self.assertRaises(ValidationError):
            SourceRecordRetire(rationale=" " * 12)
        with self.assertRaises(HTTPException) as missing:
            retire_evidence_record("LOCAL-MISSING000000", SourceRecordRetire(rationale="Synthetic retirement reason."), self.db, self.reviewer)
        self.assertEqual(missing.exception.status_code, 404)

        source = add_evidence_record(SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="other", claim="A synthetic source claim.", outcome="result", authority="curated",
        ), self.db, self.user)
        retire_evidence_record(source["record_id"], SourceRecordRetire(rationale="The synthetic source entry was found to be outdated."), self.db, self.reviewer)
        with self.assertRaises(HTTPException) as duplicate:
            retire_evidence_record(source["record_id"], SourceRecordRetire(rationale="The synthetic source entry was found to be outdated."), self.db, self.reviewer)
        self.assertEqual(duplicate.exception.status_code, 409)

        restored = add_evidence_record(SourceRecordCreate(
            entity_type="email", value="hr@example.invalid", source_name="Synthetic source",
            source_type="other", source_ref="", claim="A synthetic source claim.", outcome="result", authority="curated",
        ), self.db, self.user)
        self.assertNotEqual(restored["record_id"], source["record_id"])
        self.assertEqual(self.db.query(SourceRecord).filter_by(active=True).count(), 1)


if __name__ == "__main__":
    unittest.main()
