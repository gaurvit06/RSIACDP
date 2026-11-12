"""Compare four scorer-format runs on exactly the same labeled test cases."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

from .evaluate import load, score

GOLD_KEYS = ("submitted_at", "campaign_id", "gold_entities", "gold_supported_entities", "gold_adverse_verdict")
PROVENANCE_META = ("provider", "model_version", "prompt_sha256", "retrieval_policy", "lawful_access")


def validate_llm_provenance(path: Path, test_case_ids: set[str]) -> None:
    sidecar = path.with_suffix(path.suffix + ".provenance.jsonl")
    try:
        lines = sidecar.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError("LLM/web-search provenance sidecar is missing or unreadable") from exc
    records = []
    for line_number, line in enumerate(lines, 1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM/web-search provenance line {line_number} is invalid JSON") from exc
    if any(not isinstance(item, dict) or not isinstance(item.get("case_id"), str) or not item["case_id"].strip() for item in records):
        raise ValueError("LLM/web-search provenance case IDs must be non-empty strings")
    by_case = {item["case_id"]: item for item in records}
    if len(by_case) != len(records) or set(by_case) != test_case_ids:
        raise ValueError("LLM/web-search provenance case IDs must exactly match the test split")
    for row_number, item in enumerate(records, start=1):
        metadata = item.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("lawful_access") is not True or any(
            not isinstance(metadata.get(key), str) or not metadata[key].strip()
            for key in PROVENANCE_META[:-1]
        ):
            raise ValueError(f"LLM/web-search provenance metadata is incomplete at row {row_number}")
        digest = metadata["prompt_sha256"].lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"LLM/web-search prompt hash is invalid at row {row_number}")
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"LLM/web-search sources are missing at row {row_number}")
        source_references = set()
        for source in sources:
            if not isinstance(source, dict) or any(
                not isinstance(source.get(key), str) or not source[key].strip()
                for key in ("source", "reference", "retrieved_at", "content_sha256")
            ):
                raise ValueError(f"LLM/web-search source provenance is incomplete at row {row_number}")
            try:
                retrieved = datetime.fromisoformat(str(source["retrieved_at"]).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"LLM/web-search retrieval timestamp is invalid at row {row_number}") from None
            if retrieved.tzinfo is None:
                raise ValueError(f"LLM/web-search retrieval timestamp lacks timezone at row {row_number}")
            content_hash = source["content_sha256"].lower()
            if len(content_hash) != 64 or any(char not in "0123456789abcdef" for char in content_hash):
                raise ValueError(f"LLM/web-search source hash is invalid at row {row_number}")
            source_references.add(source["reference"])
        claim_sources = item.get("supported_claim_sources")
        if not isinstance(claim_sources, list):
            raise ValueError(f"LLM/web-search supported-claim provenance is missing at row {row_number}")
        for claim in claim_sources:
            if (
                not isinstance(claim, dict) or set(claim) != {"type", "value", "source_references"}
                or not isinstance(claim["type"], str) or not claim["type"].strip()
                or not isinstance(claim["value"], str) or not claim["value"].strip()
                or not isinstance(claim["source_references"], list) or not claim["source_references"]
                or any(not isinstance(reference, str) or not reference.strip() for reference in claim["source_references"])
                or not set(claim["source_references"]).issubset(source_references)
            ):
                raise ValueError(f"LLM/web-search supported-claim provenance is invalid at row {row_number}")


def compare(paths: dict[str, Path]) -> dict:
    runs = {name: load(path) for name, path in paths.items()}
    test_sets = {name: {str(row["case_id"]): row for row in rows if row["split"] == "test"} for name, rows in runs.items()}
    reference_name = next(iter(test_sets))
    reference = test_sets[reference_name]
    for name, records in test_sets.items():
        if set(records) != set(reference):
            raise ValueError(f"{name} run has a different test case ID set from {reference_name}")
        for row_number, (case_id, row) in enumerate(records.items(), start=1):
            if any(row[key] != reference[case_id][key] for key in GOLD_KEYS):
                raise ValueError(f"{name} run changes gold labels/provenance fields at test row {row_number}")
    if "llm_web_search" in paths:
        validate_llm_provenance(paths["llm_web_search"], set(reference))
    return {
        "test_case_count": len(reference),
        "systems": {name: score(rows) for name, rows in runs.items()},
        "limitations": "Comparison only applies to the supplied authorized test cases and recorded run outputs; it is not evidence of current real-world performance.",
    }


def main(args: list[str]) -> int:
    if len(args) != 4:
        print(f"usage: {Path(sys.argv[0]).name} TFIDF.jsonl LLM_WEB_SEARCH.jsonl NO_GRAPH.jsonl FULL_PIPELINE.jsonl", file=sys.stderr)
        return 2
    labels = ("tfidf_logreg", "llm_web_search", "evidence_pipeline_no_graph", "full_evidence_pipeline")
    try:
        print(json.dumps(compare({label: Path(path) for label, path in zip(labels, args)}), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"comparison input error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
