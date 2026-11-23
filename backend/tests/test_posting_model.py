import unittest

from app.posting_model import ABSTAIN, HIGH, LOW, predict, predict_fields


class PostingModelTests(unittest.TestCase):
    def test_three_distinct_recognized_words_are_required(self):
        for text, count in (("software engineer", 2), ("engineer ENGINEER engineer", 1),
                            ("software engineer xqzzzzq", 2), ("software engineer needed", 3)):
            with self.subTest(text=text):
                result = predict(text)
                self.assertEqual(result["matched_words"], count)
                self.assertEqual(result["score"] is None, count < 3)
                self.assertEqual(result["label"] == ABSTAIN, count < 3)
                self.assertEqual(result["threshold"], 0.35)

    def test_trained_predictions_and_insufficient_text(self):
        examples = [
            ("Work from home earn money weekly with no experience required. Data entry clerks needed immediately. Cash paid weekly.", HIGH),
            ("software engineer needed", LOW),
            ("https://example.invalid/jobs/123", ABSTAIN),
            ("", ABSTAIN),
        ]
        for text, label in examples:
            with self.subTest(label=label):
                result = predict(text)
                self.assertEqual(result["label"], label)
                self.assertEqual(result, predict(text))
                if label == ABSTAIN:
                    self.assertIsNone(result["score"])
                else:
                    self.assertEqual(result["score"] >= result["threshold"], label == HIGH)

    def test_guided_fields_match_original_dashboard_probability(self):
        body = "Our engineering team is hiring a software engineer to design and test applications, collaborate with designers, and maintain distributed systems."
        prediction = predict("Job title: Software engineer\nLocation: Bengaluru\nJob description:\n" + body)
        self.assertAlmostEqual(prediction["score"], 0.5542692274846878, places=10)
        guided = f"Job title: Engineer\nCompany: Example\nRequirements: Python\nSalary disclosed: Yes\nCompany logo present: Yes\nJob description:\n{body}"
        self.assertEqual(predict(guided), predict_fields("Engineer", "Example", body, "Python", True, True))
