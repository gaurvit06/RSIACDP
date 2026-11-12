import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.db import Base
from app.main import register
from app.models import AccountProvisioningGate, User
from app.schemas import RegisterRequest


def test_request() -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/auth/register",
        "raw_path": b"/api/auth/register",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 43121),
        "server": ("localhost", 8000),
    })


class AccountProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(AccountProvisioningGate(id=1, generation=0))
            db.commit()
        self.settings_patch = patch.multiple(
            "app.main.settings",
            jwt_secret="synthetic-test-secret-that-is-at-least-32-characters-long",
            initial_investigator_code="investigator-test-code",
            initial_reviewer_code="reviewer-test-code",
            register_max_requests=20,
            register_window_seconds=900,
            register_lockout_seconds=900,
        )
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_one_time_privileged_roles_are_serialized_and_cannot_be_reused(self):
        with Session(self.engine) as db:
            investigator = register(RegisterRequest(email="first@example.com", password="synthetic-password-1", setup_code="investigator-test-code"), test_request(), db)
            reviewer = register(RegisterRequest(email="reviewer@example.com", password="synthetic-password-2", setup_code="reviewer-test-code"), test_request(), db)
            self.assertEqual(investigator["user"]["role"], "investigator")
            self.assertEqual(reviewer["user"]["role"], "reviewer")
            gate = db.get(AccountProvisioningGate, 1)
            self.assertEqual(gate.generation, 2)
            with self.assertRaises(HTTPException) as raised:
                register(RegisterRequest(email="second-reviewer@example.com", password="synthetic-password-3", setup_code="reviewer-test-code"), test_request(), db)
            self.assertEqual(raised.exception.status_code, 409)
            db.rollback()
            users = db.scalars(select(User).order_by(User.id)).all()
            self.assertEqual([user.role for user in users], ["investigator", "reviewer"])

    def test_registration_fails_closed_when_gate_row_is_missing(self):
        with Session(self.engine) as db:
            db.delete(db.get(AccountProvisioningGate, 1))
            db.commit()
            with self.assertRaises(HTTPException) as raised:
                register(RegisterRequest(email="blocked@example.com", password="synthetic-password-1", setup_code="investigator-test-code"), test_request(), db)
            self.assertEqual(raised.exception.status_code, 503)
            self.assertEqual(db.scalar(select(User.id).limit(1)), None)


if __name__ == "__main__":
    unittest.main()
