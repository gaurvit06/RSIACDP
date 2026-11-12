"""Database-backed password-reset handler checks without TestClient startup."""
import hashlib
import hmac
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.db import Base
from app.main import consume_password_reset, issue_password_reset
from app.models import AuditEvent, PasswordResetToken, User
from app.schemas import PasswordResetConsumeRequest, PasswordResetIssueRequest
from app.security import hash_password, verify_password


def request_from_localhost() -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/api/auth/reset-password",
        "raw_path": b"/api/auth/reset-password",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 43121),
        "server": ("localhost", 8000),
    })


class PasswordResetHandlerTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.settings_patch = patch.multiple(
            "app.main.settings",
            jwt_secret="synthetic-password-reset-test-secret-32-bytes-minimum",
            password_reset_token_minutes=20,
            login_max_attempts=8,
            login_window_seconds=900,
            login_lockout_seconds=900,
        )
        self.settings_patch.start()
        with Session(self.engine) as db:
            self.reviewer = User(email="reviewer@example.invalid", password_hash=hash_password("synthetic reviewer password"), role="reviewer")
            self.target = User(email="target@example.invalid", password_hash=hash_password("synthetic original password"), role="analyst")
            db.add_all([self.reviewer, self.target])
            db.commit()
            db.refresh(self.reviewer)
            db.refresh(self.target)
            self.reviewer_id = self.reviewer.id
            self.target_id = self.target.id

    def tearDown(self):
        self.settings_patch.stop()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def issue(self, db: Session) -> str:
        reviewer = db.get(User, self.reviewer_id)
        response = issue_password_reset(
            self.target_id,
            PasswordResetIssueRequest(rationale="Verified account holder through approved synthetic test channel."),
            db,
            reviewer,
        )
        self.assertIn("no-store", response.headers.get("cache-control", ""))
        return json.loads(response.body)["reset_token"]

    def test_reset_tokens_are_hashed_replaced_one_time_and_revoke_sessions(self):
        with Session(self.engine) as db:
            target = db.get(User, self.target_id)
            target_token_version = target.token_version
            first_token = self.issue(db)
            first_hash = hmac.new(
                b"synthetic-password-reset-test-secret-32-bytes-minimum",
                first_token.encode(),
                hashlib.sha256,
            ).hexdigest()
            stored = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == first_hash))
            self.assertIsNotNone(stored)
            self.assertNotEqual(stored.token_hash, first_token)
            self.assertGreater(stored.expires_at, stored.created_at)

            second_token = self.issue(db)
            self.assertIsNotNone(stored.consumed_at)
            with self.assertRaises(HTTPException) as replaced:
                consume_password_reset(
                    PasswordResetConsumeRequest(token=first_token, new_password="synthetic replacement password"),
                    request_from_localhost(),
                    db,
                )
            self.assertEqual(replaced.exception.status_code, 400)

            result = consume_password_reset(
                PasswordResetConsumeRequest(token=second_token, new_password="synthetic replacement password"),
                request_from_localhost(),
                db,
            )
            self.assertEqual(result["status"], "password_updated")
            db.refresh(target)
            self.assertEqual(target.token_version, target_token_version + 1)
            self.assertTrue(verify_password("synthetic replacement password", target.password_hash))
            self.assertFalse(verify_password("synthetic original password", target.password_hash))
            with self.assertRaises(HTTPException) as reused:
                consume_password_reset(
                    PasswordResetConsumeRequest(token=second_token, new_password="another synthetic replacement"),
                    request_from_localhost(),
                    db,
                )
            self.assertEqual(reused.exception.status_code, 400)
            audit = db.scalars(select(AuditEvent).where(AuditEvent.action == "password_reset_completed")).all()
            self.assertEqual(len(audit), 1)
            self.assertNotIn(first_token, str(audit[0].detail))
            self.assertNotIn(second_token, str(audit[0].detail))

    def test_expired_reset_token_cannot_change_password(self):
        with Session(self.engine) as db:
            token = self.issue(db)
            digest = hmac.new(
                b"synthetic-password-reset-test-secret-32-bytes-minimum",
                token.encode(),
                hashlib.sha256,
            ).hexdigest()
            reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == digest))
            reset.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
            target = db.get(User, self.target_id)
            original_hash = target.password_hash
            with self.assertRaises(HTTPException) as expired:
                consume_password_reset(
                    PasswordResetConsumeRequest(token=token, new_password="synthetic replacement password"),
                    request_from_localhost(),
                    db,
                )
            self.assertEqual(expired.exception.status_code, 400)
            db.refresh(target)
            self.assertEqual(target.password_hash, original_hash)


if __name__ == "__main__":
    unittest.main()
