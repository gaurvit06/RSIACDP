"""Run an operator-supplied LLM/web-search adapter on the held-out split only.

The adapter is explicit configuration, not a production dependency. It must
provide `metadata` and a `run_case(case)` callable; see evaluation/README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable

from .evaluate import validate_time_splits


PREDICTION_FIELDS = {
    "predicted_entities", "predicted_campaign_id", "predicted_supported_entities",
    "predicted_adverse_verdict",
}
METADATA_FIELDS = {"provider", "model_version", "prompt_sha256", "retrieval_policy", "lawful_access"}
SOURCE_FIELDS = {"source", "reference", "retrieved_at", "content_sha256"}
SAFE_RETRIEVAL_ERRORS = {"timeout", "rate_limited", "unavailable", "http_error", "provider_error", "parse_error"}
INPUT_FIELDS = {
    "case_id", "submitted_at", "split", "campaign_id", "submitted_text",
    "gold_entities", "gold_supported_entities", "gold_adverse_verdict",
}


def read_input(path: Path) -> tuple[list[dict], str]:
    """Read the annotated experiment input, not scorer-format predictions."""
    raw = path.read_bytes()
    rows: list[dict] = []
    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON") from exc
        if not isinstance(row, dict) or set(row) != INPUT_FIELDS:
            raise ValueError(f"line {line_no}: fields must be exactly {sorted(INPUT_FIELDS)}")
        if not isinstance(row["case_id"], str) or not row["case_id"].strip():
            raise ValueError(f"line {line_no}: case_id must be a non-empty string")
        if row["split"] not in {"train", "dev", "test"}:
            raise ValueError(f"line {line_no}: split must be train, dev, or test")
        if not isinstance(row["submitted_text"], str):
            raise ValueError(f"line {line_no}: submitted_text must be text")
        if row["campaign_id"] is not None and (
            not isinstance(row["campaign_id"], str) or not row["campaign_id"].strip()
        ):
            raise ValueError(f"line {line_no}: campaign_id must be null or a non-empty string")
        if not isinstance(row["gold_adverse_verdict"], bool):
            raise ValueError(f"line {line_no}: gold_adverse_verdict must be a JSON boolean")
        for field in ("gold_entities", "gold_supported_entities"):
            entities = row[field]
            if not isinstance(entities, list) or any(
            not isinstance(entity, dict) or set(entity) != {"type", "value"}
            or not isinstance(entity["type"], str) or not entity["type"].strip()
            or not isinstance(entity["value"], str) or not entity["value"].strip()
            for entity in entities
            ):
                raise ValueError(f"line {line_no}: {field} must contain type/value string objects")
        gold_entity_keys = {(item["type"], item["value"]) for item in row["gold_entities"]}
        support_keys = [(item["type"], item["value"]) for item in row["gold_supported_entities"]]
        if len(set(support_keys)) != len(support_keys) or not set(support_keys).issubset(gold_entity_keys):
            raise ValueError(f"line {line_no}: gold_supported_entities must be unique and a subset of gold_entities")
        rows.append(row)
    if not rows:
        raise ValueError("dataset has no records")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("case_id values must be unique")
    campaign_splits: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["campaign_id"]:
            campaign_splits[row["campaign_id"]].add(row["split"])
    if any(len(splits) > 1 for splits in campaign_splits.values()):
        raise ValueError("campaign leakage across splits")
    validate_time_splits(rows)
    if not any(row["split"] == "test" for row in rows):
        raise ValueError("dataset has no test records")
    return rows, hashlib.sha256(raw).hexdigest()


def run(rows: list[dict], adapter: Callable[[dict], dict], metadata: dict, clock=time.perf_counter) -> tuple[list[dict], list[dict]]:
    if not isinstance(metadata, dict):
        raise ValueError("adapter metadata must be an object")
    missing_meta = METADATA_FIELDS - metadata.keys()
    if missing_meta:
        raise ValueError(f"adapter metadata missing: {sorted(missing_meta)}")
    if metadata.get("lawful_access") is not True:
        raise ValueError("adapter must attest lawful_access=true for this experiment")
    prompt_hash = metadata.get("prompt_sha256")
    if not isinstance(prompt_hash, str):
        raise ValueError("prompt_sha256 must be a 64-character SHA-256 hex digest")
    if len(prompt_hash) != 64 or any(char not in "0123456789abcdef" for char in prompt_hash.lower()):
        raise ValueError("prompt_sha256 must be a 64-character SHA-256 hex digest")
    for field in ("provider", "model_version", "retrieval_policy"):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            raise ValueError("provider, model_version, and retrieval_policy must be non-empty strings")
    safe_metadata = {field: metadata[field] for field in METADATA_FIELDS}

    output, provenance = [], []
    for row_number, source in enumerate(rows, start=1):
        # Keep train/dev source text out of prediction artifacts. They are not
        # needed by the comparator, and only held-out predictions are reported.
        if source["split"] != "test":
            continue
        # Never expose gold labels or split metadata to the model/search adapter.
        case = {key: source[key] for key in ("case_id", "submitted_at", "submitted_text") if key in source}
        started = clock()
        try:
            result = adapter(case)
        except Exception as exc:
            # Provider exceptions can echo prompts, retrieved text, or secrets.
            # Preserve only a row number and diagnostic class; case IDs can also
            # contain personal data and must not be copied into console errors.
            raise ValueError(f"adapter failed for evaluation row {row_number}: {type(exc).__name__}") from None
        elapsed_ms = (clock() - started) * 1000
        if not isinstance(result, dict):
            raise ValueError(f"adapter result for evaluation row {row_number} must be an object")
        missing = PREDICTION_FIELDS - result.keys()
        if missing:
            raise ValueError(f"adapter result for evaluation row {row_number} missing: {sorted(missing)}")
        if not isinstance(result["predicted_entities"], list) or any(
            not isinstance(entity, dict) or set(entity) != {"type", "value"} or
            not all(isinstance(entity[key], str) and entity[key].strip() for key in ("type", "value"))
            for entity in result["predicted_entities"]
        ):
            raise ValueError(f"adapter entities for evaluation row {row_number} must be [{'{'}type,value{'}'}] objects")
        supported_entities = result["predicted_supported_entities"]
        if not isinstance(supported_entities, list) or any(
            not isinstance(entity, dict) or set(entity) != {"type", "value", "source_references"}
            or not all(isinstance(entity[key], str) and entity[key].strip() for key in ("type", "value"))
            or not isinstance(entity["source_references"], list) or not entity["source_references"]
            or any(not isinstance(reference, str) or not reference.strip() for reference in entity["source_references"])
            for entity in supported_entities
        ):
            raise ValueError(f"adapter supported-claim predictions for evaluation row {row_number} must include type, value, and source_references")
        supported_keys = [(item["type"], item["value"]) for item in supported_entities]
        if len(set(supported_keys)) != len(supported_keys):
            raise ValueError(f"adapter supported-claim predictions for evaluation row {row_number} must be unique")
        predicted_entity_keys = {(item["type"], item["value"]) for item in result["predicted_entities"]}
        if not set(supported_keys).issubset(predicted_entity_keys):
            raise ValueError(f"adapter supported claims must also appear in predicted_entities at evaluation row {row_number}")
        if not isinstance(result["predicted_adverse_verdict"], bool):
            raise ValueError(f"adapter adverse-assessment prediction for evaluation row {row_number} must be a boolean")
        sources = result.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"adapter must return at least one traceable source for evaluation row {row_number}")
        safe_sources = []
        for item in sources:
            if not isinstance(item, dict) or set(item) != SOURCE_FIELDS or not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in SOURCE_FIELDS
            ):
                raise ValueError(f"each source for evaluation row {row_number} must contain only source, reference, retrieved_at, and content_sha256 strings")
            if any(len(item[key]) > 2048 for key in SOURCE_FIELDS):
                raise ValueError(f"source provenance field exceeds its length limit at evaluation row {row_number}")
            try:
                retrieved_at = datetime.fromisoformat(item["retrieved_at"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"source retrieval timestamp is invalid at evaluation row {row_number}") from exc
            if retrieved_at.tzinfo is None:
                raise ValueError(f"source retrieval timestamp lacks timezone at evaluation row {row_number}")
            digest = item["content_sha256"].lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError(f"source content_sha256 for evaluation row {row_number} must be a SHA-256 hex digest")
            safe_sources.append({**item, "content_sha256": digest})
        available_references = {item["reference"] for item in safe_sources}
        if any(not set(item["source_references"]).issubset(available_references) for item in supported_entities):
            raise ValueError(f"supported-claim source references are missing from provenance at evaluation row {row_number}")
        output.append({
            **{key: source[key] for key in ("case_id", "submitted_at", "split", "campaign_id", "gold_entities", "gold_supported_entities", "gold_adverse_verdict")},
            "predicted_entities": result["predicted_entities"],
            "predicted_campaign_id": result["predicted_campaign_id"],
            "predicted_supported_entities": [
                {"type": item["type"], "value": item["value"]} for item in supported_entities
            ],
            "predicted_adverse_verdict": result["predicted_adverse_verdict"],
            "processing_ms": round(max(0.0, elapsed_ms), 3),
        })
        retrieval_error = result.get("retrieval_error")
        if retrieval_error is not None and (
            not isinstance(retrieval_error, str) or retrieval_error not in SAFE_RETRIEVAL_ERRORS
        ):
            retrieval_error = "unspecified"
        provenance.append({"case_id": source["case_id"], "metadata": safe_metadata, "sources": safe_sources,
                           "supported_claim_sources": [
                               {"type": item["type"], "value": item["value"], "source_references": item["source_references"]}
                               for item in supported_entities
                           ],
                           "retrieval_error": retrieval_error})
    return output, provenance


def _atomic_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--adapter", required=True, help="Explicit import path MODULE:CALLABLE")
    args = parser.parse_args(argv)
    try:
        module_name, callable_name = args.adapter.split(":", 1)
        module = importlib.import_module(module_name)
        adapter = getattr(module, callable_name)
        rows, _dataset_sha256 = read_input(args.input)
        predictions, provenance = run(rows, adapter, getattr(module, "metadata", {}))
        _atomic_jsonl(args.output, predictions)
        _atomic_jsonl(args.output.with_suffix(args.output.suffix + ".provenance.jsonl"), provenance)
        return 0
    except (OSError, ValueError, ImportError, AttributeError) as exc:
        print(f"LLM/web-search evaluation error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
