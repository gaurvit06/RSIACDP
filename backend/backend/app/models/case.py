import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.connection import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    input_type = Column(
        String(50),
        nullable=False
    )

    original_content = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="new"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )