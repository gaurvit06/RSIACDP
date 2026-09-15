from sqlalchemy.orm import Session

from app.models.evidence import Evidence


EVIDENCE_WEIGHTS = {
    "strong": 3,
    "medium": 2,
    "weak": 1,
}

VERIFIED_SCAM_THRESHOLD = 6
SUSPICIOUS_THRESHOLD = 3


def calculate_evidence_score(
    db: Session,
    case_id: str
) -> dict:

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .all()
    )

    score = 0

    breakdown = {
        "strong": 0,
        "medium": 0,
        "weak": 0,
    }

    authoritative_count = 0

    for evidence in evidence_items:

        reliability = (
            evidence.reliability
            .lower()
            .strip()
        )

        if reliability in EVIDENCE_WEIGHTS:

            score += EVIDENCE_WEIGHTS[reliability]

            breakdown[reliability] += 1

        if evidence.authoritative:
            authoritative_count += 1

    return {
        "score": score,
        "breakdown": breakdown,
        "evidence_count": len(evidence_items),
        "authoritative_count": authoritative_count,
    }


def determine_verdict(
    score: int,
    evidence_count: int,
    authoritative_count: int
) -> str:

    if evidence_count == 0:
        return "Insufficient Evidence"

    if (
        score >= VERIFIED_SCAM_THRESHOLD
        and authoritative_count >= 1
    ):
        return "Verified Scam"

    if score >= SUSPICIOUS_THRESHOLD:
        return "Suspicious"

    return "Insufficient Evidence"


def generate_verdict_explanation(
    score: int,
    evidence_count: int,
    breakdown: dict,
    authoritative_count: int,
    verdict: str
) -> str:

    strong_count = breakdown.get("strong", 0)
    medium_count = breakdown.get("medium", 0)
    weak_count = breakdown.get("weak", 0)

    if verdict == "Verified Scam":

        return (
            f"The case has {evidence_count} evidence item(s) "
            f"with a total evidence score of {score}. "
            f"It contains {strong_count} strong, "
            f"{medium_count} medium, and {weak_count} weak "
            f"evidence item(s), including "
            f"{authoritative_count} authoritative evidence item(s). "
            f"The evidence threshold and authoritative evidence "
            f"requirement for a Verified Scam verdict have been reached."
        )

    if verdict == "Suspicious":

        return (
            f"The case has {evidence_count} evidence item(s) "
            f"with a total evidence score of {score}. "
            f"It contains {strong_count} strong, "
            f"{medium_count} medium, and {weak_count} weak "
            f"evidence item(s). "
            f"It has {authoritative_count} authoritative evidence "
            f"item(s). The available evidence shows suspicious "
            f"signals but does not satisfy the requirements "
            f"for a Verified Scam verdict."
        )

    return (
        f"The case has {evidence_count} evidence item(s) "
        f"with a total evidence score of {score}. "
        f"It contains {strong_count} strong, "
        f"{medium_count} medium, and {weak_count} weak "
        f"evidence item(s), including "
        f"{authoritative_count} authoritative evidence item(s). "
        f"The available evidence is not sufficient to "
        f"support a stronger verdict."
    )


def evaluate_case(
    db: Session,
    case_id: str
) -> dict:

    result = calculate_evidence_score(
        db=db,
        case_id=case_id
    )

    verdict = determine_verdict(
        score=result["score"],
        evidence_count=result["evidence_count"],
        authoritative_count=result["authoritative_count"]
    )

    explanation = generate_verdict_explanation(
        score=result["score"],
        evidence_count=result["evidence_count"],
        breakdown=result["breakdown"],
        authoritative_count=result["authoritative_count"],
        verdict=verdict
    )

    return {
        "case_id": str(case_id),
        "verdict": verdict,
        "score": result["score"],
        "evidence_count": result["evidence_count"],
        "authoritative_count": result["authoritative_count"],
        "breakdown": result["breakdown"],
        "explanation": explanation,
    }