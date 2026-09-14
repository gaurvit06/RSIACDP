import re
from urllib.parse import urlparse


def normalize_phone(phone: str) -> str:
    """
    Normalize an Indian phone number to +91XXXXXXXXXX format.
    """
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"

    if len(digits) == 10:
        return f"+91{digits}"

    return phone.strip()


def normalize_email(email: str) -> str:
    """
    Normalize an email address.
    """
    return email.strip().lower()


def normalize_domain(domain: str) -> str:
    """
    Normalize a domain from a URL or plain domain string.
    """
    value = domain.strip().lower()

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    parsed = urlparse(value)

    hostname = parsed.hostname or ""
    hostname = hostname.lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


def normalize_upi(upi: str) -> str:
    """
    Normalize a UPI ID.
    """
    return upi.strip().lower()