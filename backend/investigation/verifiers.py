from urllib.parse import urlparse
from .reference_data import load_company_domains


FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "rediffmail.com",
    "proton.me",
    "protonmail.com",
}


def email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].strip().lower()


def clean_domain(value: str) -> str:
    value = (value or "").strip().lower()

    if not value:
        return ""

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    parsed = urlparse(value)
    domain = parsed.netloc or parsed.path

    if domain.startswith("www."):
        domain = domain[4:]

    return domain.split(":")[0]


def verify_free_email(emails):
    findings = []

    for email in emails:
        domain = email_domain(email)
        if domain in FREE_EMAIL_DOMAINS:
            findings.append({
                "check": "Email provider",
                "status": "warning",
                "message": f"{email} uses free email provider {domain}.",
                "email": email,
                "domain": domain,
            })
        elif domain:
            findings.append({
                "check": "Email provider",
                "status": "pass",
                "message": f"{email} uses domain {domain}.",
                "email": email,
                "domain": domain,
            })

    if not emails:
        findings.append({
            "check": "Email provider",
            "status": "info",
            "message": "No email address was extracted.",
        })

    return findings


def verify_company_email_domain(companies, emails):
    company_domains = load_company_domains()
    findings = []

    for company in companies:
        official = company_domains.get(company.lower())

        if not official:
            findings.append({
                "check": "Company email-domain match",
                "status": "info",
                "message": f"No prototype reference domain is available for {company}.",
                "company": company,
            })
            continue

        if not emails:
            findings.append({
                "check": "Company email-domain match",
                "status": "info",
                "message": f"No email available to compare with {company}'s reference domain.",
                "company": company,
                "official_domain": official,
            })
            continue

        for email in emails:
            domain = email_domain(email)

            if domain == official or domain.endswith("." + official):
                status = "pass"
                message = f"{email} matches the prototype reference domain {official}."
            else:
                status = "warning"
                message = (
                    f"{email} does not match the prototype reference domain "
                    f"{official} for {company}."
                )

            findings.append({
                "check": "Company email-domain match",
                "status": status,
                "message": message,
                "company": company,
                "email": email,
                "observed_domain": domain,
                "official_domain": official,
            })

    return findings


def verify_company_website_domain(companies, domains):
    company_domains = load_company_domains()
    findings = []

    for company in companies:
        official = company_domains.get(company.lower())

        if not official:
            continue

        if not domains:
            findings.append({
                "check": "Company website-domain match",
                "status": "info",
                "message": f"No website domain was extracted for comparison with {company}.",
                "company": company,
                "official_domain": official,
            })
            continue

        for raw_domain in domains:
            domain = clean_domain(raw_domain)

            if domain == official or domain.endswith("." + official):
                status = "pass"
                message = f"{domain} matches the prototype reference domain {official}."
            else:
                status = "warning"
                message = (
                    f"{domain} differs from the prototype reference domain "
                    f"{official} for {company}."
                )

            findings.append({
                "check": "Company website-domain match",
                "status": status,
                "message": message,
                "company": company,
                "observed_domain": domain,
                "official_domain": official,
            })

    return findings
