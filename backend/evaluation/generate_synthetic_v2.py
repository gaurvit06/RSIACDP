"""Generate fictional, campaign-separated evaluation fixtures, not performance evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def generate(output: Path) -> None:
    # Exclusive directory creation protects prior annotations and run outputs.
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict] = []
    provenance: list[dict] = []
    for split, month in (("train", 1), ("dev", 2), ("test", 3)):
        for group in range(12):
            domain = f"campaign-{split}-{group:02d}.invalid"
            email = f"contact-{split}-{group:02d}@{domain}"
            email_entity = {"type": "email", "value": email}
            domain_entity = {"type": "domain", "value": domain}
            concern = group % 2 == 0
            reference = f"synthetic://fixture-v2/{split}/{group:02d}"
            wording = (
                "Recruitment enquiry. A registration fee was mentioned.",
                "Please review this interview invitation.",
                "Remote role enquiry; please verify the sender.",
            )[group % 3]
            for member in range(3):
                case_id = f"synthetic-{split}-{group:02d}-{member}"
                text = f"SYNTHETIC TEST ONLY. {wording} Contact: {email}. Reference {case_id}."
                rows.append({
                    "case_id": case_id,
                    "submitted_at": f"2026-{month:02d}-{group + 1:02d}T10:0{member}:00Z",
                    "split": split,
                    "campaign_id": f"synthetic-{split}-group-{group:02d}",
                    "submitted_text": text,
                    "gold_entities": [email_entity, domain_entity],
                    "gold_supported_entities": [email_entity] if concern else [],
                    "gold_adverse_verdict": concern,
                })
                provenance.append({
                    "case_id": case_id,
                    "synthetic": True,
                    "reference": reference,
                    "annotation_method": "generator-defined fixture, not independent adjudication",
                    "claim": "fictional source allegation exists" if concern else "no allegation in the complete fictional fixture universe",
                    "scope": "email and email-derived domain extraction; exact-email campaign fixtures",
                    "source_spans": [
                        {"type": "email", "start": text.index(email), "end": text.index(email) + len(email)},
                        {"type": "domain", "start": text.index(domain), "end": text.index(domain) + len(domain)},
                    ],
                    "limitations": "Reserved .invalid identifiers only; no real source retrieval, person, payment account, or authoritative confirmation.",
                })

    def write_jsonl(name: str, values: list[dict]) -> bytes:
        payload = ("\n".join(json.dumps(row, sort_keys=True) for row in values) + "\n").encode()
        (output / name).write_bytes(payload)
        return payload

    payload = write_jsonl("synthetic-input.jsonl", rows)
    write_jsonl("synthetic-provenance.jsonl", provenance)
    (output / "MANIFEST.json").write_text(json.dumps({
        "synthetic": True,
        "generator_version": "synthetic-fixtures-v2",
        "records": len(rows),
        "splits": {"train": 36, "dev": 36, "test": 36},
        "sha256": hashlib.sha256(payload).hexdigest(),
        "purpose": "Integration rehearsal only; not evidence of Indian recruitment-scam accuracy.",
        "limitations": [
            "Templates and vocabulary overlap across time splits and are unrealistic.",
            "Dates and labels are simulated and not human-adjudicated.",
            "Coverage is limited to reserved email and derived domain identifiers; there is no OCR, multilingual, phone, UPI, bank, or live-web data.",
            "Each generated campaign has a unique reserved domain to avoid unrelated fixtures linking through a shared placeholder host.",
            "Do not load fictional source allegations into a production evidence corpus.",
        ],
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory; must not exist")
    generate(parser.parse_args().output)
