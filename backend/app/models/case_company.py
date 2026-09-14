from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CaseCompany(Base):
    __tablename__ = "case_companies"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        primary_key=True
    )