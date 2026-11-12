"""Offline persistence checks for graph projection retry and generation races."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.graph_outbox import enqueue_graph_sync, process_graph_projection_once
from app.models import Case, GraphProjectionOutbox, User


class GraphOutboxTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.sessions() as db:
            user = User(email="graph-user@example.invalid", password_hash="synthetic-hash", role="investigator")
            db.add(user)
            db.flush()
            self.case = Case(
                case_ref="RC-1234ABCD",
                title="Synthetic graph projection case",
                input_kind="message",
                submitted_text="Synthetic fixture only",
                consent_version="test-consent-v1",
                created_by=user.id,
            )
            db.add(self.case)
            db.commit()
            self.case_id = self.case.id

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def queue_projection(self):
        with patch("app.graph_outbox.graph_store.configured", return_value=True):
            with self.sessions() as db:
                self.assertTrue(enqueue_graph_sync(db, self.case_id))
                db.commit()

    def current_outbox(self):
        with self.sessions() as db:
            return db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == self.case_id))

    def test_projection_failure_is_requeued_with_bounded_backoff_and_safe_error(self):
        self.queue_projection()
        with patch("app.graph_outbox.SessionLocal", self.sessions), patch(
            "app.graph_outbox.graph_store.configured", return_value=True
        ), patch("app.graph_outbox.graph_store.sync_from_db", side_effect=RuntimeError("private path must not persist")):
            self.assertTrue(process_graph_projection_once())

        row = self.current_outbox()
        self.assertEqual(row.status, "queued")
        self.assertEqual(row.attempts, 1)
        self.assertEqual(row.last_error, "RuntimeError")
        self.assertNotIn("private path", row.last_error)
        available_at = row.available_at
        if available_at.tzinfo is None:  # SQLite does not preserve timezone metadata.
            available_at = available_at.replace(tzinfo=timezone.utc)
        self.assertGreater(available_at, datetime.now(timezone.utc))

    def test_change_during_projection_keeps_newer_generation_queued(self):
        self.queue_projection()

        def enqueue_new_generation(db, case):
            with self.sessions() as concurrent_db:
                self.assertTrue(enqueue_graph_sync(concurrent_db, self.case_id))
                concurrent_db.commit()

        with patch("app.graph_outbox.SessionLocal", self.sessions), patch(
            "app.graph_outbox.graph_store.configured", return_value=True
        ), patch("app.graph_outbox.graph_store.sync_from_db", side_effect=enqueue_new_generation):
            self.assertTrue(process_graph_projection_once())

        row = self.current_outbox()
        self.assertEqual(row.generation, 2)
        self.assertEqual(row.status, "queued")
        available_at = row.available_at
        if available_at.tzinfo is None:  # SQLite does not preserve timezone metadata.
            available_at = available_at.replace(tzinfo=timezone.utc)
        self.assertLessEqual(available_at, datetime.now(timezone.utc))
        self.assertEqual(row.last_error, "")

    def test_delete_tombstone_survives_case_row_deletion_until_projected(self):
        with patch("app.graph_outbox.graph_store.configured", return_value=True):
            with self.sessions() as db:
                self.assertTrue(enqueue_graph_sync(db, self.case_id, operation="delete"))
                db.delete(db.get(Case, self.case_id))
                db.commit()

        with patch("app.graph_outbox.SessionLocal", self.sessions), patch(
            "app.graph_outbox.graph_store.configured", return_value=True
        ), patch("app.graph_outbox.graph_store.delete_case") as delete_case:
            self.assertTrue(process_graph_projection_once())

        delete_case.assert_called_once_with(self.case_id)
        row = self.current_outbox()
        self.assertEqual(row.operation, "delete")
        self.assertEqual(row.status, "completed")


if __name__ == "__main__":
    unittest.main()
