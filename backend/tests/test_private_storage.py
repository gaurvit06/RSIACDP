import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.private_storage import decode_upload_encryption_key, ensure_private_upload_dir, is_private_upload_name, read_private_upload, write_private_upload


class PrivateStorageTests(unittest.TestCase):
    def test_directory_is_created_and_restricted_on_posix(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            upload_dir = Path(parent) / "nested" / "private_uploads"
            ensure_private_upload_dir(upload_dir)
            self.assertTrue(upload_dir.is_dir())
            if os.name == "posix":
                self.assertEqual(upload_dir.stat().st_mode & 0o777, 0o700)

    def test_upload_is_created_exclusively_and_restricted_on_posix(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            upload_dir = Path(parent) / "private_uploads"
            ensure_private_upload_dir(upload_dir)
            target = upload_dir / ("a" * 48 + ".pdf")
            write_private_upload(target, b"synthetic-private-fixture")
            self.assertEqual(target.read_bytes(), b"synthetic-private-fixture")
            self.assertEqual(read_private_upload(target, 100), b"synthetic-private-fixture")
            with self.assertRaises(FileExistsError):
                write_private_upload(target, b"replacement")
            if os.name == "posix":
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_encrypted_upload_hides_plaintext_and_round_trips(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            target = Path(parent) / ("b" * 48 + ".png")
            plaintext = b"sensitive synthetic file bytes"
            key = bytes(range(32))
            write_private_upload(target, plaintext, key)
            stored = target.read_bytes()
            self.assertNotIn(plaintext, stored)
            self.assertEqual(read_private_upload(target, len(plaintext), key), plaintext)

    def test_encrypted_upload_fails_closed_on_wrong_key_downgrade_and_size_overflow(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            target = Path(parent) / ("c" * 48 + ".pdf")
            write_private_upload(target, b"synthetic content", b"a" * 32)
            with self.assertRaisesRegex(ValueError, "authentication failed"):
                read_private_upload(target, 100, b"b" * 32)
            with self.assertRaisesRegex(ValueError, "key is required"):
                read_private_upload(target, 100)
            with self.assertRaisesRegex(ValueError, "size limit"):
                read_private_upload(target, 4, b"a" * 32)
            target.write_bytes(b"unmarked plaintext")
            with self.assertRaisesRegex(ValueError, "format is invalid"):
                read_private_upload(target, 100, b"a" * 32)

    def test_encrypted_upload_is_bound_to_its_opaque_filename(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            original = Path(parent) / ("d" * 48 + ".pdf")
            renamed = Path(parent) / ("e" * 48 + ".pdf")
            write_private_upload(original, b"synthetic private contents", b"z" * 32)
            original.replace(renamed)
            with self.assertRaisesRegex(ValueError, "authentication failed"):
                read_private_upload(renamed, 100, b"z" * 32)

    def test_encryption_key_requires_canonical_base64_for_exactly_32_bytes(self):
        import base64
        valid = base64.b64encode(b"k" * 32).decode("ascii")
        self.assertEqual(decode_upload_encryption_key(valid), b"k" * 32)
        self.assertIsNone(decode_upload_encryption_key(""))
        for invalid in ("not-base64!", base64.b64encode(b"short").decode("ascii"), valid.rstrip("=")):
            with self.subTest(value=invalid), self.assertRaisesRegex(ValueError, "UPLOAD_ENCRYPTION_KEY"):
                decode_upload_encryption_key(invalid)

    def test_generated_upload_name_validation_is_shared_and_fail_closed(self):
        self.assertTrue(is_private_upload_name("a" * 48 + ".pdf"))
        for invalid in (
            "../" + "a" * 48 + ".pdf",
            "A" * 48 + ".pdf",
            "a" * 48 + ".exe",
            "operator-notes.txt",
            None,
        ):
            with self.subTest(value=invalid):
                self.assertFalse(is_private_upload_name(invalid))

        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            with self.assertRaisesRegex(ValueError, "filename is invalid"):
                write_private_upload(Path(parent) / "operator-notes.txt", b"not an upload")

    def test_failed_file_write_closes_and_removes_partial_upload(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-storage-") as parent:
            upload_dir = Path(parent) / "private_uploads"
            ensure_private_upload_dir(upload_dir)
            target = upload_dir / ("f" * 48 + ".pdf")
            with patch("app.private_storage.os.fdopen", side_effect=OSError("synthetic write failure")):
                with self.assertRaisesRegex(OSError, "synthetic write failure"):
                    write_private_upload(target, b"synthetic-private-fixture")
            self.assertFalse(target.exists())
