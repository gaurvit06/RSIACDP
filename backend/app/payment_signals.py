"""Locate explicit recruitment-fee wording in the original material."""
import re
from collections.abc import Iterator
from itertools import chain


FEE = (r"(?:registration|application|processing|security|equipment|training|verification|"
       r"interview|onboarding|joining|placement|recruitment|background(?: check)?)\s+(?:fees?|deposit|charge)\b")
MONEY = r"(?:₹\s*|(?:INR|Rs\.?)\s*)[0-9][0-9,]*(?:\.[0-9]{1,2})?"
REQUIREMENT = r"(?:is\s+|will\s+be\s+)?(?:required|mandatory|payable|due|needed|must\s+be\s+paid)\b"
PAYMENT = re.compile(
    rf"\b{FEE}\s*[:=–-]\s*{MONEY}"
    rf"|\b{FEE}\s+(?:of\s+{MONEY}\s+)?{REQUIREMENT}"
    rf"|\b(?:pay|send|transfer|remit|submit)\s+(?:{MONEY}\s+(?:as|for)\s+)?"
    rf"(?:(?:a|an|the|your|refundable|non-refundable|one-time)\s+){{0,3}}{FEE}"
    rf"|\b(?:pay|transfer|send|remit)\s+{MONEY}\s+(?:before\s+(?:receiving\s+)?|to\s+(?:reserve|secure|release|receive)\s+)"
    rf"(?:(?:the|a|an|your)\s+)?(?:offer letter|appointment letter|joining slot|interview slot|job offer)\b",
    re.I,
)
BOUNDARY = re.compile(r"[!?\r\n;]|(?<![Rr][Ss])\.(?=\s|$)")
CAUTION = re.compile(
    r"\b(?:no|not|never|without|waiv\w*|optional|exempt\w*|avoid|beware|warning|for\s+example|"
    r"hypothetical|if|scammers?|fraudsters?|don't|do\s+not|won't|shouldn't|reimburs\w*|"
    r"(?:we|employer|company)\s+(?:(?:will|shall)\s+)?(?:pay|cover)s?|"
    r"employer[- ]paid|company[- ]paid|covered\s+by|paid\s+by\s+(?:the\s+)?(?:company|employer))\b",
    re.I,
)
ADVISORY_INTRO = re.compile(r"\b(?:warning|beware|example\s+of|watch\s+out\s+for|never\s+follow)\b", re.I)


def payment_spans(text: str) -> Iterator[tuple[int, int]]:
    start = 0
    previous = ""
    for end in chain(BOUNDARY.finditer(text), [None]):
        stop = end.start() if end else len(text)
        clause = text[start:stop]
        # Keep an advisory heading attached to a quotation on the following line.
        advisory = previous.rstrip().endswith(":") and ADVISORY_INTRO.search(previous)
        if not advisory and not CAUTION.search(clause) and text[stop:stop + 1] != "?":
            for match in PAYMENT.finditer(clause):
                amount = re.search(MONEY, match.group(), re.I)
                if amount and not re.search(r"[1-9]", amount.group()):
                    continue
                yield start + match.start(), start + match.end()
        if clause.strip():
            previous = clause
        start = stop + 1
