"""Regression coverage for automatic vacancy corroboration."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base
from app.findings import rebuild_system_findings
from app.models import Case, Entity, Evidence, User
from app.vacancy_verification import SOURCE, check_vacancy, compare, index_jobs

TITLE = "Test Engineer"
BODY = ("Design instruments for thermal measurements inside controlled vacuum chambers. "
        "Document calibration procedures and coordinate independent trials with technicians.")
BOARD = {"jobs": [{"id": 42, "title": TITLE, "content": BODY}]}


class OfficialVacancyTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        config = patch.object(settings, "official_job_boards", "Example=example")
        config.start()
        self.addCleanup(config.stop)
        self.user = User(email="example@example.invalid", password_hash="test", role="investigator")
        self.db.add(self.user)
        self.db.flush()
        self.case = Case(case_ref="TEST-42", title=TITLE, input_kind="text", submitted_text=BODY,
                         created_by=self.user.id, consent_version="test")
        self.case.entities = [Entity(entity_type=k, raw_value=v, normalized_value=v.casefold())
                              for k, v in [("company_claim", "Example"), ("job_title_claim", TITLE)]]
        self.case.evidence = [Evidence(source_name="Submission", source_type="submitted_material",
                                      outcome="result", claim="Submitted text")]
        self.db.add(self.case)
        self.db.flush()

    def check(self, index):
        with patch("app.vacancy_verification.board_index", return_value=(index, datetime.now(timezone.utc))):
            return check_vacancy(self.db, self.case)

    def test_confirmation_retains_source_and_survives_no_human_action(self):
        self.assertTrue(self.check(index_jobs(BOARD)))
        findings = rebuild_system_findings(self.db, self.case)
        vacancy = next(f for f in findings if f.scope == "vacancy")
        self.assertEqual(self.case.assessment, "Confirmed by an authoritative source")
        result = self.db.get(Evidence, vacancy.supporting_evidence_ids[0])
        self.assertEqual(result.review_status, "unreviewed")
        self.assertIsNone(result.reviewed_by)
        self.assertEqual(result.source_ref, "https://job-boards.greenhouse.io/example/jobs/42")
        self.assertEqual(len(result.details["content_sha256"]), 64)
        self.assertFalse(self.check(index_jobs(BOARD)))
        result.review_status = "contradicts"
        self.db.flush()
        rebuild_system_findings(self.db, self.case)
        self.assertEqual(self.case.assessment, "Insufficient evidence")
        result.review_status = "unreviewed"
        self.case.entities[1].review_status = "rejected"
        self.db.flush()
        self.assertFalse(any(f.scope == "vacancy" for f in rebuild_system_findings(self.db, self.case)))

    def test_unavailable_retries_and_empty_board_is_inconclusive(self):
        self.assertTrue(self.check(None))
        rebuild_system_findings(self.db, self.case)
        self.assertEqual(self.case.assessment, "Insufficient evidence")
        self.assertTrue(self.check(index_jobs({"jobs": []})))
        rows = self.db.scalars(select(Evidence).where(Evidence.source_type == SOURCE).order_by(Evidence.id)).all()
        self.assertEqual([r.outcome for r in rows], ["unavailable", "no_result"])
        rebuild_system_findings(self.db, self.case)
        self.assertEqual(self.case.assessment, "Insufficient evidence")

    def test_unsupported_company_never_contacts_board(self):
        self.case.entities[0].raw_value = "Unknown"
        with patch("app.vacancy_verification.board_index") as fetch:
            self.assertTrue(check_vacancy(self.db, self.case))
            fetch.assert_not_called()
        evidence = self.db.scalar(select(Evidence).where(Evidence.source_type == SOURCE))
        self.assertEqual(evidence.outcome, "not_checked")

    def test_title_alone_wrong_title_duplicate_listings_and_boilerplate(self):
        titles = {TITLE.casefold()}
        self.assertFalse(compare(TITLE, titles, index_jobs(BOARD)))
        self.assertFalse(compare(BODY, {"other role"}, index_jobs(BOARD)))
        duplicates = {"jobs": BOARD["jobs"] + [dict(BOARD["jobs"][0], id=43)]}
        self.assertTrue(self.check(index_jobs(duplicates)))
        result = self.db.scalar(select(Evidence).where(Evidence.source_type == SOURCE))
        self.assertEqual(result.outcome, "no_result")
        boilerplate = {"jobs": [dict(id=i+1, title=str(i), content=BODY) for i in range(10)]}
        self.assertFalse(compare(BODY, {"1"}, index_jobs(boilerplate)))
