from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CaseDomain(Base):
    __tablename__ = "case_domains"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    domain_id = Column(
        UUID(as_uuid=True),
        ForeignKey("domains.id"),
        primary_key=True
    )