def calculate_risk(evidence):
    score = min(sum(item.get("weight", 0) for item in evidence), 100)

    if score >= 60:
        verdict = "HIGH RISK"
    elif score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "LOW RISK"

    if evidence:
        codes = ", ".join(item["code"] for item in evidence)
        explanation = (
            f"The prototype assigned {score}/100 based on these triggered evidence rules: "
            f"{codes}. This is a risk assessment, not a legal determination that the recruiter "
            f"or job is fraudulent."
        )
    else:
        explanation = (
            "No current prototype risk rule was triggered. LOW RISK does not prove that the "
            "job is genuine; it only means the available prototype checks found no configured "
            "risk indicators."
        )

    return {
        "score": score,
        "verdict": verdict,
        "explanation": explanation,
    }
