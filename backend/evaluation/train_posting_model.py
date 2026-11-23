"""From backend: python -m evaluation.train_posting_model CSV ARTIFACT METRICS_JSON."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from evaluation import legacy_posting_model as posting_model
from evaluation.run_postings_csv import material, metrics, split


def train(csv_path, artifact, report):
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len({r["job_id"] for r in rows}) != len(rows) or any(r["fraudulent"] not in {"0", "1"} for r in rows):
        raise ValueError("Expected unique job IDs and binary labels")
    train_rows = [r for r in rows if split(r) == "train"]
    test_rows = [r for r in rows if split(r) == "test"]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True)
    x = vectorizer.fit_transform(posting_model.clean(material(r)) for r in train_rows)
    classifier = LogisticRegression(class_weight="balanced", solver="liblinear", random_state=42, max_iter=500)
    classifier.fit(x, [int(r["fraudulent"]) for r in train_rows])
    features = {posting_model.feature_key(t): [float(idf), float(coef)] for t,idf,coef in zip(
        vectorizer.get_feature_names_out(), vectorizer.idf_, classifier.coef_[0])}
    assert len(features) == x.shape[1]
    model = dict(format=1, features=features, threshold=0.5, min_words=3, intercept=float(classifier.intercept_[0]))
    content = json.dumps(model, separators=(",", ":"), sort_keys=True).encode()
    temp = artifact.with_suffix(".tmp")
    temp.write_bytes(gzip.compress(content, mtime=0))
    # Verify exported inference before promoting the artifact.
    posting_model.ARTIFACT = temp
    posting_model.load_model.cache_clear()
    test_text = [material(r) for r in test_rows]
    probs = classifier.predict_proba(vectorizer.transform(map(posting_model.clean, test_text)))[:, 1]
    scored = []
    for r, text, probability in zip(test_rows, test_text, probs):
        pred = posting_model.predict(text)
        if pred["score"] is not None and abs(pred["score"] - probability) > 0.000001:
            raise ValueError("Exported inference diverged from the trained estimator")
        scored.append(dict(label=int(r["fraudulent"]), flag=pred["label"] == posting_model.HIGH, decision=pred["label"]))
    summary = dict(version=posting_model.load_model()[1], sklearn=sklearn.__version__,
                   dataset_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(), train=len(train_rows),
                   holdout=metrics(scored), abstained=sum(r["decision"] == posting_model.ABSTAIN for r in scored))
    temp.replace(artifact)
    report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("csv", "artifact", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    train(args.csv, args.artifact, args.report)
