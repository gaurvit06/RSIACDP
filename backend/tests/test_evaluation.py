import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from evaluation.evaluate import load, score
from evaluation.ablate_graph import ablate
from evaluation.compare_runs import compare, validate_llm_provenance


def record(case_id, **overrides):
    row = {
        "case_id": case_id,
        "submitted_at": "2026-01-01T00:00:00Z",
        "split": "test",
        "campaign_id": None,
        "predicted_campaign_id": None,
        "gold_entities": [],
        "predicted_entities": [],
        "gold_supported_entities": [],
        "predicted_supported_entities": [],
        "gold_adverse_verdict": False,
        "predicted_adverse_verdict": False,
        "processing_ms": 10,
    }
    row.update(overrides)
    return row


class EvaluationTests(unittest.TestCase):
    def test_loader_rejects_string_booleans_and_nonfinite_latency(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            for field_value, message in (("false", "must be a boolean"), (float("nan"), "processing_ms must be non-negative")):
                row = record("bad")
                if message == "must be a boolean":
                    row["predicted_adverse_verdict"] = field_value
                else:
                    row["processing_ms"] = field_value
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                with self.subTest(value=field_value), self.assertRaisesRegex(ValueError, message):
                    load(path)

    def test_loader_rejects_naive_timestamps_and_invalid_entity_shapes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            row = record("bad", submitted_at="2026-01-01T00:00:00")
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "include a timezone"):
                load(path)
            row = record("bad", gold_entities=[{"type": "email", "value": None}])
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gold_entities must contain"):
                load(path)

    def test_reports_entity_campaign_evidence_verdict_and_latency_metrics(self):
        rows = [
            record("a", campaign_id="gold", predicted_campaign_id="predicted", gold_entities=[{"type": "email", "value": "x@example.invalid"}], predicted_entities=[{"type": "email", "value": "x@example.invalid"}], gold_supported_entities=[{"type": "email", "value": "x@example.invalid"}], predicted_supported_entities=[{"type": "email", "value": "x@example.invalid"}], processing_ms=5),
            record("b", campaign_id="gold", predicted_campaign_id="predicted", gold_adverse_verdict=False, predicted_adverse_verdict=True, processing_ms=15),
        ]
        metrics = score(rows)
        self.assertEqual(metrics["entity_micro"]["f1"], 1.0)
        self.assertEqual(metrics["campaign_pairwise"]["f1"], 1.0)
        self.assertEqual(metrics["evidence_support_precision"], 1.0)
        self.assertEqual(metrics["evidence_support_recall"], 1.0)
        self.assertEqual(metrics["verdict_false_positive_rate"], 0.5)
        self.assertEqual(metrics["processing_ms"]["mean"], 10.0)

    def test_bootstrap_intervals_are_deterministic_and_cover_required_metrics(self):
        entity = {"type": "email", "value": "hr@example.invalid"}
        rows = [
            record("a", campaign_id="gold-a", predicted_campaign_id="pred-a", gold_entities=[entity], predicted_entities=[entity], gold_supported_entities=[entity], predicted_supported_entities=[entity], processing_ms=5),
            record("b", campaign_id="gold-a", predicted_campaign_id="pred-a", gold_adverse_verdict=False, predicted_adverse_verdict=True, processing_ms=15),
            record("c", campaign_id="gold-b", predicted_campaign_id="pred-b", processing_ms=25),
        ]
        first = score(rows, bootstrap_resamples=250, bootstrap_seed=7)
        second = score(rows, bootstrap_resamples=250, bootstrap_seed=7)
        expected = {"entity_micro_f1", "campaign_pairwise_f1", "evidence_support_precision", "verdict_false_positive_rate", "processing_ms_mean", "processing_ms_p95"}
        self.assertEqual(set(first["confidence_intervals"]), expected)
        self.assertEqual(first["confidence_intervals"], second["confidence_intervals"])
        for interval in first["confidence_intervals"].values():
            self.assertEqual(interval["total_resamples"], 250)
            if interval["lower"] is not None:
                self.assertLessEqual(interval["lower"], interval["upper"])

    def test_bootstrap_rejects_invalid_configuration(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            score([record("one")], bootstrap_resamples=0)
        with self.assertRaisesRegex(ValueError, "seed must be an integer"):
            score([record("one")], bootstrap_seed=True)

    def test_rejects_campaign_leakage_between_time_splits(self):
        train = record("train", split="train", campaign_id="shared")
        test = record("test", campaign_id="shared")
        with self.assertRaisesRegex(ValueError, "campaign leakage") as caught:
            score([train, test])
        self.assertNotIn("shared", str(caught.exception))

    def test_reports_undefined_precision_when_no_evidence_is_predicted(self):
        metrics = score([record("only")])
        self.assertIsNone(metrics["evidence_support_precision"])
        interval = metrics["confidence_intervals"]["evidence_support_precision"]
        self.assertIsNone(interval["lower"])
        self.assertIsNone(interval["upper"])
        self.assertEqual(interval["valid_resamples"], 0)

    def test_evidence_support_scores_claims_independently_within_a_case(self):
        gold = [{"type": "email", "value": "good@example.invalid"}]
        predicted = [*gold, {"type": "phone", "value": "+919999999999"}]
        metrics = score([record("one-case", gold_entities=gold, predicted_entities=predicted, gold_supported_entities=gold, predicted_supported_entities=predicted)])
        self.assertEqual(metrics["evidence_support_precision"], 0.5)
        self.assertEqual(metrics["evidence_support_recall"], 1.0)
        self.assertEqual(metrics["evidence_support_claims"], {"tp": 1, "fp": 1, "fn": 0})

    def test_graph_ablation_removes_campaign_predictions_and_uses_measured_off_times(self):
        rows = [
            record("a", campaign_id="gold", predicted_campaign_id="predicted"),
            record("b", campaign_id="gold", predicted_campaign_id="predicted"),
        ]
        ablated, metrics = ablate(rows, {"a": 7.0, "b": 8.0})
        self.assertTrue(all(row["predicted_campaign_id"] is None for row in ablated))
        self.assertEqual([row["processing_ms"] for row in ablated], [7.0, 8.0])
        self.assertEqual(metrics["campaign_pairwise"]["recall"], 0.0)

    def test_comparison_requires_identical_test_ids_and_gold_labels(self):
        first = [record("a", campaign_id="gold", predicted_campaign_id="p"), record("b", campaign_id="gold", predicted_campaign_id="p")]
        same = [dict(row) for row in first]
        runs = {name: same for name in ("tfidf_logreg", "llm_web_search", "evidence_pipeline_no_graph", "full_evidence_pipeline")}
        with TemporaryDirectory() as directory:
            paths = {name: Path(directory) / f"{name}.jsonl" for name in runs}
            sidecar = paths["llm_web_search"].with_suffix(".jsonl.provenance.jsonl")
            sidecar.write_text("".join(json.dumps({
                "case_id": row["case_id"],
                "metadata": {"provider": "test", "model_version": "v1", "prompt_sha256": "a" * 64, "retrieval_policy": "fixture", "lawful_access": True},
                "sources": [{"source": "fixture", "reference": "SRC-1", "retrieved_at": "2026-01-01T00:00:00Z", "content_sha256": "b" * 64}],
                "supported_claim_sources": [],
            }) + "\n" for row in same), encoding="utf-8")
            with patch("evaluation.compare_runs.load", side_effect=lambda path: runs[path.stem]):
                result = compare(paths)
            self.assertEqual(result["test_case_count"], 2)
            self.assertEqual(result["systems"]["full_evidence_pipeline"]["bootstrap"]["resamples"], 1000)
            self.assertIn("campaign_pairwise_f1", result["systems"]["evidence_pipeline_no_graph"]["confidence_intervals"])
            altered = [dict(row) for row in first]
            altered[0] = {**altered[0], "gold_adverse_verdict": True}
            runs["llm_web_search"] = altered
            with patch("evaluation.compare_runs.load", side_effect=lambda path: runs[path.stem]):
                with self.assertRaisesRegex(ValueError, "changes gold labels") as caught:
                    compare(paths)
                self.assertNotIn("case-a", str(caught.exception))

    def test_graph_ablation_id_mismatch_reports_counts_not_case_identifiers(self):
        with self.assertRaisesRegex(ValueError, "missing=1, extra=1") as caught:
            ablate([record("private-case-id")], {"another-private-case-id": 1.0})
        self.assertNotIn("private-case-id", str(caught.exception))

    def test_comparison_rejects_missing_llm_provenance(self):
        rows = [record("a")]
        with TemporaryDirectory() as directory:
            paths = {name: Path(directory) / f"{name}.jsonl" for name in ("tfidf_logreg", "llm_web_search", "evidence_pipeline_no_graph", "full_evidence_pipeline")}
            runs = {path.stem: rows for path in paths.values()}
            with patch("evaluation.compare_runs.load", side_effect=lambda path: runs[path.stem]):
                with self.assertRaisesRegex(ValueError, "sidecar is missing"):
                    compare(paths)

    def test_llm_provenance_rejects_coerced_metadata_and_source_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "llm.jsonl"
            sidecar = path.with_suffix(path.suffix + ".provenance.jsonl")
            row = {
                "case_id": "case-a",
                "metadata": {"provider": 7, "model_version": "v1", "prompt_sha256": "a" * 64, "retrieval_policy": "fixture", "lawful_access": True},
                "sources": [{"source": "fixture", "reference": "SRC-1", "retrieved_at": "2026-01-01T00:00:00Z", "content_sha256": "b" * 64}],
                "supported_claim_sources": [],
            }
            sidecar.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata is incomplete"):
                validate_llm_provenance(path, {"case-a"})
            row["metadata"]["provider"] = "test"
            row["sources"][0]["reference"] = 17
            sidecar.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source provenance is incomplete"):
                validate_llm_provenance(path, {"case-a"})


if __name__ == "__main__":
    unittest.main()
