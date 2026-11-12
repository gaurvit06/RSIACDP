"""Validation responses must not echo submitted text or secrets."""
import json
import unittest

from fastapi.exceptions import RequestValidationError

from app.main import app, safe_validation_details


class ValidationPrivacyTests(unittest.TestCase):
    def test_api_validation_handler_keeps_field_guidance_but_drops_input_and_context(self):
        sensitive = "private recruiter phone +91 98765 43210 and token=secret-value"
        error = RequestValidationError([{
            "type": "string_too_short",
            "loc": ("body", "submitted_text"),
            "msg": f"Value {sensitive} is too short",
            "input": sensitive,
            "ctx": {"error": sensitive},
        }])
        body = {"detail": safe_validation_details(error.errors())}
        rendered = json.dumps(body)
        self.assertIn(RequestValidationError, app.exception_handlers)
        self.assertEqual(body["detail"][0]["loc"], ["body", "submitted_text"])
        self.assertEqual(body["detail"][0]["msg"], "Text is shorter than the allowed minimum.")
        self.assertNotIn("98765", rendered)
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("private recruiter", rendered)


if __name__ == "__main__":
    unittest.main()
