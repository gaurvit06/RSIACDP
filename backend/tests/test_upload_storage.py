from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

from app import upload_storage
from app.config import settings
from app.private_storage import UPLOAD_MAGIC


class SupabasePrivateStorageTests(unittest.TestCase):
    def setUp(self):
        self.backend = settings.upload_storage_backend
        self.url = settings.supabase_url
        self.service_key = settings.supabase_service_role_key
        self.bucket = settings.supabase_storage_bucket
        settings.upload_storage_backend = "supabase"
        settings.supabase_url = "https://project.example.supabase.co"
        settings.supabase_service_role_key = "unit-test-service-key-that-is-never-real"
        settings.supabase_storage_bucket = "private-evidence"
        self.filename = "a" * 48 + ".pdf"

    def tearDown(self):
        settings.upload_storage_backend = self.backend
        settings.supabase_url = self.url
        settings.supabase_service_role_key = self.service_key
        settings.supabase_storage_bucket = self.bucket

    def client_patch(self, handler):
        real_client = httpx.Client
        return patch.object(
            upload_storage.httpx,
            "Client",
            side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
        )

    def test_opaque_server_key_uses_gateway_header(self):
        settings.supabase_service_role_key = "sb_secret_synthetic-only"
        self.assertEqual(upload_storage._headers(), {"apikey": "sb_secret_synthetic-only"})

    def test_upload_download_and_delete_use_private_authenticated_storage_api(self):
        key = b"k" * 32
        plaintext = b"synthetic private evidence"
        stored = {}
        calls = []

        def handler(request):
            calls.append(request)
            self.assertEqual(request.headers["apikey"], settings.supabase_service_role_key)
            self.assertEqual(request.headers["authorization"], f"Bearer {settings.supabase_service_role_key}")
            if request.method == "POST":
                self.assertEqual(request.headers["x-upsert"], "false")
                stored[self.filename] = request.content
                return httpx.Response(200, json={"Key": self.filename})
            if request.method == "GET":
                return httpx.Response(200, content=stored[self.filename])
            if request.method == "DELETE":
                self.assertTrue(request.url.path.endswith("/object/private-evidence"))
                self.assertEqual(json.loads(request.content), {"prefixes": [self.filename]})
                return httpx.Response(200, json=[{"name": self.filename}])
            raise AssertionError(f"Unexpected request method {request.method}")

        with self.client_patch(handler):
            upload_storage.store_upload(self.filename, plaintext, key)
            self.assertTrue(stored[self.filename].startswith(UPLOAD_MAGIC))
            self.assertNotIn(plaintext, stored[self.filename])
            self.assertEqual(upload_storage.load_upload(self.filename, 1024, key), plaintext)
            upload_storage.delete_upload(self.filename)

        self.assertEqual([request.method for request in calls], ["POST", "GET", "DELETE"])
        self.assertTrue(all("project.example.supabase.co" in request.url.host for request in calls))

    def test_upload_listing_accepts_only_opaque_files_with_timezone_metadata(self):
        payload = [
            {"name": self.filename, "created_at": "2026-11-01T10:00:00Z"},
            {"name": "not-an-opaque-file.pdf", "created_at": "2026-11-01T10:00:00Z"},
            {"name": "b" * 48 + ".png", "created_at": "invalid"},
        ]

        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.url.path.endswith("/object/list/private-evidence"))
            return httpx.Response(200, json=payload)

        with self.client_patch(handler):
            files = upload_storage.list_uploads()
        self.assertEqual(files, [(self.filename, datetime(2026, 11, 1, 10, tzinfo=timezone.utc))])

    def test_remote_download_enforces_encrypted_size_bound(self):
        def handler(request):
            return httpx.Response(200, content=b"x" * 2048)

        with self.client_patch(handler):
            with self.assertRaisesRegex(ValueError, "size limit"):
                upload_storage.load_upload(self.filename, 20, b"k" * 32)


if __name__ == "__main__":
    unittest.main()
