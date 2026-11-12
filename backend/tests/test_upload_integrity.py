"""Worker input must match the bytes and size recorded at upload intake."""
import hashlib
import base64
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.worker import read_uploaded_text
from app.private_storage import write_private_upload
import fitz


class UploadIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rsaicdp-integrity-")
        self.upload_dir = Path(self.temp.name)
        self.stored_name = "a" * 48 + ".pdf"
        self.path = self.upload_dir / self.stored_name

    def tearDown(self):
        self.temp.cleanup()

    def read(self, details, max_bytes=None):
        with patch("app.worker.settings.upload_dir", self.upload_dir):
            if max_bytes is None:
                return read_uploaded_text(SimpleNamespace(details=details))
            with patch("app.worker.settings.max_upload_bytes", max_bytes):
                return read_uploaded_text(SimpleNamespace(details=details))

    def test_worker_rejects_content_changed_since_intake(self):
        original = b"original bytes"
        self.path.write_bytes(b"modified bytes")
        with self.assertRaisesRegex(ValueError, "integrity check failed"):
            self.read({
                "stored_name": self.stored_name,
                "media_type": "application/pdf",
                "sha256": hashlib.sha256(original).hexdigest(),
            })

    def test_worker_rejects_upload_over_configured_size_before_parsing(self):
        content = b"x" * 9
        self.path.write_bytes(content)
        with self.assertRaisesRegex(ValueError, "configured size limit"):
            self.read({
                "stored_name": self.stored_name,
                "media_type": "application/pdf",
                "sha256": hashlib.sha256(content).hexdigest(),
            }, max_bytes=8)

    def test_worker_requires_a_well_formed_intake_hash(self):
        self.path.write_bytes(b"content")
        with self.assertRaisesRegex(ValueError, "integrity reference is invalid"):
            self.read({"stored_name": self.stored_name, "media_type": "application/pdf"})

    def test_worker_decrypts_authenticated_upload_before_hash_and_pdf_processing(self):
        key = b"k" * 32
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Recruitment Analyst")
        content = pdf.tobytes()
        pdf.close()
        write_private_upload(self.path, content, key)
        details = {
            "stored_name": self.stored_name,
            "media_type": "application/pdf",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        encoded_key = base64.b64encode(key).decode("ascii")
        with patch("app.worker.settings.upload_encryption_key", encoded_key):
            document = self.read(details)
        self.assertIn("Recruitment Analyst", document.text)


if __name__ == "__main__":
    unittest.main()
