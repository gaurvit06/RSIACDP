"""Opt-in concurrency check for privileged account provisioning on PostgreSQL.

Requires a dedicated disposable database whose name ends in ``_test``. The test
creates and deletes only synthetic accounts and throttle rows; the gate counter
is intentionally left advanced. It does not drop tables or the database.
"""
import os
import secrets
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.main import register, registration_throttle_fingerprint
from app.models import AccountProvisioningGate, LoginThrottle, User
from app.schemas import RegisterRequest


TEST_DATABASE_URL = os.getenv("RSAICDP_PROVISIONING_TEST_DATABASE_URL", "")


def make_request(address: str) -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/auth/register",
        "raw_path": b"/api/auth/register",
        "query_string": b"",
        "headers": [],
        "client": (address, 43121),
        "server": ("localhost", 8000),
    })


@unittest.skipUnless(TEST_DATABASE_URL, "set RSAICDP_PROVISIONING_TEST_DATABASE_URL to an isolated PostgreSQL database ending in _test")
class PostgresAccountProvisioningConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_name = urlsplit(TEST_DATABASE_URL).path.rsplit("/", 1)[-1]
        if not database_name.endswith("_test"):
            raise RuntimeError("Refusing to run provisioning test unless the database name ends in _test")
        cls.engine = create_engine(TEST_DATABASE_URL, pool_size=4, max_overflow=0)
        if cls.engine.dialect.name != "postgresql":
            cls.engine.dispose()
            raise RuntimeError("Provisioning concurrency test requires PostgreSQL")
        with Session(cls.engine) as db:
            if db.scalar(select(func.count()).select_from(User)) != 0:
                cls.engine.dispose()
                raise RuntimeError("Provisioning concurrency test requires an empty disposable users table")
            if db.get(AccountProvisioningGate, 1) is None:
                cls.engine.dispose()
                raise RuntimeError("Run Alembic migrations before the provisioning concurrency test")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_simultaneous_first_investigator_and_reviewer_claims_are_single_winner(self):
        suffix = secrets.token_hex(6)
        prefix = f"provision-test-{suffix}"
        addresses = ["198.51.100.10", "198.51.100.11", "198.51.100.12", "198.51.100.13"]
        self.settings_patch = patch.multiple(
            "app.main.settings",
            jwt_secret=f"synthetic-postgres-test-secret-{secrets.token_hex(24)}",
            initial_investigator_code="synthetic-investigator-code",
            initial_reviewer_code="synthetic-reviewer-code",
            register_max_requests=20,
            register_window_seconds=900,
            register_lockout_seconds=900,
        )
        self.settings_patch.start()

        def race(role: str, setup_code: str, offset: int):
            start = threading.Barrier(2)
            second_attempted_gate = threading.Event()
            local = threading.local()
            observed_gate_updates = 0
            observed_lock = threading.Lock()

            def before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
                nonlocal observed_gate_updates
                if "update account_provisioning_gates" not in statement.lower():
                    return
                with observed_lock:
                    observed_gate_updates += 1
                    local.gate_update_index = observed_gate_updates
                    if observed_gate_updates == 2:
                        second_attempted_gate.set()

            def after_cursor_execute(connection, cursor, statement, parameters, context, executemany):
                if getattr(local, "gate_update_index", None) == 1 and not second_attempted_gate.wait(timeout=10):
                    raise AssertionError("second registration never attempted the gate while the first transaction held it")

            def contend(index: int):
                actual_index = offset + index
                email = f"{prefix}-{role}-{index}@example.com"
                body = RegisterRequest(email=email, password=f"Synthetic-test-passphrase-{actual_index}-long", setup_code=setup_code)
                with Session(self.engine) as db:
                    start.wait(timeout=10)
                    try:
                        response = register(body, make_request(addresses[actual_index]), db)
                        return ("created", response["user"]["role"], email)
                    except HTTPException as error:
                        db.rollback()
                        return ("rejected", error.status_code, email)

            from sqlalchemy import event
            event.listen(self.engine, "before_cursor_execute", before_cursor_execute)
            event.listen(self.engine, "after_cursor_execute", after_cursor_execute)
            try:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(contend, (0, 1)))
                self.assertTrue(second_attempted_gate.is_set())
                return results
            finally:
                event.remove(self.engine, "before_cursor_execute", before_cursor_execute)
                event.remove(self.engine, "after_cursor_execute", after_cursor_execute)

        try:
            investigator_results = race("investigator", "synthetic-investigator-code", 0)
            self.assertEqual(sum(result[:2] == ("created", "investigator") for result in investigator_results), 1)
            self.assertEqual(sum(result[:2] == ("rejected", 403) for result in investigator_results), 1)
            with Session(self.engine) as db:
                self.assertEqual(db.scalar(select(func.count()).select_from(User)), 1)
                self.assertEqual(db.scalar(select(User.role)), "investigator")

            reviewer_results = race("reviewer", "synthetic-reviewer-code", 2)
            self.assertEqual(sum(result[:2] == ("created", "reviewer") for result in reviewer_results), 1)
            self.assertEqual(sum(result[:2] == ("rejected", 409) for result in reviewer_results), 1)
            with Session(self.engine) as db:
                roles = db.scalars(select(User.role).order_by(User.role)).all()
                self.assertEqual(roles, ["investigator", "reviewer"])
        finally:
            try:
                with Session(self.engine) as db:
                    db.execute(delete(User).where(User.email.like(f"{prefix}-%")))
                    fingerprints = [registration_throttle_fingerprint(address) for address in addresses]
                    db.execute(delete(LoginThrottle).where(LoginThrottle.fingerprint.in_(fingerprints)))
                    db.commit()
            finally:
                self.settings_patch.stop()


if __name__ == "__main__":
    unittest.main()
