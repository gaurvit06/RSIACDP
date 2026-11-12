"""Deterministic, dependency-free TF-IDF + binary logistic-regression baseline.

This is an offline evaluation baseline only. It is not used by the application
to assess, accuse, or make investigator decisions.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

try:
    from .evaluate import score, validate_time_splits
except ImportError:  # Allow direct execution as a script from this directory.
    from evaluate import score, validate_time_splits

TOKEN = re.compile(r"(?u)\b\w\w+\b")
EPOCHS = 400
LEARNING_RATE = 0.5
L2 = 0.0001
THRESHOLD = 0.5


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.casefold())


def read_training_data(path: Path) -> tuple[list[dict], str]:
    raw = path.read_bytes()
    rows = []
    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
        required = {"case_id", "submitted_at", "split", "campaign_id", "submitted_text", "gold_entities", "gold_supported_entities", "gold_adverse_verdict"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"line {line_no}: missing fields {sorted(missing)}")
        if row["split"] not in {"train", "dev", "test"}:
            raise ValueError(f"line {line_no}: split must be train, dev, or test")
        if not isinstance(row["submitted_text"], str) or not isinstance(row["gold_adverse_verdict"], bool):
            raise ValueError(f"line {line_no}: submitted_text must be text and gold_adverse_verdict must be boolean")
        for field in ("gold_entities", "gold_supported_entities"):
            entities = row[field]
            if not isinstance(entities, list) or any(
                not isinstance(entity, dict) or set(entity) != {"type", "value"}
                or not isinstance(entity["type"], str) or not entity["type"].strip()
                or not isinstance(entity["value"], str) or not entity["value"].strip()
                for entity in entities
            ):
                raise ValueError(f"line {line_no}: {field} must contain type/value string objects")
        all_entities = {(item["type"], item["value"]) for item in row["gold_entities"]}
        supported_entities = [(item["type"], item["value"]) for item in row["gold_supported_entities"]]
        if len(set(supported_entities)) != len(supported_entities) or not set(supported_entities).issubset(all_entities):
            raise ValueError(f"line {line_no}: gold_supported_entities must be unique and a subset of gold_entities")
        rows.append(row)
    if not rows:
        raise ValueError("dataset has no records")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("case_id values must be unique")
    train_campaigns: dict[str, set[str]] = {}
    for row in rows:
        if row["campaign_id"]:
            train_campaigns.setdefault(str(row["campaign_id"]), set()).add(row["split"])
    leakage = sorted(campaign for campaign, splits in train_campaigns.items() if len(splits) > 1)
    if leakage:
        raise ValueError(f"campaign leakage across splits ({len(leakage)} campaign labels)")
    validate_time_splits(rows)
    if not any(row["split"] == "train" for row in rows) or not any(row["split"] == "test" for row in rows):
        raise ValueError("dataset must contain train and test records")
    return rows, hashlib.sha256(raw).hexdigest()


def make_tfidf(texts: list[str]) -> tuple[list[str], dict[str, float], list[dict[int, float]]]:
    tokenized = [tokenize(text) for text in texts]
    vocabulary = sorted({token for document in tokenized for token in document})
    indexes = {token: i for i, token in enumerate(vocabulary)}
    document_frequency = Counter(token for document in tokenized for token in set(document))
    idf = {token: math.log((1 + len(tokenized)) / (1 + document_frequency[token])) + 1 for token in vocabulary}
    vectors = []
    for document in tokenized:
        counts = Counter(document)
        total = sum(counts.values()) or 1
        values = {indexes[token]: (count / total) * idf[token] for token, count in counts.items()}
        norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
        vectors.append({index: value / norm for index, value in values.items()})
    return vocabulary, idf, vectors


def transform(text: str, vocabulary: list[str], idf: dict[str, float]) -> dict[int, float]:
    indexes = {token: i for i, token in enumerate(vocabulary)}
    tokens = tokenize(text)
    counts = Counter(token for token in tokens if token in indexes)
    total = sum(counts.values()) or 1
    values = {indexes[token]: (count / total) * idf[token] for token, count in counts.items()}
    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {index: value / norm for index, value in values.items()}


def sigmoid(value: float) -> float:
    value = max(-35.0, min(35.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def fit(vectors: list[dict[int, float]], labels: list[int], vocabulary_size: int) -> tuple[list[float], float]:
    if len(set(labels)) != 2:
        raise ValueError("training split must contain both adverse and non-adverse labels")
    weights = [0.0] * vocabulary_size
    bias = 0.0
    count = len(vectors)
    for _ in range(EPOCHS):
        gradient = [0.0] * vocabulary_size
        bias_gradient = 0.0
        for vector, label in zip(vectors, labels):
            probability = sigmoid(bias + sum(weights[index] * value for index, value in vector.items()))
            error = probability - label
            bias_gradient += error
            for index, value in vector.items():
                gradient[index] += error * value
        bias -= LEARNING_RATE * (bias_gradient / count)
        for index in range(vocabulary_size):
            weights[index] -= LEARNING_RATE * (gradient[index] / count + L2 * weights[index])
    return weights, bias


def run(rows: list[dict], dataset_hash: str) -> tuple[list[dict], dict]:
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]
    vocabulary, idf, train_vectors = make_tfidf([row["submitted_text"] for row in train])
    labels = [int(row["gold_adverse_verdict"]) for row in train]
    weights, bias = fit(train_vectors, labels, len(vocabulary))
    predictions = []
    for row in test:
        start = time.perf_counter()
        vector = transform(row["submitted_text"], vocabulary, idf)
        probability = sigmoid(bias + sum(weights[index] * value for index, value in vector.items()))
        processing_ms = (time.perf_counter() - start) * 1000.0
        predictions.append({
            "case_id": row["case_id"],
            "submitted_at": row["submitted_at"],
            "split": row["split"],
            "campaign_id": row["campaign_id"],
            "predicted_campaign_id": None,
            "gold_entities": row["gold_entities"],
            "predicted_entities": [],
            "gold_supported_entities": row["gold_supported_entities"],
            "predicted_supported_entities": [],
            "gold_adverse_verdict": row["gold_adverse_verdict"],
            "predicted_adverse_verdict": probability >= THRESHOLD,
            "processing_ms": processing_ms,
        })
    metrics = score(predictions)
    metrics["baseline"] = {
        "name": "TF-IDF + binary logistic regression",
        "dataset_sha256": dataset_hash,
        "training_cases": len(train),
        "test_cases": len(test),
        "vocabulary_size": len(vocabulary),
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "l2": L2,
        "decision_threshold": THRESHOLD,
        "processing_boundary": "per-test-case TF-IDF transform plus logistic-regression prediction; excludes training and file I/O",
        "capabilities": "Text-only classifier. It does not extract entities, check evidence sources, or form campaigns; corresponding predicted outputs are empty/false by design.",
    }
    return predictions, metrics


def main(args: list[str]) -> int:
    if len(args) != 2:
        print(f"usage: {Path(sys.argv[0]).name} INPUT.jsonl PREDICTIONS.jsonl", file=sys.stderr)
        return 2
    try:
        rows, dataset_hash = read_training_data(Path(args[0]))
        predictions, metrics = run(rows, dataset_hash)
        output = Path(args[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions), encoding="utf-8")
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"baseline input error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
