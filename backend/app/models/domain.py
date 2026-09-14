import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.connection import Base


class Domain(Base):
    __tablename__ = "domains"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    domain_name = Column(
        String(255),
        nullable=False
    )

    normalized_domain = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    first_seen = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    last_seen = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )