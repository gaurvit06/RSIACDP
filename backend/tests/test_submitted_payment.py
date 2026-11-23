import unittest
from types import SimpleNamespace

from app.extract import extract
from app.findings import assess_case


class SubmittedPaymentTests(unittest.TestCase):
    def assess(self, material, source_review="unreviewed", reject=False):
        source = SimpleNamespace(id=7, source_type="submitted_material", authority="user_submitted",
                                 outcome="result", review_status=source_review, details={})
        entities = [SimpleNamespace(id=i + 1, case_id=1, entity_type=e.kind, raw_value=e.raw,
                                    normalized_value=e.normalized, source_start_char=e.start_char,
                                    source_end_char=e.end_char, source_location="submitted_text",
                                    review_status="rejected" if reject else "needs_review")
                    for i, e in enumerate(extract(material))]
        return assess_case(entities, [source], material)

    def test_payment_requests_cite_only_submitted_evidence(self):
        for text in ("To reserve your joining slot, a refundable equipment deposit of INR 2,750 is required by Friday.",
                     "Registration fee: INR 4999.", "Pay INR 4999 before receiving an offer letter.",
                     "Applicants must pay a training fee before onboarding."):
            with self.subTest(text=text):
                decisions, overall = self.assess(text)
                self.assertEqual(overall, "Evidence supports concern")
                self.assertEqual(decisions[-1]["supporting_evidence_ids"], [7])
                self.assertEqual(decisions[-1]["scope"], "material")

    def test_benign_and_ambiguous_material(self):
        for text in ("Salary: INR 42,000 per month. No recruitment fees are charged.",
                     "No registration fee is required.", "Never pay a training fee.",
                     "Does the employer require you to pay a registration fee?",
                     "Warning: scammers may ask you to pay a processing fee.",
                     "We will pay the training fee.", "Application fee: INR 0.",
                     "Your interview is waived.", "Send your documents before Friday."):
            with self.subTest(text=text):
                self.assertEqual(self.assess(text)[1], "Insufficient evidence")

    def test_review_withdraws_automatic_signal(self):
        for status in ("irrelevant", "contradicts", "needs_review"):
            self.assertEqual(self.assess("Registration fee: INR 4999.", status)[1], "Insufficient evidence")
        self.assertEqual(self.assess("Registration fee: INR 4999.", reject=True)[1], "Insufficient evidence")
