import re
import unicodedata
from bisect import bisect_left
from urllib.parse import urlsplit, urlunsplit
from dataclasses import dataclass

@dataclass
class Extracted:
    kind: str
    raw: str
    normalized: str
    excerpt: str
    start_char: int
    end_char: int
    confidence: float = 0.99
    uncertainty: str = "Exact text match from deterministic parser; investigator confirmation is still required."

PATTERNS = {
    # Permit sentence punctuation after the address (especially a final period)
    # while still rejecting a match that stops before a word or hyphen suffix.
    "email": re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@(?:[A-Z0-9\u0080-\uffff-]+\.)+[A-Z\u0080-\uffff]{2,}(?![\w-])", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\w)"),
    # Keep a sentence-final period out of the handle while requiring the
    # provider suffix itself to end in an alphanumeric character. A dot may
    # separate suffix components, but a dot followed by a word character means
    # this is not a UPI-style identifier boundary.
    "upi_id": re.compile(r"(?<![\w.-])[A-Z0-9._-]{2,256}@[A-Z0-9](?:[A-Z0-9.-]{0,62}[A-Z0-9])?(?=$|[\s,;:!?)}\]]|\.(?=\s|$))", re.I),
    "ifsc_code": re.compile(r"(?<![A-Z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Z0-9])", re.I),
    "url": re.compile(r"https?://[^\s<>\"']+", re.I),
}
FEE_TERM_PATTERN = re.compile(
    r"\b(?:(?:registration|application|processing|security|training|verification|interview|onboarding|placement|job|document|background)\s+)?(?:fee|deposit|charge)\b",
    re.I,
)
FEE_PAYMENT_BEFORE_PATTERN = re.compile(
    r"\b(?:pay(?:ment|ing|s)?|paid|send|transfer|deposit|submit|collect(?:ed)?|charge(?:d)?|"
    r"ask(?:ed)?\s+to\s+pay|request(?:ed)?\s+payment|must\s+pay|should\s+pay)\b"
    r"[^.!?;\r\n]{0,80}$",
    re.I,
)
FEE_REQUIREMENT_AFTER_PATTERN = re.compile(
    r"^\s*(?:(?:of|amount(?:ing)?\s+to)\s+(?:₹|INR\s*|Rs\.?\s*)?\d[\d,]*(?:\.\d{1,2})?\s*)?"
    r"(?:(?:is|are|was|were|be|being|has\s+been|will\s+be)\s+)?"
    r"(?:required|needed|mandatory|payable|due|requested|charged)\b"
    r"|^\s*(?:needs?\s+to\s+be|must\s+be|should\s+be)\s+paid\b",
    re.I,
)
FEE_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|never|without|waived?|free\s+of)\b[^.!?;\r\n]{0,45}"
    r"\b(?:fee|deposit|charge)\b"
    r"|\b(?:fee|deposit|charge)\b[^.!?;\r\n]{0,45}"
    r"\b(?:not\s+(?:required|needed|payable|due|requested|charged|applicable)|waived?|free)\b",
    re.I,
)
CLAUSE_BOUNDARY_PATTERN = re.compile(r"[!?;\r\n]|\.(?=\s|$)")
BANK_ACCOUNT_PATTERN = re.compile(
    r"(?i)\b(?:bank\s+account|account|a/c)(?:\s+(?:number|no\.?))?\s*[:#=\-]?\s*((?:[0-9][ -]?){8,17}[0-9])\b"
)

LABELLED_CLAIMS = {
    "industry_claim": re.compile(r"(?im)^[ \t]*industry[ \t]*:[ \t]*([^\r\n]{2,120})$"),
    "employment_type_claim": re.compile(r"(?im)^[ \t]*employment type[ \t]*:[ \t]*([^\r\n]{2,120})$"),
    "company_claim": re.compile(r"(?im)^\s*(?:company(?:\s+name)?|organization(?:\s+name)?|employer|hiring\s+company)\s*[:\-]\s*([^\r\n]{2,120})"),
    "job_title_claim": re.compile(r"(?im)^\s*(?:job\s*(?:title|role|opening|vacancy)?|position|role|designation|vacancy|opening)\s*[:\-]\s*([^\r\n]{2,120})"),
    "recruiter_claim": re.compile(r"(?im)^\s*(?:recruiter(?:\s+name)?|hr\s*(?:contact|name)|contact\s*(?:person|name)|hiring\s+manager)\s*[:\-]\s*([^\r\n]{2,120})"),
    "location_claim": re.compile(r"(?im)^\s*(?:job\s*location|work\s*location|office\s*location|posting\s*location|workplace|location)\s*[:\-]\s*([^\r\n]{2,120})"),
}
# Narrow narrative patterns are deliberately limited to common, explicit hiring
# constructions. They produce review candidates only; these phrases do not
# establish that the named employer or vacancy is genuine.
NARRATIVE_HIRING_PATTERN = re.compile(
    r"(?i)\b(?:we(?:\s+are|['’]re)?\s+hiring|hiring\s+for|opening\s+for|vacancy\s+for)\s+"
    r"(?:(?:a|an|the)\s+)?(?P<role>[^,\r\n.!?;]{2,80}?)\s+(?:at|with|for)\s+"
    r"(?P<company>[^,\r\n.!?;]{2,100})"
)
NARRATIVE_LOCATION_PATTERN = re.compile(
    r"(?i)\b(?:work(?:ing)?\s+(?:from|in)|based\s+in|located\s+in|office\s+in|job\s+location|location)"
    r"(?:\s*(?:is|[:=-]))?\s+"
    r"(?P<location>[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){0,3}?)"
    r"(?=\s*(?:[,.;!?\r\n]|$|\b(?:and|for|with|at|from|hybrid|remote|is|are|offers?|offering|starts?|starting)\b))"
)
DATE_PATTERN = re.compile(r"(?<!\d)(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})(?!\d)", re.I)
AMOUNT_PATTERN = re.compile(r"(?<!\w)(?:₹|INR\s*|Rs\.?\s*)\s*\d[\d,]*(?:\.\d{1,2})?(?!\w)", re.I)
PAYMENT_AMOUNT_CONTEXT = re.compile(
    r"\b(?:registration|application|processing|security|training|verification|interview|onboarding)\s+(?:fee|deposit|charge)\b"
    r"|\b(?:pay(?!\s+package)|payment|transfer|send|deposit|fee|amount\s+payable|charge(?:d)?)\b",
    re.I,
)
COMPENSATION_AMOUNT_CONTEXT = re.compile(
    r"\b(?:salary|stipend|compensation|ctc|wage|lpa|pay\s+package|package|per\s+month|per\s+annum|monthly\s+(?:pay|salary)|annual\s+(?:salary|package))\b",
    re.I,
)


