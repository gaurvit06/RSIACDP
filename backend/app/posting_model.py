"""Reproduce the hiring-market dashboard's fitted text and numeric logistic regression."""
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

ARTIFACT = Path(__file__).with_name("hiring_market_lr.json.gz")
HIGH = "Higher fraud risk"
LOW = "Lower fraud risk"
ABSTAIN = "More posting text needed"
TOKEN = re.compile(r"\b[a-z]{2,}\b")
URGENT = ("urgent", "immediate", "asap", "hurry", "limited", "act now", "no experience",
          "work from home", "earn money", "easy money", "guaranteed", "weekly pay",
          "quick money", "high pay", "bonus", "100%", "free training", "daily pay")
HEADER = re.compile(
    r"^(job title|company|company name|location|industry|employment type|department|"
    r"required experience|requirements|benefits|job description|description|salary range|"
    r"salary disclosed|company logo present|required education|function|company profile):[ \t]*(.*)$", re.I)


def posting_fields(text):
    """Map Casework's labelled material to the six inputs in the reference form."""
    fields = {}
    description = []
    multiline = None
    for line in text.splitlines():
        match = HEADER.match(line.strip())
        if match:
            key, value = match[1].lower(), match[2].strip()
            multiline = key if key in {"requirements", "description", "job description", "benefits", "company profile"} else None
            fields.setdefault(key, []).append(value)
        elif multiline:
            fields[multiline].append(line)
        else:
            description.append(line)
    if not fields:
        return "", "", text, "", False, False
    values = {key: "\n".join(lines).strip() for key, lines in fields.items()}
    desc = "\n".join(x for x in ("\n".join(description).strip(), values.get("job description"),
                                 values.get("description")) if x)
    salary = values.get("salary disclosed", "").lower() == "yes" or bool(re.search(r"\d", values.get("salary range", "")))
    return (values.get("job title", ""), values.get("company") or values.get("company name") or values.get("company profile", ""),
            desc, values.get("requirements", ""), salary, values.get("company logo present", "").lower() == "yes")


@lru_cache(maxsize=1)
def load_model():
    raw = ARTIFACT.read_bytes()
    model = json.loads(gzip.decompress(raw))
    if model["format"] != "hiring-market-lr-v1" or len(model["features"]) != 5000 or len(model["numeric"]) != 10:
        raise ValueError("Invalid hiring-market classifier artifact")
    return model, model["format"] + "-" + hashlib.sha256(raw).hexdigest()[:12]


def predict(text):
    return predict_fields(*posting_fields(text or ""))


def predict_fields(title, company, description, requirements, salary, logo):
    model, version = load_model()
    raw = " ".join((title, company, description, requirements)).lower()
    cleaned = re.sub(r"<.*?>", " ", raw)
    cleaned = re.sub(r"http\S+|www\.\S+", " ", cleaned)
    tokens = TOKEN.findall(re.sub(r"[^a-z\s]", " ", cleaned))
    terms = Counter(tokens)
    terms.update(a + " " + b for a, b in zip(tokens, tokens[1:]))
    norm = weighted = 0.0
    matched = 0
    for term, count in terms.items():
        entry = model["features"].get(term)
        if entry is not None:
            value = (1 + math.log(count)) * entry[0]
            norm += value * value
            weighted += value * entry[1]
            matched += int(" " not in term)
    numeric = dict(has_salary=int(salary), has_company_logo=int(logo),
                   has_company_profile=int(bool(company.strip())), has_requirements=int(bool(requirements.strip())),
                   has_benefits=0, has_questions=0, telecommuting=0,
                   has_urgency_words=int(any(word in raw for word in URGENT)), desc_length=len(description))
    numeric["profile_completeness"] = sum(numeric[k] for k in ("has_salary", "has_company_logo", "has_company_profile", "has_requirements"))
    result = dict(label=ABSTAIN, model_version=version, threshold=model["threshold"], matched_words=matched, score=None)
    if matched >= model["min_words"]:
        logit = model["intercept"] + weighted / math.sqrt(norm)
        logit += sum(numeric[k] * coefficient for k, coefficient in model["numeric"].items())
        score = 1 / (1 + math.exp(-logit)) if logit >= 0 else math.exp(logit) / (1 + math.exp(logit))
        result.update(label=HIGH if score >= model["threshold"] else LOW, score=score)
    return result
