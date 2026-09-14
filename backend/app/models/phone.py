import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class Phone(Base):
    __tablename__ = "phones"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    number = Column(
        String(50),
        nullable=False
    )

    normalized_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    country = Column(
        String(10),
        nullable=True
    )