"""Human-readable rendering for already-redacted investigation reports."""
from __future__ import annotations

import re


_MARKDOWN_SPECIALS = re.compile(r"([\\`*_{}\[\]()#!|])")


def _text(value: object) -> str:
    """Escape inline user/source text so it cannot add report sections or links."""
    value = str(value).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    escaped = _MARKDOWN_SPECIALS.sub(r"\\\1", value).replace("<", "‹").replace(">", "›")
    # Keep GFM-style bare-URL autolinking from turning source text into links.
    return escaped.replace("://", "&#58;&#47;&#47;")


def _values(value: object) -> str:
    if isinstance(value, dict):
        return "; ".join(f"{_text(key)}: {_text(item)}" for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_text(item) for item in value)
    return _text(value)


def render_markdown_report(document: dict) -> str:
    lines = [
        "# Recruitment Scam Investigation Report",
        "",
        "> Investigative report. Repeated identifiers and campaign links are leads, not proof of wrongdoing. "
        "A missing, empty, unavailable, or failed check is not proof of fraud or legitimacy.",
        "",
        "## Case scope",
        "",
        f"- **Case reference:** {_text(document.get('case_ref', 'Unavailable'))}",
        f"- **Title:** {_text(document.get('title', 'Unavailable'))}",
        f"- **System assessment:** {_text(document.get('assessment', 'Insufficient evidence'))}",
        f"- **Submitted:** {_text(document.get('created_at', 'Unavailable'))}",
        f"- **Report generated:** {_text(document.get('generated_at', 'Unavailable'))}",
        f"- **Consent:** {_values(document.get('consent', {}))}",
        "",
        "## Evidence summary",
        "",
    ]
    summary = document.get("evidence_summary", {})
    lines.append(f"- **Total records:** {_text(summary.get('total', 0))}")
    for outcome, count in sorted(summary.get("by_outcome", {}).items()):
        lines.append(f"- **Outcome · {_text(outcome)}:** {_text(count)}")
    for status, count in sorted(summary.get("by_review_status", {}).items()):
        lines.append(f"- **Review · {_text(status)}:** {_text(count)}")

    lines.extend(["", "## Extracted identifiers and claims", ""])
    entities = document.get("entities", [])
    if not entities:
        lines.append("No candidate entities were recorded.")
    for entity in entities:
        lines.append(
            f"- **{_text(entity.get('type', 'unknown'))}:** {_text(entity.get('value', '[redacted]'))}; "
            f"review {_text(entity.get('review_status', 'unknown'))}; "
            f"source {_text(entity.get('source_location', 'not recorded'))}; "
            f"characters {_text(entity.get('source_start_char', 'n/a'))}–{_text(entity.get('source_end_char', 'n/a'))}; "
            f"parser confidence {_text(entity.get('extraction_confidence', 'n/a'))}; "
            f"{_text(entity.get('extraction_uncertainty', 'uncertainty not recorded'))}"
        )

    lines.extend(["", "## Evidence records", ""])
    evidence = document.get("evidence", [])
    if not evidence:
        lines.append("No evidence records were recorded.")
    for item in evidence:
        lines.extend([
            f"### Evidence #{_text(item.get('id', 'unknown'))}",
            "",
            f"- **Source:** {_text(item.get('source_name', '[source name restricted for privacy]'))} ({_text(item.get('source_type', 'unknown'))})",
            f"- **Reference:** {_text(item.get('source_ref', '[reference restricted for privacy]'))}",
            f"- **Outcome / authority:** {_text(item.get('outcome', 'unknown'))} / {_text(item.get('authority', 'unknown'))}",
            f"- **Retrieved:** {_text(item.get('retrieved_at', 'not recorded'))}",
            f"- **Review:** {_text(item.get('review_status', 'unknown'))}; {_text(item.get('review_reason', '[review rationale restricted for privacy]'))}",
            f"- **Claim:** {_text(item.get('claim', '[source claim restricted for privacy]'))}",
            f"- **Excerpt:** {_text(item.get('excerpt', '[source excerpt restricted for privacy]'))}",
            "",
        ])

    lines.extend(["## Machine findings", ""])
    findings = document.get("machine_findings", [])
    if not findings:
        lines.append("No active machine findings were recorded.")
    for finding in findings:
        lines.extend([
            f"### {_text(finding.get('assessment', 'Insufficient evidence'))} · {_text(finding.get('scope', 'unknown scope'))}",
            "",
            f"- **Claim:** {_text(finding.get('claim', '[claim restricted for privacy]'))}",
            f"- **Observation:** {_text(finding.get('observation', 'No observation recorded'))}",
            f"- **Rule:** {_text(finding.get('rule_name', 'unknown'))} / {_text(finding.get('rule_version', 'unknown'))}",
            f"- **Evidence records:** {_values(finding.get('evidence_ids', [])) or 'none'}; supporting {_values(finding.get('supporting_evidence_ids', [])) or 'none'}; conflicting {_values(finding.get('conflict_evidence_ids', [])) or 'none'}; awaiting review {_values(finding.get('unreviewed_evidence_ids', [])) or 'none'}",
            f"- **Limitations:** {_text(finding.get('limitations', 'Limitations were not recorded'))}",
            "",
        ])
        for snapshot in finding.get("evidence_snapshot", []):
            lines.append(
                f"  - Evidence #{_text(snapshot.get('evidence_id', 'unknown'))}: "
                f"{_text(snapshot.get('source_name', '[source name restricted for privacy]'))}; "
                f"{_text(snapshot.get('outcome', 'unknown'))}; retrieved {_text(snapshot.get('retrieved_at', 'not recorded'))}; "
                f"{_text(snapshot.get('source_ref', '[reference restricted for privacy]'))}"
            )
        lines.append("")

    lines.extend(["## Finding history", ""])
    history = document.get("finding_history", [])
    if not history:
        lines.append("No prior or superseded findings were recorded.")
    for finding in history:
        state = "active" if finding.get("active") else "superseded"
        lines.append(
            f"- **{_text(state)} · {_text(finding.get('assessment', 'Insufficient evidence'))}**; "
            f"claim {_text(finding.get('claim', '[claim restricted for privacy]'))}; "
            f"rule {_text(finding.get('rule_name', 'unknown'))}/{_text(finding.get('rule_version', 'unknown'))}; "
            f"recorded {_text(finding.get('created_at', 'not recorded'))}; "
            f"superseded {_text(finding.get('superseded_at') or 'not superseded')}"
        )

    lines.extend([
        "## Campaign links",
        "",
        _text(document.get("campaign_link_note", "Campaign connections are investigative leads, not determinations of wrongdoing.")),
        "",
    ])
    links = document.get("campaign_links", [])
    if not links:
        lines.append("No campaign links were recorded.")
    for link in links:
        lines.append(
            f"- Cases {_text(link.get('left_case_id', '?'))} ↔ {_text(link.get('right_case_id', '?'))}; "
            f"strength {_text(link.get('strength', 'n/a'))}/100; {_text(link.get('review_status', 'unknown'))}; "
            f"rule {_text(link.get('rule_version', 'unknown'))}; reasons: {_values(link.get('reasons', []))}"
        )

    lines.extend(["", "## Human investigator dispositions", ""])
    dispositions = document.get("human_dispositions", [])
    if not dispositions:
        lines.append("No human dispositions were recorded.")
    for item in dispositions:
        lines.append(
            f"- **{_text(item.get('display_label', item.get('disposition', 'unknown')))}** · "
            f"status {_text(item.get('status', 'unknown'))}; evidence {_values(item.get('evidence_ids', [])) or 'none'}; "
            f"rationale {_text(item.get('rationale', '[review rationale restricted for privacy]'))}; "
            f"recorded {_text(item.get('created_at', 'not recorded'))}; reviewed {_text(item.get('reviewed_at', 'not reviewed'))}"
        )

    lines.extend(["", "## Audit timeline", ""])
    timeline = document.get("timeline", [])
    if not timeline:
        lines.append("No audit events were recorded.")
    for event in timeline:
        lines.append(
            f"- {_text(event.get('occurred_at', 'time not recorded'))} — "
            f"{_text(event.get('action', 'event'))} ({_text(event.get('actor_type', 'unknown actor'))}); "
            f"details: {_values(event.get('details', {}))}"
        )

    lines.extend([
        "",
        "## Rule versions and limitations",
        "",
        f"- **Rule versions:** {_values(document.get('rule_versions', [])) or 'none'}",
        f"- **Limitations:** {_text(document.get('limitations', 'No limitations were recorded'))}",
        "",
        "This report separates observed evidence, source claims, deterministic system findings, and human review actions. "
        "The platform does not determine that a person or organization committed wrongdoing.",
        "",
    ])
    return "\n".join(lines)
