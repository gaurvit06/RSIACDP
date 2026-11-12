import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.file_validation import content_matches_type
from app import graph_store
from app.models import Case, Entity, Evidence, User
from app.main import graph as graph_endpoint


class FileValidationTests(unittest.TestCase):
    def test_accepts_matching_signatures(self):
        self.assertTrue(content_matches_type(b"%PDF-1.7 payload", "application/pdf"))
        self.assertTrue(content_matches_type(b"\x89PNG\r\n\x1a\n" + b"x" * 16, "image/png"))
        self.assertTrue(content_matches_type(b"\xff\xd8\xffpayload", "image/jpeg"))
        self.assertTrue(content_matches_type(b"RIFF" + b"0000" + b"WEBP" + b"payload", "image/webp"))

    def test_rejects_mismatched_and_unknown_content_types(self):
        self.assertFalse(content_matches_type(b"%PDF-1.7", "image/png"))
        self.assertFalse(content_matches_type(b"plain text", "application/pdf"))
        self.assertFalse(content_matches_type(b"%PDF-1.7", "application/octet-stream"))


class GraphProjectionTests(unittest.TestCase):
    def test_projection_merges_normalized_cross_case_entity_keys(self):
        session = MagicMock()
        driver = MagicMock()
        driver.__enter__.return_value = driver
        driver.session.return_value.__enter__.return_value = session
        entity = {"entity_key": "phone:9876543210", "entity_type": "phone", "normalized_value": "9876543210", "display_value": "••••3210", "review_status": "needs_review"}
        evidence = {"evidence_key": "evidence:opaque", "case_id": 1, "source_type": "curated_local_corpus", "source_ref": "https://source.example.test/[path redacted]", "outcome": "result", "authority": "government", "retrieved_at": "2026-10-23T00:00:00+00:00", "review_status": "relevant", "matched_entity_key": "phone:9876543210"}
        with patch.object(graph_store, "_driver", return_value=driver), patch.object(graph_store, "configured", return_value=True):
            graph_store.sync_case(1, "RC-1", "2026-10-23T00:00:00+00:00", [entity], [evidence], [])
        query = session.run.call_args_list[0].args[0]
        params = session.run.call_args_list[0].kwargs
        self.assertIn("MERGE (e:CaseworkIdentifier {entity_key: item.entity_key})", query)
        self.assertEqual(params["entities"][0]["entity_key"], "phone:9876543210")
        all_queries = " ".join(call.args[0] for call in session.run.call_args_list)
        self.assertIn("CASEWORK_HAS_EVIDENCE", all_queries)
        self.assertIn("CASEWORK_CHECKS_IDENTIFIER", all_queries)
        self.assertIn("REMOVE c.title", all_queries)
        self.assertIn("REMOVE v.source_name, v.claim, v.excerpt, v.review_reason", all_queries)
        self.assertNotIn("SET v.claim", all_queries)
        self.assertNotIn("SET v.excerpt", all_queries)
        self.assertNotIn("SET v.review_reason", all_queries)
        self.assertEqual(session.run.call_args_list[1].kwargs["evidence"][0]["source_type"], "curated_local_corpus")

    def test_evidence_projection_preserves_provenance_and_redacts_identifiers(self):
        evidence = SimpleNamespace(
            id=19, case_id=3, source_name="Registry for +91 98765 43210", source_type="curated_local_corpus",
            source_ref="https://registry.example.test/private?phone=9876543210",
            claim="Matched phone +91 98765 43210", outcome="result", excerpt="Record: +91 98765 43210",
            authority="government", retrieved_at=datetime(2026, 10, 23, tzinfo=timezone.utc),
            review_status="relevant", review_reason="Confirmed +91 98765 43210",
            details={"matched_entity_type": "phone", "matched_normalized_value": "9876543210"},
        )
        node = graph_store.serialize_evidence(evidence)
        self.assertTrue(node["evidence_key"].startswith("evidence:"))
        self.assertEqual(node["case_id"], 3)
        self.assertEqual(node["source_type"], "curated_local_corpus")
        self.assertEqual(node["outcome"], "result")
        self.assertEqual(node["review_status"], "relevant")
        self.assertEqual(node["matched_entity_key"], "phone:9876543210")
        self.assertNotIn("9876543210", node["source_ref"])
        self.assertNotIn("source_name", node)
        self.assertNotIn("claim", node)
        self.assertNotIn("excerpt", node)
        self.assertNotIn("review_reason", node)
        self.assertEqual(node["retrieved_at"], "2026-10-23T00:00:00+00:00")

    def test_evidence_matches_entity_through_internal_fingerprint(self):
        evidence = SimpleNamespace(
            id=20, case_id=3, source_name="source", source_type="curated_local_corpus", source_ref="LOCAL-ABCDEF0123456789",
            outcome="result", authority="curated", retrieved_at=None, review_status="unreviewed", review_reason="",
            details={"entity_fingerprint": "fingerprint-value"},
        )
        node = graph_store.serialize_evidence(evidence, {"fingerprint-value": "email:agent@example.org"})
        self.assertEqual(node["matched_entity_key"], "email:agent@example.org")

    def test_graph_campaign_edge_preserves_signal_strength_and_rule_version(self):
        session = MagicMock()
        driver = MagicMock()
        driver.__enter__.return_value = driver
        driver.session.return_value.__enter__.return_value = session
        responses = [
            SimpleNamespace(data=lambda: [
                {"case_id": 7, "case_ref": "RC-12345678", "created_at": "2026-10-23", "entities": []},
                {"case_id": 8, "case_ref": "RC-87654321", "created_at": "2026-10-23", "entities": []},
            ]),
            SimpleNamespace(data=lambda: []),
            SimpleNamespace(data=lambda: []),
            SimpleNamespace(data=lambda: [{"left_id": 7, "right_id": 8, "review_status": "proposed", "strength": 40, "rule_version": "campaign-signals-v3", "reasons": ["phone exact match (+40)"]}]),
        ]
        session.run.side_effect = responses
        with patch.object(graph_store, "_driver", return_value=driver):
            result = graph_store.graph_data()
        campaign_edge = next(edge for edge in result["edges"] if edge["kind"] == "proposed_campaign_link")
        self.assertEqual(campaign_edge["strength"], 40)
        self.assertEqual(campaign_edge["rule_version"], "campaign-signals-v3")
        self.assertIn("strength AS strength", session.run.call_args_list[3].args[0])
        self.assertIn("rule_version AS rule_version", session.run.call_args_list[3].args[0])

    def test_postgres_fallback_graph_returns_provenance_without_free_text(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                user = User(email="graph-inspector@example.invalid", password_hash="test-only", role="investigator")
                db.add(user)
                db.flush()
                case = Case(case_ref="RC-12345678", title="Recruiter phone +91 98765 43210", input_kind="plain_text", submitted_text="private", consent_version="test-v1", created_by=user.id)
                db.add(case)
                db.flush()
                entity = Entity(case_id=case.id, entity_type="phone", raw_value="+91 98765 43210", normalized_value="9876543210", review_status="confirmed")
                evidence = Evidence(case_id=case.id, source_name="Registry +91 98765 43210", source_type="curated_local_corpus", source_ref="https://registry.example.test/person/9876543210?phone=9876543210", claim="Phone +91 98765 43210 flagged", outcome="result", excerpt="Record for +91 98765 43210", authority="government", review_status="relevant", review_reason="Checked +91 98765 43210", details={"matched_entity_type": "phone", "matched_normalized_value": "9876543210"})
                db.add_all([entity, evidence])
                db.commit()
                with patch("app.main.graph_store.configured", return_value=False):
                    result = graph_endpoint(db, user)
                evidence_node = next(node for node in result["nodes"] if node["type"] == "evidence")
                self.assertEqual(result["projection"], "postgresql-derived")
                self.assertEqual(evidence_node["source_type"], "curated_local_corpus")
                self.assertEqual(evidence_node["review_status"], "relevant")
                self.assertEqual(evidence_node["label"], "curated_local_corpus · result")
                self.assertNotIn("source_name", evidence_node)
                self.assertNotIn("claim", evidence_node)
                self.assertNotIn("excerpt", evidence_node)
                self.assertNotIn("review_reason", evidence_node)
                self.assertNotIn("title", next(node for node in result["nodes"] if node["type"] == "case"))
                self.assertNotIn("9876543210", str(result))
                self.assertTrue(any(edge["kind"] == "checks_identifier" for edge in result["edges"]))
        finally:
            Base.metadata.drop_all(engine)
            engine.dispose()

    def test_graph_labels_mask_contact_identifiers(self):
        self.assertEqual(graph_store.display_identifier("phone", "9876543210"), "••••3210")
        self.assertEqual(graph_store.display_identifier("upi_id", "worker@bank"), "••••")
        self.assertEqual(graph_store.display_identifier("email", "agent@example.org"), "a***@example.org")
        self.assertEqual(graph_store.display_identifier("recruiter_claim", "Ravi Kumar"), "[name masked]")
        self.assertEqual(graph_store.display_identifier("url", "https://example.org/private/path"), "[web identifier masked]")
        self.assertEqual(graph_store.display_identifier("domain", "example.org"), "[web identifier masked]")

    def test_graph_node_id_does_not_disclose_identifier(self):
        entity_key = "phone:9876543210"
        node_id = graph_store.entity_node_id(entity_key)
        self.assertNotIn("9876543210", node_id)
        self.assertEqual(node_id, graph_store.entity_node_id(entity_key))


if __name__ == "__main__":
    unittest.main()
