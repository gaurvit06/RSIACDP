from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CasePhone(Base):
    __tablename__ = "case_phones"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    phone_id = Column(
        UUID(as_uuid=True),
        ForeignKey("phones.id"),
        primary_key=True
    )