from sqlalchemy.orm import Session

from app.models.evidence import Evidence


# Evidence weights
EVIDENCE_WEIGHTS = {
    "strong": 3,
    "medium": 2,
    "weak": 1,
}


# Verdict thresholds
VERIFIED_SCAM_THRESHOLD = 6
SUSPICIOUS_THRESHOLD = 3


def calculate_evidence_score(
    db: Session,
    case_id: str,
) -> dict:
    """
    Calculate a deterministic evidence score for a case.

    Strong evidence = 3 points
    Medium evidence = 2 points
    Weak evidence = 1 point

    The score is based only on stored evidence.
    It does not depend on an LLM decision.
    """

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

    for evidence in evidence_items:

        reliability = evidence.reliability.lower().strip()

        if reliability in EVIDENCE_WEIGHTS:

            score += EVIDENCE_WEIGHTS[reliability]
            breakdown[reliability] += 1

    return {
        "score": score,
        "breakdown": breakdown,
        "evidence_count": len(evidence_items),
    }


def determine_verdict(
    score: int,
    evidence_count: int,
) -> str:
    """
    Determine the final case verdict.

    The system avoids making a strong accusation
    when there is insufficient evidence.
    """

    if evidence_count == 0:
        return "Insufficient Evidence"

    if score >= VERIFIED_SCAM_THRESHOLD:
        return "Verified Scam"

    if score >= SUSPICIOUS_THRESHOLD:
        return "Suspicious"

    return "Insufficient Evidence"


def generate_verdict_explanation(
    score: int,
    evidence_count: int,
    breakdown: dict,
    verdict: str,
) -> str:
    """
    Generate a deterministic human-readable explanation.
    """

    strong_count = breakdown.get("strong", 0)
    medium_count = breakdown.get("medium", 0)
    weak_count = breakdown.get("weak", 0)

    if verdict == "Verified Scam":
        return (
            f"The case has {evidence_count} evidence item(s) "
            f"with a total evidence score of {score}. "
            f"It contains {strong_count} strong, "
            f"{medium_count} medium, and {weak_count} weak "
            f"evidence item(s). The evidence threshold for "
            f"a Verified Scam verdict has been reached."
        )

    if verdict == "Suspicious":
        return (
            f"The case has {evidence_count} evidence item(s) "
            f"with a total evidence score of {score}. "
            f"It contains {strong_count} strong, "
            f"{medium_count} medium, and {weak_count} weak "
            f"evidence item(s). The available evidence shows "
            f"suspicious signals but does not reach the "
            f"Verified Scam threshold."
        )

    return (
        f"The case has {evidence_count} evidence item(s) "
        f"with a total evidence score of {score}. "
        f"The available evidence is not sufficient to "
        f"support a stronger verdict."
    )


def evaluate_case(
    db: Session,
    case_id: str,
) -> dict:
    """
    Complete deterministic case evaluation.

    Steps:
    1. Collect evidence
    2. Calculate evidence score
    3. Determine verdict
    4. Generate explanation
    """

    result = calculate_evidence_score(
        db=db,
        case_id=case_id,
    )

    verdict = determine_verdict(
        score=result["score"],
        evidence_count=result["evidence_count"],
    )

    explanation = generate_verdict_explanation(
        score=result["score"],
        evidence_count=result["evidence_count"],
        breakdown=result["breakdown"],
        verdict=verdict,
    )

    return {
        "case_id": str(case_id),
        "verdict": verdict,
        "score": result["score"],
        "evidence_count": result["evidence_count"],
        "breakdown": result["breakdown"],
        "explanation": explanation,
    }