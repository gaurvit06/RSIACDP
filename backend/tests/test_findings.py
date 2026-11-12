import hashlib
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from app.findings import LIMITATIONS, assess_case


def make_entity(review_status="confirmed", entity_type="phone"):
    value = "+91 98765 43210" if entity_type == "phone" else "agency@example.org"
    normalized = "9876543210" if entity_type == "phone" else value
    return SimpleNamespace(id=1, case_id=1, entity_type=entity_type, raw_value=value, normalized_value=normalized, review_status=review_status)


def make_evidence(entity, outcome="result", review_status="relevant", authority="government", category="government", record_ref="https://records.example.gov/item/1"):
    fingerprint = hashlib.sha256(f"{entity.entity_type}:{entity.normalized_value}".encode()).hexdigest()
    return SimpleNamespace(
        id=4, case_id=1, outcome=outcome, review_status=review_status, authority=authority,
        source_name="Synthetic source", source_type="curated_local_corpus", source_ref="LOCAL-TEST-1",
        claim="Synthetic record supports an identifier observation", excerpt="Synthetic excerpt",
        retrieved_at=datetime.now(timezone.utc), details={"entity_fingerprint": fingerprint, "source_category": category, "source_record_ref": record_ref},
    )


class FindingRuleTests(unittest.TestCase):
    def test_authoritative_label_requires_confirmed_entity_and_relevant_traceable_result(self):
        entity = make_entity()
        result, assessment = assess_case([entity], [make_evidence(entity)])
        self.assertEqual(assessment, "Confirmed by an authoritative source")
        self.assertEqual(result[0]["evidence_ids"], [4])
        self.assertIn("does not establish wrongdoing", LIMITATIONS)

        entity.review_status = "needs_review"
        _, assessment = assess_case([entity], [make_evidence(entity)])
        self.assertEqual(assessment, "Insufficient evidence")

    def test_unverified_report_is_allegation_and_requires_relevance_review(self):
        entity = make_entity()
        report = make_evidence(entity, authority="unverified_public_report", category="news")
        findings, assessment = assess_case([entity], [report])
        self.assertEqual(assessment, "Evidence supports concern")
        self.assertIn("allegation", findings[0]["observation"])

        report.review_status = "unreviewed"
        _, assessment = assess_case([entity], [report])
        self.assertEqual(assessment, "Insufficient evidence")

    def test_no_result_is_neutral_and_errors_never_become_negative_evidence(self):
        entity = make_entity()
        no_result = make_evidence(entity, outcome="no_result", authority="curated", category=None, record_ref="")
        _, assessment = assess_case([entity], [no_result])
        self.assertEqual(assessment, "No adverse evidence found")

        error = make_evidence(entity, outcome="error", authority="curated", category=None, record_ref="")
        _, assessment = assess_case([entity], [error])
        self.assertEqual(assessment, "Insufficient evidence")

    def test_withdrawn_local_no_result_cannot_remain_a_current_negative_assessment(self):
        entity = make_entity()
        withdrawn = make_evidence(entity, outcome="no_result", authority="curated", category=None, record_ref="")
        withdrawn.details["source_record_withdrawn"] = True
        withdrawn.review_status = "needs_review"

        findings, assessment = assess_case([entity], [withdrawn])

        self.assertEqual(assessment, "Insufficient evidence")
        self.assertEqual(findings[0]["unreviewed_evidence_ids"], [withdrawn.id])
        self.assertIn("withdrawn", findings[0]["observation"])

    def test_withdrawn_relevant_result_cannot_support_a_finding(self):
        entity = make_entity()
        withdrawn = make_evidence(entity, review_status="relevant")
        withdrawn.details["source_record_withdrawn"] = True

        findings, assessment = assess_case([entity], [withdrawn])

        self.assertEqual(assessment, "Insufficient evidence")
        self.assertEqual(findings[0]["supporting_evidence_ids"], [])
        self.assertEqual(findings[0]["unreviewed_evidence_ids"], [withdrawn.id])

    def test_withdrawn_evidence_reviewed_irrelevant_is_not_left_in_review_queue(self):
        entity = make_entity()
        withdrawn = make_evidence(entity, review_status="irrelevant")
        withdrawn.details["source_record_withdrawn"] = True

        findings, assessment = assess_case([entity], [withdrawn])

        self.assertEqual(assessment, "Insufficient evidence")
        self.assertEqual(findings[0]["supporting_evidence_ids"], [])
        self.assertEqual(findings[0]["unreviewed_evidence_ids"], [])

    def test_active_result_can_support_finding_without_counting_withdrawn_result(self):
        entity = make_entity()
        withdrawn = make_evidence(entity, review_status="relevant")
        withdrawn.details["source_record_withdrawn"] = True
        active = make_evidence(entity, record_ref="https://records.example.gov/item/2")
        active.id = 8

        findings, assessment = assess_case([entity], [withdrawn, active])

        self.assertEqual(assessment, "Confirmed by an authoritative source")
        self.assertEqual(findings[0]["supporting_evidence_ids"], [active.id])
        self.assertIn(withdrawn.id, findings[0]["unreviewed_evidence_ids"])

    def test_withdrawn_source_does_not_hide_an_investigator_recorded_conflict(self):
        entity = make_entity()
        withdrawn = make_evidence(entity, outcome="result", review_status="needs_review")
        withdrawn.details["source_record_withdrawn"] = True
        conflict = make_evidence(entity, outcome="result", review_status="contradicts")
        conflict.id = 9

        findings, assessment = assess_case([entity], [withdrawn, conflict])

        self.assertEqual(assessment, "Insufficient evidence")
        self.assertEqual(findings[0]["conflict_evidence_ids"], [conflict.id])
        self.assertIn("does not resolve the conflict", findings[0]["observation"])

    def test_external_registry_result_cannot_become_local_corpus_assessment(self):
        entity = make_entity(entity_type="domain")
        registry = make_evidence(entity, outcome="result", authority="registry_data", category=None, record_ref="")
        registry.source_type = "rdap_registry"
        _, assessment = assess_case([entity], [registry])
        self.assertEqual(assessment, "Insufficient evidence")
        empty_registry = make_evidence(entity, outcome="no_result", authority="registry_data", category=None, record_ref="")
        empty_registry.source_type = "rdap_registry"
        _, assessment = assess_case([entity], [empty_registry])
        self.assertEqual(assessment, "Insufficient evidence")

    def test_investigator_marked_conflict_blocks_stronger_assessment(self):
        entity = make_entity()
        conflict = make_evidence(entity)
        conflict.review_status = "contradicts"
        findings, assessment = assess_case([entity], [conflict])
        self.assertEqual(assessment, "Insufficient evidence")
        self.assertEqual(findings[0]["conflict_evidence_ids"], [conflict.id])

    def test_unsupported_claim_type_blocks_case_level_no_adverse_outcome(self):
        phone = make_entity()
        role = SimpleNamespace(id=2, case_id=1, entity_type="job_title_claim", raw_value="Analyst", normalized_value="analyst", review_status="confirmed")
        no_result = make_evidence(phone, outcome="no_result", authority="curated", category=None, record_ref="")
        _, assessment = assess_case([phone, role], [no_result])
        self.assertEqual(assessment, "Insufficient evidence")


if __name__ == "__main__":
    unittest.main()
