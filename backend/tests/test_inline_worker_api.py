"""Integration check for API-owned worker lifecycle on single-service hosts."""
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch


TEST_ROOT = Path(tempfile.mkdtemp(prefix="rsaicdp-inline-worker-api-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'integration.db').as_posix()}"
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET"] = "inline-worker-test-only-secret-0123456789"
os.environ["INITIAL_INVESTIGATOR_CODE"] = "inline-worker-investigator-test-code-123456"
os.environ["INITIAL_REVIEWER_CODE"] = "inline-worker-reviewer-test-code-abcdef"
os.environ["UPLOAD_DIR"] = str(TEST_ROOT / "private_uploads")
os.environ["RUN_INLINE_WORKER"] = "false"

from fastapi.testclient import TestClient
from app import main
from app.config import settings
from app.db import engine


class InlineWorkerApiLifecycleTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def test_api_lifespan_starts_and_stops_inline_worker(self):
        started = threading.Event()
        stopped = threading.Event()

        def worker_target(stop_event):
            started.set()
            stop_event.wait()
            stopped.set()

        with patch.object(settings, "run_inline_worker", True), patch("app.worker.run_worker", worker_target):
            with TestClient(main.app) as client:
                self.assertTrue(started.wait(2), "API startup did not start the inline worker")
                self.assertEqual(client.get("/health/ready").status_code, 200)
            self.assertTrue(stopped.wait(2), "API shutdown did not signal the inline worker")


if __name__ == "__main__":
    unittest.main()
