from sqlalchemy.orm import Session

from app.models.case import Case
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

    # Step 1: Detect connected campaigns
    detect_campaigns(db)

    # Step 2: Build the complete investigation report
    report = build_investigation_report(
        db=db,
        case_id=case_id
    )

    # Step 3: Update case status
    case.status = "investigated"

    db.commit()

    # Refresh report-related case status
    report["status"] = case.status

    return report