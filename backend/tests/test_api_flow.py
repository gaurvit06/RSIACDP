"""End-to-end API/worker check using a disposable SQLite database."""
import os
import hashlib
import hmac
from pathlib import Path
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(tempfile.mkdtemp(prefix="rsaicdp-api-tests-"))
TEST_INVESTIGATOR_CODE = "test-only-initial-investigator-code-123456"
TEST_REVIEWER_CODE = "test-only-separate-reviewer-code-abcdef7890"
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'integration.db').as_posix()}"
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET"] = "integration-test-only-secret-0123456789"
os.environ["INITIAL_INVESTIGATOR_CODE"] = TEST_INVESTIGATOR_CODE
os.environ["INITIAL_REVIEWER_CODE"] = TEST_REVIEWER_CODE
os.environ["UPLOAD_DIR"] = str(TEST_ROOT / "private_uploads")

from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch
from app.main import app
from app.main import graph as graph_endpoint, review_entity as review_entity_endpoint
from app.config import settings
from app.db import SessionLocal, engine, get_db
from app.models import ProcessingJob, User, Case, Entity, Evidence, AuditEvent, HumanDisposition, LoginThrottle, GraphProjectionOutbox, PasswordResetToken
from app.schemas import ReviewRequest
from app.models import utcnow
from app.worker import process_job, purge_expired_records
from app.source_adapters import RdapDomainAdapter
from app.graph_outbox import enqueue_graph_sync, process_graph_projection_once
from app.security import create_token, hash_password


class CaseFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        engine.dispose()
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def test_z_cookie_session_is_http_only_csrf_protected_and_revoked(self):
        # The registration-limit test intentionally leaves its shared test-client
        # address throttled. Start this independent auth-flow test with a clean bucket.
        with SessionLocal() as db:
            db.execute(delete(LoginThrottle))
            db.commit()
        credentials = {"email": "cookie-session@example.net", "password": "cookie session passphrase long", "session_mode": "cookie"}
        registered = self.client.post("/api/auth/register", json=credentials)
        self.assertEqual(registered.status_code, 200, registered.text)
        self.assertNotIn("access_token", registered.json())
        self.assertEqual(registered.json()["token_type"], "cookie")
        cookie_header = registered.headers.get("set-cookie", "").lower()
        self.assertIn("casework_session=", cookie_header)
        self.assertIn("httponly", cookie_header)
        self.assertIn("samesite=strict", cookie_header)
        self.assertIn("path=/api", cookie_header)

        session = self.client.get("/api/auth/me")
        self.assertEqual(session.status_code, 200, session.text)
        csrf_token = session.json().get("csrf_token")
        self.assertTrue(csrf_token)
        self.assertNotIn("access_token", session.json())

        policy = self.client.get("/api/policy").json()
        case_payload = {
            "title": "Synthetic cookie session case",
            "input_kind": "text",
            "submitted_text": "Synthetic cookie session identifier cookie-case@example.net",
            "consent_version": policy["consent_version"],
            "consent": True,
            "rdap_consent": False,
        }
        missing_csrf = self.client.post("/api/cases", json=case_payload)
        self.assertEqual(missing_csrf.status_code, 403, missing_csrf.text)
        created = self.client.post("/api/cases", headers={"X-CSRF-Token": csrf_token}, json=case_payload)
        self.assertEqual(created.status_code, 200, created.text)

        signed_out = self.client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
        self.assertEqual(signed_out.status_code, 200, signed_out.text)
        self.assertIn("max-age=0", signed_out.headers.get("set-cookie", "").lower())
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

        logged_in = self.client.post("/api/auth/login", json=credentials)
        self.assertEqual(logged_in.status_code, 200, logged_in.text)
        self.assertNotIn("access_token", logged_in.json())
        self.assertIn("httponly", logged_in.headers.get("set-cookie", "").lower())
        refreshed_session = self.client.get("/api/auth/me")
        self.assertEqual(refreshed_session.status_code, 200, refreshed_session.text)
        refreshed_csrf = refreshed_session.json()["csrf_token"]
        self.assertEqual(self.client.post("/api/auth/logout", headers={"X-CSRF-Token": refreshed_csrf}).status_code, 200)

    def test_liveness_and_readiness_report_database_failure_without_leaking_details(self):
        live = self.client.get("/health/live")
        ready = self.client.get("/health/ready")
        self.assertEqual(live.status_code, 200)
        self.assertEqual(live.json()["status"], "ok")
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json()["dependencies"]["postgres"], "ready")
        self.assertEqual(self.client.get("/health").json()["status"], "ready")

        class BrokenSession:
            def execute(self, statement):
                raise SQLAlchemyError("password=must-not-leak")

        def broken_db():
            yield BrokenSession()

        app.dependency_overrides[get_db] = broken_db
        try:
            failed = self.client.get("/health/ready")
        finally:
            app.dependency_overrides.pop(get_db, None)
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.json()["dependencies"]["postgres"], "unavailable")
        self.assertNotIn("must-not-leak", failed.text)

    def test_case_is_processed_against_local_corpus_and_redacted_for_analyst(self):
        response = self.client.post("/api/auth/register", json={"email": "investigator@example.net", "password": "correct horse battery staple", "setup_code": TEST_INVESTIGATOR_CODE})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("cache-control"), "no-store, private")
        self.assertEqual(response.headers.get("pragma"), "no-cache")
        investigator_token = response.json()["access_token"]
        investigator_headers = {"Authorization": f"Bearer {investigator_token}"}
        self.assertEqual(self.client.get("/api/processing-status").status_code, 401)

        unsupported_authority = self.client.post("/api/evidence-corpus", headers=investigator_headers, json={
            "entity_type": "phone", "value": "+91 90000 00000", "source_name": "Unverified source",
            "source_type": "other", "claim": "Unsupported authoritative claim", "outcome": "result",
            "excerpt": "No verifiable evidence.", "authority": "government"
        })
        self.assertEqual(unsupported_authority.status_code, 400)

        stale_consent = self.client.post("/api/cases", headers=investigator_headers, json={
            "title": "Synthetic case", "input_kind": "message", "submitted_text": "Sample message text.",
            "consent_version": "obsolete-v0", "consent": True
        })
        self.assertEqual(stale_consent.status_code, 400)
        self.assertIn("Consent notice changed", stale_consent.json()["detail"])

        source = self.client.post("/api/evidence-corpus", headers=investigator_headers, json={
            "entity_type": "phone", "value": "+91 98765 43210", "source_name": "Synthetic test registry",
            "source_type": "government", "source_ref": "https://registry.example.test/records/Asha-Menon?phone=9876543210",
            "claim": "Synthetic fixture records an identifier associated with Asha Menon for pipeline testing",
            "outcome": "result", "excerpt": "Synthetic test evidence mentions Asha Menon at +91 98765 43210.", "authority": "government"
        })
        self.assertEqual(source.status_code, 200, source.text)

        submitted_text = "Recruiter: Asha Menon\nRecruiter asked me to call +91 98765 43210 about an offer."
        submitted = self.client.post("/api/cases", headers=investigator_headers, json={
            "title": "Asha Menon synthetic recruitment case", "input_kind": "message",
            "submitted_text": submitted_text,
            "consent_version": "consent-v2", "consent": True
        })
        self.assertEqual(submitted.status_code, 200, submitted.text)
        case_id = submitted.json()["id"]
        self.assertEqual(submitted.json()["status"], "queued")
        queued_status = self.client.get("/api/processing-status", headers=investigator_headers)
        self.assertEqual(queued_status.status_code, 200, queued_status.text)
        self.assertEqual(next(item for item in queued_status.json()["items"] if item["case_id"] == case_id)["case_status"], "queued")

        with SessionLocal() as db:
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case_id))
            self.assertIsNotNone(job)
            process_job(db, job)

        completed_status = self.client.get("/api/processing-status", headers=investigator_headers)
        self.assertEqual(next(item for item in completed_status.json()["items"] if item["case_id"] == case_id)["case_status"], "completed")

        reviewed = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers)
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        detail = reviewed.json()
        self.assertEqual(detail["processing"]["status"], "completed")
        self.assertIn("case_accessed", [event["action"] for event in detail["timeline"]])
        self.assertIn("9876543210", [entity["normalized"] for entity in detail["entities"]])
        phone_entity = next(entity for entity in detail["entities"] if entity["type"] == "phone")
        self.assertEqual(phone_entity["source_location"], "submitted_text")
        self.assertEqual(submitted_text[phone_entity["source_start_char"]:phone_entity["source_end_char"]], "+91 98765 43210")
        self.assertIn("Synthetic test registry", [evidence["source_name"] for evidence in detail["evidence"]])
        self.assertEqual(detail["assessment"], "Insufficient evidence")
        corpus_evidence = next(item for item in detail["evidence"] if item["source_name"] == "Synthetic test registry")
        evidence_review = self.client.post(f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review", headers=investigator_headers, json={"status": "relevant", "rationale": "The local fixture supports only the identifier observation."})
        self.assertEqual(evidence_review.status_code, 200, evidence_review.text)
        self.assertEqual(evidence_review.json()["review_status"], "relevant")
        still_unconfirmed = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()
        self.assertEqual(still_unconfirmed["assessment"], "Insufficient evidence")
        confirmed_extraction = self.client.post(f"/api/cases/{case_id}/entities/{phone_entity['id']}/review", headers=investigator_headers, json={"status": "confirmed", "rationale": "The identifier exactly matches the submitted source text."})
        self.assertEqual(confirmed_extraction.status_code, 200, confirmed_extraction.text)
        claim_assessment = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()
        self.assertEqual(claim_assessment["assessment"], "Confirmed by an authoritative source")
        active_findings = claim_assessment["findings"]
        self.assertTrue(any(item["scope"] == "case" and item["assessment"] == claim_assessment["assessment"] for item in active_findings))
        identifier_finding = next(item for item in active_findings if item["entity_id"] == phone_entity["id"])
        self.assertIn(corpus_evidence["id"], identifier_finding["evidence_ids"])
        self.assertEqual(identifier_finding["evidence_snapshot"][0]["retrieved_at"], corpus_evidence["retrieved_at"])
        self.assertEqual(identifier_finding["evidence_snapshot"][0]["source_ref"], "https://registry.example.test/records/Asha-Menon?phone=9876543210")
        self.assertEqual(identifier_finding["rule_version"], "exact-source-evidence-v1")
        conflicted = self.client.post(f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review", headers=investigator_headers, json={"status": "contradicts", "rationale": "This source record does not support the claim as stated and must be surfaced as a conflict."})
        self.assertEqual(conflicted.status_code, 200, conflicted.text)
        conflict_detail = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()
        self.assertEqual(conflict_detail["assessment"], "Insufficient evidence")
        case_conflict = next(item for item in conflict_detail["findings"] if item["scope"] == "case")
        self.assertIn(corpus_evidence["id"], case_conflict["conflict_evidence_ids"])
        evidence_review = self.client.post(f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review", headers=investigator_headers, json={"status": "relevant", "rationale": "After checking the source again, it supports the limited identifier-presence claim."})
        self.assertEqual(evidence_review.status_code, 200, evidence_review.text)
        self.assertEqual(self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()["assessment"], "Confirmed by an authoritative source")
        self.assertIn("evidence_reviewed", [event["action"] for event in self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()["timeline"]])

        unsupported_proposal = self.client.post(f"/api/cases/{case_id}/disposition", headers=investigator_headers, json={"disposition": "confirmed_authoritative", "rationale": "This disposition has no attached evidence and must be rejected.", "evidence_ids": []})
        self.assertEqual(unsupported_proposal.status_code, 400)
        proposed = self.client.post(f"/api/cases/{case_id}/disposition", headers=investigator_headers, json={"disposition": "confirmed_authoritative", "rationale": "The reviewed synthetic source supports this specific identifier claim.", "evidence_ids": [corpus_evidence["id"]]})
        self.assertEqual(proposed.status_code, 200, proposed.text)
        self.assertEqual(proposed.json()["status"], "pending_review")
        analyst_as_reviewer = self.client.get("/api/dispositions/pending", headers=investigator_headers)
        self.assertEqual(analyst_as_reviewer.status_code, 403)
        reviewer = self.client.post("/api/auth/register", json={"email": "reviewer@example.net", "password": "independent reviewer account passphrase", "setup_code": TEST_REVIEWER_CODE})
        self.assertEqual(reviewer.status_code, 200, reviewer.text)
        self.assertEqual(reviewer.json()["user"]["role"], "reviewer")
        reviewer_headers = {"Authorization": f"Bearer {reviewer.json()['access_token']}"}
        reviewer_case = self.client.get(f"/api/cases/{case_id}", headers=reviewer_headers)
        self.assertEqual(reviewer_case.status_code, 200, reviewer_case.text)
        self.assertEqual(reviewer_case.json()["title"], "Asha Menon synthetic recruitment case")
        self.assertIn("Asha Menon", reviewer_case.text)
        pending = self.client.get("/api/dispositions/pending", headers=reviewer_headers)
        self.assertEqual([item["id"] for item in pending.json()], [proposed.json()["id"]])
        self.assertEqual(pending.json()[0]["rationale"], "The reviewed synthetic source supports this specific identifier claim.")
        self.assertEqual(pending.json()[0]["evidence"][0]["review_status"], "relevant")
        self.assertIn("Asha Menon", pending.json()[0]["evidence"][0]["excerpt"])
        changed = self.client.post(f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review", headers=investigator_headers, json={"status": "irrelevant", "rationale": "A new review found this evidence does not support the claim."})
        self.assertEqual(changed.status_code, 200)
        after_irrelevance = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()
        self.assertEqual(after_irrelevance["assessment"], "Insufficient evidence")
        self.assertTrue(any(not finding["active"] for finding in self.client.get(f"/api/cases/{case_id}/report", headers=investigator_headers).json()["finding_history"]))
        stale_approval = self.client.patch(f"/api/dispositions/{proposed.json()['id']}/review", headers=reviewer_headers, json={"status": "approved", "rationale": "Attempt to approve after supporting evidence lost relevance."})
        self.assertEqual(stale_approval.status_code, 409)
        restored = self.client.post(f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review", headers=investigator_headers, json={"status": "relevant", "rationale": "The reviewed source is again relevant to this specific claim."})
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()["assessment"], "Confirmed by an authoritative source")
        approved = self.client.patch(f"/api/dispositions/{proposed.json()['id']}/review", headers=reviewer_headers, json={"status": "approved", "rationale": "Independent review confirms the cited source supports this claim."})
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "approved")

        second_case = self.client.post("/api/cases", headers=investigator_headers, json={
            "title": "Second synthetic recruitment case", "input_kind": "message",
            "submitted_text": "A different offer listed +91 98765 43210 as its contact number.",
            "consent_version": "consent-v2", "consent": True
        })
        self.assertEqual(second_case.status_code, 200, second_case.text)
        second_case_id = second_case.json()["id"]
        with SessionLocal() as db:
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == second_case_id))
            process_job(db, job)
        first_phone = next(entity for entity in detail["entities"] if entity["type"] == "phone")
        rejected_entity = self.client.post(f"/api/cases/{case_id}/entities/{first_phone['id']}/review", headers=investigator_headers, json={"status": "rejected", "rationale": "This extracted identifier is not confirmed from the submitted source."})
        self.assertEqual(rejected_entity.status_code, 200)
        no_link = self.client.post(f"/api/cases/{second_case_id}/link/refresh", headers=investigator_headers)
        self.assertEqual(no_link.status_code, 200)
        self.assertEqual(no_link.json()["links"], [])
        confirmed_entity = self.client.post(f"/api/cases/{case_id}/entities/{first_phone['id']}/review", headers=investigator_headers, json={"status": "confirmed", "rationale": "The digits match the value shown in the source text."})
        self.assertEqual(confirmed_entity.status_code, 200)
        linked = self.client.post(f"/api/cases/{second_case_id}/link/refresh", headers=investigator_headers)
        self.assertEqual(linked.status_code, 200, linked.text)
        self.assertEqual(len(linked.json()["links"]), 1)
        self.assertEqual(linked.json()["links"][0]["rule_version"], "campaign-signals-v3-threshold-40")
        self.assertEqual(linked.json()["links"][0]["strength"], 40)
        with SessionLocal() as db:
            link_run = db.scalar(select(AuditEvent).where(AuditEvent.case_id == second_case_id, AuditEvent.action == "campaign_links_recomputed").order_by(AuditEvent.id.desc()))
            self.assertIsInstance(link_run.detail.get("campaign_linking_ms"), (int, float))
            self.assertGreaterEqual(link_run.detail["campaign_linking_ms"], 0)
        original_threshold = settings.campaign_link_threshold
        try:
            settings.campaign_link_threshold = 30
            revised_threshold = self.client.post(f"/api/cases/{second_case_id}/link/refresh", headers=investigator_headers)
            self.assertEqual(revised_threshold.status_code, 200)
            self.assertEqual(revised_threshold.json()["links"][0]["rule_version"], "campaign-signals-v3-threshold-30")
        finally:
            settings.campaign_link_threshold = original_threshold
        historical = self.client.get(f"/api/cases/{second_case_id}", headers=investigator_headers).json()["links"]
        self.assertEqual({link["rule_version"] for link in historical}, {"campaign-signals-v3-threshold-30", "campaign-signals-v3-threshold-40"})

        web_case_ids = []
        for title in ("Synthetic web lead A", "Synthetic web lead B"):
            created = self.client.post("/api/cases", headers=investigator_headers, json={"title": title, "input_kind": "url", "submitted_text": "Open this role: https://jobs.example.org/CapitalRole", "consent_version": "consent-v2", "consent": True})
            self.assertEqual(created.status_code, 200, created.text)
            web_case_ids.append(created.json()["id"])
            with SessionLocal() as db:
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == created.json()["id"]))
                process_job(db, job)
        weak = self.client.post(f"/api/cases/{web_case_ids[1]}/link/refresh", headers=investigator_headers)
        self.assertEqual(len(weak.json()["links"]), 1)
        self.assertEqual(weak.json()["links"][0]["strength"], 25)
        self.assertEqual(weak.json()["links"][0]["review_status"], "low_signal")
        campaign_groups = self.client.get("/api/campaigns", headers=investigator_headers)
        self.assertEqual(campaign_groups.status_code, 200, campaign_groups.text)
        strong_group = next(group for group in campaign_groups.json() if {case["id"] for case in group["cases"]} >= {case_id, second_case_id})
        self.assertEqual(strong_group["classification"], "possible_campaign_lead")
        self.assertEqual(strong_group["links"][0]["matched_entities"][0]["case_id"], case_id)
        self.assertTrue(any("weight 40" in reason for reason in strong_group["links"][0]["reasons"]))

        analyst = self.client.post("/api/auth/register", json={"email": "analyst@example.net", "password": "another correct horse staple"})
        self.assertEqual(analyst.status_code, 200, analyst.text)
        self.assertEqual(analyst.json()["user"]["role"], "analyst")
        analyst_headers = {"Authorization": f"Bearer {analyst.json()['access_token']}"}
        self.assertEqual(self.client.get("/api/corrections", headers=analyst_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/graph", headers=analyst_headers).status_code, 403)
        redacted = self.client.get(f"/api/cases/{case_id}", headers=analyst_headers)
        self.assertEqual(redacted.status_code, 200, redacted.text)
        self.assertNotIn("9876543210", redacted.text)
        self.assertNotIn("Asha Menon", redacted.text)
        self.assertIn("[source excerpt restricted for privacy]", redacted.text)
        self.assertIn("https://registry.example.test/[path redacted]?[query redacted]", redacted.text)
        self.assertNotIn("Asha-Menon", redacted.text)
        self.assertNotIn("Synthetic test evidence mentions", redacted.text)
        redacted_list = self.client.get("/api/cases", headers=analyst_headers)
        self.assertEqual(redacted_list.status_code, 200, redacted_list.text)
        self.assertNotIn("9876543210", redacted_list.text)
        self.assertNotIn("Asha Menon", redacted_list.text)
        redacted_campaigns = self.client.get("/api/campaigns", headers=analyst_headers)
        self.assertEqual(redacted_campaigns.status_code, 200, redacted_campaigns.text)
        self.assertNotIn("9876543210", redacted_campaigns.text)
        self.assertNotIn("Asha Menon", redacted_campaigns.text)
        redacted_report = self.client.get(f"/api/cases/{case_id}/report", headers=analyst_headers)
        self.assertEqual(redacted_report.status_code, 200, redacted_report.text)
        self.assertEqual(redacted_report.headers.get("cache-control"), "no-store, private")
        self.assertNotIn("Asha Menon", redacted_report.text)
        self.assertNotIn("Asha-Menon", redacted_report.text)
        self.assertNotIn("Synthetic fixture records an identifier associated with", redacted_report.text)

        # Internal exception strings may carry paths or material-derived values;
        # the case API must return a safe recovery message instead.
        with SessionLocal() as db:
            failed_job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case_id))
            failed_job.last_error = r"RuntimeError: private path C:\\vault\\Asha Menon\\9876543210.pdf"
            failed_job.status = "failed"
            db.get(Case, case_id).status = "failed"
            db.commit()
        failure_detail = self.client.get(f"/api/cases/{case_id}", headers=analyst_headers)
        self.assertEqual(failure_detail.status_code, 200, failure_detail.text)
        self.assertIn("An investigator can retry processing", failure_detail.json()["processing"]["error"])
        self.assertNotIn("C:\\\\vault", failure_detail.text)
        self.assertNotIn("Asha Menon", failure_detail.text)
        self.assertNotIn("9876543210", failure_detail.text)

        rejected_again = self.client.post(f"/api/cases/{case_id}/entities/{first_phone['id']}/review", headers=investigator_headers, json={"status": "rejected", "rationale": "A correction review rejected this identifier association."})
        self.assertEqual(rejected_again.status_code, 200)
        stale_links = self.client.get(f"/api/cases/{second_case_id}", headers=investigator_headers).json()["links"]
        self.assertTrue(all(link["review_status"] == "stale" for link in stale_links))
        self.assertIn("case_link_withdrawn_after_entity_rejection", [event["action"] for event in self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()["timeline"]])
        confirmed_again = self.client.post(f"/api/cases/{case_id}/entities/{first_phone['id']}/review", headers=investigator_headers, json={"status": "confirmed", "rationale": "A correction review confirms the identifier value in the submitted source."})
        self.assertEqual(confirmed_again.status_code, 200)
        reactivated = self.client.post(f"/api/cases/{second_case_id}/link/refresh", headers=investigator_headers)
        self.assertEqual(reactivated.status_code, 200)
        self.assertEqual(reactivated.json()["links"][0]["review_status"], "proposed")

        report = self.client.get(f"/api/cases/{case_id}/report", headers=investigator_headers)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertNotIn("9876543210", report.text)
        exported = report.json()
        self.assertEqual(exported["evidence_summary"]["by_review_status"]["relevant"], 1)
        self.assertEqual(exported["assessment"], "Confirmed by an authoritative source")
        self.assertTrue(any(item["scope"] == "case" for item in exported["machine_findings"]))
        self.assertTrue(exported["campaign_links"])
        self.assertTrue(all("rule_version" in item for item in exported["campaign_links"]))
        self.assertNotIn("9876543210", str(exported["campaign_links"]))
        self.assertIn("investigative leads", exported["campaign_link_note"])
        self.assertIn("evidence_reviewed", [event["action"] for event in exported["timeline"]])
        self.assertTrue(all("source_location" in item for item in exported["entities"]))
        self.assertEqual(exported["human_dispositions"][0]["status"], "approved")

        markdown = self.client.get(f"/api/cases/{case_id}/report?format=markdown", headers=investigator_headers)
        self.assertEqual(markdown.status_code, 200, markdown.text)
        self.assertTrue(markdown.headers.get("content-type", "").startswith("text/markdown"))
        self.assertIn("attachment; filename=\"", markdown.headers.get("content-disposition", ""))
        self.assertIn("## Evidence records", markdown.text)
        self.assertIn("## Audit timeline", markdown.text)
        self.assertNotIn("9876543210", markdown.text)

        denied_investigator_retirement = self.client.post(
            f"/api/evidence-corpus/{source.json()['record_id']}/retire",
            headers=investigator_headers,
            json={"rationale": "The source record must be withdrawn for this synthetic test."},
        )
        self.assertEqual(denied_investigator_retirement.status_code, 403)
        denied_analyst_retirement = self.client.post(
            f"/api/evidence-corpus/{source.json()['record_id']}/retire",
            headers=analyst_headers,
            json={"rationale": "The source record must be withdrawn for this synthetic test."},
        )
        self.assertEqual(denied_analyst_retirement.status_code, 403)

        retired = self.client.post(
            f"/api/evidence-corpus/{source.json()['record_id']}/retire",
            headers=reviewer_headers,
            json={"rationale": "The synthetic source record has been withdrawn for an end-to-end review test."},
        )
        self.assertEqual(retired.status_code, 200, retired.text)
        self.assertEqual(retired.json()["affected_evidence_count"], 2)
        self.assertEqual(retired.json()["affected_case_count"], 2)
        retired_detail = self.client.get(f"/api/cases/{case_id}", headers=investigator_headers).json()
        self.assertEqual(retired_detail["assessment"], "Insufficient evidence")
        retired_evidence = next(item for item in retired_detail["evidence"] if item["id"] == corpus_evidence["id"])
        self.assertEqual(retired_evidence["review_status"], "needs_review")
        self.assertIn("withdrawn", retired_evidence["review_reason"])
        withdrawn_review_attempt = self.client.post(
            f"/api/cases/{case_id}/evidence/{corpus_evidence['id']}/review",
            headers=investigator_headers,
            json={"status": "relevant", "rationale": "Attempt to restore withdrawn evidence."},
        )
        self.assertEqual(withdrawn_review_attempt.status_code, 409, withdrawn_review_attempt.text)
        withdrawn_disposition_attempt = self.client.post(
            f"/api/cases/{case_id}/disposition",
            headers=investigator_headers,
            json={
                "disposition": "confirmed_authoritative",
                "rationale": "Attempt to cite a withdrawn synthetic source record.",
                "evidence_ids": [corpus_evidence["id"]],
            },
        )
        self.assertEqual(withdrawn_disposition_attempt.status_code, 400, withdrawn_disposition_attempt.text)
        retired_disposition = next(item for item in retired_detail["human_dispositions"] if item["id"] == proposed.json()["id"])
        self.assertEqual(retired_disposition["status"], "pending_review")
        corpus_after_retirement = self.client.get("/api/evidence-corpus", headers=reviewer_headers)
        self.assertEqual(corpus_after_retirement.status_code, 200)
        stored_retired_source = next(item for item in corpus_after_retirement.json() if item["record_id"] == source.json()["record_id"])
        self.assertFalse(stored_retired_source["active"])
        self.assertIn("withdrawn", stored_retired_source["retirement_reason"])
        repeated_retirement = self.client.post(
            f"/api/evidence-corpus/{source.json()['record_id']}/retire",
            headers=reviewer_headers,
            json={"rationale": "This source was already withdrawn in the synthetic test."},
        )
        self.assertEqual(repeated_retirement.status_code, 409)

    def test_uploaded_text_pdf_is_queued_and_processed(self):
        import fitz
        login = self.client.post("/api/auth/login", json={"email": "investigator@example.net", "password": "correct horse battery staple"})
        self.assertEqual(login.status_code, 200, login.text)
        token = login.json()["access_token"]
        policy = self.client.get("/api/policy").json()
        self.assertEqual(policy["max_upload_bytes"], settings.max_upload_bytes)
        self.assertEqual(policy["allowed_upload_media_types"], ["image/png", "image/jpeg", "image/webp", "application/pdf"])
        unsupported = self.client.post("/api/cases/upload", headers={"Authorization": f"Bearer {token}"}, data={"title": "Unsupported fixture", "consent_version": "consent-v2", "consent": "true"}, files={"file": ("offer.txt", b"synthetic", "text/plain")})
        self.assertEqual(unsupported.status_code, 415)
        with patch("app.main.settings.max_upload_bytes", 16):
            oversized = self.client.post("/api/cases/upload", headers={"Authorization": f"Bearer {token}"}, data={"title": "Oversized fixture", "consent_version": "consent-v2", "consent": "true"}, files={"file": ("large.png", b"x" * 17, "image/png")})
        self.assertEqual(oversized.status_code, 413)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Contact recruiter at +91 91234 56789")
        payload = doc.tobytes()
        doc.close()
        stale_upload = self.client.post("/api/cases/upload", headers={"Authorization": f"Bearer {token}"}, data={"title": "Synthetic PDF case", "consent_version": "obsolete-v0", "consent": "true"}, files={"file": ("offer.pdf", payload, "application/pdf")})
        self.assertEqual(stale_upload.status_code, 400)
        uploaded = self.client.post("/api/cases/upload", headers={"Authorization": f"Bearer {token}"}, data={"title": "Synthetic PDF case", "consent_version": "consent-v2", "consent": "true"}, files={"file": ("offer.pdf", payload, "application/pdf")})
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        case_id = uploaded.json()["id"]
        self.assertEqual(uploaded.json()["status"], "queued")
        with SessionLocal() as db:
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case_id))
            process_job(db, job)
        detail = self.client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(detail["processing"]["status"], "completed")
        self.assertIn("9123456789", [entity["normalized"] for entity in detail["entities"]])
        phone = next(entity for entity in detail["entities"] if entity["type"] == "phone")
        self.assertEqual(phone["source_location"], "pdf_page_1")
        self.assertEqual(detail["submitted_text"][phone["source_start_char"]:phone["source_end_char"]], "+91 91234 56789")
        empty_lookup = next(item for item in detail["evidence"] if item["source_name"] == "Curated local evidence corpus")
        self.assertEqual(empty_lookup["outcome"], "no_result")
        self.assertIn("not evidence of fraud or legitimacy", empty_lookup["excerpt"])

    def test_graph_outbox_retries_and_preserves_newer_generation(self):
        with SessionLocal() as db:
            user = db.scalar(select(User).limit(1))
            if user is None:
                user = User(email="graph-outbox@example.invalid", password_hash="test-only", role="admin")
                db.add(user)
                db.flush()
            case = Case(case_ref="RC-ABCDEF02", title="Synthetic outbox case", input_kind="text", consent_version="test-v2", created_by=user.id)
            db.add(case)
            db.flush()
            entity = Entity(case_id=case.id, entity_type="phone", raw_value="+91 98765 12345", normalized_value="9876512345", source_excerpt="Synthetic outbox contact", review_status="needs_review")
            db.add(entity)
            db.flush()
            case_id = case.id
            with patch("app.graph_outbox.graph_store.configured", return_value=True):
                self.assertTrue(enqueue_graph_sync(db, case_id))
            db.commit()
            entity_id = entity.id

            with patch("app.graph_outbox.graph_store.configured", return_value=True):
                review_entity_endpoint(case_id, entity_id, ReviewRequest(status="confirmed", rationale="Synthetic API route queues graph state."), db, user)

        with patch("app.graph_outbox.graph_store.configured", return_value=True), patch("app.graph_outbox.graph_store.sync_from_db", side_effect=RuntimeError("synthetic transient outage")):
            self.assertTrue(process_graph_projection_once())
        with SessionLocal() as db:
            job = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
            self.assertEqual(job.status, "queued")
            self.assertEqual(job.attempts, 1)
            self.assertEqual(job.last_error, "RuntimeError")
            user = db.scalar(select(User).limit(1))
            with patch("app.graph_outbox.graph_store.configured", return_value=True), patch("app.main.graph_store.configured", return_value=True), patch("app.main.graph_store.graph_data") as neo4j_read:
                graph_result = graph_endpoint(db, user)
                self.assertEqual(graph_result["projection"], "postgresql-derived")
                self.assertIn(f"case:{case_id}", [node["id"] for node in graph_result["nodes"]])
                neo4j_read.assert_not_called()
            job.available_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        def enqueue_newer_generation(db, case):
            with SessionLocal() as other_db:
                self.assertTrue(enqueue_graph_sync(other_db, case.id))
                other_db.commit()

        with patch("app.graph_outbox.graph_store.configured", return_value=True), patch("app.graph_outbox.graph_store.sync_from_db", side_effect=enqueue_newer_generation):
            self.assertTrue(process_graph_projection_once())
        with SessionLocal() as db:
            job = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
            self.assertEqual(job.status, "queued")
            self.assertEqual(job.generation, 3)
            self.assertEqual(job.last_error, "")

        with patch("app.graph_outbox.graph_store.configured", return_value=True), patch("app.graph_outbox.graph_store.sync_from_db") as projection:
            self.assertTrue(process_graph_projection_once())
            projection.assert_called_once()
        with SessionLocal() as db:
            job = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
            self.assertEqual(job.status, "completed")
            self.assertEqual(job.generation, 3)
            self.assertEqual(job.attempts, 1)

    def test_retention_removes_expired_case_audit_and_upload(self):
        upload_dir = Path(os.environ["UPLOAD_DIR"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = "d" * 48 + ".pdf"
        (upload_dir / stored_name).write_bytes(b"synthetic private data")
        with SessionLocal() as db:
            user = db.scalar(select(User).limit(1))
            if user is None:
                user = User(email="retention@example.net", password_hash="test-only", role="investigator")
                db.add(user)
                db.flush()
            old_time = datetime.now(timezone.utc) - timedelta(days=200)
            case = Case(case_ref="RC-EXPIRED", title="Expired synthetic case", input_kind="file", status="completed", consent_version="test-v1", created_by=user.id, created_at=old_time)
            db.add(case)
            db.flush()
            case_id = case.id
            db.add(Evidence(case_id=case.id, source_name="Test upload", source_type="uploaded_file", source_ref="synthetic", claim="synthetic", outcome="result", excerpt="", authority="user_submitted", details={"stored_name": stored_name}))
            db.add(AuditEvent(case_id=case.id, actor_id=user.id, action="test", detail={}))
            db.add(AuditEvent(case_id=None, actor_id=user.id, action="global_test", detail={}, created_at=old_time))
            db.add(LoginThrottle(fingerprint="f" * 64, attempts=2, window_started_at=old_time.timestamp(), locked_until=0, updated_at=old_time))
            db.commit()
        with patch("app.graph_outbox.graph_store.configured", return_value=True):
            removed = purge_expired_records()
        self.assertEqual(removed, 1)
        self.assertFalse((upload_dir / stored_name).exists())
        with SessionLocal() as db:
            self.assertIsNone(db.get(Case, case_id))
            self.assertEqual(db.scalar(select(AuditEvent).where(AuditEvent.case_id == case_id)), None)
            self.assertEqual(db.scalar(select(AuditEvent).where(AuditEvent.action == "global_test")), None)
            self.assertIsNone(db.get(LoginThrottle, "f" * 64))
            tombstone = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
            self.assertEqual(tombstone.operation, "delete")
            self.assertEqual(tombstone.status, "queued")
        with patch("app.graph_outbox.graph_store.configured", return_value=True), patch("app.graph_outbox.graph_store.delete_case") as delete_projection:
            self.assertTrue(process_graph_projection_once())
            delete_projection.assert_called_once_with(case_id)
        with SessionLocal() as db:
            tombstone = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
            self.assertEqual(tombstone.status, "completed")

    def test_retention_creates_missing_private_upload_directory(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-retention-") as parent:
            missing_upload_dir = Path(parent) / "private" / "uploads"
            self.assertFalse(missing_upload_dir.exists())
            with patch("app.worker.settings.upload_dir", missing_upload_dir):
                self.assertEqual(purge_expired_records(), 0)
            self.assertTrue(missing_upload_dir.is_dir())
            self.assertEqual(list(missing_upload_dir.iterdir()), [])

    def test_processing_failure_logs_exception_type_without_exception_text(self):
        secret_fixture = "private path C:\\vault\\Example Person\\9876543210.pdf"
        with SessionLocal() as db:
            user = db.scalar(select(User).limit(1))
            if user is None:
                user = User(email="worker-log@example.net", password_hash="test-only", role="investigator")
                db.add(user)
                db.flush()
            case = Case(case_ref="RC-LOGTEST", title="Synthetic worker log case", input_kind="text", submitted_text="Synthetic test text", consent_version="test-v1", created_by=user.id)
            db.add(case)
            db.flush()
            case_id = case.id
            job = ProcessingJob(case_id=case.id, status="processing", attempts=1)
            db.add(job)
            db.commit()
            db.refresh(job)
            self.assertIsNotNone(db.get(Case, case_id))
            with patch("app.worker.log.error") as failure_log, patch("app.worker.extract", side_effect=RuntimeError(secret_fixture)) as extraction:
                process_job(db, job)
            persisted_job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case_id))
            self.assertEqual(persisted_job.last_error, "RuntimeError")
            self.assertNotIn(secret_fixture, persisted_job.last_error)
        extraction.assert_called_once()
        failure_log.assert_called_once()
        log_arguments = failure_log.call_args.args
        self.assertEqual(log_arguments[0], "Case processing failed for case id %s on attempt %s (%s)")
        self.assertEqual(log_arguments[1:], (case_id, 1, "RuntimeError"))
        self.assertNotIn(secret_fixture, repr(log_arguments))
        self.assertNotIn("Example Person", repr(log_arguments))

    def test_login_failures_are_generic_persisted_and_throttled(self):
        original_limit = settings.login_max_attempts
        settings.login_max_attempts = 3
        try:
            failures = [self.client.post("/api/auth/login", json={"email": "unknown-rate-limit@example.net", "password": "incorrect candidate password"}) for _ in range(3)]
            self.assertEqual([response.status_code for response in failures], [401, 401, 401])
            self.assertEqual(len({response.json()["detail"] for response in failures}), 1)
            locked = self.client.post("/api/auth/login", json={"email": "unknown-rate-limit@example.net", "password": "incorrect candidate password"})
            self.assertEqual(locked.status_code, 429)
            self.assertIn("Retry-After", locked.headers)
            valid_user = self.client.post("/api/auth/login", json={"email": "investigator@example.net", "password": "correct horse battery staple"})
            self.assertEqual(valid_user.status_code, 200, valid_user.text)
            with SessionLocal() as db:
                failed_events = db.scalars(select(AuditEvent).where(AuditEvent.action == "login_failed")).all()
                throttles = db.scalars(select(LoginThrottle)).all()
                self.assertTrue(failed_events)
                self.assertTrue(all("unknown-rate-limit@example.net" not in str(event.detail) for event in failed_events))
                self.assertTrue(throttles)
        finally:
            settings.login_max_attempts = original_limit

    def test_registration_requests_are_limited_per_direct_client(self):
        original_limit = settings.register_max_requests
        settings.register_max_requests = 2
        try:
            with SessionLocal() as db:
                db.execute(delete(LoginThrottle))
                db.commit()
            with SessionLocal() as db:
                is_first_account = db.scalar(select(User.id).limit(1)) is None
            bootstrap = {"setup_code": TEST_INVESTIGATOR_CODE} if is_first_account else {}
            first = self.client.post("/api/auth/register", json={"email": "registration-one@example.net", "password": "a sufficiently long passphrase", **bootstrap})
            second = self.client.post("/api/auth/register", json={"email": "registration-two@example.net", "password": "a sufficiently long passphrase"})
            limited = self.client.post("/api/auth/register", json={"email": "registration-three@example.net", "password": "a sufficiently long passphrase"})
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(second.status_code, 200, second.text)
            self.assertEqual(limited.status_code, 429, limited.text)
            self.assertIn("Retry-After", limited.headers)
            # A client-supplied forwarding header must not create a new bucket;
            # the server keys on the connection peer, not untrusted X-Forwarded-For.
            spoofed = self.client.post("/api/auth/register", headers={"X-Forwarded-For": "203.0.113.99"}, json={"email": "registration-four@example.net", "password": "a sufficiently long passphrase"})
            self.assertEqual(spoofed.status_code, 429, spoofed.text)
        finally:
            settings.register_max_requests = original_limit

    def test_reviewer_account_controls_revoke_sessions_and_preserve_reviewer(self):
        with SessionLocal() as db:
            reviewer = User(email="lifecycle-reviewer@example.net", password_hash=hash_password("reviewer test passphrase long"), role="reviewer")
            second_reviewer = User(email="lifecycle-second-reviewer@example.net", password_hash=hash_password("reviewer test passphrase long"), role="reviewer")
            analyst = User(email="lifecycle-analyst@example.net", password_hash=hash_password("analyst test passphrase long"), role="analyst")
            db.add_all([reviewer, second_reviewer, analyst])
            db.commit()
            for user in (reviewer, second_reviewer, analyst):
                db.refresh(user)
            reviewer_id, second_reviewer_id, analyst_id = reviewer.id, second_reviewer.id, analyst.id
            reviewer_token, analyst_token = create_token(reviewer), create_token(analyst)

        reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
        analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
        listed = self.client.get("/api/accounts", headers=reviewer_headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertIn("lifecycle-analyst@example.net", {account["email"] for account in listed.json()})
        denied = self.client.get("/api/accounts", headers=analyst_headers)
        self.assertEqual(denied.status_code, 403)
        denied_update = self.client.patch(f"/api/accounts/{second_reviewer_id}/status", headers=analyst_headers, json={"active": False, "rationale": "Analyst accounts may not change workspace access."})
        self.assertEqual(denied_update.status_code, 403)

        suspended = self.client.patch(f"/api/accounts/{analyst_id}/status", headers=reviewer_headers, json={"active": False, "rationale": "Account access paused after an operator security review."})
        self.assertEqual(suspended.status_code, 200, suspended.text)
        self.assertFalse(suspended.json()["active"])
        self.assertEqual(self.client.get("/api/auth/me", headers=analyst_headers).status_code, 401)

        reactivated = self.client.patch(f"/api/accounts/{analyst_id}/status", headers=reviewer_headers, json={"active": True, "rationale": "Access restored after the operator resolved the account review."})
        self.assertEqual(reactivated.status_code, 200, reactivated.text)
        self.assertTrue(reactivated.json()["active"])
        # Reactivation does not revive the old bearer token.
        self.assertEqual(self.client.get("/api/auth/me", headers=analyst_headers).status_code, 401)

        self_suspend = self.client.patch(f"/api/accounts/{reviewer_id}/status", headers=reviewer_headers, json={"active": False, "rationale": "Attempt to disable the current reviewer account."})
        self.assertEqual(self_suspend.status_code, 409)
        second_suspend = self.client.patch(f"/api/accounts/{second_reviewer_id}/status", headers=reviewer_headers, json={"active": False, "rationale": "Remove a duplicate test reviewer account."})
        self.assertEqual(second_suspend.status_code, 200, second_suspend.text)
        with SessionLocal() as db:
            active_reviewers = db.scalars(select(User).where(User.role == "reviewer", User.active.is_(True))).all()
            self.assertTrue(any(user.id == reviewer_id for user in active_reviewers))
            self.assertFalse(any(user.id == second_reviewer_id for user in active_reviewers))
            changes = db.scalars(select(AuditEvent).where(AuditEvent.action == "account_status_changed")).all()
            self.assertGreaterEqual(len(changes), 3)
            self.assertTrue(any(event.detail.get("account_id") == analyst_id and event.detail.get("active") is False for event in changes))

    def test_reviewer_issued_password_reset_is_hashed_expiring_and_one_time(self):
        with SessionLocal() as db:
            reviewer = User(email="reset-reviewer@example.net", password_hash=hash_password("reviewer test passphrase long"), role="reviewer")
            target = User(email="reset-target@example.net", password_hash=hash_password("old target passphrase long"), role="analyst")
            db.add_all([reviewer, target])
            db.commit()
            db.refresh(reviewer)
            db.refresh(target)
            reviewer_token = create_token(reviewer)
            target_token = create_token(target)
            reviewer_id, target_id = reviewer.id, target.id

        reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
        target_headers = {"Authorization": f"Bearer {target_token}"}
        denied = self.client.post(f"/api/accounts/{target_id}/password-reset", headers=target_headers, json={"rationale": "Analysts cannot issue password reset tokens."})
        self.assertEqual(denied.status_code, 403)
        issued = self.client.post(f"/api/accounts/{target_id}/password-reset", headers=reviewer_headers, json={"rationale": "The account holder verified identity through the operator's approved channel."})
        self.assertEqual(issued.status_code, 200, issued.text)
        self.assertIn("no-store", issued.headers.get("Cache-Control", ""))
        first_token = issued.json()["reset_token"]
        with SessionLocal() as db:
            stored = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == target_id, PasswordResetToken.consumed_at.is_(None)))
            self.assertIsNotNone(stored)
            self.assertNotEqual(stored.token_hash, first_token)
            self.assertGreater(stored.expires_at, stored.created_at)

        replaced = self.client.post(f"/api/accounts/{target_id}/password-reset", headers=reviewer_headers, json={"rationale": "Issue a fresh token after the holder could not use the first one."})
        self.assertEqual(replaced.status_code, 200, replaced.text)
        second_token = replaced.json()["reset_token"]
        old_token = self.client.post("/api/auth/reset-password", json={"token": first_token, "new_password": "a new sufficiently long password"})
        self.assertEqual(old_token.status_code, 400)
        completed = self.client.post("/api/auth/reset-password", json={"token": second_token, "new_password": "a new sufficiently long password"})
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(self.client.get("/api/auth/me", headers=target_headers).status_code, 401)
        old_password = self.client.post("/api/auth/login", json={"email": "reset-target@example.net", "password": "old target passphrase long"})
        new_password = self.client.post("/api/auth/login", json={"email": "reset-target@example.net", "password": "a new sufficiently long password"})
        self.assertEqual(old_password.status_code, 401)
        self.assertEqual(new_password.status_code, 200, new_password.text)
        reused = self.client.post("/api/auth/reset-password", json={"token": second_token, "new_password": "another sufficiently long password"})
        self.assertEqual(reused.status_code, 400)
        with SessionLocal() as db:
            self.assertTrue(all(item.consumed_at is not None for item in db.scalars(select(PasswordResetToken).where(PasswordResetToken.user_id == target_id)).all()))
            events = db.scalars(select(AuditEvent).where(AuditEvent.action == "password_reset_completed")).all()
            self.assertTrue(any(event.detail.get("account_id") == target_id for event in events))
            self.assertNotIn(first_token, str(events))
            self.assertNotIn(second_token, str(events))
        expires = self.client.post(f"/api/accounts/{target_id}/password-reset", headers=reviewer_headers, json={"rationale": "Verify expiry validation on a newly issued one-time credential."})
        self.assertEqual(expires.status_code, 200, expires.text)
        expired_token = expires.json()["reset_token"]
        with SessionLocal() as db:
            row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hmac.new(settings.jwt_secret.encode("utf-8"), expired_token.encode("utf-8"), hashlib.sha256).hexdigest()))
            row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        expired = self.client.post("/api/auth/reset-password", json={"token": expired_token, "new_password": "expired token password should fail"})
        self.assertEqual(expired.status_code, 400)

    def test_public_correction_request_can_be_reviewed_by_investigator(self):
        login = self.client.post("/api/auth/login", json={"email": "investigator@example.net", "password": "correct horse battery staple"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        case_response = self.client.post("/api/cases", headers=headers, json={"title": "Synthetic correction test", "input_kind": "message", "submitted_text": "Call +91 91234 56789 about the role.", "consent_version": "consent-v2", "consent": True})
        self.assertEqual(case_response.status_code, 200, case_response.text)
        case_id = case_response.json()["id"]
        with SessionLocal() as db:
            process_job(db, db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case_id)))
        case_detail = self.client.get(f"/api/cases/{case_id}", headers=headers).json()
        entity = next(item for item in case_detail["entities"] if item["type"] == "phone")
        related_case_response = self.client.post("/api/cases", headers=headers, json={"title": "Synthetic correction link case", "input_kind": "message", "submitted_text": "The offer lists +91 91234 56789 for questions.", "consent_version": "consent-v2", "consent": True})
        related_case_id = related_case_response.json()["id"]
        with SessionLocal() as db:
            process_job(db, db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == related_case_id)))
        initial_link = self.client.post(f"/api/cases/{related_case_id}/link/refresh", headers=headers)
        self.assertEqual(len(initial_link.json()["links"]), 1)
        public = self.client.post("/api/corrections", json={"case_ref": case_detail["case_ref"], "requester_email": "affected@example.net", "description": "This report identifies my contact number incorrectly; please review the source and remove the wrong association."})
        self.assertEqual(public.status_code, 202, public.text)
        request_ref = public.json()["request_ref"]
        self.assertNotIn("case_exists", public.json())
        self.assertNotIn("status_token_hash", public.json())
        status_url = f"/api/corrections/{request_ref}/status"
        invalid_status = self.client.post(status_url, json={"status_token": "x" * 40})
        self.assertEqual(invalid_status.status_code, 404)
        valid_status = self.client.post(status_url, json={"status_token": public.json()["status_token"]})
        self.assertEqual(valid_status.status_code, 200)
        self.assertEqual(valid_status.json()["status"], "received")
        self.assertEqual(valid_status.json()["status_message"], "Your request has been received and is awaiting review.")
        self.assertNotIn("resolution", valid_status.json())
        unauthorized = self.client.get("/api/corrections")
        self.assertEqual(unauthorized.status_code, 401)
        reviewed = self.client.patch(f"/api/corrections/{request_ref}", headers=headers, json={"status": "investigating", "resolution": "Reviewed the referenced evidence; contact +91 91234 56789 and payment handle candidate@okaxis were masked."})
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertEqual(reviewed.json()["status"], "investigating")
        applied = self.client.post(f"/api/corrections/{request_ref}/apply", headers=headers, json={"entity_id": entity["id"], "entity_action": "reject", "resolution": "Reviewed the submitted source and correction claim; the listed phone does not belong in this case."})
        self.assertEqual(applied.status_code, 200, applied.text)
        self.assertEqual(applied.json()["status"], "resolved")
        replay = self.client.post(f"/api/corrections/{request_ref}/apply", headers=headers, json={"entity_id": entity["id"], "entity_action": "reject", "resolution": "Repeated submissions must not apply the same correction twice."})
        self.assertEqual(replay.status_code, 409, replay.text)
        updated = self.client.get(f"/api/cases/{case_id}", headers=headers).json()
        self.assertEqual(next(item for item in updated["entities"] if item["id"] == entity["id"])["review_status"], "rejected")
        self.assertTrue(any(link["review_status"] == "stale" for link in updated["links"]), updated["links"])
        self.assertIn("correction_applied", [event["action"] for event in updated["timeline"]])
        requester_update = self.client.post(status_url, json={"status_token": public.json()["status_token"]})
        self.assertEqual(requester_update.json()["status"], "resolved")
        self.assertNotIn("resolution", requester_update.json())
        self.assertNotIn("91234 56789", requester_update.text)
        self.assertNotIn("candidate@okaxis", requester_update.text)
        self.assertEqual(requester_update.json()["status_message"], "The review is complete. Any applicable record correction has been applied.")
        replacement_request = self.client.post("/api/corrections", json={"case_ref": case_detail["case_ref"], "requester_email": "affected@example.net", "description": "The extracted phone value has a digit error and should be corrected to the value in the source material."})
        replacement_case = self.client.post("/api/cases", headers=headers, json={"title": "Synthetic corrected-number match", "input_kind": "message", "submitted_text": "The recruitment contact number is +91 99887 76655.", "consent_version": "consent-v2", "consent": True})
        self.assertEqual(replacement_case.status_code, 200, replacement_case.text)
        replacement_case_id = replacement_case.json()["id"]
        with SessionLocal() as db:
            process_job(db, db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == replacement_case_id)))
        replacement = self.client.post(f"/api/corrections/{replacement_request.json()['request_ref']}/apply", headers=headers, json={"entity_id": entity["id"], "entity_action": "correct", "corrected_value": "+91 99887 76655", "resolution": "Compared the submitted source with the extraction and corrected the phone value using the deterministic Indian phone normalizer."})
        self.assertEqual(replacement.status_code, 200, replacement.text)
        updated = self.client.get(f"/api/cases/{case_id}", headers=headers).json()
        corrected_entity = next(item for item in updated["entities"] if item["id"] == entity["id"])
        self.assertEqual(corrected_entity["review_status"], "confirmed")
        self.assertEqual(corrected_entity["normalized"], "9988776655")
        self.assertTrue(any({link["left_case_id"], link["right_case_id"]} == {case_id, replacement_case_id} and link["review_status"] in {"proposed", "low_signal"} for link in replacement.json()["links"]), replacement.json()["links"])
        evidence_item = updated["evidence"][0]
        second_correction = self.client.post("/api/corrections", json={"case_ref": case_detail["case_ref"], "requester_email": "affected@example.net", "description": "The evidence status for this source result is disputed; please review whether it contradicts the case claim."})
        self.assertEqual(second_correction.status_code, 202, second_correction.text)
        invalid_dual_target = self.client.post(f"/api/corrections/{second_correction.json()['request_ref']}/apply", headers=headers, json={"entity_id": entity["id"], "entity_action": "reject", "evidence_id": evidence_item["id"], "evidence_action": "contradicts", "resolution": "Only one target can be changed at a time to preserve a reviewable correction record."})
        self.assertEqual(invalid_dual_target.status_code, 400)
        evidence_applied = self.client.post(f"/api/corrections/{second_correction.json()['request_ref']}/apply", headers=headers, json={"evidence_id": evidence_item["id"], "evidence_action": "contradicts", "resolution": "Review shows the recorded evidence does not support the associated claim and must be surfaced as a conflict."})
        self.assertEqual(evidence_applied.status_code, 200, evidence_applied.text)
        latest = self.client.get(f"/api/cases/{case_id}", headers=headers).json()
        self.assertEqual(next(item for item in latest["evidence"] if item["id"] == evidence_item["id"])["review_status"], "contradicts")
        self.assertEqual(latest["assessment"], "Insufficient evidence")
        self.assertTrue(any(event["action"] == "correction_applied" for event in latest["timeline"]))
        signed_out = self.client.post("/api/auth/logout", headers=headers)
        self.assertEqual(signed_out.status_code, 200, signed_out.text)
        revoked = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(revoked.status_code, 401)

    def test_public_correction_intake_is_rate_limited(self):
        original_limit = settings.correction_max_requests
        settings.correction_max_requests = 2
        correction_throttle = hmac.new(
            settings.jwt_secret.encode("utf-8"),
            b"correction_request|testclient",
            hashlib.sha256,
        ).hexdigest()
        with SessionLocal() as db:
            db.execute(delete(LoginThrottle).where(LoginThrottle.fingerprint == correction_throttle))
            db.commit()
        payload = {
            "case_ref": "RC-1234ABCD",
            "requester_email": "affected@example.net",
            "description": "Please review whether the information associated with this reference is accurate.",
        }
        try:
            first = self.client.post("/api/corrections", json=payload)
            second = self.client.post("/api/corrections", json=payload)
            limited = self.client.post("/api/corrections", json=payload)
        finally:
            settings.correction_max_requests = original_limit
            # This test deliberately exhausts the shared test-client address;
            # leave subsequent integration tests with an independent limit window.
            with SessionLocal() as db:
                db.execute(delete(LoginThrottle).where(LoginThrottle.fingerprint == correction_throttle))
                db.commit()
        self.assertEqual(first.status_code, 202, first.text)
        self.assertEqual(second.status_code, 202, second.text)
        self.assertEqual(limited.status_code, 429, limited.text)
        self.assertGreater(int(limited.headers["retry-after"]), 0)

    def test_optional_rdap_requires_persisted_separate_consent_and_worker_gate(self):
        old_enabled = settings.rdap_enabled
        settings.rdap_enabled = True
        try:
            investigator = self.client.post("/api/auth/login", json={"email": "investigator@example.net", "password": "correct horse battery staple"})
            self.assertEqual(investigator.status_code, 200, investigator.text)
            headers = {"Authorization": f"Bearer {investigator.json()['access_token']}"}
            policy = self.client.get("/api/policy").json()
            self.assertEqual(policy["consent_version"], "consent-v3-rdap")
            self.assertIn("may log", policy["rdap_disclosure"])
            base = {"title": "Optional RDAP consent case", "input_kind": "url", "submitted_text": "Offer: https://jobs.example.org/role"}
            missing = self.client.post("/api/cases", headers=headers, json={**base, "consent_version": "consent-v3-rdap", "consent": True})
            self.assertEqual(missing.status_code, 400)
            stale = self.client.post("/api/cases", headers=headers, json={**base, "consent_version": "consent-v2", "consent": True, "rdap_consent": True})
            self.assertEqual(stale.status_code, 400)
            created = self.client.post("/api/cases", headers=headers, json={**base, "consent_version": "consent-v3-rdap", "consent": True, "rdap_consent": True})
            self.assertEqual(created.status_code, 200, created.text)
            self.assertTrue(created.json()["external_source_consent"])
            self.assertEqual(created.json()["consent_version"], "consent-v3-rdap")
            with SessionLocal() as db:
                case = db.get(Case, created.json()["id"])
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == case.id))
                with patch.object(RdapDomainAdapter, "check", return_value=[]) as rdap_check:
                    process_job(db, job)
                    self.assertTrue(any(call.args[0].entity_type == "domain" for call in rdap_check.call_args_list))
            details = self.client.get(f"/api/cases/{created.json()['id']}", headers=headers).json()
            self.assertEqual(details["processing"]["status"], "completed")
            self.assertTrue(
                any(item["action"] == "processing_completed" and item["detail"].get("external_source_checks_enabled") for item in details["timeline"]),
                details["timeline"],
            )
        finally:
            settings.rdap_enabled = old_enabled


if __name__ == "__main__":
    unittest.main()
