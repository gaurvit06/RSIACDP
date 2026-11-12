import unittest
from types import SimpleNamespace

from app.reporting import render_markdown_report
from app.main import serialize_finding


class MarkdownReportTests(unittest.TestCase):
    def test_report_contains_provenance_decisions_limits_and_safe_language(self):
        document = {
            "case_ref": "RC-1234ABCD",
            "title": "[case title restricted for privacy]",
            "assessment": "Insufficient evidence",
            "created_at": "2026-01-01T00:00:00+00:00",
            "generated_at": "2026-01-02T00:00:00+00:00",
            "consent": {"version": "consent-v2"},
            "evidence_summary": {"total": 1, "by_outcome": {"result": 1}, "by_review_status": {"relevant": 1}},
            "entities": [{"type": "phone", "value": "••••••3210", "review_status": "confirmed", "source_location": "page 1", "source_start_char": 4, "source_end_char": 14, "extraction_confidence": 0.99, "extraction_uncertainty": "Claim truth is unverified."}],
            "evidence": [{"id": 7, "source_name": "[source name restricted for privacy]", "source_type": "curated", "source_ref": "https://example.org", "outcome": "result", "authority": "curated", "retrieved_at": "2026-01-01T01:00:00+00:00", "review_status": "relevant", "review_reason": "[review rationale restricted for privacy]", "claim": "[source claim restricted for privacy]", "excerpt": "[source excerpt restricted for privacy]"}],
            "machine_findings": [{"assessment": "Insufficient evidence", "scope": "claim", "claim": "[claim restricted for privacy]", "observation": "No adverse evidence found.", "rule_name": "exact-source-evidence", "rule_version": "v1", "evidence_ids": [7], "supporting_evidence_ids": [], "conflict_evidence_ids": [], "unreviewed_evidence_ids": [], "limitations": "This does not determine wrongdoing.", "evidence_snapshot": [{"evidence_id": 7, "source_name": "[source name restricted for privacy]", "outcome": "result", "retrieved_at": "2026-01-01T01:00:00+00:00", "source_ref": "https://example.org"}]}],
            "finding_history": [{"active": False, "assessment": "No adverse evidence found", "claim": "[claim restricted for privacy]", "rule_name": "exact-source-evidence", "rule_version": "v1", "created_at": "2025-12-31T00:00:00+00:00", "superseded_at": "2026-01-01T00:00:00+00:00"}],
            "campaign_link_note": "Campaign connections are investigative leads.",
            "campaign_links": [{"left_case_id": 1, "right_case_id": 2, "strength": 60, "review_status": "proposed", "rule_version": "exact-v1", "reasons": ["shared phone identifier [redacted]"]}],
            "human_dispositions": [{"display_label": "Insufficient evidence", "status": "approved", "evidence_ids": [7], "rationale": "[review rationale restricted for privacy]", "created_at": "2026-01-01T02:00:00+00:00", "reviewed_at": "2026-01-01T03:00:00+00:00"}],
            "timeline": [{"occurred_at": "2026-01-01T03:00:00+00:00", "action": "evidence_reviewed", "actor_type": "workspace_user", "details": {"status": "relevant"}}],
            "rule_versions": ["exact-v1"],
            "limitations": "Evidence limitations apply.",
        }
        rendered = render_markdown_report(document)
        for expected in (
            "## Case scope", "## Evidence records", "## Machine findings", "## Campaign links",
            "## Finding history", "## Human investigator dispositions", "## Audit timeline", "exact-v1",
            "2026-01-01T01:00:00+00:00", "leads, not proof of wrongdoing", "••••••3210",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
        self.assertNotIn("9876543210", rendered)

    def test_source_text_cannot_create_markdown_headings_or_links(self):
        hostile = "# fake section [click](https://attacker.invalid) and https://other.invalid <script>bad()</script>"
        rendered = render_markdown_report({"case_ref": "RC-1234ABCD", "title": hostile})
        self.assertNotIn("\n# fake section", rendered)
        self.assertIn(r"\# fake section", rendered)
        self.assertNotIn("[click](https://attacker.invalid)", rendered)
        self.assertNotIn("https://other.invalid", rendered)
        self.assertNotIn("<script>", rendered)

    def test_analyst_finding_snapshot_drops_unexpected_stored_fields(self):
        finding = SimpleNamespace(
            evidence_snapshot=[{
                "evidence_id": 3,
                "source_name": "Synthetic source",
                "source_type": "curated_local_corpus",
                "source_ref": "https://example.invalid/person/private?phone=9876543210",
                "claim": "Synthetic claim",
                "outcome": "result",
                "authority": "government",
                "retrieved_at": "2026-10-26T00:00:00+00:00",
                "future_private_field": "Synthetic person name and secret value",
            }],
            id=1,
            entity_id=2,
            scope="entity",
            claim="Synthetic identifier claim",
            assessment="Insufficient evidence",
            observation="No finding is made.",
            evidence_ids=[3],
            supporting_evidence_ids=[],
            conflict_evidence_ids=[],
            unreviewed_evidence_ids=[3],
            rule_name="test-rule",
            rule_version="test-v1",
            limitations="Synthetic limitation.",
            created_at=SimpleNamespace(isoformat=lambda: "2026-10-26T00:00:00+00:00"),
        )
        result = serialize_finding(finding, redact=True)
        snapshot = result["evidence_snapshot"][0]
        self.assertEqual(
            set(snapshot),
            {"evidence_id", "source_name", "source_type", "source_ref", "claim", "outcome", "authority", "retrieved_at"},
        )
        self.assertNotIn("future_private_field", snapshot)
        self.assertEqual(snapshot["source_name"], "[source name restricted for privacy]")
        self.assertEqual(snapshot["claim"], "[source claim restricted for privacy]")
        self.assertNotIn("9876543210", snapshot["source_ref"])


if __name__ == "__main__":
    unittest.main()
