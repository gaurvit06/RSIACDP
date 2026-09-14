import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.connection import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True
    )

    evidence_type = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    source = Column(
        String(255),
        nullable=False
    )

    source_url = Column(
        String(1000),
        nullable=True
    )

    retrieved_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    result = Column(
        Text,
        nullable=True
    )

    reliability = Column(
        String(50),
        nullable=False
    )