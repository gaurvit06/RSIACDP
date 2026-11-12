"""Shared display-safe transformations for sensitive identifiers."""
import re
from urllib.parse import urlsplit


_PRIVATE_AUDIT_KEYS = {
    "matched_normalized_value", "stored_name", "raw_value", "normalized_value",
    "source_excerpt", "status_token_hash", "rationale", "review_rationale",
    "resolution", "before", "after", "changes", "source_ref", "source_record_ref",
    "excerpt", "claim",
    "reviewed_by",
}

# Analyst timelines and downloaded reports are intentionally metadata-only.
# Audit details are produced by the application today, but using an allowlist
# also prevents a future event field from exposing arbitrary user/source text.
_SAFE_AUDIT_KEYS = {
    "account_count", "actor_type", "attempt_count", "authority", "case_count",
    "consent_version", "disposition", "disposition_id", "entity_id",
    "entity_type", "evidence_id", "evidence_ids", "external_source_consent",
    "format", "group_count", "input_kind", "link_id", "locked",
    "matched_case_count", "outcome", "previous_status", "record_count",
    "request_count", "request_ref", "retry_after_seconds", "rule_version",
    "status", "threshold", "trigger",
}


def _mask_contact_patterns(value: str) -> str:
    value = re.sub(r"(?i)([A-Z0-9._%+-])[A-Z0-9._%+-]*(@[A-Z0-9.-]+\.[A-Z]{2,})", r"\1***\2", value)
    # UPI handles commonly use a dotless PSP suffix, unlike email domains.
    # Mask them in arbitrary excerpts and audit text as well as structured fields.
    value = re.sub(r"(?i)(?<![\w.-])[A-Z0-9._-]{2,256}@[A-Z0-9-]{2,64}(?![\w.-])", "[UPI masked]", value)
    value = re.sub(r"(?i)\b(?:account(?:\s*(?:no\.?|number))?|a/c|bank\s*account)\s*[:#=-]?\s*\d{9,18}\b", "account [masked]", value)
    value = re.sub(r"(?i)\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN masked]", value)
    value = re.sub(r"(?<!\d)(?:(?:\d{4}[ -]){2}\d{4}|\d{12})(?!\d)", "[12-digit identifier masked]", value)
    value = re.sub(r"(?<!\w)(?:\+?91[\s-]?)?[6-9](?:[\s-]*\d){9}(?!\w)", "••••••••", value)
    value = re.sub(r"(?i)\b[A-Z0-9._-]{2,}@[A-Z0-9.-]{2,}\b", "••••", value)
    return value


def redact_source_ref(value: str) -> str:
    """Preserve a traceable web origin while hiding paths, queries, and embedded contacts."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() in {"http", "https"} and parsed.hostname:
            if parsed.username or parsed.password:
                return "[source reference restricted]"
            host = parsed.hostname.lower()
            if ":" in host and not host.startswith("["):
                host = f"[{host}]"
            origin = _mask_contact_patterns(f"{parsed.scheme.lower()}://{host}")
            suffix = "/[path redacted]" if parsed.path not in {"", "/"} else ""
            suffix += "?[query redacted]" if parsed.query else ""
            suffix += "#[fragment redacted]" if parsed.fragment else ""
            return origin + suffix
    except ValueError:
        pass
    if re.fullmatch(r"(?:LOCAL-[A-F0-9]{16}|[a-f0-9]{64})", value):
        return value
    return "[source reference restricted]"


def redact_text(value: str) -> str:
    """Mask common contact details and labeled recruiter names in untrusted text."""
    value = re.sub(r"(?im)(\b(?:recruiter(?:\s+name)?|hr\s*contact|contact\s*person)\s*[:=-]\s*)[^\r\n]{2,120}", r"\1[name masked]", value)
    value = re.sub(r"(?i)\bhttps?://[^\s<>\"']+", lambda match: redact_source_ref(match.group(0)), value)
    value = _mask_contact_patterns(value)
    return value


def redact_data(value):
    """Expose only approved audit metadata, never arbitrary strings, to analysts."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_data(item) for item in value]
    if isinstance(value, dict):
        return {
            key: ("[redacted]" if key in _PRIVATE_AUDIT_KEYS else redact_data(item))
            for key, item in value.items()
            if key in _SAFE_AUDIT_KEYS or key in _PRIVATE_AUDIT_KEYS
        }
    return value


def mask_identifier(entity_type: str, value: str) -> str:
    """Return a privacy-preserving display form without changing stored evidence."""
    if entity_type == "email" and "@" in value:
        local, domain = value.split("@", 1)
        return f"{local[:1]}***@{domain}"
    if entity_type == "phone":
        return "••••" + value[-4:]
    if entity_type == "upi_id":
        return "••••"
    if entity_type in {"url", "domain"}:
        return "[web identifier masked]"
    if entity_type == "recruiter_claim":
        return "[name masked]"
    if entity_type == "location_claim":
        return "[location masked]"
    if entity_type == "fee_request":
        return "[payment request text masked]"
    if entity_type in {"company_claim", "job_title_claim", "date_claim", "payment_amount_claim"}:
        return redact_text(value)
    return "[identifier masked]"
