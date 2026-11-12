import io
import os
import errno
import tarfile
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from app.restore_uploads import restore_archive
from app.private_storage import read_private_upload, write_private_upload


def add_file(archive: tarfile.TarFile, name: str, content: bytes = b"synthetic upload"):
    info = tarfile.TarInfo(name)
    info.size = len(content)
    archive.addfile(info, io.BytesIO(content))


class RestoreUploadsTests(unittest.TestCase):
    def test_stages_on_upload_volume_and_rolls_back_if_install_fails(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "uploads.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                add_file(archive, "a" * 48 + ".pdf", b"replacement upload")
            upload_dir = root / "private_uploads"
            upload_dir.mkdir()
            existing = upload_dir / ("b" * 48 + ".pdf")
            existing.write_bytes(b"keep existing upload")
            real_replace = os.replace

            def fail_cross_device_or_install(source, destination):
                source_path = Path(source)
                destination_path = Path(destination)
                self.assertEqual(source_path.stat().st_dev, destination_path.parent.stat().st_dev)
                if source_path.name == "a" * 48 + ".pdf" and destination_path.parent == upload_dir:
                    raise OSError(errno.EIO, "synthetic install failure")
                return real_replace(source, destination)

            with patch("app.restore_uploads.os.replace", side_effect=fail_cross_device_or_install):
                with self.assertRaisesRegex(OSError, "synthetic install failure"):
                    restore_archive(archive_path, upload_dir, 1024)

            self.assertEqual(existing.read_bytes(), b"keep existing upload")
            self.assertEqual([path.name for path in upload_dir.iterdir()], [existing.name])

    def test_accepts_authenticated_ciphertext_header_over_plaintext_limit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "source"
            source_dir.mkdir()
            source = source_dir / ("a" * 48 + ".pdf")
            plaintext = b"synthetic encrypted backup"
            key = b"k" * 32
            write_private_upload(source, plaintext, key)
            archive_path = root / "encrypted.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(source, arcname="./" + source.name)
            restored_dir = root / "restored"
            self.assertEqual(restore_archive(archive_path, restored_dir, len(plaintext), key), 1)
            self.assertEqual(read_private_upload(restored_dir / source.name, len(plaintext), key), plaintext)

    def test_wrong_key_or_plaintext_downgrade_preserves_existing_restore_target(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "plaintext.tar.gz"
            name = "b" * 48 + ".pdf"
            with tarfile.open(archive_path, "w:gz") as archive:
                add_file(archive, name, b"plaintext upload")
            upload_dir = root / "private_uploads"
            upload_dir.mkdir()
            existing = upload_dir / ("c" * 48 + ".pdf")
            write_private_upload(existing, b"keep current encrypted upload", b"k" * 32)
            with self.assertRaisesRegex(ValueError, "format is invalid"):
                restore_archive(archive_path, upload_dir, 1024, b"k" * 32)
            self.assertEqual(read_private_upload(existing, 1024, b"k" * 32), b"keep current encrypted upload")

    def test_accepts_dot_root_tar_layout_used_by_backup_script(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "dot-root-layout.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                root_entry = tarfile.TarInfo("./")
                root_entry.type = tarfile.DIRTYPE
                archive.addfile(root_entry)
                add_file(archive, "./" + "a" * 48 + ".pdf", b"pdf bytes")
            upload_dir = root / "private_uploads"
            count = restore_archive(archive_path, upload_dir, 1024)
            self.assertEqual(count, 1)
            self.assertEqual((upload_dir / ("a" * 48 + ".pdf")).read_bytes(), b"pdf bytes")

    def test_restores_only_valid_opaque_upload_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "uploads.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                add_file(archive, "a" * 48 + ".pdf", b"pdf bytes")
                add_file(archive, "b" * 48 + ".png", b"image bytes")
            upload_dir = root / "private_uploads"
            upload_dir.mkdir()
            (upload_dir / "old-file").write_bytes(b"old")
            restored = restore_archive(archive_path, upload_dir, 1024)
            self.assertEqual(restored, 2)
            self.assertFalse((upload_dir / "old-file").exists())
            self.assertEqual((upload_dir / ("a" * 48 + ".pdf")).read_bytes(), b"pdf bytes")

    def test_rejects_traversal_entry_before_replacing_existing_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "unsafe.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                add_file(archive, "../outside")
            upload_dir = root / "private_uploads"
            upload_dir.mkdir()
            existing = upload_dir / ("c" * 48 + ".jpg")
            existing.write_bytes(b"keep")
            with self.assertRaisesRegex(ValueError, "unsafe archive entry"):
                restore_archive(archive_path, upload_dir, 1024)
            self.assertEqual(existing.read_bytes(), b"keep")

    def test_rejects_symlinks_and_oversized_files_before_replacement(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            upload_dir = root / "private_uploads"
            upload_dir.mkdir()
            existing = upload_dir / ("d" * 48 + ".webp")
            existing.write_bytes(b"keep")
            symlink_archive = root / "symlink.tar.gz"
            with tarfile.open(symlink_archive, "w:gz") as archive:
                link = tarfile.TarInfo("e" * 48 + ".pdf")
                link.type = tarfile.SYMTYPE
                link.linkname = "../../outside"
                archive.addfile(link)
            with self.assertRaisesRegex(ValueError, "unsafe archive entry"):
                restore_archive(symlink_archive, upload_dir, 1024)
            oversized_archive = root / "large.tar.gz"
            with tarfile.open(oversized_archive, "w:gz") as archive:
                add_file(archive, "f" * 48 + ".pdf", b"x" * 20)
            with self.assertRaisesRegex(ValueError, "size limit"):
                restore_archive(oversized_archive, upload_dir, 10)
            self.assertEqual(existing.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
