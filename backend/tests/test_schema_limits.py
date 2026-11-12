import unittest

from pydantic import ValidationError

from app.schemas import CorrectionCreate, LoginRequest, RegisterRequest, SourceRecordCreate


class RequestSchemaLimitTests(unittest.TestCase):
    def test_local_corpus_accepts_bank_account_and_ifsc_identifier_types(self):
        for entity_type, value in (("bank_account", "9876543210"), ("ifsc_code", "HDFC0001234")):
            record = SourceRecordCreate(
                entity_type=entity_type, value=value, source_name="Synthetic source",
                source_type="other", claim="Synthetic test claim", outcome="result",
                authority="curated",
            )
            self.assertEqual(record.entity_type, entity_type)

    def test_login_accepts_password_at_limit_and_rejects_longer_password(self):
        valid = LoginRequest(email="person@example.org", password="x" * 128)
        self.assertEqual(len(valid.password), 128)
        with self.assertRaises(ValidationError):
            LoginRequest(email="person@example.org", password="x" * 129)

    def test_account_and_correction_emails_cannot_exceed_database_column_size(self):
        oversized_email = "a" * 310 + "@example.test"
        with self.assertRaises(ValidationError):
            RegisterRequest(email=oversized_email, password="valid-password-123", setup_code="bootstrap")
        with self.assertRaises(ValidationError):
            CorrectionCreate(case_ref="RC-ABCDEF12", requester_email=oversized_email, description="Please correct this submitted record.")


if __name__ == "__main__":
    unittest.main()
