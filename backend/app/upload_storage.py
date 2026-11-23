"""Private upload storage shared by API and worker processes."""
from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from .config import settings
from .private_storage import (
    decrypt_private_upload_bytes,
    encrypt_private_upload_bytes,
    is_private_upload_name,
    read_private_upload,
    write_private_upload,
    ensure_private_upload_dir,
)

# httpx logs request URLs at INFO, which would include opaque upload object IDs.
logging.getLogger("httpx").setLevel(logging.WARNING)


class PrivateStorageError(RuntimeError):
    """Storage operation failed without embedding credentials, URLs or object data."""


def _headers() -> dict[str, str]:
    # Supabase's opaque server keys authenticate at the API gateway.
    if settings.supabase_service_role_key.startswith("sb_secret_"):
        return {"apikey": settings.supabase_service_role_key}
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def _object_url(name: str | None = None) -> str:
    bucket = quote(settings.supabase_storage_bucket, safe="")
    base = f"{settings.supabase_url}/storage/v1/object/{bucket}"
    return f"{base}/{quote(name, safe='')}" if name is not None else base


def ensure_upload_storage() -> None:
    if settings.upload_storage_backend == "local":
        ensure_private_upload_dir(settings.upload_dir)
    elif settings.upload_storage_backend == "supabase":
        from .config import validate_upload_storage
        validate_upload_storage(settings)
    else:
        raise RuntimeError("UPLOAD_STORAGE_BACKEND must be either local or supabase")


def store_upload(name: str, content: bytes, encryption_key: bytes | None) -> None:
    if not is_private_upload_name(name):
        raise ValueError("Upload filename is invalid")
    if settings.upload_storage_backend == "local":
        ensure_private_upload_dir(settings.upload_dir)
        write_private_upload(settings.upload_dir / name, content, encryption_key)
        return
    encrypted = encrypt_private_upload_bytes(name, content, encryption_key)
    try:
        with httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            with client.stream(
                "POST",
                _object_url(name),
                headers={**_headers(), "Content-Type": "application/octet-stream", "x-upsert": "false"},
                content=encrypted,
            ) as response:
                if response.status_code not in {200, 201}:
                    raise PrivateStorageError("Private object storage rejected an upload")
    except httpx.HTTPError:
        raise PrivateStorageError("Private object storage upload failed") from None


def load_upload(name: str, maximum_plaintext_bytes: int, encryption_key: bytes | None) -> bytes:
    if not is_private_upload_name(name):
        raise ValueError("Upload filename is invalid")
    if settings.upload_storage_backend == "local":
        path = settings.upload_dir / name
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError("Private upload is missing from storage")
        return read_private_upload(path, maximum_plaintext_bytes, encryption_key)
    maximum_stored_bytes = maximum_plaintext_bytes
    if encryption_key is not None:
        from .private_storage import UPLOAD_MAGIC, UPLOAD_NONCE_BYTES, UPLOAD_TAG_BYTES
        maximum_stored_bytes += len(UPLOAD_MAGIC) + UPLOAD_NONCE_BYTES + UPLOAD_TAG_BYTES
    try:
        with httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0), follow_redirects=False) as client:
            with client.stream("GET", _object_url(name), headers=_headers()) as response:
                if response.status_code == 404:
                    raise FileNotFoundError("Private upload is missing from storage")
                if response.status_code != 200:
                    raise PrivateStorageError("Private object storage download failed")
                stored = bytearray()
                for block in response.iter_bytes(64 * 1024):
                    stored.extend(block)
                    if len(stored) > maximum_stored_bytes:
                        raise ValueError("Private upload exceeds the configured size limit")
    except httpx.HTTPError:
        raise PrivateStorageError("Private object storage download failed") from None
    return decrypt_private_upload_bytes(name, bytes(stored), maximum_plaintext_bytes, encryption_key)


def delete_upload(name: str) -> None:
    if not is_private_upload_name(name):
        raise ValueError("Upload filename is invalid")
    if settings.upload_storage_backend == "local":
        (settings.upload_dir / name).unlink(missing_ok=True)
        return
    try:
        with httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            with client.stream("DELETE", _object_url(), headers={**_headers(), "Content-Type": "application/json"}, json={"prefixes": [name]}) as response:
                if response.status_code not in {200, 204, 404}:
                    raise PrivateStorageError("Private object storage delete failed")
    except httpx.HTTPError:
        raise PrivateStorageError("Private object storage delete failed") from None


def list_uploads() -> list[tuple[str, datetime]]:
    """List opaque root objects and creation times for orphan/retention cleanup."""
    if settings.upload_storage_backend == "local":
        ensure_private_upload_dir(settings.upload_dir)
        objects: list[tuple[str, datetime]] = []
        for path in settings.upload_dir.iterdir():
            try:
                if is_private_upload_name(path.name) and path.is_file() and not path.is_symlink():
                    objects.append((path.name, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)))
            except OSError:
                continue
        return objects

    objects = []
    offset = 0
    page_size = 100
    try:
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            while True:
                with client.stream(
                    "POST",
                    f"{settings.supabase_url}/storage/v1/object/list/{quote(settings.supabase_storage_bucket, safe='')}",
                    headers={**_headers(), "Content-Type": "application/json"},
                    json={"prefix": "", "limit": page_size, "offset": offset, "sortBy": {"column": "name", "order": "asc"}},
                ) as response:
                    if response.status_code != 200:
                        raise PrivateStorageError("Private object storage listing failed")
                    payload = bytearray()
                    for block in response.iter_bytes(64 * 1024):
                        payload.extend(block)
                        if len(payload) > 2 * 1024 * 1024:
                            raise PrivateStorageError("Private object storage returned an oversized listing")
                entries = json.loads(payload)
                if not isinstance(entries, list):
                    raise PrivateStorageError("Private object storage returned an invalid listing")
                for entry in entries:
                    if not isinstance(entry, dict) or not is_private_upload_name(entry.get("name")):
                        continue
                    created = entry.get("created_at") or entry.get("updated_at")
                    if not isinstance(created, str):
                        continue
                    try:
                        timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if timestamp.tzinfo is None:
                        continue
                    objects.append((entry["name"], timestamp.astimezone(timezone.utc)))
                if len(entries) < page_size:
                    break
                offset += page_size
    except httpx.HTTPError:
        raise PrivateStorageError("Private object storage listing failed") from None
    return objects
