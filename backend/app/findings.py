"""Reproducible, source-traceable case assessments. These rules never infer guilt."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .campaign_rules import MATCHABLE_TYPES
from .models import Case, Entity, Evidence, SystemFinding
from .payment_signals import payment_spans
from .vacancy_verification import vacancy_decisions

RULE_NAME = "exact-source-evidence-v1"
RULE_VERSION = "case-evidence-v3"
PAYMENT_RULE = "submitted-recruitment-fee-v1"
LIMITATIONS = (
    "This assessment concerns only the extracted claim and evidence listed here. "
    "An exact source match does not establish wrongdoing. Empty, unavailable, failed, "
    "or unreviewed checks are not adverse evidence. Conflicting source statements are "
    "not adjudicated automatically and must be compared by an investigator."
)


def entity_fingerprint(entity: Entity) -> str:
    material = f"{entity.entity_type}:{entity.normalized_value}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def evidence_for_entity(entity: Entity, evidence: list[Evidence]) -> list[Evidence]:
    fingerprint = entity_fingerprint(entity)
    matches = []
    for item in evidence:
        details = item.details or {}
        by_fingerprint = details.get("entity_fingerprint") == fingerprint
        by_value = details.get("matched_entity_type") == entity.entity_type and details.get("matched_normalized_value") == entity.normalized_value
        if by_fingerprint or by_value:
            matches.append(item)
    return matches


def _is_authoritative_result(item: Evidence) -> bool:
    details = item.details or {}
    category = details.get("source_category")
    authority_category = {
        "government": {"government"},
        "platform_action": {"platform"},
        "authoritative_source": {"government", "platform", "company_official"},
    }
    return bool(
        item.outcome == "result"
        and item.review_status == "relevant"
        and item.authority in authority_category
        and category in authority_category[item.authority]
        and details.get("source_record_ref")
        and item.source_name.strip()
        and item.excerpt.strip()
    )


def _entity_decision(entity: Entity, evidence: list[Evidence]) -> dict:
    related = evidence_for_entity(entity, evidence)
    evidence_ids = [item.id for item in related]
    withdrawn_source_evidence = [item for item in related if (item.details or {}).get("source_record_withdrawn") is True]
    unreviewed_ids = sorted({
        item.id for item in related
        if item.review_status == "needs_review"
        or ((item.details or {}).get("source_record_withdrawn") is True and item.review_status != "irrelevant")
    })
    if entity.review_status == "rejected":
        return {
            "entity_id": entity.id,
            "claim": f"Candidate {entity.entity_type} extraction",
            "assessment": "Insufficient evidence",
            "observation": "This candidate extraction was rejected by an investigator and is excluded from machine assessment.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [],
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": unreviewed_ids,
        }
    if entity.review_status != "confirmed":
        return {
            "entity_id": entity.id,
            "claim": f"Candidate {entity.entity_type} extraction",
            "assessment": "Insufficient evidence",
            "observation": "The extracted candidate has not been confirmed by an investigator; no source-based assessment is made.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [],
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": unreviewed_ids,
        }

    relevant_results = [
        item for item in related
        if item.outcome == "result" and item.review_status == "relevant"
        and (item.details or {}).get("source_record_withdrawn") is not True
    ]
    conflicts = [
        item for item in related
        if item.review_status == "contradicts"
        and (item.details or {}).get("source_record_withdrawn") is not True
    ]
    if conflicts:
        return {
            "entity_id": entity.id,
            "claim": f"Evidence assessment for this {entity.entity_type} identifier",
            "assessment": "Insufficient evidence",
            "observation": "An investigator marked one or more source records as contradicting this claim. The system does not resolve the conflict; compare the cited sources.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [item.id for item in relevant_results],
            "conflict_evidence_ids": [item.id for item in conflicts],
            "unreviewed_evidence_ids": unreviewed_ids,
        }

    unresolved_withdrawn_source_evidence = [item for item in withdrawn_source_evidence if item.review_status != "irrelevant"]
    if unresolved_withdrawn_source_evidence and not any(
        item.outcome == "result" and item.review_status == "relevant"
        and (item.details or {}).get("source_record_withdrawn") is not True
        for item in related
    ):
        return {
            "entity_id": entity.id,
            "claim": f"Evidence assessment for this {entity.entity_type} identifier",
            "assessment": "Insufficient evidence",
            "observation": "A curated source record used by an earlier check was withdrawn. Its support no longer meets a current finding rule and requires investigator review.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [],
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": unreviewed_ids,
        }
    authoritative = [item for item in relevant_results if _is_authoritative_result(item)]
    if authoritative:
        chosen = sorted(authoritative, key=lambda item: (item.retrieved_at, item.id))
        return {
            "entity_id": entity.id,
            "claim": f"Whether an authoritative source contains a record for this {entity.entity_type} identifier",
            "assessment": "Confirmed by an authoritative source",
            "observation": "A relevant, investigator-reviewed source record contains an exact identifier match. The source's stated claim and reference are shown in the linked evidence record.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [item.id for item in chosen],
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": unreviewed_ids,
        }

    public_reports = [item for item in relevant_results if item.authority == "unverified_public_report"]
    if public_reports:
        return {
            "entity_id": entity.id,
            "claim": f"Whether a source-labeled unverified public report mentions this {entity.entity_type} identifier",
            "assessment": "Evidence supports concern",
            "observation": "A relevant source-labeled unverified public report contains an exact identifier match. This is an allegation or report, not a verified finding.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": [item.id for item in public_reports],
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": unreviewed_ids,
        }

    outcomes = [item.outcome for item in related]
    if (
        entity.entity_type in MATCHABLE_TYPES
        and related
        and all(
            item.source_type == "curated_local_corpus"
            and item.outcome == "no_result"
            and (item.details or {}).get("source_record_withdrawn") is not True
            for item in related
        )
    ):
        return {
            "entity_id": entity.id,
            "claim": f"Whether the configured local corpus contains an adverse record for this {entity.entity_type} identifier",
            "assessment": "No adverse evidence found",
            "observation": "No matching record was found in the configured local evidence corpus for this confirmed identifier.",
            "evidence_ids": evidence_ids,
            "supporting_evidence_ids": evidence_ids,
            "conflict_evidence_ids": [],
            "unreviewed_evidence_ids": [],
        }

    if not related:
        observation = "No completed source check is linked to this entity; this is not a negative result."
    elif any(item.outcome in {"unavailable", "error", "not_checked"} for item in related):
        observation = "One or more source checks were unavailable, failed, or not checked; no negative inference is made."
    elif any(item.outcome == "result" and item.review_status != "relevant" for item in related):
        observation = "A source returned a result, but an investigator has not marked it relevant; no adverse assessment is made."
    else:
        observation = "Available evidence does not meet a rule for a stronger assessment."
    return {
        "entity_id": entity.id,
        "claim": f"Evidence assessment for this {entity.entity_type} identifier",
        "assessment": "Insufficient evidence",
        "observation": observation,
        "evidence_ids": evidence_ids,
        "supporting_evidence_ids": [item.id for item in relevant_results],
        "conflict_evidence_ids": [],
        "unreviewed_evidence_ids": unreviewed_ids,
    }


def _fee_entity_span(entity: Entity, material: str) -> tuple[int, int] | None:
    start, end = entity.source_start_char, entity.source_end_char
    if start is None or end is None:
        return None
    # Text, images and PDF page one use offsets from the start of this material.
    if not entity.source_location.startswith("pdf_page_") or entity.source_location.split("_")[2] == "1":
        return start, end
    # Later PDF pages have page-relative offsets. Only align unique original text.
    excerpt, value = entity.source_excerpt, entity.raw_value
    if excerpt and value and material.count(excerpt) == 1 and excerpt.count(value) == 1:
        start = material.index(excerpt) + excerpt.index(value)
        return start, start + len(value)
    return None


def _submitted_payment_decision(material: str, entities: list[Entity], evidence: list[Evidence]) -> dict | None:
    original = next((item for item in evidence if item.source_type in {"submitted_material", "uploaded_file"}
                     and item.authority == "user_submitted" and item.outcome == "result"
                     and item.review_status in {"unreviewed", "relevant"}), None)
    if not original or not material:
        return None
    candidates = [(entity, _fee_entity_span(entity, material)) for entity in entities
                  if entity.entity_type in {"fee_request", "payment_amount_claim"}]
    for start, end in payment_spans(material):
        anchors = [(entity, span) for entity, span in candidates if span and span[0] < end and start < span[1]]
        if not anchors or any(entity.review_status == "rejected" or material[s:e] != entity.raw_value
                              for entity, (s, e) in anchors):
            continue
        entity = anchors[0][0]
        return {
            "scope": "material", "entity_id": entity.id, "rule": PAYMENT_RULE,
            "claim": "The submitted offer lists a recruitment fee or requests payment in connection with hiring.",
            "assessment": "Evidence supports concern",
            "observation": f"The submitted material contains recruitment-payment wording at characters {start}–{end} "
                           f"of the extracted text (evidence #{original.id}). Verify the request with the employer through an independent channel.",
            "limitations": "This observation concerns the wording in the submitted copy. The sender, authenticity of the vacancy and any payment remain unverified.",
            "evidence_ids": [original.id], "supporting_evidence_ids": [original.id],
            "conflict_evidence_ids": [], "unreviewed_evidence_ids": [],
        }
    return None


def assess_case(entities: list[Entity], evidence: list[Evidence], material: str = "") -> tuple[list[dict], str]:
    decisions = [_entity_decision(entity, evidence) for entity in entities]
    included = [item for item, entity in zip(decisions, entities) if entity.review_status != "rejected"]
    vacancies = list(vacancy_decisions(entities, evidence))
    decisions.extend(vacancies)
    included.extend(vacancies)
    payment = _submitted_payment_decision(material, entities, evidence)
    if payment:
        decisions.append(payment)
        included.append(payment)
    if not included:
        return decisions, "Insufficient evidence"
    if any(item["conflict_evidence_ids"] for item in included):
        overall = "Insufficient evidence"
    elif vacancies and any(item["assessment"] == "Evidence supports concern" for item in included):
        overall = "Evidence supports concern"
    elif any(item["assessment"] == "Confirmed by an authoritative source" for item in included):
        overall = "Confirmed by an authoritative source"
    elif any(item["assessment"] == "Evidence supports concern" for item in included):
        overall = "Evidence supports concern"
    elif (
        entities
        and all(entity.review_status == "confirmed" and entity.entity_type in MATCHABLE_TYPES for entity in entities)
        and all(item["assessment"] == "No adverse evidence found" for item in included)
    ):
        overall = "No adverse evidence found"
    else:
        overall = "Insufficient evidence"
    return decisions, overall


def rebuild_system_findings(db: Session, case: Case) -> list[SystemFinding]:
    """Supersede the old snapshot and persist a deterministic current assessment."""
    now = datetime.now(timezone.utc)
    old = db.scalars(select(SystemFinding).where(SystemFinding.case_id == case.id, SystemFinding.active.is_(True))).all()
    for finding in old:
        finding.active = False
        finding.superseded_at = now
    entities = db.scalars(select(Entity).where(Entity.case_id == case.id).order_by(Entity.id)).all()
    evidence = db.scalars(select(Evidence).where(Evidence.case_id == case.id).order_by(Evidence.id)).all()
    decisions, overall = assess_case(entities, evidence, case.submitted_text or "")
    findings = []
    evidence_by_id = {item.id: item for item in evidence}
    for decision in decisions:
        snapshot = []
        for evidence_id in decision["evidence_ids"]:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                continue
            details = item.details or {}
            snapshot.append({
                "evidence_id": item.id,
                "source_name": item.source_name,
                "source_type": item.source_type,
                "source_ref": details.get("source_record_ref") or item.source_ref,
                "claim": item.claim,
                "outcome": item.outcome,
                "authority": item.authority,
                "retrieved_at": item.retrieved_at.isoformat(),
            })
        findings.append(SystemFinding(
            case_id=case.id,
            entity_id=decision["entity_id"],
            scope=decision.get("scope", "entity"),
            claim=decision["claim"],
            assessment=decision["assessment"],
            observation=decision["observation"],
            evidence_ids=decision["evidence_ids"],
            supporting_evidence_ids=decision["supporting_evidence_ids"],
            evidence_snapshot=snapshot,
            conflict_evidence_ids=decision["conflict_evidence_ids"],
            unreviewed_evidence_ids=decision["unreviewed_evidence_ids"],
            rule_name=decision.get("rule", RULE_NAME),
            rule_version=decision.get("rule", RULE_NAME),
            limitations=decision.get("limitations", LIMITATIONS),
            active=True,
            created_at=now,
        ))
    overall_evidence_ids = sorted({evidence_id for decision in decisions for evidence_id in decision["evidence_ids"]})
    payment = next((item for item in decisions if item.get("scope") == "material"), None)
    if any(item["conflict_evidence_ids"] for item in decisions):
        explanation = "The sources conflict. Inspect the evidence marked as contradicting before resolving this case."
    elif overall == "Evidence supports concern" and payment:
        explanation = payment["observation"] + " " + payment["limitations"]
    elif overall != "Insufficient evidence":
        explanation = next(item["observation"] for item in decisions if item["assessment"] == overall)
    elif any(item.outcome == "result" and item.source_type == "curated_local_corpus" and item.review_status == "unreviewed" for item in evidence):
        explanation = "A local source matched. Review its claim and relevance, and confirm the extracted identifier against the submission."
    elif any(item.outcome in {"error", "unavailable", "not_checked"} for item in evidence):
        explanation = "Some checks failed or are incomplete. Inspect their outcomes and add an independently verifiable source for the claim."
    else:
        explanation = "The current evidence does not establish a supported concern or verify the vacancy. Review the extracted claims and add a traceable source if available."
    findings.append(SystemFinding(
        case_id=case.id,
        entity_id=None,
        scope="case",
        claim="Overall assessment of the submitted material and source records",
        assessment=overall,
        observation=explanation,
        evidence_ids=overall_evidence_ids,
        supporting_evidence_ids=sorted({evidence_id for finding in findings for evidence_id in finding.supporting_evidence_ids}),
        evidence_snapshot=[snapshot for finding in findings for snapshot in finding.evidence_snapshot],
        conflict_evidence_ids=sorted({evidence_id for decision in decisions for evidence_id in decision["conflict_evidence_ids"]}),
        unreviewed_evidence_ids=sorted({evidence_id for decision in decisions for evidence_id in decision["unreviewed_evidence_ids"]}),
        rule_name="case-evidence",
        rule_version=RULE_VERSION,
        limitations=LIMITATIONS,
        active=True,
        created_at=now,
    ))
    db.add_all(findings)
    case.assessment = overall
    db.flush()
    return findings
