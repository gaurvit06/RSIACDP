from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.report import InvestigationReport
from app.services.report_service import build_investigation_report
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get(
    "/case/{case_id}",
    response_model=InvestigationReport
)
def get_investigation_report(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the complete investigation report for a case.

    Authentication is required because reports
    may contain sensitive investigation information.
    """

    try:
        report = build_investigation_report(
            db=db,
            case_id=case_id
        )

        return report

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )