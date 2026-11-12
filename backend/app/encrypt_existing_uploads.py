"""Review or encrypt legacy plaintext uploads before enabling encrypted storage."""
from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path

from .config import settings, validate_upload_encryption
from .private_storage import (
    UPLOAD_MAGIC,
    decode_upload_encryption_key,
    is_private_upload_name,
    read_private_upload,
    write_private_upload,
)


def encrypt_existing_uploads(upload_dir: Path, key: bytes, maximum_plaintext_bytes: int, apply: bool = False) -> tuple[int, int]:
    """Return (already encrypted, plaintext needing encryption); optionally convert in place."""
    if len(key) != 32:
        raise ValueError("Upload encryption key must contain 32 bytes")
    if maximum_plaintext_bytes < 1:
        raise ValueError("Maximum upload size must be positive")
    if upload_dir.is_symlink() or not upload_dir.is_dir():
        raise ValueError("Upload directory must exist and must not be a symlink")

    already_encrypted = 0
    converted_or_pending = 0
    for path in sorted(upload_dir.iterdir(), key=lambda item: item.name):
        if not is_private_upload_name(path.name):
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("Upload directory contains an unsafe upload entry")
        if path.stat().st_size > maximum_plaintext_bytes + len(UPLOAD_MAGIC) + 12 + 16:
            raise ValueError("A private upload exceeds the configured size limit")
        with path.open("rb") as source:
            prefix = source.read(len(UPLOAD_MAGIC))
        if prefix == UPLOAD_MAGIC:
            read_private_upload(path, maximum_plaintext_bytes, key)
            already_encrypted += 1
            continue
        plaintext = read_private_upload(path, maximum_plaintext_bytes)
        if len(plaintext) > maximum_plaintext_bytes:
            raise ValueError("A private upload exceeds the configured size limit")
        converted_or_pending += 1
        if not apply:
            continue

        temporary_path = upload_dir / (secrets.token_hex(24) + path.suffix)
        try:
            write_private_upload(temporary_path, plaintext, key, associated_filename=path.name)
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
    return already_encrypted, converted_or_pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="encrypt plaintext uploads; without this flag only report counts")
    options = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        validate_upload_encryption(settings)
        key = decode_upload_encryption_key(settings.upload_encryption_key)
        if key is None:
            raise ValueError("Upload encryption key is required")
        encrypted, pending = encrypt_existing_uploads(
            settings.upload_dir,
            key,
            settings.max_upload_bytes,
            apply=options.apply,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Private upload conversion failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    action = "encrypted" if options.apply else "need encryption"
    print(f"Already encrypted: {encrypted}; plaintext uploads {action}: {pending}")
    if not options.apply and pending:
        print("Re-run with --apply while API and worker are stopped to convert the files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
