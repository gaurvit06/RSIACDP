"""Offline inference for the trained TF-IDF logistic regression posting classifier."""
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

ARTIFACT = Path(__file__).with_name("posting_model_v1.json.gz")
HIGH = "Higher fraud risk"
LOW = "Lower fraud risk"
ABSTAIN = "More posting text needed"
TOKEN = re.compile(r"(?u)\b\w\w+\b")
MASK = re.compile(r"#(?:url|email|phone)_[\w-]+#|https?://\S+|[\w.+-]+@[\w.-]+\.\w+", re.I)
FIELD = re.compile(r"^(?:Job title|Location|Industry|Employment type|Department|Required experience|Requirements|Benefits|Job description|Salary range|Company profile|Required education|Function|Company):[ \t]*", re.I | re.M)


def clean(text):
    return MASK.sub(" ", FIELD.sub("", text)).lower()


def feature_key(term):
    return hashlib.blake2b(term.encode(), digest_size=12).hexdigest()


@lru_cache(maxsize=1)
def load_model():
    raw = ARTIFACT.read_bytes()
    model = json.loads(gzip.decompress(raw))
    if model["format"] != 1 or not model["features"]:
        raise ValueError("Invalid posting classifier artifact")
    return model, "posting-lr-v1-" + hashlib.sha256(raw).hexdigest()[:12]


def predict(text):
    model, version = load_model()
    tokens = TOKEN.findall(clean(text or ""))
    terms = Counter(tokens)
    terms.update(a + " " + b for a, b in zip(tokens, tokens[1:]))
    norm = weighted = 0.0
    matched_words = 0
    for term, count in terms.items():
        entry = model["features"].get(feature_key(term))
        if entry is None:
            continue
        idf, coefficient = entry
        value = (1 + math.log(count)) * idf
        norm += value * value
        weighted += value * coefficient
        matched_words += int(" " not in term)
    result = dict(label=ABSTAIN, model_version=version, score=None, threshold=model["threshold"],
                  matched_words=matched_words)
    if matched_words >= model["min_words"]:
        logit = model["intercept"] + weighted / math.sqrt(norm)
        score = 1 / (1 + math.exp(-logit))
        result.update(label=HIGH if score >= model["threshold"] else LOW, score=round(score, 6))
    return result
