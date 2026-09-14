import uuid

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.connection import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(255),
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0
    )

    status = Column(
        String(50),
        nullable=False,
        default="potential"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )