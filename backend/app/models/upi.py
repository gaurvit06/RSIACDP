import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class UPI(Base):
    __tablename__ = "upis"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    upi_id = Column(
        String(255),
        nullable=False
    )

    normalized_upi = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )