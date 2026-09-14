from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Case
from app.services.verdict_engine import evaluate_case


router = APIRouter(
    prefix="/verdicts",
    tags=["Verdicts"]
)


@router.get("/{case_id}")
def get_case_verdict(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Evaluate a case and return its deterministic verdict.
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

    return evaluate_case(
        db=db,
        case_id=case_id
    )