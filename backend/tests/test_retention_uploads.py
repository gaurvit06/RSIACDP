"""Retention must never remove an aged upload still referenced by a live case."""
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Case, Evidence, User
from app.worker import purge_expired_records


class RetentionUploadTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.temp = tempfile.TemporaryDirectory(prefix="rsaicdp-retention-upload-")
        self.upload_dir = Path(self.temp.name) / "private"
        self.upload_dir.mkdir(mode=0o700)

    def tearDown(self):
        self.temp.cleanup()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_orphan_sweep_preserves_old_file_referenced_by_nonexpired_evidence(self):
        stored_name = "a" * 48 + ".pdf"
        upload = self.upload_dir / stored_name
        upload.write_bytes(b"synthetic private upload")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=400)).timestamp()
        os.utime(upload, (old_timestamp, old_timestamp))

        with Session(self.engine) as db:
            user = User(email="retention@example.invalid", password_hash="test-only", role="investigator")
            db.add(user)
            db.flush()
            case = Case(
                case_ref="RC-CCCCCCCC", title="Recent synthetic case", input_kind="upload",
                submitted_text=None, consent_version="consent-v2", created_by=user.id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(case)
            db.flush()
            db.add(Evidence(
                case_id=case.id, source_name="User upload", source_type="uploaded_file",
                source_ref="upload", claim="Synthetic uploaded material", outcome="not_checked",
                details={"stored_name": stored_name},
            ))
            db.commit()

        with patch("app.worker.SessionLocal", self.sessions), \
             patch("app.worker.settings.upload_dir", self.upload_dir), \
             patch("app.worker.settings.retention_days", 180), \
             patch("app.graph_outbox.graph_store.configured", return_value=False):
            removed = purge_expired_records()

        self.assertEqual(removed, 0)
        self.assertTrue(upload.exists(), "an active evidence reference must protect its original file regardless of mtime")

    def test_retention_log_does_not_include_filesystem_exception_text(self):
        stored_name = "b" * 48 + ".pdf"
        upload = self.upload_dir / stored_name
        upload.write_bytes(b"synthetic expired upload")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=400)).timestamp()
        os.utime(upload, (old_timestamp, old_timestamp))
        with Session(self.engine) as db:
            user = User(email="expired@example.invalid", password_hash="test-only", role="investigator")
            db.add(user)
            db.flush()
            case = Case(
                case_ref="RC-DDDDDDDD", title="Expired synthetic case", input_kind="upload",
                submitted_text=None, consent_version="consent-v2", created_by=user.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=400),
            )
            db.add(case)
            db.flush()
            db.add(Evidence(
                case_id=case.id, source_name="User upload", source_type="uploaded_file",
                source_ref="upload", claim="Synthetic uploaded material", outcome="not_checked",
                details={"stored_name": stored_name},
            ))
            db.commit()

        sensitive_path = "C:\\private\\secret-person\\phone-9999999999.pdf"
        with patch("app.worker.SessionLocal", self.sessions), \
             patch("app.worker.settings.upload_dir", self.upload_dir), \
             patch("app.worker.settings.retention_days", 180), \
             patch("app.graph_outbox.graph_store.configured", return_value=False), \
             patch.object(type(upload), "unlink", side_effect=OSError(sensitive_path)), \
             self.assertLogs("case-worker", level="WARNING") as captured:
            removed = purge_expired_records()

        self.assertEqual(removed, 1)
        rendered = "\n".join(captured.output)
        self.assertNotIn("secret-person", rendered)
        self.assertNotIn("9999999999", rendered)
        self.assertIn("error=OSError", rendered)

    def test_expired_case_upload_is_removed_after_its_reference_is_deleted(self):
        stored_name = "c" * 48 + ".pdf"
        upload = self.upload_dir / stored_name
        upload.write_bytes(b"synthetic expired upload")
        with Session(self.engine) as db:
            user = User(email="expired-cleanup@example.invalid", password_hash="test-only", role="investigator")
            db.add(user)
            db.flush()
            case = Case(
                case_ref="RC-EEEEEEEE", title="Expired synthetic case", input_kind="upload",
                submitted_text=None, consent_version="consent-v2", created_by=user.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=400),
            )
            db.add(case)
            db.flush()
            db.add(Evidence(
                case_id=case.id, source_name="User upload", source_type="uploaded_file",
                source_ref="upload", claim="Synthetic uploaded material", outcome="not_checked",
                details={"stored_name": stored_name},
            ))
            db.commit()

        with patch("app.worker.SessionLocal", self.sessions), \
             patch("app.worker.settings.upload_dir", self.upload_dir), \
             patch("app.worker.settings.retention_days", 180), \
             patch("app.graph_outbox.graph_store.configured", return_value=False):
            removed = purge_expired_records()

        self.assertEqual(removed, 1)
        self.assertFalse(upload.exists(), "a file referenced only by an expired case must be deleted")

    def test_orphan_sweep_preserves_unrelated_aged_files(self):
        unrelated = self.upload_dir / "operator-notes.txt"
        unrelated.write_text("synthetic operator note", encoding="utf-8")
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=400)).timestamp()
        os.utime(unrelated, (old_timestamp, old_timestamp))

        with patch("app.worker.SessionLocal", self.sessions), \
             patch("app.worker.settings.upload_dir", self.upload_dir), \
             patch("app.worker.settings.retention_days", 180), \
             patch("app.graph_outbox.graph_store.configured", return_value=False):
            removed = purge_expired_records()

        self.assertEqual(removed, 0)
        self.assertTrue(unrelated.exists(), "retention may prune only names generated for private uploads")


if __name__ == "__main__":
    unittest.main()
