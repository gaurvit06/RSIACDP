from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseResponse


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
    db: Session = Depends(get_db)
):
    new_case = Case(
        input_type=case_data.input_type,
        original_content=case_data.original_content,
        status="new"
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
    case_id,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(
        Case.id == case_id
    ).first()

    return case