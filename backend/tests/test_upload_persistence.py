"""Private upload bytes and case records must be compensated together."""
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.main import persist_uploaded_case
from app.models import Case, Evidence, User
from app.private_storage import UPLOAD_MAGIC, is_private_upload_name, read_private_upload


class UploadPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False, expire_on_commit=False)
        self.user = User(email="upload-test@example.invalid", password_hash="test-only", role="investigator")
        self.db.add(self.user)
        self.db.commit()
        self.temp = tempfile.TemporaryDirectory(prefix="rsaicdp-upload-commit-")
        self.upload_dir = Path(self.temp.name) / "private"

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.temp.cleanup()

    def test_success_commits_case_and_generated_upload_reference(self):
        with patch("app.main.settings.upload_dir", self.upload_dir), patch(
            "app.main.settings.app_environment", "testing"
        ), patch("app.main.settings.upload_encryption_key", ""):
            case = persist_uploaded_case(
                self.db, self.user, "Synthetic upload", "consent-v2", False,
                b"synthetic private file", "application/pdf",
            )

        evidence = self.db.scalar(select(Evidence).where(Evidence.case_id == case.id))
        stored_name = evidence.details["stored_name"]
        self.assertTrue(is_private_upload_name(stored_name))
        self.assertEqual((self.upload_dir / stored_name).read_bytes(), b"synthetic private file")
        self.assertEqual(self.db.scalar(select(Case).where(Case.id == case.id)).status, "queued")
        self.assertIn("Test-only mode permits unencrypted synthetic fixtures", evidence.excerpt)
        self.assertNotIn("application-encrypted", evidence.excerpt)

    def test_database_failure_rolls_back_records_and_removes_private_file(self):
        with patch("app.main.settings.upload_dir", self.upload_dir), patch(
            "app.main.settings.app_environment", "testing"
        ), patch("app.main.settings.upload_encryption_key", ""), patch.object(
            self.db, "commit", side_effect=RuntimeError("synthetic commit failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                persist_uploaded_case(
                    self.db, self.user, "Synthetic upload", "consent-v2", False,
                    b"synthetic private file", "application/pdf",
                )

        self.assertEqual(self.db.scalars(select(Case)).all(), [])
        self.assertEqual(list(self.upload_dir.iterdir()), [])

    def test_missing_encryption_key_fails_closed_outside_testing(self):
        with patch("app.main.settings.upload_dir", self.upload_dir), patch(
            "app.main.settings.app_environment", "development"
        ), patch("app.main.settings.upload_encryption_key", ""):
            with self.assertRaisesRegex(RuntimeError, "UPLOAD_ENCRYPTION_KEY"):
                persist_uploaded_case(
                    self.db, self.user, "Synthetic upload", "consent-v2", False,
                    b"must not be stored without encryption", "application/pdf",
                )

        self.assertEqual(self.db.scalars(select(Case)).all(), [])
        self.assertEqual(list(self.upload_dir.iterdir()), [])

    def test_intake_encrypts_original_and_keeps_plaintext_digest_provenance(self):
        original = b"synthetic sensitive upload contents"
        key = b"e" * 32
        encoded_key = base64.b64encode(key).decode("ascii")
        with patch("app.main.settings.upload_dir", self.upload_dir), patch(
            "app.main.settings.app_environment", "testing"
        ), patch(
            "app.main.settings.upload_encryption_key", encoded_key
        ):
            case = persist_uploaded_case(
                self.db, self.user, "Synthetic encrypted upload", "consent-v2", False,
                original, "application/pdf",
            )

        evidence = self.db.scalar(select(Evidence).where(Evidence.case_id == case.id))
        stored_name = evidence.details["stored_name"]
        ciphertext = (self.upload_dir / stored_name).read_bytes()
        self.assertTrue(ciphertext.startswith(UPLOAD_MAGIC))
        self.assertNotIn(original, ciphertext)
        self.assertIn("application-encrypted", evidence.excerpt)
        self.assertEqual(evidence.details["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(read_private_upload(self.upload_dir / stored_name, 1024, key), original)


if __name__ == "__main__":
    unittest.main()
