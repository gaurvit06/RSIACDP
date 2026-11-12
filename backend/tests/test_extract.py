import unittest
from app.extract import extract, normalize


class ExtractionTests(unittest.TestCase):
    def test_finds_email_and_normalizes_domain(self):
        text = "Contact Hiring@Example.COM for the role"
        found = extract(text)
        email = next(item for item in found if item.kind == "email")
        self.assertEqual(email.normalized, "Hiring@example.com")
        self.assertIn("Hiring@Example.COM", email.excerpt)
        self.assertEqual(text[email.start_char:email.end_char], email.raw)

    def test_finds_email_before_sentence_ending_punctuation(self):
        text = "For the vacancy, contact recruiter@example.invalid."
        email = next(item for item in extract(text) if item.kind == "email")
        self.assertEqual(email.raw, "recruiter@example.invalid")
        self.assertEqual(text[email.start_char:email.end_char], email.raw)

    def test_normalizes_indian_phone_without_replacing_raw_value(self):
        found = extract("Call +91 98765 43210")
        phone = next(item for item in found if item.kind == "phone")
        self.assertEqual(phone.raw, "+91 98765 43210")
        self.assertEqual(phone.normalized, "9876543210")

    def test_extracts_labeled_bank_account_without_double_counting_as_phone(self):
        text = "Beneficiary account number: 98765 43210"
        found = extract(text)
        account = next(item for item in found if item.kind == "bank_account")
        self.assertEqual(account.raw, "98765 43210")
        self.assertEqual(account.normalized, "9876543210")
        self.assertEqual(text[account.start_char:account.end_char], account.raw)
        self.assertFalse(any(item.kind == "phone" for item in found))
        self.assertIn("unverified", account.uncertainty)

    def test_extracts_and_normalizes_ifsc_code(self):
        text = "Transfer reference IFSC: hdfc0001234 before proceeding"
        item = next(item for item in extract(text) if item.kind == "ifsc_code")
        self.assertEqual(item.raw, "hdfc0001234")
        self.assertEqual(item.normalized, "HDFC0001234")
        self.assertEqual(text[item.start_char:item.end_char], item.raw)

    def test_does_not_extract_unlabeled_long_number_as_bank_account(self):
        found = extract("Reference number 123456789012345678 is shown.")
        self.assertFalse(any(item.kind == "bank_account" for item in found))

    def test_excludes_email_shape_from_upi_candidates(self):
        found = extract("Send details to jobs@example.com and payments to staff@okaxis")
        self.assertIn("jobs@example.com", [item.raw for item in found if item.kind == "email"])
        self.assertIn("staff@okaxis", [item.raw for item in found if item.kind == "upi_id"])
        self.assertNotIn("jobs@example.com", [item.raw for item in found if item.kind == "upi_id"])

    def test_upi_id_at_sentence_end_excludes_terminal_period_from_value_and_span(self):
        text = "Pay the requested amount to candidate.test@upi."
        found = extract(text)
        item = next(item for item in found if item.kind == "upi_id")
        self.assertEqual(item.raw, "candidate.test@upi")
        self.assertEqual(text[item.start_char:item.end_char], "candidate.test@upi")

    def test_dotted_email_domain_is_not_truncated_into_a_upi_identifier(self):
        found = extract("Contact staff@example.test. for details.")
        self.assertIn("staff@example.test", [item.raw for item in found if item.kind == "email"])
        self.assertNotIn("staff@example.test", [item.raw for item in found if item.kind == "upi_id"])

    def test_derives_domain_from_submitted_url(self):
        found = extract("Apply here: https://Careers.Example.org/opening?id=4")
        self.assertIn("https://careers.example.org/opening?id=4", [item.normalized for item in found if item.kind == "url"])
        self.assertIn("careers.example.org", [item.normalized for item in found if item.kind == "domain"])

    def test_url_normalization_preserves_case_sensitive_path_and_query(self):
        self.assertEqual(normalize("url", "HTTPS://Careers.Example.org:443/CasePath?Ref=ABC"), "https://careers.example.org/CasePath?Ref=ABC")
        self.assertNotEqual(normalize("url", "https://example.org/Case"), normalize("url", "https://example.org/case"))
        self.assertEqual(normalize("url", "https://bücher.example/"), "https://xn--bcher-kva.example/")

    def test_email_normalization_idna_encodes_domain_without_changing_local_part(self):
        self.assertEqual(normalize("email", "Hiring@bücher.example"), "Hiring@xn--bcher-kva.example")
        found = extract("Hiring@bücher.example")
        self.assertIn("xn--bcher-kva.example", [item.normalized for item in found if item.kind == "domain"])

    def test_fee_signal_is_only_extracted_as_a_claim(self):
        found = extract("The recruiter says a processing fee is needed before onboarding.")
        fee = next(item for item in found if item.kind == "fee_request")
        self.assertIn("processing fee", fee.raw.lower())
        self.assertEqual(normalize("fee_request", fee.raw), fee.raw.casefold())
        text = "The recruiter says a processing fee is needed before onboarding."
        self.assertEqual(text[fee.start_char:fee.end_char], fee.raw)
        self.assertIn("unverified", fee.uncertainty)

    def test_fee_mention_without_payment_request_is_not_extracted(self):
        examples = (
            "A registration fee was mentioned.",
            "We are studying processing fees in recruitment messages.",
            "The vacancy is open. A registration fee was mentioned elsewhere.",
        )
        for text in examples:
            with self.subTest(text=text):
                self.assertFalse(any(item.kind == "fee_request" for item in extract(text)))

    def test_explicit_payment_request_and_requirement_are_extracted(self):
        examples = (
            "Please send a registration fee of INR 500 before onboarding.",
            "Applicants are asked to pay a training fee before onboarding.",
            "The recruiter requested payment of a placement fee before the interview.",
            "A security deposit is mandatory before the interview.",
            "The processing fee of INR 500.00 is required.",
        )
        for text in examples:
            with self.subTest(text=text):
                fee = next(item for item in extract(text) if item.kind == "fee_request")
                self.assertEqual(text[fee.start_char:fee.end_char], fee.raw)

    def test_no_fee_or_waived_fee_is_not_extracted_as_a_request(self):
        examples = (
            "No registration fee is required.",
            "The processing fee is not payable.",
            "The security deposit was waived.",
        )
        for text in examples:
            with self.subTest(text=text):
                self.assertFalse(any(item.kind == "fee_request" for item in extract(text)))

    def test_amount_is_a_payment_claim_only_near_explicit_payment_wording(self):
        text = "The recruiter asks you to pay INR 2,500 before onboarding."
        item = next(item for item in extract(text) if item.kind == "payment_amount_claim")
        self.assertEqual(item.raw, "INR 2,500")
        self.assertEqual(text[item.start_char:item.end_char], item.raw)
        self.assertIn("unverified", item.uncertainty)

    def test_salary_is_not_mislabeled_as_a_payment_request(self):
        text = "Monthly salary: INR 45,000. No candidate fee is requested."
        found = extract(text)
        salary = next(item for item in found if item.kind == "compensation_amount_claim")
        self.assertEqual(salary.raw, "INR 45,000")
        self.assertFalse(any(item.kind == "payment_amount_claim" for item in found))

    def test_lpa_is_recognized_as_compensation_context(self):
        text = "The advertised package is ₹12 LPA."
        item = next(item for item in extract(text) if item.kind == "compensation_amount_claim")
        self.assertEqual(item.raw, "₹12")

    def test_context_free_amount_is_not_assigned_a_payment_or_salary_meaning(self):
        found = extract("Reference the amount INR 12,500 in the attached table.")
        self.assertFalse(any(item.kind in {"payment_amount_claim", "compensation_amount_claim"} for item in found))

    def test_ambiguous_nearby_salary_and_fee_context_does_not_create_payment_claim(self):
        found = extract("Salary INR 45,000 and a separate fee may apply later.")
        self.assertFalse(any(item.kind == "payment_amount_claim" for item in found))

    def test_explicitly_labelled_claims_keep_exact_spans_and_uncertainty(self):
        text = "Company: Example Hiring Ltd\nRole: Data Analyst\nRecruiter: Ravi Kumar\nLocation: Pune\nDate: 21/10/2026\nPlease pay INR 2,500."
        found = extract(text)
        for kind, expected in (("company_claim", "Example Hiring Ltd"), ("job_title_claim", "Data Analyst"), ("recruiter_claim", "Ravi Kumar"), ("location_claim", "Pune"), ("date_claim", "21/10/2026"), ("payment_amount_claim", "INR 2,500")):
            candidate = next(item for item in found if item.kind == kind)
            self.assertEqual(candidate.raw, expected)
            self.assertEqual(text[candidate.start_char:candidate.end_char], expected)
            self.assertTrue(candidate.uncertainty)
            self.assertGreater(candidate.confidence, 0)
            self.assertLess(candidate.confidence, 1)

    def test_common_recruitment_label_variants_remain_explicit_claims(self):
        text = (
            "Company Name: Example Hiring Ltd\n"
            "Designation: Data Analyst\n"
            "Vacancy: Recruitment Associate\n"
            "HR Name: Ravi Kumar\n"
            "Office Location: Pune"
        )
        found = extract(text)
        expected = {
            ("company_claim", "Example Hiring Ltd"),
            ("job_title_claim", "Data Analyst"),
            ("job_title_claim", "Recruitment Associate"),
            ("recruiter_claim", "Ravi Kumar"),
            ("location_claim", "Pune"),
        }
        actual = {(item.kind, item.raw) for item in found}
        self.assertTrue(expected.issubset(actual))
        for item in found:
            if item.kind in {"company_claim", "job_title_claim", "recruiter_claim", "location_claim"}:
                self.assertEqual(text[item.start_char:item.end_char], item.raw)
                self.assertIn("unverified", item.uncertainty)

    def test_extracts_narrow_narrative_hiring_phrase_as_low_confidence_candidates(self):
        text = "We are hiring Data Analysts at Example Hiring Ltd. Apply by email."
        found = extract(text)
        for kind, expected in (("job_title_claim", "Data Analysts"), ("company_claim", "Example Hiring Ltd")):
            item = next(item for item in found if item.kind == kind)
            self.assertEqual(item.raw, expected)
            self.assertEqual(text[item.start_char:item.end_char], expected)
            self.assertEqual(item.confidence, 0.55)
            self.assertIn("unverified", item.uncertainty)

    def test_extracts_hiring_for_phrase_without_treating_unrelated_prose_as_claims(self):
        text = "Opening for a Senior Data Analyst at Example Labs, Bengaluru."
        found = extract(text)
        role = next(item for item in found if item.kind == "job_title_claim")
        company = next(item for item in found if item.kind == "company_claim")
        self.assertEqual(role.raw, "Senior Data Analyst")
        self.assertEqual(company.raw, "Example Labs")
        claim_types = {"company_claim", "job_title_claim", "recruiter_claim", "location_claim"}
        unrelated = extract("Ravi Kumar is hiring Data Analysts in Pune for Example Hiring Ltd.")
        self.assertFalse(any(item.kind in claim_types for item in unrelated))

    def test_extracts_location_from_constrained_mixed_message_context(self):
        text = "We have a hybrid analyst role; the recruiter is based in Pune and interviews next week."
        location = next(item for item in extract(text) if item.kind == "location_claim")
        self.assertEqual(location.raw, "Pune")
        self.assertEqual(text[location.start_char:location.end_char], location.raw)
        self.assertEqual(location.confidence, 0.55)
        self.assertIn("unverified", location.uncertainty)

    def test_extracts_multiword_workplace_but_not_home_or_unrelated_places(self):
        workplace = "Office in New Delhi, India."
        location = next(item for item in extract(workplace) if item.kind == "location_claim")
        self.assertEqual(location.raw, "New Delhi")
        self.assertEqual(workplace[location.start_char:location.end_char], location.raw)
        self.assertFalse(any(item.kind == "location_claim" for item in extract("Work from home; I live in Pune.")))

    def test_does_not_mistake_job_functions_for_workplace_locations(self):
        text = "We have an open role in customer support and a position in software engineering."
        self.assertFalse(any(item.kind == "location_claim" for item in extract(text)))

    def test_does_not_infer_company_role_or_recruiter_from_unlabelled_prose(self):
        found = extract("Ravi Kumar is hiring Data Analysts in Pune for Example Hiring Ltd.")
        claim_types = {"company_claim", "job_title_claim", "recruiter_claim", "location_claim"}
        self.assertFalse(any(item.kind in claim_types for item in found))


if __name__ == "__main__":
    unittest.main()
