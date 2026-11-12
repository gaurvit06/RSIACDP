from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    setup_code: str = Field(default="", max_length=200)
    session_mode: Literal["bearer", "cookie"] = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)
    session_mode: Literal["bearer", "cookie"] = "bearer"


class AccountStatusRequest(BaseModel):
    active: bool
    rationale: str = Field(min_length=10, max_length=2000)


class PasswordResetIssueRequest(BaseModel):
    rationale: str = Field(min_length=10, max_length=2000)


class PasswordResetConsumeRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    input_kind: str = Field(pattern="^(text|url|email|message)$")
    submitted_text: str = Field(min_length=1, max_length=100000)
    consent_version: str = Field(min_length=1, max_length=40)
    consent: bool
    rdap_consent: bool = False


class ReviewRequest(BaseModel):
    status: str = Field(pattern="^(confirmed|rejected|needs_review)$")
    rationale: str = Field(min_length=3, max_length=2000)


class EvidenceReviewRequest(BaseModel):
    status: str = Field(pattern="^(relevant|irrelevant|needs_review|contradicts)$")
    rationale: str = Field(min_length=10, max_length=2000)


class DispositionRequest(BaseModel):
    disposition: str = Field(pattern="^(confirmed_authoritative|evidence_supports_concern|insufficient_evidence|no_adverse_evidence)$")
    rationale: str = Field(min_length=10, max_length=4000)
    evidence_ids: list[int] = Field(default_factory=list, max_length=100)


class DispositionReviewRequest(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    rationale: str = Field(min_length=10, max_length=4000)


class SourceRecordCreate(BaseModel):
    entity_type: str = Field(pattern="^(email|phone|upi_id|bank_account|ifsc_code|url|domain)$")
    value: str = Field(min_length=2, max_length=1000)
    source_name: str = Field(min_length=2, max_length=160)
    source_type: str = Field(pattern="^(government|company_official|platform|news|complaint|other)$")
    source_ref: str = Field(default="", max_length=1000)
    claim: str = Field(min_length=3, max_length=1000)
    outcome: str = Field(pattern="^(result|no_result|unavailable|error)$")
    excerpt: str = Field(default="", max_length=10000)
    authority: str = Field(pattern="^(government|platform_action|authoritative_source|curated|unverified_public_report)$")


class SourceRecordRetire(BaseModel):
    rationale: str = Field(min_length=10, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def require_non_whitespace_rationale(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Enter at least 10 non-whitespace characters")
        return cleaned


class CorrectionCreate(BaseModel):
    case_ref: str = Field(pattern="^RC-[A-F0-9]{8}$")
    requester_email: EmailStr = Field(max_length=320)
    description: str = Field(min_length=15, max_length=5000)


class CorrectionReview(BaseModel):
    status: str = Field(pattern="^(investigating|resolved|rejected)$")
    resolution: str = Field(min_length=5, max_length=4000)


class CorrectionStatusRequest(BaseModel):
    status_token: str = Field(min_length=32, max_length=128)


class CorrectionApply(BaseModel):
    resolution: str = Field(min_length=10, max_length=4000)
    entity_id: int | None = None
    entity_action: str | None = Field(default=None, pattern="^(confirm|reject|correct)$")
    corrected_value: str | None = Field(default=None, min_length=2, max_length=1000)
    evidence_id: int | None = None
    evidence_action: str | None = Field(default=None, pattern="^(relevant|irrelevant|needs_review|contradicts)$")
