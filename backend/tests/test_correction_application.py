"""Database-backed correction application checks without an HTTP event loop."""
import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.findings import entity_fingerprint
from app.main import apply_correction, disposition as submit_disposition, graph, list_campaigns, report, review_disposition
from app.models import AuditEvent, Case, CaseLink, CorrectionRequest, Entity, Evidence, GraphProjectionOutbox, HumanDisposition, User
from app.schemas import CorrectionApply, DispositionRequest, DispositionReviewRequest


class CorrectionApplicationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False, expire_on_commit=False)
        self.user = User(email="investigator@example.invalid", password_hash="test-only", role="investigator")
        self.case = Case(
            case_ref="RC-AAAAAAAA", title="Synthetic correction case", input_kind="message",
            submitted_text="Synthetic fixture", consent_version="consent-v2", created_by=1,
        )
        self.other_case = Case(
            case_ref="RC-BBBBBBBB", title="Synthetic related case", input_kind="message",
            submitted_text="Synthetic fixture", consent_version="consent-v2", created_by=1,
        )
        self.db.add_all([self.user, self.case, self.other_case])
        self.db.flush()
        self.entity = Entity(
            case_id=self.case.id, entity_type="phone", raw_value="+91 91234 56789",
            normalized_value="9123456789", review_status="confirmed",
        )
        other_entity = Entity(
            case_id=self.other_case.id, entity_type="phone", raw_value="+91 99887 76655",
            normalized_value="9988776655", review_status="needs_review",
        )
        self.request = CorrectionRequest(
            request_ref="CR-0123456789AB", case_ref=self.case.case_ref,
            requester_email="requester@example.invalid", description="Synthetic correction request fixture.",
            status="received", status_token_hash="a" * 64,
        )
        self.db.add_all([self.entity, other_entity, self.request])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_corrected_entity_discovers_link_and_cannot_be_replayed(self):
        result = apply_correction(
            self.request.request_ref,
            CorrectionApply(
                entity_id=self.entity.id, entity_action="correct",
                corrected_value="+91 99887 76655",
                resolution="Corrected using the verified synthetic source fixture.",
            ),
            self.db,
            self.user,
        )
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(len(result["links"]), 1)
        link = self.db.scalar(select(CaseLink))
        self.assertEqual(link.review_status, "proposed")
        self.assertEqual({link.left_case_id, link.right_case_id}, {self.case.id, self.other_case.id})

        report_response = report(self.case.id, self.db, self.user)
        report_document = json.loads(report_response.body)
        self.assertEqual(len(report_document["campaign_links"]), 1)
        self.assertEqual(report_document["campaign_links"][0]["review_status"], "proposed")
        self.assertIn("rule_version", report_document["campaign_links"][0])
        self.assertNotIn("91234 56789", report_response.body.decode())
        self.assertNotIn("99887 76655", report_response.body.decode())
        self.assertNotIn("requester@example.invalid", report_response.body.decode())

        markdown_response = report(self.case.id, self.db, self.user, format="markdown")
        markdown_report = markdown_response.body.decode()
        self.assertEqual(markdown_response.media_type, "text/markdown")
        self.assertIn("## Evidence records", markdown_report)
        self.assertIn("## Campaign links", markdown_report)
        self.assertNotIn("91234 56789", markdown_report)
        self.assertNotIn("99887 76655", markdown_report)
        self.assertNotIn("requester@example.invalid", markdown_report)

        with self.assertRaises(HTTPException) as raised:
            apply_correction(
                self.request.request_ref,
                CorrectionApply(
                    entity_id=self.entity.id, entity_action="reject",
                    resolution="A repeated correction must be refused.",
                ),
                self.db,
                self.user,
            )
        self.assertEqual(raised.exception.status_code, 409)

    def test_corrected_entity_enqueues_graph_projection_in_same_transaction(self):
        with patch("app.main.graph_store.configured", return_value=True):
            apply_correction(
                self.request.request_ref,
                CorrectionApply(
                    entity_id=self.entity.id,
                    entity_action="correct",
                    corrected_value="+91 99887 76655",
                    resolution="Corrected using the synthetic source fixture.",
                ),
                self.db,
                self.user,
            )

        self.db.refresh(self.entity)
        outbox = self.db.scalar(
            select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == self.case.id)
        )
        self.assertEqual(self.entity.normalized_value, "9988776655")
        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.operation, "upsert")
        self.assertEqual(outbox.status, "queued")
        self.assertGreaterEqual(outbox.generation, 1)

    def test_evidence_correction_reopens_approved_stronger_disposition(self):
        reviewer = User(email="reviewer@example.invalid", password_hash="test-only", role="reviewer")
        self.db.add(reviewer)
        evidence = Evidence(
            case_id=self.case.id,
            source_name="Synthetic reviewed source",
            source_type="curated_local_corpus",
            source_ref="LOCAL-SYNTHETIC-1",
            claim="Synthetic record for exact identifier",
            outcome="result",
            excerpt="Synthetic excerpt",
            authority="unverified_public_report",
            review_status="relevant",
        )
        self.db.add(evidence)
        self.db.flush()
        disposition = HumanDisposition(
            case_id=self.case.id,
            disposition="evidence_supports_concern",
            rationale="Synthetic investigator rationale based on this source.",
            evidence_ids=[evidence.id],
            status="approved",
            proposed_by=self.user.id,
            reviewed_by=reviewer.id,
            review_rationale="Synthetic independent review rationale.",
        )
        self.db.add(disposition)
        self.db.commit()

        apply_correction(
            self.request.request_ref,
            CorrectionApply(
                evidence_id=evidence.id,
                evidence_action="irrelevant",
                resolution="The source does not support the referenced claim.",
            ),
            self.db,
            self.user,
        )

        self.db.refresh(disposition)
        self.assertEqual(disposition.status, "pending_review")
        self.assertIsNone(disposition.reviewed_by)
        self.assertIsNone(disposition.reviewed_at)
        event = self.db.scalar(select(AuditEvent).where(AuditEvent.action == "human_disposition_reopened_after_correction"))
        self.assertIsNotNone(event)
        self.assertEqual(event.detail["previous_review"]["reviewed_by"], reviewer.id)
        document = json.loads(report(self.case.id, self.db, self.user).body)
        self.assertEqual(document["human_dispositions"][0]["status"], "pending_review")

    def test_entity_correction_reopens_disposition_linked_to_old_identifier_evidence(self):
        evidence = Evidence(
            case_id=self.case.id,
            source_name="Synthetic old-identifier source",
            source_type="curated_local_corpus",
            source_ref="LOCAL-SYNTHETIC-OLD",
            claim="Synthetic evidence for the original phone identifier",
            outcome="result",
            excerpt="Synthetic excerpt",
            authority="unverified_public_report",
            review_status="relevant",
            details={"entity_fingerprint": entity_fingerprint(self.entity)},
        )
        reviewer = User(email="reviewer@example.invalid", password_hash="test-only", role="reviewer")
        self.db.add_all([evidence, reviewer])
        self.db.flush()
        disposition = HumanDisposition(
            case_id=self.case.id,
            disposition="evidence_supports_concern",
            rationale="Synthetic rationale about the original identifier.",
            evidence_ids=[evidence.id],
            status="approved",
            proposed_by=self.user.id,
            reviewed_by=reviewer.id,
            review_rationale="Synthetic separate reviewer decision.",
        )
        self.db.add(disposition)
        self.db.commit()

        apply_correction(
            self.request.request_ref,
            CorrectionApply(
                entity_id=self.entity.id,
                entity_action="correct",
                corrected_value="+91 99887 76655",
                resolution="The original extracted phone value was incorrect.",
            ),
            self.db,
            self.user,
        )

        self.db.refresh(disposition)
        self.assertEqual(disposition.status, "pending_review")
        event = self.db.scalar(select(AuditEvent).where(AuditEvent.action == "human_disposition_reopened_after_correction"))
        self.assertEqual(event.detail["trigger"], "entity_claim_changed")
        self.assertEqual(event.detail["changed_evidence_ids"], [evidence.id])

    def test_closed_correction_requests_cannot_change_case_records(self):
        original_value = self.entity.raw_value
        for status in ("rejected", "resolved"):
            with self.subTest(status=status):
                self.request.status = status
                self.db.commit()
                with self.assertRaises(HTTPException) as raised:
                    apply_correction(
                        self.request.request_ref,
                        CorrectionApply(
                            entity_id=self.entity.id,
                            entity_action="reject",
                            resolution="This closed request must not alter case data.",
                        ),
                        self.db,
                        self.user,
                    )
                self.assertEqual(raised.exception.status_code, 409)
                self.db.refresh(self.entity)
                self.assertEqual(self.entity.raw_value, original_value)
                self.assertEqual(
                    self.db.scalar(select(AuditEvent).where(AuditEvent.action == "correction_applied")),
                    None,
                )

    def test_correction_cannot_restore_withdrawn_evidence_as_relevant_or_contradictory(self):
        evidence = Evidence(
            case_id=self.case.id,
            source_name="Withdrawn synthetic source",
            source_type="curated_local_corpus",
            source_ref="LOCAL-WITHDRAWN-1",
            claim="Synthetic source claim",
            outcome="result",
            excerpt="Synthetic source excerpt",
            authority="government",
            review_status="needs_review",
            details={"source_record_withdrawn": True},
        )
        self.db.add(evidence)
        self.db.commit()

        for action in ("relevant", "contradicts"):
            with self.subTest(action=action):
                with self.assertRaises(HTTPException) as raised:
                    apply_correction(
                        self.request.request_ref,
                        CorrectionApply(
                            evidence_id=evidence.id,
                            evidence_action=action,
                            resolution="The retired source cannot be restored through correction.",
                        ),
                        self.db,
                        self.user,
                    )
                self.assertEqual(raised.exception.status_code, 409)
                self.db.refresh(evidence)
                self.assertEqual(evidence.review_status, "needs_review")
                self.db.refresh(self.request)
                self.assertEqual(self.request.status, "received")

    def test_withdrawn_evidence_cannot_support_or_approve_stronger_human_disposition(self):
        evidence = Evidence(
            case_id=self.case.id,
            source_name="Withdrawn synthetic source",
            source_type="curated_local_corpus",
            source_ref="LOCAL-WITHDRAWN-DISPOSITION",
            claim="Synthetic source claim",
            outcome="result",
            excerpt="Synthetic source excerpt",
            authority="government",
            review_status="relevant",
            details={"source_record_withdrawn": True},
        )
        reviewer = User(email="separate-reviewer@example.invalid", password_hash="test-only", role="reviewer")
        self.db.add_all([evidence, reviewer])
        self.db.flush()

        with self.assertRaises(HTTPException) as submission:
            submit_disposition(
                self.case.id,
                DispositionRequest(
                    disposition="confirmed_authoritative",
                    rationale="Synthetic stronger disposition rationale.",
                    evidence_ids=[evidence.id],
                ),
                self.db,
                self.user,
            )
        self.assertEqual(submission.exception.status_code, 400)

        pending = HumanDisposition(
            case_id=self.case.id,
            disposition="confirmed_authoritative",
            rationale="Legacy synthetic disposition citing withdrawn evidence.",
            evidence_ids=[evidence.id],
            status="pending_review",
            proposed_by=self.user.id,
        )
        self.db.add(pending)
        self.db.commit()

        with self.assertRaises(HTTPException) as approval:
            review_disposition(
                pending.id,
                DispositionReviewRequest(status="approved", rationale="A separate reviewer is checking the synthetic source.", resolution="Do not approve withdrawn support."),
                self.db,
                reviewer,
            )
        self.assertEqual(approval.exception.status_code, 409)

    def test_postgres_graph_fallback_masks_identifiers_and_source_url_details(self):
        self.db.add(self.entity)
        self.db.flush()
        evidence = Evidence(
            case_id=self.case.id,
            source_name="Private source title",
            source_type="curated_local_corpus",
            source_ref="https://records.example.org/person/Asha-Menon?phone=9876543210",
            claim="Private source claim naming Asha Menon",
            outcome="result",
            excerpt="Asha Menon phone 9876543210",
            authority="curated",
            review_status="relevant",
            details={"entity_fingerprint": entity_fingerprint(self.entity)},
        )
        self.db.add(evidence)
        self.db.commit()

        with patch("app.main.graph_store.configured", return_value=False):
            result = graph(self.db, self.user)

        encoded = json.dumps(result)
        self.assertEqual(result["projection"], "postgresql-derived")
        self.assertIn("https://records.example.org/[path redacted]?[query redacted]", encoded)
        self.assertIn("••••6789", [node["label"] for node in result["nodes"]])
        for private_value in ("9876543210", "Asha-Menon", "Private source title", "Private source claim"):
            self.assertNotIn(private_value, encoded)

    def test_analyst_campaign_view_masks_shared_identifiers_and_related_source_text(self):
        self.db.add(Entity(
            case_id=self.other_case.id,
            entity_type="phone",
            raw_value="+91 91234 56789",
            normalized_value="9123456789",
            review_status="confirmed",
        ))
        self.db.add(CaseLink(
            left_case_id=self.case.id,
            right_case_id=self.other_case.id,
            rule_version="exact-v1",
            strength=100,
            reasons=["Exact phone match: 9123456789 (weight 100)"],
            review_status="proposed",
        ))
        self.db.add(Evidence(
            case_id=self.case.id,
            source_name="Synthetic private source title",
            source_type="curated_local_corpus",
            source_ref="https://records.example.invalid/person/Asha-Menon?phone=9123456789",
            claim="Synthetic claim identifying Asha Menon",
            outcome="result",
            excerpt="Asha Menon contact 9123456789",
            authority="curated",
            details={"matched_entity_type": "phone", "matched_normalized_value": "9123456789"},
        ))
        analyst = User(email="analyst@example.invalid", password_hash="test-only", role="analyst")
        self.db.add(analyst)
        self.db.commit()

        result = list_campaigns(self.db, analyst)
        encoded = json.dumps(result)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["links"][0]["matched_entities"][0]["value"], "••••6789")
        for private_value in (
            "9123456789", "Private source title", "person/Asha-Menon", "Synthetic claim identifying Asha Menon",
        ):
            self.assertNotIn(private_value, encoded)
        self.assertIn("https://records.example.invalid/[path redacted]?[query redacted]", encoded)


if __name__ == "__main__":
    unittest.main()
