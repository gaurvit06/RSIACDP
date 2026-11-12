"""Opt-in PostgreSQL concurrency test for corpus lookup versus reviewer retirement.

Set RSAICDP_RETIREMENT_TEST_DATABASE_URL to a migrated disposable database whose
name ends in ``_test``. The test inserts and removes only synthetic rows.
"""
import os
import secrets
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from sqlalchemy import delete, event, select
from sqlalchemy.orm import Session

from app.db import Base
from app.main import retire_evidence_record
from app.models import AuditEvent, Case, Entity, Evidence, GraphProjectionOutbox, HumanDisposition, SourceRecord, SystemFinding, User
from app.schemas import SourceRecordRetire
from app.source_adapters import LocalEvidenceCorpusAdapter


TEST_DATABASE_URL = os.getenv("RSAICDP_RETIREMENT_TEST_DATABASE_URL", "")


@unittest.skipUnless(TEST_DATABASE_URL, "set RSAICDP_RETIREMENT_TEST_DATABASE_URL to an isolated migrated PostgreSQL database ending in _test")
class PostgresSourceRetirementConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine

        database_name = urlsplit(TEST_DATABASE_URL).path.rsplit("/", 1)[-1]
        if not database_name.endswith("_test"):
            raise RuntimeError("Refusing to run source retirement test unless database name ends in _test")
        cls.engine = create_engine(TEST_DATABASE_URL, pool_size=4, max_overflow=0)
        if cls.engine.dialect.name != "postgresql":
            cls.engine.dispose()
            raise RuntimeError("Source retirement concurrency test requires PostgreSQL")
        required_tables = {"source_records", "graph_projection_outbox", "system_findings"}
        if not required_tables <= set(Base.metadata.tables):
            cls.engine.dispose()
            raise RuntimeError("Application schema is not fully loaded")
        with cls.engine.connect() as connection:
            inspector_tables = set(__import__("sqlalchemy").inspect(connection).get_table_names())
        if not required_tables <= inspector_tables:
            cls.engine.dispose()
            raise RuntimeError("Run Alembic migrations before the source retirement test")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_retirement_waits_for_inflight_lookup_then_withdraws_its_evidence(self):
        suffix = secrets.token_hex(6).upper()
        investigator_email = f"retirement-{suffix.lower()}@example.invalid"
        reviewer_email = f"retirement-review-{suffix.lower()}@example.invalid"
        record_id = f"RETIRE-{suffix}"
        case_ref = f"RC-{suffix[:8]}"
        with Session(self.engine) as db:
            investigator = User(email=investigator_email, password_hash="synthetic-test-hash", role="investigator")
            reviewer = User(email=reviewer_email, password_hash="synthetic-test-hash", role="reviewer")
            db.add_all([investigator, reviewer])
            db.flush()
            source = SourceRecord(
                record_id=record_id, entity_type="email", normalized_value=f"recruiter-{suffix.lower()}@example.invalid",
                source_name="Synthetic concurrency fixture", source_type="government",
                source_ref=f"https://source.example.invalid/{suffix}", claim="Synthetic source record for concurrency testing.",
                outcome="result", excerpt="Synthetic excerpt.", authority="government", created_by=investigator.id,
            )
            case = Case(case_ref=case_ref, title="Synthetic retirement concurrency case", input_kind="message", consent_version="consent-v2", created_by=investigator.id)
            db.add_all([source, case])
            db.flush()
            entity = Entity(case_id=case.id, entity_type="email", raw_value=source.normalized_value, normalized_value=source.normalized_value, review_status="confirmed")
            db.add(entity)
            db.commit()
            case_id = case.id
            entity_id = entity.id
            investigator_id = investigator.id
            reviewer_id = reviewer.id

        lookup_locked = threading.Event()
        allow_lookup_commit = threading.Event()
        retirement_query_started = threading.Event()
        retirement_finished = threading.Event()
        retirement_thread = threading.local()

        def before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
            if getattr(retirement_thread, "active", False):
                normalized_sql = statement.lower()
                if "source_records" in normalized_sql and "for update" in normalized_sql:
                    retirement_query_started.set()

        event.listen(self.engine, "before_cursor_execute", before_cursor_execute)

        def process_lookup_and_persist():
            with Session(self.engine) as db:
                entity = db.get(Entity, entity_id)
                observations = LocalEvidenceCorpusAdapter(db).check(entity)
                if not observations or observations[0].outcome != "result":
                    raise AssertionError("Expected the active synthetic source record to match")
                lookup_locked.set()
                if not allow_lookup_commit.wait(timeout=10):
                    raise AssertionError("Test did not release the lookup transaction")
                observation = observations[0]
                db.add(Evidence(
                    case_id=case_id, source_name=observation.source_name, source_type=observation.source_type,
                    source_ref=observation.source_ref, claim=observation.claim, outcome=observation.outcome,
                    excerpt=observation.excerpt, authority=observation.authority, retrieved_at=observation.retrieved_at,
                    details=observation.details,
                ))
                db.commit()

        def retire_source_record():
            if not lookup_locked.wait(timeout=10):
                raise AssertionError("Lookup transaction never acquired the source row lock")
            retirement_thread.active = True
            with Session(self.engine) as db:
                reviewer = db.get(User, reviewer_id)
                result = retire_evidence_record(record_id, SourceRecordRetire(rationale="Synthetic concurrency test retirement rationale."), db, reviewer)
                retirement_finished.set()
                return result

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                lookup = pool.submit(process_lookup_and_persist)
                retirement = pool.submit(retire_source_record)
                self.assertTrue(lookup_locked.wait(timeout=10))
                self.assertTrue(retirement_query_started.wait(timeout=10), "retirement never reached its row-locking query")
                self.assertFalse(retirement_finished.wait(timeout=0.25), "retirement should wait for the in-flight source lookup transaction")
                allow_lookup_commit.set()
                lookup.result(timeout=10)
                result = retirement.result(timeout=10)
                self.assertTrue(retirement_finished.is_set())
                self.assertEqual(result["affected_evidence_count"], 1)
                self.assertEqual(result["affected_case_count"], 1)

            with Session(self.engine) as db:
                record = db.scalar(select(SourceRecord).where(SourceRecord.record_id == record_id))
                evidence = db.scalar(select(Evidence).where(Evidence.source_ref == record_id))
                case = db.get(Case, case_id)
                self.assertFalse(record.active)
                self.assertEqual(evidence.review_status, "needs_review")
                self.assertTrue(evidence.details["source_record_withdrawn"])
                self.assertEqual(case.assessment, "Insufficient evidence")
        finally:
            event.remove(self.engine, "before_cursor_execute", before_cursor_execute)
            allow_lookup_commit.set()
            with Session(self.engine) as db:
                db.execute(delete(AuditEvent).where((AuditEvent.case_id == case_id) | (AuditEvent.actor_id.in_([investigator_id, reviewer_id]))))
                db.execute(delete(SystemFinding).where(SystemFinding.case_id == case_id))
                db.execute(delete(HumanDisposition).where(HumanDisposition.case_id == case_id))
                db.execute(delete(Evidence).where(Evidence.case_id == case_id))
                db.execute(delete(Entity).where(Entity.case_id == case_id))
                db.execute(delete(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id))
                db.execute(delete(Case).where(Case.id == case_id))
                db.execute(delete(SourceRecord).where(SourceRecord.record_id == record_id))
                db.execute(delete(User).where(User.email.in_([investigator_email, reviewer_email])))
                db.commit()


if __name__ == "__main__":
    unittest.main()
