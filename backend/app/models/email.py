import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    address = Column(
        String(255),
        nullable=False
    )

    normalized_address = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    domain = Column(
        String(255),
        nullable=True
    )