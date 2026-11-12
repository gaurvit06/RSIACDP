import unittest
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.main import create_correction, enforce_public_correction_rate_limit, _throttle_fingerprint
from app.models import CorrectionRequest, LoginThrottle
from app.schemas import CorrectionCreate


class PublicCorrectionThrottleTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        LoginThrottle.__table__.create(self.engine)
        CorrectionRequest.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.original_settings = (
            settings.jwt_secret,
            settings.correction_max_requests,
            settings.correction_window_seconds,
            settings.correction_lockout_seconds,
        )
        settings.jwt_secret = "unit-test-secret"
        settings.correction_max_requests = 2
        settings.correction_window_seconds = 60
        settings.correction_lockout_seconds = 120

    def tearDown(self):
        (
            settings.jwt_secret,
            settings.correction_max_requests,
            settings.correction_window_seconds,
            settings.correction_lockout_seconds,
        ) = self.original_settings
        self.db.close()
        self.engine.dispose()

    def test_requests_are_counted_then_locked_until_window_and_lockout_expire(self):
        address = "203.0.113.12"
        enforce_public_correction_rate_limit(address, self.db, now=1000)
        enforce_public_correction_rate_limit(address, self.db, now=1001)

        with self.assertRaises(HTTPException) as caught:
            enforce_public_correction_rate_limit(address, self.db, now=1002)
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(caught.exception.headers["Retry-After"], "120")

        with self.assertRaises(HTTPException):
            enforce_public_correction_rate_limit(address, self.db, now=1061)
        enforce_public_correction_rate_limit(address, self.db, now=1123)

        row = self.db.scalar(select(LoginThrottle))
        self.assertEqual(row.attempts, 1)
        self.assertEqual(row.window_started_at, 1123)

    def test_throttle_stores_only_a_scoped_hmac_fingerprint(self):
        address = "198.51.100.77"
        enforce_public_correction_rate_limit(address, self.db, now=1000)

        row = self.db.scalar(select(LoginThrottle))
        self.assertEqual(row.fingerprint, _throttle_fingerprint("correction_request", address))
        self.assertNotIn(address, row.fingerprint)
        self.assertEqual(len(row.fingerprint), 64)

    def test_correction_route_persists_only_requests_within_limit(self):
        settings.correction_max_requests = 1
        request_context = SimpleNamespace(client=SimpleNamespace(host="192.0.2.40"))
        body = CorrectionCreate(
            case_ref="RC-1234ABCD",
            requester_email="affected@example.net",
            description="Please review whether the information associated with this reference is accurate.",
        )

        response = create_correction(body, request_context, self.db)

        self.assertTrue(response["received"])
        self.assertIn("status_token", response)
        with self.assertRaises(HTTPException) as caught:
            create_correction(body, request_context, self.db)
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(len(self.db.scalars(select(CorrectionRequest)).all()), 1)


if __name__ == "__main__":
    unittest.main()
