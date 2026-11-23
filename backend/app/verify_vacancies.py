"""Apply the automatic vacancy check to already completed cases."""
import argparse

from sqlalchemy import select

from .db import SessionLocal
from .findings import rebuild_system_findings
from .graph_outbox import enqueue_graph_sync
from .models import Case
from .vacancy_verification import check_vacancy, configured_boards


def verify_completed(db, case_ref=None):
    last_id = 0
    checked = changed = 0
    while True:
        with db.begin():
            query = select(Case).where(Case.status == "completed", Case.id > last_id)
            if case_ref:
                query = query.where(Case.case_ref == case_ref)
            case = db.scalar(query.order_by(Case.id).limit(1).with_for_update())
            if case is None:
                return checked, changed
            last_id = case.id
            checked += 1
            if check_vacancy(db, case):
                rebuild_system_findings(db, case)
                enqueue_graph_sync(db, case.id)
                changed += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-ref")
    options = parser.parse_args()
    if not configured_boards():
        parser.exit(message="Official board checks are disabled.\n")
    with SessionLocal() as session:
        count, updates = verify_completed(session, options.case_ref)
    print(f"Inspected {count} completed cases. Updated {updates}.")
