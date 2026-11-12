from datetime import datetime, timezone
import hashlib
from types import SimpleNamespace
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.main import correction_status
from app.models import CorrectionRequest
from app.public_status import public_correction_status
from app.schemas import CorrectionStatusRequest


class PublicCorrectionStatusTests(unittest.TestCase):
    def test_public_status_never_returns_investigator_free_text(self):
        private_note = "Reviewed for Asha Kumar; call 9876543210 or see passport ABCDE1234F"
        request = SimpleNamespace(
            request_ref="CR-0123456789AB",
            status="resolved",
            resolution=private_note,
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )

        result = public_correction_status(request)

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(
            result["status_message"],
            "The review is complete. Any applicable record correction has been applied.",
        )
        self.assertNotIn("resolution", result)
        self.assertNotIn(private_note, str(result))
        self.assertNotIn("Asha Kumar", str(result))
        self.assertNotIn("9876543210", str(result))
        self.assertNotIn("ABCDE1234F", str(result))

    def test_unknown_legacy_status_uses_fixed_neutral_message(self):
        request = SimpleNamespace(
            request_ref="CR-0123456789AB",
            status="legacy-internal-value",
            resolution="never expose this",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )

        result = public_correction_status(request)

        self.assertEqual(result["status"], "investigating")
        self.assertEqual(result["status_message"], "Your request is being reviewed.")
        self.assertNotIn("legacy-internal-value", str(result))
        self.assertNotIn("resolution", result)

    def test_status_handler_checks_token_and_omits_investigator_note(self):
        engine = create_engine("sqlite://")
        CorrectionRequest.__table__.create(engine)
        token = "correction-status-token-with-at-least-32-characters"
        note = "Reviewed the materials for a named requester and a private source record."
        with Session(engine) as db:
            db.add(CorrectionRequest(
                request_ref="CR-0123456789AB",
                case_ref="RC-1234ABCD",
                requester_email="affected@example.net",
                status_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                description="Synthetic correction request description.",
                status="resolved",
                resolution=note,
            ))
            db.commit()
            result = correction_status("CR-0123456789AB", CorrectionStatusRequest(status_token=token), db)
            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["status_message"], "The review is complete. Any applicable record correction has been applied.")
            self.assertNotIn("resolution", result)
            self.assertNotIn(note, str(result))
            with self.assertRaises(HTTPException) as caught:
                correction_status("CR-0123456789AB", CorrectionStatusRequest(status_token="x" * 40), db)
            self.assertEqual(getattr(caught.exception, "status_code", None), 404)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
