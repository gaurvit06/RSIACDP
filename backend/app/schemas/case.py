from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseCreate(BaseModel):
    input_type: str
    original_content: str | None = None
    consent_given: bool = False


class CaseResponse(BaseModel):
    id: UUID
    input_type: str
    original_content: str | None
    status: str
    consent_given: bool
    created_at: datetime

    class Config:
        from_attributes = True