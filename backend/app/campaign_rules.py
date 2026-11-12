"""Versioned, deterministic signals for case-to-case investigative leads."""
from __future__ import annotations

import re
from urllib.parse import urlsplit


RULE_VERSION = "campaign-signals-v3"
SIGNAL_WEIGHTS = {"phone": 40, "email": 40, "upi_id": 40, "bank_account": 40, "url": 25, "domain": 15}
MATCHABLE_TYPES = frozenset(SIGNAL_WEIGHTS)


def rule_version(threshold: int) -> str:
    return f"{RULE_VERSION}-threshold-{threshold}"


def web_host(entity_type: str, normalized_value: str) -> str | None:
    if entity_type == "domain":
        return normalized_value.casefold().rstrip(".")
    if entity_type == "url":
        try:
            return urlsplit(normalized_value).hostname.casefold().rstrip(".")
        except (AttributeError, ValueError):
            return None
    return None


def score_matches(matches: set[tuple[str, str]]) -> tuple[int, list[str]]:
    """Score unique identifier signals; URL/domain forms of one host count once."""
    signals: dict[str, tuple[int, set[tuple[str, str]]]] = {}
    for entity_type, normalized_value in matches:
        weight = SIGNAL_WEIGHTS.get(entity_type)
        if weight is None:
            continue
        host = web_host(entity_type, normalized_value)
        signal_key = f"web:{host}" if host else f"{entity_type}:{normalized_value}"
        current_weight, members = signals.get(signal_key, (0, set()))
        members.add((entity_type, normalized_value))
        signals[signal_key] = (max(current_weight, weight), members)
    strength = min(100, sum(weight for weight, _ in signals.values()))
    explanations = []
    for signal_key, (weight, members) in signals.items():
        if signal_key.startswith("web:"):
            types = ", ".join(sorted({kind for kind, _ in members}))
            explanations.append(f"Shared web host {signal_key.removeprefix('web:')} via {types} (weight {weight})")
        else:
            kind, value = next(iter(members))
            explanations.append(f"Exact {kind} match: {value} (weight {weight})")
    return strength, sorted(explanations)


def link_state(strength: int, threshold: int) -> str:
    return "proposed" if strength >= threshold else "low_signal"


def redact_link_reason(reason: str) -> str:
    """Keep investigative signal type/weight while masking embedded identifiers and hosts."""
    exact = re.fullmatch(r"Exact ([a-z_]+) match: .+ \(weight (\d+)\)", reason)
    if exact:
        entity_type, weight = exact.groups()
        if entity_type in SIGNAL_WEIGHTS:
            return f"Exact {entity_type} match: [identifier masked] (weight {weight})"
        return f"Exact identifier match: [identifier masked] (weight {weight})"

    web = re.fullmatch(r"Shared web host .+ via ([a-z_, ]+) \(weight (\d+)\)", reason)
    if web:
        entity_types, weight = web.groups()
        kinds = [kind.strip() for kind in entity_types.split(",")]
        if kinds and all(kind in {"url", "domain"} for kind in kinds):
            return f"Shared web host [host masked] via {', '.join(kinds)} (weight {weight})"

    return "Campaign link details masked"
