from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CaseRecruiter(Base):
    __tablename__ = "case_recruiters"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    recruiter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recruiters.id"),
        primary_key=True
    )