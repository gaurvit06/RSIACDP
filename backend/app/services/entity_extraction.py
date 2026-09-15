import re
from urllib.parse import urlparse


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?"
)

DOMAIN_PATTERN = re.compile(
    r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b"
)

UPI_PATTERN = re.compile(
    r"\b[A-Za-z0-9._-]+@[A-Za-z][A-Za-z0-9._-]*\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?(?:[6-9]\d{9}|[6-9]\d{4}[\s-]\d{5})(?!\d)"
)


def extract_emails(text: str) -> list[str]:
    if not text:
        return []

    return sorted(
        set(
            match.group(0).lower()
            for match in EMAIL_PATTERN.finditer(text)
        )
    )


def extract_urls(text: str) -> list[str]:
    if not text:
        return []

    return sorted(
        set(
            match.group(0).rstrip(".,);]}")
            for match in URL_PATTERN.finditer(text)
        )
    )


def extract_upis(text: str) -> list[str]:
    if not text:
        return []

    results = []

    for match in UPI_PATTERN.finditer(text):
        value = match.group(0).lower()

        # Do not treat email addresses as UPI IDs.
        if EMAIL_PATTERN.fullmatch(value):
            continue

        results.append(value)

    return sorted(set(results))


def extract_phones(text: str) -> list[str]:
    if not text:
        return []

    results = []

    for match in PHONE_PATTERN.finditer(text):
        value = match.group(0).strip()

        # Remove spaces and hyphens.
        value = re.sub(r"[\s-]", "", value)

        results.append(value)

    return sorted(set(results))


def extract_domains(text: str) -> list[str]:
    if not text:
        return []

    results = []

    # Domains found inside URLs.
    for url in extract_urls(text):
        parsed = urlparse(url)

        if parsed.hostname:
            hostname = parsed.hostname.lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            results.append(hostname)

    # Standalone domains.
    for match in DOMAIN_PATTERN.finditer(text):
        domain = match.group(0).lower()

        # Ignore domains that are part of an email address.
        start = match.start()
        end = match.end()

        before = text[max(0, start - 1):start]
        after = text[end:end + 1]

        if before == "@":
            continue

        # Ignore the domain portion of an email address.
        if after == "@" or (
            start > 0
            and "@" in text[max(0, start - 100):start]
            and text[max(0, start - 100):start].split("@")[-1].strip()
        ):
            continue

        results.append(domain)

    return sorted(set(results))


def extract_entities(text: str) -> dict:
    """
    Extract common recruitment-investigation entities
    from submitted text using deterministic regular expressions.
    """

    if not text:
        return {
            "phones": [],
            "emails": [],
            "domains": [],
            "upis": [],
            "urls": [],
        }

    return {
        "phones": extract_phones(text),
        "emails": extract_emails(text),
        "domains": extract_domains(text),
        "upis": extract_upis(text),
        "urls": extract_urls(text),
    }