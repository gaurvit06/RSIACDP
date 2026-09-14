from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.campaign_case import CampaignCase

from app.models.case_phone import CasePhone
from app.models.case_email import CaseEmail
from app.models.case_domain import CaseDomain
from app.models.case_upi import CaseUPI

from app.services.investigation_graph import (
    build_investigation_graph,
    find_connected_case_groups,
)


# Weight assigned to each shared entity type.
# This measures campaign connection strength,
# not proof that the campaign is fraudulent.
ENTITY_WEIGHTS = {
    "phone": 0.30,
    "email": 0.25,
    "domain": 0.25,
    "upi": 0.20,
}


def calculate_campaign_confidence(
    db: Session,
    case_ids: list[str],
) -> float:
    """
    Calculate deterministic campaign-connection confidence.

    The score is based on distinct entity types that are
    shared by two or more cases.

    This score indicates how strongly cases appear to be
    connected to the same campaign. It does not prove fraud.
    """

    shared_entity_types = set()

    # Check for shared phone numbers.
    phone_count = (
        db.query(CasePhone.phone_id)
        .filter(CasePhone.case_id.in_(case_ids))
        .group_by(CasePhone.phone_id)
        .having(func.count(CasePhone.case_id) >= 2)
        .count()
    )

    if phone_count > 0:
        shared_entity_types.add("phone")

    # Check for shared email addresses.
    email_count = (
        db.query(CaseEmail.email_id)
        .filter(CaseEmail.case_id.in_(case_ids))
        .group_by(CaseEmail.email_id)
        .having(func.count(CaseEmail.case_id) >= 2)
        .count()
    )

    if email_count > 0:
        shared_entity_types.add("email")

    # Check for shared domains.
    domain_count = (
        db.query(CaseDomain.domain_id)
        .filter(CaseDomain.case_id.in_(case_ids))
        .group_by(CaseDomain.domain_id)
        .having(func.count(CaseDomain.case_id) >= 2)
        .count()
    )

    if domain_count > 0:
        shared_entity_types.add("domain")

    # Check for shared UPI IDs.
    upi_count = (
        db.query(CaseUPI.upi_id)
        .filter(CaseUPI.case_id.in_(case_ids))
        .group_by(CaseUPI.upi_id)
        .having(func.count(CaseUPI.case_id) >= 2)
        .count()
    )

    if upi_count > 0:
        shared_entity_types.add("upi")

    # Add the weights of all shared entity types.
    confidence = sum(
        ENTITY_WEIGHTS[entity_type]
        for entity_type in shared_entity_types
    )

    # Keep the score between 0 and 1.
    return round(min(confidence, 1.0), 2)


def get_campaign_status(confidence: float) -> str:
    """
    Convert campaign-connection confidence into
    a deterministic connection status.

    This status describes the strength of the connection.
    It is not a final scam verdict.
    """

    if confidence >= 0.60:
        return "strongly_connected"

    if confidence >= 0.30:
        return "connected"

    return "potential"


def get_existing_campaign(
    db: Session,
    case_ids: list[str],
):
    """
    Check whether a campaign already contains exactly
    the same connected case group.
    """

    target_case_ids = {
        str(case_id)
        for case_id in case_ids
    }

    campaigns = db.query(Campaign).all()

    for campaign in campaigns:

        existing_case_ids = {
            str(link.case_id)
            for link in (
                db.query(CampaignCase)
                .filter(
                    CampaignCase.campaign_id == campaign.id
                )
                .all()
            )
        }

        if existing_case_ids == target_case_ids:
            return campaign

    return None


def detect_campaigns(db: Session) -> list[Campaign]:
    """
    Detect connected recruitment scam campaigns.

    Existing campaigns are reused instead of creating
    duplicate campaigns for the same case group.

    Existing campaigns are also updated with the latest
    confidence and connection status.
    """

    # Build the investigation graph.
    graph = build_investigation_graph(db)

    # Find groups containing two or more connected cases.
    case_groups = find_connected_case_groups(graph)

    campaigns = []

    for index, case_group in enumerate(case_groups, start=1):

        # Check whether this exact case group already
        # has a campaign.
        existing_campaign = get_existing_campaign(
            db,
            case_group,
        )

        # Calculate the latest confidence regardless
        # of whether the campaign already exists.
        confidence = calculate_campaign_confidence(
            db,
            case_group,
        )

        status = get_campaign_status(
            confidence
        )

        # Reuse and update existing campaign.
        if existing_campaign is not None:

            existing_campaign.confidence = confidence
            existing_campaign.status = status

            campaigns.append(existing_campaign)

            continue

        # Create a new campaign.
        campaign = Campaign(
            name=f"Recruitment Scam Campaign {index}",
            confidence=confidence,
            status=status,
        )

        db.add(campaign)
        db.flush()

        # Link every case in the group to the campaign.
        for case_id in case_group:

            db.add(
                CampaignCase(
                    campaign_id=campaign.id,
                    case_id=case_id,
                )
            )

        campaigns.append(campaign)

    db.commit()

    return campaigns