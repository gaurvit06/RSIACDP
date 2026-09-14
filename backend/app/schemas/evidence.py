from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvidenceCreate(BaseModel):
    case_id: UUID
    evidence_type: str
    description: str | None = None
    source: str
    source_url: str | None = None
    result: str | None = None
    reliability: str


class EvidenceResponse(BaseModel):
    id: UUID
    case_id: UUID
    evidence_type: str
    description: str | None
    source: str
    source_url: str | None
    retrieved_at: datetime
    result: str | None
    reliability: str

    class Config:
        from_attributes = True