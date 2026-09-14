from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportEntity(BaseModel):
    entity_type: str
    value: str


class ReportEvidence(BaseModel):
    id: UUID
    evidence_type: str
    description: str | None
    source: str
    source_url: str | None
    retrieved_at: datetime
    result: str | None
    reliability: str

    class Config:
        from_attributes = True


class ReportCampaign(BaseModel):
    id: UUID
    name: str
    confidence: float
    status: str

    class Config:
        from_attributes = True


class InvestigationReport(BaseModel):
    case_id: UUID
    input_type: str
    status: str

    entities: list[ReportEntity]
    evidence: list[ReportEvidence]
    connected_case_ids: list[UUID]
    campaigns: list[ReportCampaign]

    verdict: str
    score: int
    explanation: str