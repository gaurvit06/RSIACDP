"""Small dependency-free scorer for the documented time-split JSONL format."""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def f1_counts(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else (0.0 if precision == 0 or recall == 0 else None)
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def pairs(groups: dict[str, str]) -> set[tuple[str, str]]:
    by_cluster: dict[str, list[str]] = defaultdict(list)
    for case_id, cluster in groups.items():
        if cluster:
            by_cluster[cluster].append(case_id)
    return {(a, b) for members in by_cluster.values() for i, a in enumerate(sorted(members)) for b in sorted(members)[i + 1:]}


def validate_time_splits(rows: list[dict]) -> None:
    by_split: dict[str, list[datetime]] = defaultdict(list)
    for index, row in enumerate(rows, 1):
        try:
            submitted = datetime.fromisoformat(str(row["submitted_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"record {index}: submitted_at must be an ISO-8601 timestamp") from exc
        if submitted.tzinfo is None:
            raise ValueError(f"record {index}: submitted_at must include a timezone")
        by_split[row["split"]].append(submitted.astimezone(timezone.utc))
    order = [split for split in ("train", "dev", "test") if by_split.get(split)]
    for earlier, later in zip(order, order[1:]):
        if max(by_split[earlier]) >= min(by_split[later]):
            raise ValueError(f"time split overlap: {earlier} must end before {later} begins")


def _test_metrics(test: list[dict]) -> dict:
    """Calculate the reported metrics for a set of test-case observations."""
    gold_entities, pred_entities = set(), set()
    gold_clusters, pred_clusters = {}, {}
    ev_tp = ev_fp = ev_fn = verdict_fp = verdict_negatives = 0
    times = []
    for row in test:
        cid = str(row["case_id"])
        for entity in row["gold_entities"]:
            gold_entities.add((cid, entity["type"], entity["value"]))
        for entity in row["predicted_entities"]:
            pred_entities.add((cid, entity["type"], entity["value"]))
        if row["campaign_id"]:
            gold_clusters[cid] = str(row["campaign_id"])
        if row.get("predicted_campaign_id"):
            pred_clusters[cid] = str(row["predicted_campaign_id"])
        gold_supported = {(cid, item["type"], item["value"]) for item in row["gold_supported_entities"]}
        predicted_supported = {(cid, item["type"], item["value"]) for item in row["predicted_supported_entities"]}
        ev_tp += len(gold_supported & predicted_supported)
        ev_fp += len(predicted_supported - gold_supported)
        ev_fn += len(gold_supported - predicted_supported)
        verdict_negatives += int(not row["gold_adverse_verdict"])
        verdict_fp += int(row["predicted_adverse_verdict"] and not row["gold_adverse_verdict"])
        times.append(float(row["processing_ms"]))

    entity = f1_counts(len(gold_entities & pred_entities), len(pred_entities - gold_entities), len(gold_entities - pred_entities))
    gold_counts = Counter(gold_clusters.values())
    predicted_counts = Counter(pred_clusters.values())
    overlap_counts = Counter((gold_clusters[cid], pred_clusters[cid]) for cid in gold_clusters.keys() & pred_clusters.keys())
    gold_pair_count = sum(count * (count - 1) // 2 for count in gold_counts.values())
    predicted_pair_count = sum(count * (count - 1) // 2 for count in predicted_counts.values())
    true_pair_count = sum(count * (count - 1) // 2 for count in overlap_counts.values())
    campaign = f1_counts(true_pair_count, predicted_pair_count - true_pair_count, gold_pair_count - true_pair_count)
    ordered = sorted(times)
    return {
        "entity_micro": entity,
        "campaign_pairwise": campaign,
        "evidence_support_precision": ev_tp / (ev_tp + ev_fp) if ev_tp + ev_fp else None,
        "evidence_support_recall": ev_tp / (ev_tp + ev_fn) if ev_tp + ev_fn else None,
        "evidence_support_claims": {"tp": ev_tp, "fp": ev_fp, "fn": ev_fn},
        "verdict_false_positive_rate": verdict_fp / verdict_negatives if verdict_negatives else None,
        "processing_ms": {"mean": statistics.fmean(times), "p95": ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]},
    }


def _bootstrap_intervals(test: list[dict], resamples: int, seed: int) -> dict:
    """Bootstrap cases for per-case metrics and gold campaign groups for pairwise F1."""
    rng = random.Random(seed)
    metric_paths = {
        "entity_micro_f1": ("entity_micro", "f1"),
        "campaign_pairwise_f1": ("campaign_pairwise", "f1"),
        "evidence_support_precision": ("evidence_support_precision",),
        "verdict_false_positive_rate": ("verdict_false_positive_rate",),
        "processing_ms_mean": ("processing_ms", "mean"),
        "processing_ms_p95": ("processing_ms", "p95"),
    }
    samples = {name: [] for name in metric_paths}
    campaign_groups: dict[str, list[dict]] = defaultdict(list)
    for row in test:
        group = f"campaign:{row['campaign_id']}" if row["campaign_id"] else f"case:{row['case_id']}"
        campaign_groups[group].append(row)
    group_values = list(campaign_groups.values())
    for replicate in range(resamples):
        case_draw = []
        for draw, index in enumerate(rng.choices(range(len(test)), k=len(test))):
            row = dict(test[index])
            row["case_id"] = f"bootstrap-case-{replicate}-{draw}"
            case_draw.append(row)
        campaign_draw = []
        for group_draw, index in enumerate(rng.choices(range(len(group_values)), k=len(group_values))):
            for member_index, member in enumerate(group_values[index]):
                row = dict(member)
                row["case_id"] = f"bootstrap-campaign-{replicate}-{group_draw}-{member_index}"
                campaign_draw.append(row)
        metrics_by_name = {"case": _test_metrics(case_draw), "campaign": _test_metrics(campaign_draw)}
        for name, path in metric_paths.items():
            value = metrics_by_name["campaign" if name == "campaign_pairwise_f1" else "case"]
            for key in path:
                value = value[key]
            if value is not None and math.isfinite(value):
                samples[name].append(float(value))

    minimum_valid = math.ceil(resamples * 0.8)
    intervals = {}
    for name, values in samples.items():
        ordered = sorted(values)
        if len(ordered) < minimum_valid:
            lower = upper = None
        else:
            lower = ordered[max(0, math.ceil(0.025 * len(ordered)) - 1)]
            upper = ordered[max(0, math.ceil(0.975 * len(ordered)) - 1)]
        intervals[name] = {
            "lower": lower,
            "upper": upper,
            "confidence_level": 0.95,
            "valid_resamples": len(ordered),
            "total_resamples": resamples,
            "method": "gold campaign-group percentile bootstrap" if name == "campaign_pairwise_f1" else "case-level percentile bootstrap",
        }
    return intervals


def load(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {line_no}: each JSONL record must be an object")
        required = {"case_id", "submitted_at", "split", "campaign_id", "gold_entities", "predicted_entities", "gold_supported_entities", "predicted_supported_entities", "gold_adverse_verdict", "predicted_adverse_verdict", "processing_ms"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"line {line_no}: missing fields {sorted(missing)}")
        if not isinstance(row["case_id"], str) or not row["case_id"].strip():
            raise ValueError(f"line {line_no}: case_id must be a non-empty string")
        if not isinstance(row["split"], str) or row["split"] not in {"train", "dev", "test"}:
            raise ValueError(f"line {line_no}: split must be train, dev, or test")
        if row["campaign_id"] is not None and (not isinstance(row["campaign_id"], str) or not row["campaign_id"].strip()):
            raise ValueError(f"line {line_no}: campaign_id must be null or a non-empty string")
        if row.get("predicted_campaign_id") is not None and (not isinstance(row["predicted_campaign_id"], str) or not row["predicted_campaign_id"].strip()):
            raise ValueError(f"line {line_no}: predicted_campaign_id must be null or a non-empty string")
        for field in ("gold_adverse_verdict", "predicted_adverse_verdict"):
            if not isinstance(row[field], bool):
                raise ValueError(f"line {line_no}: {field} must be a boolean")
        for field in ("gold_entities", "predicted_entities", "gold_supported_entities", "predicted_supported_entities"):
            entities = row[field]
            if not isinstance(entities, list) or any(
                not isinstance(entity, dict)
                or not isinstance(entity.get("type"), str) or not entity["type"].strip()
                or not isinstance(entity.get("value"), str) or not entity["value"].strip()
                for entity in entities
            ):
                raise ValueError(f"line {line_no}: {field} must contain objects with non-empty string type and value")
        for support_field, entity_field in (("gold_supported_entities", "gold_entities"), ("predicted_supported_entities", "predicted_entities")):
            supported = {(item["type"], item["value"]) for item in row[support_field]}
            entities = {(item["type"], item["value"]) for item in row[entity_field]}
            if not supported.issubset(entities):
                raise ValueError(f"line {line_no}: {support_field} must be a subset of {entity_field}")
        if (
            isinstance(row["processing_ms"], bool)
            or not isinstance(row["processing_ms"], (int, float))
            or not math.isfinite(row["processing_ms"])
            or row["processing_ms"] < 0
        ):
            raise ValueError(f"line {line_no}: processing_ms must be non-negative")
        rows.append(row)
    if not rows:
        raise ValueError("dataset has no records")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("case_id values must be unique per run")
    validate_time_splits(rows)
    return rows


def score(rows: list[dict], *, bootstrap_resamples: int = 1000, bootstrap_seed: int = 20261103) -> dict:
    if isinstance(bootstrap_resamples, bool) or not isinstance(bootstrap_resamples, int) or bootstrap_resamples < 1:
        raise ValueError("bootstrap_resamples must be a positive integer")
    if isinstance(bootstrap_seed, bool) or not isinstance(bootstrap_seed, int):
        raise ValueError("bootstrap_seed must be an integer")
    train_campaigns: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["campaign_id"]:
            train_campaigns[row["campaign_id"]].add(row["split"])
    leakage = sorted(campaign for campaign, splits in train_campaigns.items() if len(splits) > 1)
    if leakage:
        raise ValueError(f"campaign leakage across splits ({len(leakage)} campaign labels)")
    validate_time_splits(rows)

    test = [row for row in rows if row["split"] == "test"]
    if not test:
        raise ValueError("dataset has no test records")
    metrics = _test_metrics(test)
    return {
        "test_cases": len(test),
        **metrics,
        "confidence_intervals": _bootstrap_intervals(test, bootstrap_resamples, bootstrap_seed),
        "bootstrap": {"method": "case-level percentile; gold campaign-group percentile for campaign pairwise F1", "confidence_level": 0.95, "resamples": bootstrap_resamples, "seed": bootstrap_seed, "minimum_valid_fraction": 0.8},
        "limitations": "Metrics describe only the provided authorized test split; they are not a determination of wrongdoing or a guarantee of real-world performance.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DATA.jsonl")
    try:
        print(json.dumps(score(load(Path(sys.argv[1]))), indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"evaluation input error: {exc}") from exc