def _clean_claim(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def _clause_bounds(text: str, position: int, boundaries: list[int]) -> tuple[int, int]:
    """Return a conservative sentence-like span without splitting decimals or hostnames."""
    right_index = bisect_left(boundaries, position)
    left = boundaries[right_index - 1] + 1 if right_index else 0
    right = boundaries[right_index] if right_index < len(boundaries) else len(text)
    return left, right

def normalize(kind: str, value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip()
    if kind in {"email", "upi_id"}:
        left, sep, right = value.rpartition("@")
        if not sep:
            return value.casefold()
        try:
            normalized_domain = right.encode("idna").decode("ascii").lower()
        except UnicodeError:
            normalized_domain = right.casefold()
        return f"{left}@{normalized_domain}"
    if kind == "domain":
        try:
            return value.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError:
            return value.rstrip(".").casefold()
    if kind == "phone":
        digits = re.sub(r"\D", "", value)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        return digits
    if kind == "bank_account":
        return re.sub(r"[^0-9]", "", value)
    if kind == "ifsc_code":
        return re.sub(r"\s+", "", value).upper()
    if kind == "url":
        value = value.rstrip(".,);]")
        try:
            parsed = urlsplit(value)
            host = parsed.hostname
            if not parsed.scheme or not host or parsed.username is not None or parsed.password is not None:
                return value
            if ":" in host:
                normalized_host = f"[{host.lower()}]"
            else:
                normalized_host = host.encode("idna").decode("ascii").lower()
            port = parsed.port
            if port and not (parsed.scheme.lower() == "http" and port == 80) and not (parsed.scheme.lower() == "https" and port == 443):
                normalized_host = f"{normalized_host}:{port}"
            return urlunsplit((parsed.scheme.lower(), normalized_host, parsed.path, parsed.query, parsed.fragment))
        except (UnicodeError, ValueError):
            return value
    return re.sub(r"\s+", " ", value).strip().casefold()

def extract(text: str) -> list[Extracted]:
    found: dict[tuple[str, str], Extracted] = {}
    clause_boundaries = [match.start() for match in CLAUSE_BOUNDARY_PATTERN.finditer(text)]
    bank_account_matches = list(BANK_ACCOUNT_PATTERN.finditer(text))
    bank_account_spans = [match.span(1) for match in bank_account_matches]
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            if kind == "phone" and any(start < match.end() and match.start() < end for start, end in bank_account_spans):
                # A labeled bank account can have phone-shaped digits; preserve the
                # financial identifier's stronger source context and avoid a duplicate phone.
                continue
            raw = match.group(0).strip()
            if kind == "upi_id" and "." in raw.rsplit("@", 1)[-1]:
                # Email and UPI syntax overlap. Domain-like suffixes are only retained as UPI
                # when the local part resembles a payment handle and isn't an email address.
                continue
            start, end = max(0, match.start() - 90), min(len(text), match.end() + 90)
            item = Extracted(kind, raw, normalize(kind, raw), text[start:end], match.start(), match.end())
            found[(kind, item.normalized)] = item
            if kind == "email":
                email_domain = raw.rpartition("@")[2]
                domain = Extracted("domain", email_domain, normalize("domain", email_domain), text[start:end], match.start(), match.end())
                found[("domain", domain.normalized)] = domain
            if kind == "url":
                host = urlsplit(raw).hostname
                if host:
                    try:
                        normalized_host = host.encode("idna").decode("ascii").lower()
                    except UnicodeError:
                        normalized_host = host.casefold()
                    domain = Extracted("domain", host, normalized_host, text[start:end], match.start(), match.end())
                    found[("domain", domain.normalized)] = domain
    for match in FEE_TERM_PATTERN.finditer(text):
        # Check only the containing sentence so unrelated payment language in
        # a neighboring sentence cannot turn a fee mention into a request.
        left, right = _clause_bounds(text, match.start(), clause_boundaries)
        sentence = text[left:right].strip()
        before, after = text[left:match.start()], text[match.end():right]
        if FEE_NEGATION_PATTERN.search(sentence):
            continue
        if not (FEE_PAYMENT_BEFORE_PATTERN.search(before) or FEE_REQUIREMENT_AFTER_PATTERN.search(after)):
            continue
        raw = sentence
        start = left + len(text[left:right]) - len(text[left:right].lstrip())
        end = start + len(raw)
        normalized = normalize("fee_request", raw)
        found[("fee_request", normalized)] = Extracted(
            "fee_request", raw, normalized, text[max(0, start - 90):min(len(text), end + 90)],
            start, end, 0.75,
            "Candidate extracted from explicit payment-request or payment-requirement wording; the request and its accuracy are unverified and require investigator review.",
        )
    for match in bank_account_matches:
        start, end = match.span(1)
        raw = match.group(1).strip()
        digit_count = len(re.sub(r"[^0-9]", "", raw))
        if not 9 <= digit_count <= 18:
            continue
        left, right = max(0, start - 90), min(len(text), end + 90)
        normalized = normalize("bank_account", raw)
        found[("bank_account", normalized)] = Extracted(
            "bank_account", raw, normalized, text[left:right], start, end, 0.85,
            "Digits were extracted after an explicit bank-account label; account ownership and any alleged use are unverified.",
        )
    for kind, pattern in LABELLED_CLAIMS.items():
        for match in pattern.finditer(text):
            original = match.group(1)
            leading = len(original) - len(original.lstrip())
            trailing = len(original) - len(original.rstrip())
            raw = _clean_claim(original)
            if not raw:
                continue
            start, end = match.span(1)
            start += leading
            end -= trailing
            left, right = max(0, start - 90), min(len(text), end + 90)
            normalized = normalize(kind, raw)
            found[(kind, normalized)] = Extracted(kind, raw, normalized, text[left:right], start, end, 0.75, "Explicitly labeled user-submitted claim; wording and truth are unverified.")
    for match in NARRATIVE_HIRING_PATTERN.finditer(text):
        for kind, group in (("job_title_claim", "role"), ("company_claim", "company")):
            original = match.group(group)
            leading = len(original) - len(original.lstrip())
            trailing = len(original) - len(original.rstrip())
            raw = _clean_claim(original).strip(" \t,:")
            if len(raw) < 2:
                continue
            start, end = match.span(group)
            start += leading
            end -= trailing
            # The capture may include trailing punctuation after trimming text;
            # keep source offsets exact if boundary cleanup removed characters.
            while start < end and text[start] in " \t,:":
                start += 1
            while end > start and text[end - 1] in " \t,:":
                end -= 1
            raw = text[start:end]
            left, right = max(0, start - 90), min(len(text), end + 90)
            normalized = normalize(kind, raw)
            found.setdefault(
                (kind, normalized),
                Extracted(
                    kind, raw, normalized, text[left:right], start, end, 0.55,
                    "Candidate inferred from a constrained hiring phrase; the wording, employer identity, and vacancy are unverified and require investigator review.",
                ),
            )
    for match in NARRATIVE_LOCATION_PATTERN.finditer(text):
        original = match.group("location")
        leading = len(original) - len(original.lstrip())
        trailing = len(original) - len(original.rstrip())
        start, end = match.span("location")
        start += leading
        end -= trailing
        while start < end and text[start] in " \t,:":
            start += 1
        while end > start and text[end - 1] in " \t,:.;!?":
            end -= 1
        raw = text[start:end]
        if not raw or normalize("location_claim", raw) in {"home", "remote", "hybrid", "anywhere"}:
            continue
        left, right = max(0, start - 90), min(len(text), end + 90)
        normalized = normalize("location_claim", raw)
        found.setdefault(
            ("location_claim", normalized),
            Extracted(
                "location_claim", raw, normalized, text[left:right], start, end, 0.55,
                "Candidate inferred from an explicit workplace/location phrase; the claimed location and job context are unverified and require investigator review.",
            ),
        )
    for match in DATE_PATTERN.finditer(text):
        raw = match.group(0).strip()
        start, end = match.span()
        left, right = max(0, start - 90), min(len(text), end + 90)
        found[("date_claim", normalize("date_claim", raw))] = Extracted(
            "date_claim", raw, normalize("date_claim", raw), text[left:right], start, end, 0.85,
            "Literal date shape; context and accuracy are unverified.",
        )
    for match in AMOUNT_PATTERN.finditer(text):
        raw = match.group(0).strip()
        start, end = match.span()
        left, right = max(0, start - 120), min(len(text), end + 120)
        context = text[left:right]
        context_start = left
        payment_matches = list(PAYMENT_AMOUNT_CONTEXT.finditer(context))
        compensation_matches = list(COMPENSATION_AMOUNT_CONTEXT.finditer(context))

        def distance(match: re.Match[str]) -> int:
            match_start, match_end = context_start + match.start(), context_start + match.end()
            return max(start - match_end, match_start - end, 0)

        payment_distance = min((distance(item) for item in payment_matches), default=None)
        compensation_distance = min((distance(item) for item in compensation_matches), default=None)
        if payment_distance is not None and (compensation_distance is None or payment_distance < compensation_distance):
            kind = "payment_amount_claim"
            uncertainty = "Currency amount occurs near explicit payment-request wording; the request, currency meaning, and accuracy are unverified."
        elif compensation_distance is not None and (payment_distance is None or compensation_distance < payment_distance):
            kind = "compensation_amount_claim"
            uncertainty = "Currency amount occurs near explicit compensation wording; the claimed compensation and currency meaning are unverified."
        else:
            # A number alone, or equally close competing contexts, cannot
            # establish whether it is a fee, salary, or unrelated amount.
            continue
        found[(kind, normalize(kind, raw))] = Extracted(
            kind, raw, normalize(kind, raw), context, start, end, 0.85, uncertainty,
        )
    return list(found.values())
