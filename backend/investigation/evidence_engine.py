from .verifiers import (
    FREE_EMAIL_DOMAINS,
    email_domain,
    verify_company_email_domain,
    verify_company_website_domain,
)


PAYMENT_TERMS = (
    "registration fee",
    "processing fee",
    "security deposit",
    "training fee",
    "interview fee",
    "verification fee",
    "pay",
    "payment",
    "deposit",
    "send money",
)

URGENCY_TERMS = (
    "immediately",
    "urgent",
    "today only",
    "limited time",
    "within 24 hours",
    "act now",
)


def _evidence(code, severity, claim, weight, source, observed=None):
    return {
        "code": code,
        "severity": severity,
        "claim": claim,
        "weight": weight,
        "source": source,
        "observed": observed,
    }


def generate_evidence(payload):
    text = (payload.get("text") or "").lower()
    entities = payload.get("entities") or {}

    companies = entities.get("companies") or []
    emails = entities.get("emails") or []
    domains = entities.get("domains") or []
    upi_ids = entities.get("upi_ids") or []
    amounts = entities.get("amounts") or []

    evidence = []

    payment_term = next((term for term in PAYMENT_TERMS if term in text), None)

    if payment_term and (amounts or upi_ids):
        evidence.append(
            _evidence(
                code="PAYMENT_REQUEST",
                severity="HIGH",
                claim="The recruitment message appears to request a payment or fee.",
                weight=35,
                source="message text + extracted payment indicators",
                observed={
                    "matched_term": payment_term,
                    "amounts": amounts,
                    "upi_ids": upi_ids,
                },
            )
        )

    for email in emails:
        domain = email_domain(email)
        if domain in FREE_EMAIL_DOMAINS:
            evidence.append(
                _evidence(
                    code="FREE_EMAIL_PROVIDER",
                    severity="MEDIUM",
                    claim=f"Recruiter email {email} uses a free email provider.",
                    weight=15,
                    source="email-domain check",
                    observed={"email": email, "domain": domain},
                )
            )

    for finding in verify_company_email_domain(companies, emails):
        if finding["status"] == "warning":
            evidence.append(
                _evidence(
                    code="EMAIL_DOMAIN_MISMATCH",
                    severity="HIGH",
                    claim=(
                        f"Recruiter email domain does not match the prototype "
                        f"reference domain for {finding['company']}."
                    ),
                    weight=20,
                    source="local company-domain reference",
                    observed={
                        "company": finding["company"],
                        "email": finding["email"],
                        "observed_domain": finding["observed_domain"],
                        "reference_domain": finding["official_domain"],
                    },
                )
            )

    for finding in verify_company_website_domain(companies, domains):
        if finding["status"] == "warning":
            evidence.append(
                _evidence(
                    code="DOMAIN_MISMATCH",
                    severity="HIGH",
                    claim=(
                        f"Submitted website domain differs from the prototype "
                        f"reference domain for {finding['company']}."
                    ),
                    weight=20,
                    source="local company-domain reference",
                    observed={
                        "company": finding["company"],
                        "observed_domain": finding["observed_domain"],
                        "reference_domain": finding["official_domain"],
                    },
                )
            )

    if upi_ids and payment_term:
        evidence.append(
            _evidence(
                code="UPI_PAYMENT_CHANNEL",
                severity="MEDIUM",
                claim="A UPI identifier appears in recruitment payment context.",
                weight=15,
                source="message text + extracted UPI",
                observed={"upi_ids": upi_ids},
            )
        )

    urgency_term = next((term for term in URGENCY_TERMS if term in text), None)
    if urgency_term:
        evidence.append(
            _evidence(
                code="URGENCY_LANGUAGE",
                severity="LOW",
                claim="The message uses urgency language that can increase pressure on the recipient.",
                weight=10,
                source="message-text rule",
                observed={"matched_term": urgency_term},
            )
        )

    # Avoid accidental duplicate evidence codes for the prototype score.
    deduped = {}
    for item in evidence:
        deduped.setdefault(item["code"], item)

    return list(deduped.values())
