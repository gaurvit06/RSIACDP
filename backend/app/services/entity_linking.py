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


def link_phone_to_case(
    db: Session,
    case_id,
    phone: str,
):
    """
    Create or reuse a Phone entity and link it to a case.
    """

    normalized = normalize_phone(phone)

    phone_entity = (
        db.query(Phone)
        .filter(Phone.normalized_number == normalized)
        .first()
    )

    if phone_entity is None:
        phone_entity = Phone(
            number=phone,
            normalized_number=normalized,
            country="IN",
        )
        db.add(phone_entity)
        db.flush()

    existing_link = (
        db.query(CasePhone)
        .filter(
            CasePhone.case_id == case_id,
            CasePhone.phone_id == phone_entity.id,
        )
        .first()
    )

    if existing_link is None:
        db.add(
            CasePhone(
                case_id=case_id,
                phone_id=phone_entity.id,
            )
        )

    return phone_entity


def link_email_to_case(
    db: Session,
    case_id,
    email: str,
):
    """
    Create or reuse an Email entity and link it to a case.
    """

    normalized = normalize_email(email)

    email_entity = (
        db.query(Email)
        .filter(Email.normalized_address == normalized)
        .first()
    )

    if email_entity is None:
        email_domain = (
            normalized.split("@", 1)[1]
            if "@" in normalized
            else None
        )

        email_entity = Email(
            address=email,
            normalized_address=normalized,
            domain=email_domain,
        )

        db.add(email_entity)
        db.flush()

    existing_link = (
        db.query(CaseEmail)
        .filter(
            CaseEmail.case_id == case_id,
            CaseEmail.email_id == email_entity.id,
        )
        .first()
    )

    if existing_link is None:
        db.add(
            CaseEmail(
                case_id=case_id,
                email_id=email_entity.id,
            )
        )

    return email_entity


def link_domain_to_case(
    db: Session,
    case_id,
    domain: str,
):
    """
    Create or reuse a Domain entity and link it to a case.
    """

    normalized = normalize_domain(domain)

    domain_entity = (
        db.query(Domain)
        .filter(Domain.normalized_domain == normalized)
        .first()
    )

    if domain_entity is None:
        domain_entity = Domain(
            domain_name=domain,
            normalized_domain=normalized,
        )

        db.add(domain_entity)
        db.flush()

    existing_link = (
        db.query(CaseDomain)
        .filter(
            CaseDomain.case_id == case_id,
            CaseDomain.domain_id == domain_entity.id,
        )
        .first()
    )

    if existing_link is None:
        db.add(
            CaseDomain(
                case_id=case_id,
                domain_id=domain_entity.id,
            )
        )

    return domain_entity


def link_upi_to_case(
    db: Session,
    case_id,
    upi: str,
):
    """
    Create or reuse a UPI entity and link it to a case.
    """

    normalized = normalize_upi(upi)

    upi_entity = (
        db.query(UPI)
        .filter(UPI.normalized_upi == normalized)
        .first()
    )

    if upi_entity is None:
        upi_entity = UPI(
            upi_id=upi,
            normalized_upi=normalized,
        )

        db.add(upi_entity)
        db.flush()

    existing_link = (
        db.query(CaseUPI)
        .filter(
            CaseUPI.case_id == case_id,
            CaseUPI.upi_id == upi_entity.id,
        )
        .first()
    )

    if existing_link is None:
        db.add(
            CaseUPI(
                case_id=case_id,
                upi_id=upi_entity.id,
            )
        )

    return upi_entity


def link_entities_to_case(
    db: Session,
    case_id,
    phones: list[str] | None = None,
    emails: list[str] | None = None,
    domains: list[str] | None = None,
    upis: list[str] | None = None,
):
    """
    Link extracted entities to an existing case.

    Existing entities are reused using deterministic normalization.
    """

    case = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if case is None:
        raise ValueError("Case not found")

    phones = phones or []
    emails = emails or []
    domains = domains or []
    upis = upis or []

    linked = {
        "phones": [],
        "emails": [],
        "domains": [],
        "upis": [],
    }

    for phone in phones:
        entity = link_phone_to_case(
            db,
            case_id,
            phone,
        )
        linked["phones"].append(str(entity.id))

    for email in emails:
        entity = link_email_to_case(
            db,
            case_id,
            email,
        )
        linked["emails"].append(str(entity.id))

    for domain in domains:
        entity = link_domain_to_case(
            db,
            case_id,
            domain,
        )
        linked["domains"].append(str(entity.id))

    for upi in upis:
        entity = link_upi_to_case(
            db,
            case_id,
            upi,
        )
        linked["upis"].append(str(entity.id))

    db.commit()

    return {
        "case_id": str(case_id),
        "linked_entities": linked,
    }