import unittest

from app.privacy import mask_identifier, redact_data, redact_source_ref, redact_text


class IdentifierDisplayPrivacyTests(unittest.TestCase):
    def test_contact_identifiers_are_masked_for_default_display(self):
        self.assertEqual(mask_identifier("phone", "+919876543210"), "••••3210")
        self.assertEqual(mask_identifier("email", "person@example.org"), "p***@example.org")
        self.assertEqual(mask_identifier("upi_id", "person@okaxis"), "••••")
        self.assertEqual(mask_identifier("recruiter_claim", "Asha Kumar"), "[name masked]")

    def test_bank_account_and_ifsc_values_are_masked_by_default(self):
        self.assertEqual(mask_identifier("bank_account", "9876543210"), "[identifier masked]")
        self.assertEqual(mask_identifier("ifsc_code", "HDFC0001234"), "[identifier masked]")

    def test_web_identifiers_hide_url_path_query_and_domain_by_default(self):
        self.assertEqual(mask_identifier("url", "https://jobs.example.org/candidate/9876543210?upi=person@okaxis"), "[web identifier masked]")
        self.assertEqual(mask_identifier("domain", "private-recruiter.example.org"), "[web identifier masked]")

    def test_free_text_and_location_claims_are_masked(self):
        self.assertEqual(mask_identifier("location_claim", "Flat 12, 9876543210 Road"), "[location masked]")
        self.assertEqual(mask_identifier("fee_request", "Pay 2,500 to person@okaxis at +91 98765 43210"), "[payment request text masked]")

    def test_preserved_claim_values_scrub_embedded_contacts(self):
        value = "Acme Ltd; recruiter: Asha Menon; call +91 98765 43210 or person@okaxis"
        displayed = mask_identifier("company_claim", value)
        self.assertNotIn("Asha Menon", displayed)
        self.assertNotIn("98765 43210", displayed)
        self.assertNotIn("person@okaxis", displayed)

    def test_safe_claim_types_are_preserved_and_unknown_types_fail_closed(self):
        self.assertEqual(mask_identifier("job_title_claim", "Data Analyst"), "Data Analyst")
        self.assertEqual(mask_identifier("payment_amount_claim", "INR 2,500"), "INR 2,500")
        self.assertEqual(mask_identifier("future_identifier_type", "arbitrary sensitive value"), "[identifier masked]")

    def test_source_reference_keeps_origin_but_hides_paths_queries_and_host_contacts(self):
        self.assertEqual(
            redact_source_ref("https://jobs.example.org/candidate/asha?phone=9876543210"),
            "https://jobs.example.org/[path redacted]?[query redacted]",
        )
        self.assertEqual(
            redact_source_ref("https://9876543210.example.org/record"),
            "https://••••••••.example.org/[path redacted]",
        )
        self.assertEqual(redact_source_ref("https://user:secret@example.org/private"), "[source reference restricted]")
        self.assertEqual(redact_source_ref("LOCAL-0123456789ABCDEF"), "LOCAL-0123456789ABCDEF")
        self.assertEqual(redact_source_ref("unrecognized reference"), "[source reference restricted]")

    def test_arbitrary_redacted_text_and_audit_data_hide_urls_and_private_fields(self):
        safe_text = redact_text("Open https://jobs.example.org/private?phone=9876543210 now")
        self.assertNotIn("/private", safe_text)
        self.assertNotIn("9876543210", safe_text)
        safe_audit = redact_data({
            "comment": "Call +91 98765 43210 at person@okaxis",
            "source_ref": "private",
            "reviewed_by": 17,
            "status": "relevant",
            "future_field": {"untrusted": "Asha Menon and her private details"},
        })
        self.assertNotIn("comment", safe_audit)
        self.assertNotIn("future_field", safe_audit)
        self.assertEqual(safe_audit["status"], "relevant")
        self.assertEqual(safe_audit["source_ref"], "[redacted]")
        self.assertEqual(safe_audit["reviewed_by"], "[redacted]")

    def test_arbitrary_text_masks_dotless_upi_handles(self):
        safe_text = redact_text("Transfer to candidate@okaxis or another.user@paytm")
        self.assertNotIn("candidate@okaxis", safe_text)
        self.assertNotIn("another.user@paytm", safe_text)

    def test_arbitrary_text_masks_common_indian_identity_and_bank_values(self):
        safe_text = redact_text("Aadhaar 1234 5678 9012, PAN ABCDE1234F, bank account: 123456789012")
        for sensitive_value in ("1234 5678 9012", "ABCDE1234F", "123456789012"):
            self.assertNotIn(sensitive_value, safe_text)


if __name__ == "__main__":
    unittest.main()
