from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseCreate(BaseModel):
    input_type: str
    original_content: str | None = None


class CaseResponse(BaseModel):
    id: UUID
    input_type: str
    original_content: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True