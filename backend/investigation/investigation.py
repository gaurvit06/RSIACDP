from .verifiers import (
    verify_free_email,
    verify_company_email_domain,
    verify_company_website_domain,
)
from .evidence_engine import generate_evidence
from .risk_engine import calculate_risk


def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object.")

    entities = payload.get("entities")
    if not isinstance(entities, dict):
        raise ValueError("Payload must contain an 'entities' object.")


def investigate_case(payload):
    validate_payload(payload)

    entities = payload.get("entities") or {}
    companies = entities.get("companies") or []
    emails = entities.get("emails") or []
    domains = entities.get("domains") or []

    verification = []
    verification.extend(verify_free_email(emails))
    verification.extend(verify_company_email_domain(companies, emails))
    verification.extend(verify_company_website_domain(companies, domains))

    evidence = generate_evidence(payload)
    risk = calculate_risk(evidence)

    return {
        "case_id": payload.get("case_id"),
        "verification": verification,
        "evidence": evidence,
        "risk": risk,
    }
