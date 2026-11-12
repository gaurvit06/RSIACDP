"""Prepare the no-graph ablation from paired full/no-graph measurements."""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

from .evaluate import load, score


def load_graph_off_times(path: Path) -> dict[str, float]:
    values = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
        case_id = str(row.get("case_id", ""))
        duration = row.get("processing_ms")
        if not case_id or not isinstance(duration, (int, float)) or duration < 0:
            raise ValueError(f"line {line_no}: case_id and non-negative processing_ms are required")
        if case_id in values:
            raise ValueError(f"line {line_no}: duplicate graph-off case_id")
        values[case_id] = float(duration)
    return values


def ablate(full_rows: list[dict], graph_off_times: dict[str, float]) -> tuple[list[dict], dict]:
    tests = [row for row in full_rows if row["split"] == "test"]
    test_ids = {str(row["case_id"]) for row in tests}
    if test_ids != set(graph_off_times):
        missing_count = len(test_ids - set(graph_off_times))
        extra_count = len(set(graph_off_times) - test_ids)
        raise ValueError(f"graph-off timing IDs must match test IDs exactly (missing={missing_count}, extra={extra_count})")
    rows = []
    for source in tests:
        row = dict(source)
        row["predicted_campaign_id"] = None
        row["processing_ms"] = graph_off_times[str(row["case_id"])]
        rows.append(row)
    return rows, score(rows)


def main(args: list[str]) -> int:
    if len(args) != 3:
        print(f"usage: {Path(sys.argv[0]).name} FULL_PIPELINE.jsonl GRAPH_OFF_TIMES.jsonl OUTPUT.jsonl", file=sys.stderr)
        return 2
    try:
        source_path = Path(args[0])
        full_rows = load(source_path)
        times = load_graph_off_times(Path(args[1]))
        rows, metrics = ablate(full_rows, times)
        output = Path(args[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        metrics["ablation"] = {
            "name": "Evidence pipeline without graph linking",
            "full_pipeline_input_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "graph_predictions": "disabled",
            "processing_boundary": "must be measured during the matched no-graph run and supplied by case_id; entity/evidence/verdict outputs are carried from the full run because graph linking does not change them",
        }
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"ablation input error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
