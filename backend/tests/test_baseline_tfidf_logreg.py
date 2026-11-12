import unittest
import contextlib
import io
import json
from pathlib import Path

from evaluation.baseline_tfidf_logreg import main, read_training_data, run


class TfidfLogisticBaselineTests(unittest.TestCase):
    def rows(self):
        return [
            {"case_id": "train-positive", "submitted_at": "2026-01-01T00:00:00Z", "split": "train", "campaign_id": "train-campaign", "submitted_text": "pay registration fee immediately fake recruitment", "gold_entities": [], "gold_supported_entities": [], "gold_adverse_verdict": True},
            {"case_id": "train-negative", "submitted_at": "2026-01-02T00:00:00Z", "split": "train", "campaign_id": None, "submitted_text": "official careers page apply through company portal", "gold_entities": [], "gold_supported_entities": [], "gold_adverse_verdict": False},
            {"case_id": "test-case", "submitted_at": "2026-02-01T00:00:00Z", "split": "test", "campaign_id": None, "submitted_text": "official company careers portal", "gold_entities": [{"type": "domain", "value": "jobs.example.invalid"}], "gold_supported_entities": [], "gold_adverse_verdict": False},
        ]

    def test_runner_trains_only_on_train_and_emits_scorer_schema(self):
        predictions, metrics = run(self.rows(), "dataset-hash")
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]["case_id"], "test-case")
        self.assertEqual(predictions[0]["predicted_entities"], [])
        self.assertIsNone(predictions[0]["predicted_campaign_id"])
        self.assertEqual(predictions[0]["predicted_supported_entities"], [])
        self.assertEqual(metrics["baseline"]["dataset_sha256"], "dataset-hash")
        self.assertEqual(metrics["baseline"]["training_cases"], 2)
        self.assertEqual(metrics["baseline"]["test_cases"], 1)
        self.assertEqual(metrics["test_cases"], 1)

    def test_loader_rejects_campaign_leakage(self):
        rows = self.rows()
        rows[0]["campaign_id"] = "private-campaign-label"
        rows[-1]["campaign_id"] = "private-campaign-label"
        directory = Path(__file__).resolve().parents[1] / ".test-runtime"
        directory.mkdir(exist_ok=True)
        path = directory / "baseline-leakage-test.jsonl"
        try:
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "campaign leakage") as caught:
                read_training_data(path)
            self.assertNotIn("private-campaign-label", str(caught.exception))
        finally:
            path.unlink(missing_ok=True)

    def test_cli_writes_test_predictions_and_metric_summary(self):
        directory = Path(__file__).resolve().parents[1] / ".test-runtime"
        directory.mkdir(exist_ok=True)
        input_path = directory / "baseline-cli-input.jsonl"
        output_path = directory / "baseline-cli-output.jsonl"
        input_path.write_text("".join(json.dumps(row) + "\n" for row in self.rows()), encoding="utf-8")
        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([str(input_path), str(output_path)])
            self.assertEqual(result, 0)
            predictions = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["case_id"] for row in predictions], ["test-case"])
            self.assertIn("dataset_sha256", output.getvalue())
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
