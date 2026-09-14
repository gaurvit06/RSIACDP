from backend.investigation.investigation import investigate_case


def suspicious_payload():
    return {
        "case_id": "TEST-001",
        "source_type": "text",
        "text": (
            "Congratulations. Selected for Software Developer at Infosys. "
            "Pay ₹2500 registration fee immediately to rahuljobs@upi."
        ),
        "entities": {
            "companies": ["Infosys"],
            "recruiters": ["Rahul"],
            "phones": ["+919876543210"],
            "emails": ["infosys.jobs@gmail.com"],
            "upi_ids": ["rahuljobs@upi"],
            "domains": ["infosys-careers-example.com"],
            "amounts": ["₹2500"],
            "job_roles": ["Software Developer"],
        },
    }


def legitimate_like_payload():
    return {
        "case_id": "TEST-002",
        "source_type": "text",
        "text": "Software Engineer opportunity at Infosys. Apply using the official careers site.",
        "entities": {
            "companies": ["Infosys"],
            "recruiters": [],
            "phones": [],
            "emails": ["careers@infosys.com"],
            "upi_ids": [],
            "domains": ["infosys.com"],
            "amounts": [],
            "job_roles": ["Software Engineer"],
        },
    }


def test_suspicious_case_is_high_risk():
    result = investigate_case(suspicious_payload())
    codes = {item["code"] for item in result["evidence"]}

    assert result["risk"]["verdict"] == "HIGH RISK"
    assert result["risk"]["score"] == 100
    assert "PAYMENT_REQUEST" in codes
    assert "FREE_EMAIL_PROVIDER" in codes
    assert "EMAIL_DOMAIN_MISMATCH" in codes
    assert "DOMAIN_MISMATCH" in codes


def test_reference_domain_case_is_low_risk():
    result = investigate_case(legitimate_like_payload())

    assert result["risk"]["verdict"] == "LOW RISK"
    assert result["risk"]["score"] == 0
    assert result["evidence"] == []
