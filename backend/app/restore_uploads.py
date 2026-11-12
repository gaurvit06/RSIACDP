"""Validate and restore the private-upload tarball produced by scripts/backup.ps1."""
from __future__ import annotations

import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from .config import settings, validate_upload_encryption
from .private_storage import (
    UPLOAD_MAGIC,
    UPLOAD_NONCE_BYTES,
    UPLOAD_TAG_BYTES,
    decode_upload_encryption_key,
    is_private_upload_name,
    read_private_upload,
)


def restore_archive(archive_path: Path, upload_dir: Path, max_file_bytes: int, encryption_key: bytes | None = None) -> int:
    """Stage validated regular upload files before replacing the live upload set."""
    upload_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Stage on the upload volume itself. The Docker named volume is a separate
    # filesystem from /app, so staging beside it makes os.replace fail with EXDEV.
    staging = Path(tempfile.mkdtemp(prefix=".private-uploads-restore-", dir=upload_dir))
    new_files = staging / "new"
    previous_files = staging / "previous"
    new_files.mkdir(mode=0o700)
    previous_files.mkdir(mode=0o700)
    count = 0
    names: set[str] = set()
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            members = archive.getmembers()
            validated: list[tuple[tarfile.TarInfo, str]] = []
            for member in members:
                # GNU tar's `-C private_uploads .` format includes one `./`
                # directory record and prefixes each flat file with `./`.
                if member.isdir() and member.name in {".", "./"}:
                    continue
                name = member.name
                while name.startswith("./"):
                    name = name[2:]
                if (not member.isfile() or PurePosixPath(name).name != name or
                        not is_private_upload_name(name) or name in names):
                    raise ValueError("Upload backup contains an unsupported or unsafe archive entry")
                encrypted_storage_limit = len(UPLOAD_MAGIC) + UPLOAD_NONCE_BYTES + UPLOAD_TAG_BYTES
                if member.size < 1 or member.size > max_file_bytes + encrypted_storage_limit:
                    raise ValueError("Upload backup contains a file outside the configured size limit")
                names.add(name)
                validated.append((member, name))
            for member, name in validated:
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError("Upload backup entry could not be read")
                destination = new_files / name
                descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with source, os.fdopen(descriptor, "wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                if destination.stat().st_size != member.size:
                    raise ValueError("Upload backup entry size did not match its archive metadata")
                # Authenticate encrypted files and enforce the plaintext byte limit
                # before the existing upload set can be replaced.
                read_private_upload(destination, max_file_bytes, encryption_key)

        # Keep the existing upload set in the same volume until every replacement
        # has been moved into place. This supports rollback if an individual move
        # fails and avoids cross-device renames on Docker named volumes.
        installed_names: list[str] = []
        try:
            for existing in upload_dir.iterdir():
                if existing != staging:
                    os.replace(existing, previous_files / existing.name)
            for staged in new_files.iterdir():
                os.replace(staged, upload_dir / staged.name)
                installed_names.append(staged.name)
                count += 1
        except OSError:
            for name in installed_names:
                restored = upload_dir / name
                if restored.is_dir() and not restored.is_symlink():
                    shutil.rmtree(restored)
                else:
                    restored.unlink(missing_ok=True)
            for previous in previous_files.iterdir():
                os.replace(previous, upload_dir / previous.name)
            raise
        if os.name == "posix":
            upload_dir.chmod(0o700)
        return count
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: python -m app.restore_uploads ARCHIVE UPLOAD_DIRECTORY", file=sys.stderr)
        return 2
    try:
        validate_upload_encryption(settings)
        count = restore_archive(
            Path(args[0]), Path(args[1]), settings.max_upload_bytes,
            decode_upload_encryption_key(settings.upload_encryption_key),
        )
    except (OSError, tarfile.TarError, ValueError, RuntimeError) as exc:
        print(f"Private upload restore failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"Restored {count} private upload files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
