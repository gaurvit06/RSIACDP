"""Export the trusted local dashboard's scikit-learn artifacts to a data-only format."""
import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path


def export(source, destination):
    fingerprints = {}

    def read(name):
        raw = (source / name).read_bytes()
        fingerprints[name] = hashlib.sha256(raw).hexdigest()
        return pickle.loads(raw)

    model = read("best_model.pkl")
    vectorizer = read("tfidf_vectorizer.pkl")
    numeric = list(read("numeric_cols.pkl"))
    names = vectorizer.get_feature_names_out()
    weights = model.coef_[0]
    if (model.classes_.tolist() != [0, 1] or len(weights) != len(names) + len(numeric)
            or vectorizer.ngram_range != (1, 2) or vectorizer.norm != "l2"
            or not vectorizer.sublinear_tf or vectorizer.stop_words is not None):
        raise ValueError("Unsupported feature configuration")
    artifact = dict(format="hiring-market-lr-v1", source_sha256=fingerprints,
                    threshold=json.loads((source / "model_info.json").read_text())["threshold"],
                    min_words=3, intercept=float(model.intercept_[0]),
                    numeric=dict(zip(numeric, weights[len(names):])),
                    features={name: [float(idf), float(weight)] for name, idf, weight in
                              zip(names, vectorizer.idf_, weights)})
    payload = json.dumps(artifact, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    destination.write_bytes(gzip.compress(payload, mtime=0))


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("source", type=Path)
    args.add_argument("destination", type=Path)
    options = args.parse_args()
    export(options.source, options.destination)
