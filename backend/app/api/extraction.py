from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Case
from app.models.user import User
from app.core.security import get_current_user

from app.services.entity_extraction import extract_entities
from app.services.entity_linking import link_entities_to_case


router = APIRouter(
    prefix="/extraction",
    tags=["Entity Extraction"]
)


@router.post("/{case_id}")
def extract_case_entities(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract entities from the original case content
    and link them to the case.

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

    if not case.original_content:
        raise HTTPException(
            status_code=400,
            detail="Case does not contain original content"
        )

    entities = extract_entities(
        case.original_content
    )

    linked_entities = link_entities_to_case(
        db=db,
        case_id=case_id,
        phones=entities["phones"],
        emails=entities["emails"],
        domains=entities["domains"],
        upis=entities["upis"],
    )

    return {
        "case_id": case_id,
        "extracted_entities": entities,
        "linked_entities": linked_entities["linked_entities"],
    }