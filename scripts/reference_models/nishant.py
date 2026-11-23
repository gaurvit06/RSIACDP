"""Train the upstream logistic-regression option and serve its text predictor on loopback."""
import argparse
import html
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / ".local" / "nishant-reference"
BUNDLE = ROOT / ".local" / "nishant-lr.joblib"
sys.path.insert(0, str(UPSTREAM))
sys.path.insert(0, str(ROOT / "backend"))
from src.feature_extraction import FeatureExtractor
from src.prediction import JobPostingPredictor
from evaluation.run_postings_csv import material, split


def train(csv_path):
    import csv
    predictor = JobPostingPredictor()
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if split(row) == "train"]
    if {r["fraudulent"] for r in rows} != {"0", "1"}:
        raise ValueError("Expected training examples of both classes")
    processor = predictor.text_processor
    frame = pd.DataFrame({"combined_text": [processor.clean_text(material(r)) for r in rows]})
    frame["processed_text"] = frame["combined_text"].map(processor.tokenize_and_lemmatize)
    extractor = FeatureExtractor()
    features = extractor.extract_all_features(frame, fit=True)
    model = LogisticRegression(random_state=42, max_iter=1000, class_weight="balanced")
    model.fit(features, [int(row["fraudulent"]) for row in rows])
    temporary = BUNDLE.with_suffix(".tmp")
    joblib.dump((model, extractor), temporary, compress=3)
    os.replace(temporary, BUNDLE)
    print(f"Saved model trained on {len(rows)} postings", flush=True)


def serve():
    predictor = JobPostingPredictor()
    predictor.model, predictor.feature_extractor = joblib.load(BUNDLE)
    template = Path(__file__).with_name("comparison.html").read_text(encoding="utf-8")

    class Handler(BaseHTTPRequestHandler):
        def page(self, text="", result="", status=200):
            page = template.replace("{{result}}", html.escape(result)).replace("{{posting}}", html.escape(text))
            data = page.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path != "/":
                return self.send_error(404)
            self.page()

        def do_POST(self):
            if self.path != "/":
                return self.send_error(404)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 150000:
                    return self.send_error(413)
                text = parse_qs(self.rfile.read(length).decode(), max_num_fields=1).get("posting", [""])[0].strip()
            except (UnicodeError, ValueError):
                return self.send_error(400)
            if not text or len(text) > 20000:
                return self.page(result="Enter between 1 and 20,000 characters.", status=422)
            try:
                prediction = predictor.predict_single(text)
            except Exception:
                return self.page(text, "Prediction unavailable. Please retry.", 500)
            label = "Higher fraud risk" if prediction["is_fake"] else "Lower fraud risk"
            self.page(text, f"{label} · Model score {prediction['probability_fake']:.3f}")

    HTTPServer(("127.0.0.1", 5178), Handler).serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path)
    args = parser.parse_args()
    if args.train:
        train(args.train)
    else:
        serve()
