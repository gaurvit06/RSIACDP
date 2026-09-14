from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    confidence: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True