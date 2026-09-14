import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "company_domains.json"


def load_company_domains():
    with open(DATA_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    return {key.lower(): value.lower() for key, value in data.items()}
