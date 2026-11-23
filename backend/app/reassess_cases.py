"""Update completed cases to the current assessment rules, preserving finding history."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal
from .findings import RULE_VERSION, rebuild_system_findings
from .models import AuditEvent, Case, SystemFinding


def reassess_completed(db: Session) -> tuple[int, int]:
    updated = changed = 0
    current = select(SystemFinding.id).where(
        SystemFinding.case_id == Case.id, SystemFinding.scope == "case",
        SystemFinding.active.is_(True), SystemFinding.rule_version == RULE_VERSION,
    ).exists()
    while True:
        with db.begin():
            case = db.scalar(select(Case).where(Case.status == "completed", ~current)
                             .order_by(Case.id).limit(1).with_for_update())
            if case is None:
                break
            prior = case.assessment
            rebuild_system_findings(db, case)
            db.add(AuditEvent(case_id=case.id, actor_id=None, action="system_findings_recomputed",
                              detail={"trigger": "rule_upgrade", "rule_version": RULE_VERSION,
                                      "previous_assessment": prior, "assessment": case.assessment}))
            updated += 1
            changed += int(prior != case.assessment)
    return updated, changed


if __name__ == "__main__":
    with SessionLocal() as session:
        updated, changed = reassess_completed(session)
    print(f"Updated {updated} completed cases; {changed} changed assessment.")
