import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from evaluation.llm_web_search import _atomic_jsonl, read_input, run
from evaluation.compare_runs import compare


METADATA = {
    "provider": "synthetic-test-adapter", "model_version": "fixture-v1",
    "prompt_sha256": "a" * 64, "retrieval_policy": "synthetic source fixture",
    "lawful_access": True,
}


def case_row(split, case_id):
    return {
        "case_id": case_id, "submitted_at": "2026-01-01T00:00:00Z", "split": split,
        "campaign_id": None, "submitted_text": "Synthetic recruitment message",
        "gold_entities": [], "gold_supported_entities": [], "gold_adverse_verdict": False,
    }


class LLMWebSearchEvaluationTests(unittest.TestCase):
    def test_documented_experiment_input_does_not_need_prediction_fields(self):
        rows = [
            {**case_row("train", "train-case"), "submitted_at": "2026-01-01T00:00:00Z"},
            {**case_row("test", "test-case"), "submitted_at": "2026-02-01T00:00:00Z"},
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "authorized-input.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            parsed, digest = read_input(path)
        self.assertEqual([row["case_id"] for row in parsed], ["train-case", "test-case"])
        self.assertEqual(len(digest), 64)
        self.assertNotIn("predicted_entities", parsed[0])

    def test_experiment_input_rejects_campaign_split_leakage(self):
        rows = [
            {**case_row("train", "train-case"), "campaign_id": "campaign-a"},
            {**case_row("test", "test-case"), "campaign_id": "campaign-a"},
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "authorized-input.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "campaign leakage"):
                read_input(path)

    def test_experiment_input_rejects_fields_outside_documented_schema(self):
        row = {**case_row("test", "test-case"), "predicted_adverse_verdict": False}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "authorized-input.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fields must be exactly"):
                read_input(path)

    def test_runs_only_test_cases_and_records_provenance_and_measured_latency(self):
        seen = []
        times = iter((4.0, 4.125))
        def adapter(case):
            seen.append(case)
            return {
                "predicted_entities": [{"type": "phone", "value": "9999999999"}],
                "predicted_campaign_id": None,
                "predicted_supported_entities": [],
                "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SYN-1", "retrieved_at": "2026-01-01T00:00:01Z", "content_sha256": "b" * 64}],
            }
        predictions, provenance = run([case_row("train", "train-1"), case_row("test", "test-1")], adapter, METADATA, clock=lambda: next(times))
        self.assertEqual(len(seen), 1)
        self.assertNotIn("gold_entities", seen[0])
        self.assertEqual([row["case_id"] for row in predictions], ["test-1"])
        self.assertEqual(predictions[0]["processing_ms"], 125.0)
        self.assertNotIn("submitted_text", predictions[0])
        self.assertEqual(provenance[0]["sources"][0]["reference"], "SYN-1")

    def test_rejects_missing_source_provenance(self):
        def adapter(_case):
            return {"predicted_entities": [], "predicted_campaign_id": None,
                    "predicted_supported_entities": [], "predicted_adverse_verdict": False}
        with self.assertRaisesRegex(ValueError, "traceable source"):
            run([case_row("test", "test-1")], adapter, METADATA)

    def test_supported_claims_keep_a_source_reference_mapping(self):
        claim = {"type": "email", "value": "hr@example.invalid", "source_references": ["SRC-1"]}
        def adapter(_case):
            return {
                "predicted_entities": [{"type": "email", "value": "hr@example.invalid"}],
                "predicted_campaign_id": None,
                "predicted_supported_entities": [claim],
                "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SRC-1", "retrieved_at": "2026-01-01T00:00:01Z", "content_sha256": "b" * 64}],
            }
        predictions, provenance = run([case_row("test", "test-1")], adapter, METADATA)
        self.assertEqual(predictions[0]["predicted_supported_entities"], [{"type": "email", "value": "hr@example.invalid"}])
        self.assertEqual(provenance[0]["supported_claim_sources"], [claim])

    def test_supported_claim_rejects_unknown_source_reference(self):
        def adapter(_case):
            return {
                "predicted_entities": [{"type": "email", "value": "hr@example.invalid"}],
                "predicted_campaign_id": None,
                "predicted_supported_entities": [{"type": "email", "value": "hr@example.invalid", "source_references": ["UNKNOWN"]}],
                "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SRC-1", "retrieved_at": "2026-01-01T00:00:01Z", "content_sha256": "b" * 64}],
            }
        with self.assertRaisesRegex(ValueError, "source references are missing"):
            run([case_row("test", "test-1")], adapter, METADATA)

    def test_rejects_source_without_content_snapshot_hash(self):
        def adapter(_case):
            return {"predicted_entities": [], "predicted_campaign_id": None,
                    "predicted_supported_entities": [], "predicted_adverse_verdict": False,
                    "sources": [{"source": "synthetic", "reference": "SYN-1", "retrieved_at": "2026-01-01T00:00:01Z"}]}
        with self.assertRaisesRegex(ValueError, "content_sha256"):
            run([case_row("test", "test-1")], adapter, METADATA)

    def test_rejects_adapter_without_lawful_access_attestation(self):
        with self.assertRaisesRegex(ValueError, "lawful_access=true"):
            run([], lambda _case: {}, {**METADATA, "lawful_access": False})

    def test_provider_failure_does_not_echo_exception_content(self):
        def broken(_case):
            raise RuntimeError("private prompt text and secret token")
        private_case_id = "private-person@example.invalid"
        with self.assertRaisesRegex(ValueError, "RuntimeError") as caught:
            run([case_row("test", private_case_id)], broken, METADATA)
        self.assertNotIn("secret token", str(caught.exception))
        self.assertNotIn("private prompt", str(caught.exception))
        self.assertNotIn(private_case_id, str(caught.exception))

    def test_provenance_sidecar_drops_extra_metadata_and_normalizes_error_text(self):
        def adapter(_case):
            return {
                "predicted_entities": [], "predicted_campaign_id": None,
                "predicted_supported_entities": [], "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SYN-1", "retrieved_at": "2026-01-01T00:00:01Z", "content_sha256": "b" * 64}],
                "retrieval_error": "request failed with Authorization: secret-token",
            }
        _, provenance = run([case_row("test", "case-private")], adapter, {**METADATA, "api_key": "secret-token"})
        self.assertNotIn("api_key", provenance[0]["metadata"])
        self.assertEqual(provenance[0]["retrieval_error"], "unspecified")
        self.assertNotIn("secret-token", json.dumps(provenance))

    def test_provenance_source_rejects_unallowlisted_free_text(self):
        def adapter(_case):
            return {
                "predicted_entities": [], "predicted_campaign_id": None,
                "predicted_supported_entities": [], "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SYN-1", "retrieved_at": "2026-01-01T00:00:01Z", "content_sha256": "b" * 64, "excerpt": "private source text"}],
            }
        with self.assertRaisesRegex(ValueError, "only source, reference") as caught:
            run([case_row("test", "test-1")], adapter, METADATA)
        self.assertNotIn("private source text", str(caught.exception))

    def test_runner_output_and_sidecar_pass_four_way_comparison(self):
        def adapter(_case):
            return {
                "predicted_entities": [], "predicted_campaign_id": None,
                "predicted_supported_entities": [], "predicted_adverse_verdict": False,
                "sources": [{"source": "synthetic", "reference": "SRC-1", "retrieved_at": "2026-01-01T00:00:00Z", "content_sha256": "b" * 64}],
            }
        rows = [{**case_row("test", "test-1"), "predicted_entities": [], "predicted_campaign_id": None,
                 "predicted_supported_entities": [], "predicted_adverse_verdict": False, "processing_ms": 1.0}]
        predictions, provenance = run(rows, adapter, METADATA)
        with TemporaryDirectory() as directory:
            llm_path = Path(directory) / "llm.jsonl"
            _atomic_jsonl(llm_path, predictions)
            _atomic_jsonl(llm_path.with_suffix(llm_path.suffix + ".provenance.jsonl"), provenance)
            paths = {
                "tfidf_logreg": Path(directory) / "tfidf.jsonl",
                "llm_web_search": llm_path,
                "evidence_pipeline_no_graph": Path(directory) / "no-graph.jsonl",
                "full_evidence_pipeline": Path(directory) / "full.jsonl",
            }
            for name, path in paths.items():
                if name != "llm_web_search":
                    _atomic_jsonl(path, rows)
            result = compare(paths)
        self.assertEqual(result["test_case_count"], 1)


if __name__ == "__main__":
    unittest.main()
