from sqlalchemy.orm import Session

from app.models.case import Case

from app.models.phone import Phone
from app.models.case_phone import CasePhone

from app.models.email import Email
from app.models.case_email import CaseEmail

from app.models.domain import Domain
from app.models.case_domain import CaseDomain

from app.models.upi import UPI
from app.models.case_upi import CaseUPI

from app.services.normalization import (
    normalize_phone,
    normalize_email,
    normalize_domain,
    normalize_upi,
)


def find_cases_by_phone(
    db: Session,
    phone: str
) -> list:
    """
    Find all cases containing the same normalized phone number.
    Matching is deterministic and exact.
    """

    normalized = normalize_phone(phone)

    results = (
        db.query(Case.id)
        .join(CasePhone, Case.id == CasePhone.case_id)
        .join(Phone, Phone.id == CasePhone.phone_id)
        .filter(Phone.normalized_number == normalized)
        .all()
    )

    return [case_id for (case_id,) in results]


def find_cases_by_email(
    db: Session,
    email: str
) -> list:
    """
    Find all cases containing the same normalized email.
    Matching is deterministic and exact.
    """

    normalized = normalize_email(email)

    results = (
        db.query(Case.id)
        .join(CaseEmail, Case.id == CaseEmail.case_id)
        .join(Email, Email.id == CaseEmail.email_id)
        .filter(Email.normalized_address == normalized)
        .all()
    )

    return [case_id for (case_id,) in results]


def find_cases_by_domain(
    db: Session,
    domain: str
) -> list:
    """
    Find all cases containing the same normalized domain.
    Matching is deterministic and exact.
    """

    normalized = normalize_domain(domain)

    results = (
        db.query(Case.id)
        .join(CaseDomain, Case.id == CaseDomain.case_id)
        .join(Domain, Domain.id == CaseDomain.domain_id)
        .filter(Domain.normalized_domain == normalized)
        .all()
    )

    return [case_id for (case_id,) in results]


def find_cases_by_upi(
    db: Session,
    upi: str
) -> list:
    """
    Find all cases containing the same normalized UPI ID.
    Matching is deterministic and exact.
    """

    normalized = normalize_upi(upi)

    results = (
        db.query(Case.id)
        .join(CaseUPI, Case.id == CaseUPI.case_id)
        .join(UPI, UPI.id == CaseUPI.upi_id)
        .filter(UPI.normalized_upi == normalized)
        .all()
    )

    return [case_id for (case_id,) in results]
def resolve_case_connections(
    db: Session,
    phone: str | None = None,
    email: str | None = None,
    domain: str | None = None,
    upi: str | None = None,
) -> dict:
    """
    Find existing cases connected to the supplied identifiers.

    Matching is deterministic and exact after normalization.
    """

    connections = {
        "phone": [],
        "email": [],
        "domain": [],
        "upi": [],
    }

    if phone:
        connections["phone"] = find_cases_by_phone(db, phone)

    if email:
        connections["email"] = find_cases_by_email(db, email)

    if domain:
        connections["domain"] = find_cases_by_domain(db, domain)

    if upi:
        connections["upi"] = find_cases_by_upi(db, upi)

    all_case_ids = set()

    for case_ids in connections.values():
        all_case_ids.update(case_ids)

    return {
        "connections": connections,
        "connected_case_ids": list(all_case_ids),
    }