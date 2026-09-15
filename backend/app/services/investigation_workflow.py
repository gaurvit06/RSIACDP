from sqlalchemy.orm import Session

from app.models.case import Case

from app.services.entity_extraction import extract_entities
from app.services.entity_linking import link_entities_to_case
from app.services.campaign_detection import detect_campaigns
from app.services.report_service import build_investigation_report


def run_investigation(
    db: Session,
    case_id: str
) -> dict:
    """
    Run the complete investigation workflow for a case.
    """

    case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if case is None:
        raise ValueError("Case not found")

    # Step 1: Extract entities from the case content.
    if case.original_content:
        entities = extract_entities(
            case.original_content
        )

        # Step 2: Link extracted entities to the case.
        link_entities_to_case(
            db=db,
            case_id=case_id,
            phones=entities["phones"],
            emails=entities["emails"],
            domains=entities["domains"],
            upis=entities["upis"],
        )

    # Step 3: Detect connected campaigns.
    detect_campaigns(db)

    # Step 4: Build the complete investigation report.
    report = build_investigation_report(
        db=db,
        case_id=case_id
    )

    # Step 5: Mark the case as investigated.
    case.status = "investigated"

    db.commit()

    report["status"] = case.status

    return report