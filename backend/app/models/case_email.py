from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class CaseEmail(Base):
    __tablename__ = "case_emails"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        primary_key=True
    )

    email_id = Column(
        UUID(as_uuid=True),
        ForeignKey("emails.id"),
        primary_key=True
    )