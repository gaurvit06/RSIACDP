from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportEntity(BaseModel):
    entity_type: str
    value: str


class ReportEvidence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    evidence_type: str
    description: str | None
    source: str
    source_url: str | None
    retrieved_at: datetime
    result: str | None
    reliability: str
    authoritative: bool


class ReportCampaign(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    confidence: float
    status: str


class InvestigationReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: UUID
    input_type: str
    status: str
    entities: list[ReportEntity]
    evidence: list[ReportEvidence]
    connected_case_ids: list[UUID]
    campaigns: list[ReportCampaign]
    verdict: str
    score: int
    evidence_count: int
    authoritative_count: int
    explanation: str