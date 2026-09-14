from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.campaign import Campaign
from app.models.campaign_case import CampaignCase

from app.models.case_phone import CasePhone
from app.models.phone import Phone

from app.models.case_email import CaseEmail
from app.models.email import Email

from app.models.case_domain import CaseDomain
from app.models.domain import Domain

from app.models.case_upi import CaseUPI
from app.models.upi import UPI

from app.services.investigation_graph import (
    build_investigation_graph,
    find_connected_case_groups,
)

from app.services.verdict_engine import evaluate_case


def build_investigation_report(
    db: Session,
    case_id: str,
) -> dict:
    """
    Build a complete investigation report for one case.

    The report combines:
    - Case information
    - Extracted entities
    - Evidence and provenance
    - Connected cases
    - Campaign information
    - Deterministic verdict
    """

    # ---------------------------------------------------------
    # 1. Find the case
    # ---------------------------------------------------------

    case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if case is None:
        raise ValueError("Case not found")


    # ---------------------------------------------------------
    # 2. Collect entities
    # ---------------------------------------------------------

    entities = []


    phone_results = (
        db.query(Phone)
        .join(
            CasePhone,
            CasePhone.phone_id == Phone.id
        )
        .filter(
            CasePhone.case_id == case_id
        )
        .all()
    )

    for phone in phone_results:
        entities.append(
            {
                "entity_type": "phone",
                "value": phone.normalized_number,
            }
        )


    email_results = (
        db.query(Email)
        .join(
            CaseEmail,
            CaseEmail.email_id == Email.id
        )
        .filter(
            CaseEmail.case_id == case_id
        )
        .all()
    )

    for email in email_results:
        entities.append(
            {
                "entity_type": "email",
                "value": email.normalized_address,
            }
        )


    domain_results = (
        db.query(Domain)
        .join(
            CaseDomain,
            CaseDomain.domain_id == Domain.id
        )
        .filter(
            CaseDomain.case_id == case_id
        )
        .all()
    )

    for domain in domain_results:
        entities.append(
            {
                "entity_type": "domain",
                "value": domain.normalized_domain,
            }
        )


    upi_results = (
        db.query(UPI)
        .join(
            CaseUPI,
            CaseUPI.upi_id == UPI.id
        )
        .filter(
            CaseUPI.case_id == case_id
        )
        .all()
    )

    for upi in upi_results:
        entities.append(
            {
                "entity_type": "upi",
                "value": upi.normalized_upi,
            }
        )


    # ---------------------------------------------------------
    # 3. Collect evidence
    # ---------------------------------------------------------

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.case_id == case_id
        )
        .order_by(
            Evidence.retrieved_at.desc()
        )
        .all()
    )


    # ---------------------------------------------------------
    # 4. Find connected cases
    # ---------------------------------------------------------

    graph = build_investigation_graph(db)

    connected_case_ids = []

    case_groups = find_connected_case_groups(graph)

    for group in case_groups:

        if str(case_id) in group:

            connected_case_ids = [
                case_id_value
                for case_id_value in group
                if case_id_value != str(case_id)
            ]

            break


    # ---------------------------------------------------------
    # 5. Find campaigns containing this case
    # ---------------------------------------------------------

    campaign_links = (
        db.query(Campaign)
        .join(
            CampaignCase,
            CampaignCase.campaign_id == Campaign.id
        )
        .filter(
            CampaignCase.case_id == case_id
        )
        .all()
    )


    # ---------------------------------------------------------
    # 6. Calculate deterministic verdict
    # ---------------------------------------------------------

    verdict_result = evaluate_case(
        db=db,
        case_id=case_id,
    )


    # ---------------------------------------------------------
    # 7. Build final report
    # ---------------------------------------------------------

    return {
        "case_id": case.id,
        "input_type": case.input_type,
        "status": case.status,

        "entities": entities,

        "evidence": evidence,

        "connected_case_ids": connected_case_ids,

        "campaigns": campaign_links,

        "verdict": verdict_result["verdict"],
        "score": verdict_result["score"],
        "explanation": verdict_result["explanation"],
    }