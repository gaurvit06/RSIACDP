from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(24), default="analyst")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AccountProvisioningGate(Base):
    """Singleton write lock serializing one-time investigator/reviewer provisioning."""
    __tablename__ = "account_provisioning_gates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class LoginThrottle(Base):
    """Hashed account/network throttle key; stores no raw email or IP address."""
    __tablename__ = "login_throttles"
    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    window_started_at: Mapped[float] = mapped_column(Float)
    locked_until: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PasswordResetToken(Base):
    """One-time reset credentials; the bearer token itself is never persisted."""
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_ref: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    input_kind: Mapped[str] = mapped_column(String(24))
    submitted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="queued")
    assessment: Mapped[str] = mapped_column(String(64), default="Insufficient evidence")
    consent_version: Mapped[str] = mapped_column(String(40))
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    external_source_consent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    entities: Mapped[list["Entity"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    raw_value: Mapped[str] = mapped_column(String(1000))
    normalized_value: Mapped[str] = mapped_column(String(1000), index=True)
    source_excerpt: Mapped[str] = mapped_column(String(1000), default="")
    source_location: Mapped[str] = mapped_column(String(80), default="submitted_text", server_default="submitted_text")
    source_start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(40), default="deterministic_regex")
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_uncertainty: Mapped[str] = mapped_column(String(300), default="", server_default="")
    review_status: Mapped[str] = mapped_column(String(24), default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped[Case] = relationship(back_populates="entities")


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    source_name: Mapped[str] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40))
    source_ref: Mapped[str] = mapped_column(String(1000), default="")
    claim: Mapped[str] = mapped_column(String(500))
    outcome: Mapped[str] = mapped_column(String(24))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    authority: Mapped[str] = mapped_column(String(40), default="user_submitted")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    review_status: Mapped[str] = mapped_column(String(24), default="unreviewed", server_default="unreviewed")
    review_reason: Mapped[str] = mapped_column(Text, default="", server_default="")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    case: Mapped[Case] = relationship(back_populates="evidence")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CaseLink(Base):
    __tablename__ = "case_links"
    __table_args__ = (UniqueConstraint("left_case_id", "right_case_id", "rule_version", name="uq_case_link_rule"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    left_case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    right_case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    rule_version: Mapped[str] = mapped_column(String(40))
    strength: Mapped[int] = mapped_column(Integer)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String(24), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    processing_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class GraphProjectionOutbox(Base):
    """Durable, coalesced work to keep the rebuildable Neo4j projection current."""
    __tablename__ = "graph_projection_outbox"
    __table_args__ = (UniqueConstraint("case_id", name="uq_graph_projection_case"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # No FK by design: a delete tombstone must survive deletion of its case row.
    case_id: Mapped[int] = mapped_column(Integer, index=True)
    operation: Mapped[str] = mapped_column(String(12), default="upsert", server_default="upsert")
    generation: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    status: Mapped[str] = mapped_column(String(16), default="queued", server_default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_error: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SourceRecord(Base):
    __tablename__ = "source_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    normalized_value: Mapped[str] = mapped_column(String(1000), index=True)
    source_name: Mapped[str] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(40))
    source_ref: Mapped[str] = mapped_column(String(1000), default="")
    claim: Mapped[str] = mapped_column(String(1000))
    outcome: Mapped[str] = mapped_column(String(24))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    authority: Mapped[str] = mapped_column(String(40), default="curated")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    retirement_reason: Mapped[str] = mapped_column(Text, default="", server_default="")


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_ref: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    case_ref: Mapped[str] = mapped_column(String(20), index=True)
    requester_email: Mapped[str] = mapped_column(String(320))
    status_token_hash: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="received", index=True)
    resolution: Mapped[str] = mapped_column(Text, default="")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class HumanDisposition(Base):
    __tablename__ = "human_dispositions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    disposition: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="recorded", server_default="recorded", index=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_rationale: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SystemFinding(Base):
    __tablename__ = "system_findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    scope: Mapped[str] = mapped_column(String(16))
    claim: Mapped[str] = mapped_column(Text)
    assessment: Mapped[str] = mapped_column(String(64))
    observation: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence_snapshot: Mapped[list] = mapped_column(JSON, default=list)
    conflict_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    unreviewed_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    rule_name: Mapped[str] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(40))
    limitations: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
