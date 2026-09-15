from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseResponse
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


@router.post(
    "/",
    response_model=CaseResponse
)
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new investigation case.

    Authentication and consent are required.
    """

    if not case_data.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Consent is required before submitting a case"
        )

    new_case = Case(
        input_type=case_data.input_type,
        original_content=case_data.original_content,
        status="new",
        consent_given=True
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return new_case


@router.get(
    "/{case_id}",
    response_model=CaseResponse
)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve an investigation case.

    Authentication is required.
    """

    case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case