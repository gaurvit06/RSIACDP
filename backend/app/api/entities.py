from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.entity_linking import link_entities_to_case


router = APIRouter(
    prefix="/entities",
    tags=["Entities"]
)


class EntityLinkRequest(BaseModel):
    case_id: str
    phones: list[str] | None = None
    emails: list[str] | None = None
    domains: list[str] | None = None
    upis: list[str] | None = None


@router.post("/link")
def link_entities(
    entity_data: EntityLinkRequest,
    db: Session = Depends(get_db)
):
    try:
        result = link_entities_to_case(
            db=db,
            case_id=entity_data.case_id,
            phones=entity_data.phones,
            emails=entity_data.emails,
            domains=entity_data.domains,
            upis=entity_data.upis,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )