from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.report import InvestigationReport
from app.services.investigation_workflow import run_investigation


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"]
)


@router.post(
    "/{case_id}/run",
    response_model=InvestigationReport
)
def run_case_investigation(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run the complete investigation workflow for a case.

    Authentication is required.
    """

    try:
        return run_investigation(
            db=db,
            case_id=case_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )