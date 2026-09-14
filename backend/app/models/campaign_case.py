from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CampaignCase(Base):
    __tablename__ = "campaign_cases"

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id"),
        primary_key=True
    )

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )