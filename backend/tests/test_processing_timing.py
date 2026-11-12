"""Worker processing-time capture excludes queue delay and stores bounded timing data."""
import math
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Case, ProcessingJob, User
from app.worker import process_job


class ProcessingTimingTests(unittest.TestCase):
    def test_successful_job_persists_finite_execution_duration(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine, expire_on_commit=False) as db:
                user = User(email="timing@example.invalid", password_hash="not-a-real-password-hash", role="analyst")
                db.add(user)
                db.flush()
                case = Case(
                    case_ref="RC-ABCDEF12",
                    title="Synthetic timing fixture",
                    input_kind="message",
                    submitted_text="Synthetic processing timing fixture with no identifiers.",
                    consent_version="consent-test",
                    created_by=user.id,
                )
                db.add(case)
                db.flush()
                job = ProcessingJob(case_id=case.id, status="queued", attempts=1, processing_ms=987.0)
                db.add(job)
                db.commit()

                process_job(db, job)

                db.refresh(job)
                self.assertEqual(job.status, "completed")
                self.assertIsNotNone(job.processing_ms)
                self.assertTrue(math.isfinite(job.processing_ms))
                self.assertGreaterEqual(job.processing_ms, 0)
                self.assertLess(job.processing_ms, 10_000)
        finally:
            Base.metadata.drop_all(engine)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
