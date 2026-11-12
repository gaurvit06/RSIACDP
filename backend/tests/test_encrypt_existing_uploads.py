import tempfile
import unittest
from pathlib import Path

from app.encrypt_existing_uploads import encrypt_existing_uploads
from app.private_storage import UPLOAD_MAGIC, read_private_upload, write_private_upload


class ExistingUploadEncryptionTests(unittest.TestCase):
    def test_dry_run_does_not_change_plaintext_and_apply_encrypts_it(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-encrypt-migration-") as directory:
            root = Path(directory)
            path = root / ("a" * 48 + ".pdf")
            original = b"synthetic legacy upload bytes"
            path.write_bytes(original)
            key = b"k" * 32

            self.assertEqual(encrypt_existing_uploads(root, key, 1024), (0, 1))
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(encrypt_existing_uploads(root, key, 1024, apply=True), (0, 1))
            self.assertTrue(path.read_bytes().startswith(UPLOAD_MAGIC))
            self.assertNotIn(original, path.read_bytes())
            self.assertEqual(read_private_upload(path, 1024, key), original)
            self.assertEqual(encrypt_existing_uploads(root, key, 1024, apply=True), (1, 0))

    def test_conversion_fails_closed_on_wrong_key_or_oversize_upload(self):
        with tempfile.TemporaryDirectory(prefix="rsaicdp-encrypt-migration-") as directory:
            root = Path(directory)
            encrypted = root / ("b" * 48 + ".png")
            write_private_upload(encrypted, b"synthetic encrypted upload", b"a" * 32)
            with self.assertRaisesRegex(ValueError, "authentication failed"):
                encrypt_existing_uploads(root, b"b" * 32, 1024)

        with tempfile.TemporaryDirectory(prefix="rsaicdp-encrypt-migration-") as directory:
            root = Path(directory)
            oversized = root / ("c" * 48 + ".jpg")
            oversized.write_bytes(b"x" * 20)
            with self.assertRaisesRegex(ValueError, "size limit"):
                encrypt_existing_uploads(root, b"k" * 32, 10, apply=True)
            self.assertEqual(oversized.read_bytes(), b"x" * 20)


if __name__ == "__main__":
    unittest.main()
