from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CaseUPI(Base):
    __tablename__ = "case_upis"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    upi_id = Column(
        UUID(as_uuid=True),
        ForeignKey("upis.id"),
        primary_key=True
    )