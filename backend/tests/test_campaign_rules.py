import unittest

from app.campaign_rules import link_state, redact_link_reason, rule_version, score_matches


class CampaignRuleTests(unittest.TestCase):
    def test_exact_strong_identifier_crosses_default_threshold(self):
        strength, reasons = score_matches({("phone", "9876543210")})
        self.assertEqual(strength, 40)
        self.assertEqual(link_state(strength, 40), "proposed")
        self.assertTrue(any("Exact phone match" in reason and "weight 40" in reason for reason in reasons))

    def test_url_and_derived_domain_are_one_infrastructure_signal(self):
        strength, _ = score_matches({("url", "https://jobs.example.org/Role"), ("domain", "jobs.example.org")})
        self.assertEqual(strength, 25)
        self.assertEqual(link_state(strength, 40), "low_signal")

    def test_independent_identifier_adds_to_link_strength(self):
        strength, _ = score_matches({("phone", "9876543210"), ("email", "hr@example.org")})
        self.assertEqual(strength, 80)

    def test_exact_bank_account_reuse_is_a_versioned_investigative_signal(self):
        strength, reasons = score_matches({("bank_account", "9876543210")})
        self.assertEqual(strength, 40)
        self.assertEqual(link_state(strength, 40), "proposed")
        self.assertTrue(any("Exact bank_account match" in reason for reason in reasons))
        self.assertIn("campaign-signals-v3", rule_version(40))

    def test_threshold_is_part_of_historical_rule_version(self):
        self.assertNotEqual(rule_version(30), rule_version(40))

    def test_redacted_link_explanations_preserve_signal_without_identifier_values(self):
        for kind, value, weight in (
            ("upi_id", "person@okaxis", "40"),
            ("bank_account", "9876543210", "40"),
            ("phone", "+919876543210", "40"),
            ("email", "person@example.test", "40"),
            ("url", "https://private.example.test/jobs/123", "25"),
        ):
            reason = f"Exact {kind} match: {value} (weight {weight})"
            redacted = redact_link_reason(reason)
            self.assertIn(f"Exact {kind} match", redacted)
            self.assertIn(f"weight {weight}", redacted)
            self.assertNotIn(value, redacted)

    def test_redacted_shared_host_explanation_hides_the_host(self):
        reason = "Shared web host private-recruiter.example via domain, url (weight 25)"
        redacted = redact_link_reason(reason)
        self.assertIn("Shared web host [host masked]", redacted)
        self.assertNotIn("private-recruiter.example", redacted)


if __name__ == "__main__":
    unittest.main()
