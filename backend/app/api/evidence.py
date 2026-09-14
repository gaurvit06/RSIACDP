from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceCreate, EvidenceResponse


router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)


@router.post(
    "/",
    response_model=EvidenceResponse
)
def create_evidence(
    evidence_data: EvidenceCreate,
    db: Session = Depends(get_db)
):
    case = (
        db.query(Case)
        .filter(Case.id == evidence_data.case_id)
        .first()
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    evidence = Evidence(
        case_id=evidence_data.case_id,
        evidence_type=evidence_data.evidence_type,
        description=evidence_data.description,
        source=evidence_data.source,
        source_url=evidence_data.source_url,
        result=evidence_data.result,
        reliability=evidence_data.reliability,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.get(
    "/case/{case_id}",
    response_model=list[EvidenceResponse]
)
def get_case_evidence(
    case_id,
    db: Session = Depends(get_db)
):
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

    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.retrieved_at.desc())
        .all()
    )