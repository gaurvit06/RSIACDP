"""Persist initial model decisions; backfill completed cases that predate the classifier."""
from sqlalchemy import or_, select

from .db import SessionLocal
from .models import AuditEvent, Case
from .posting_model import load_model, predict


def classify(db, case):
    prediction = predict("" if case.input_kind == "url" else case.submitted_text or "")
    if case.posting_prediction != prediction:
        case.posting_prediction = prediction
        db.add(AuditEvent(case_id=case.id, actor_id=None, action="posting_classified", detail=prediction))


def backfill(db):
    count = 0
    version = load_model()[1]
    stored_version = Case.posting_prediction["model_version"].as_string()
    while True:
        with db.begin():
            case = db.scalar(select(Case).where(Case.status == "completed",
                             or_(stored_version.is_(None), stored_version != version))
                             .order_by(Case.id).limit(1).with_for_update())
            if case is None:
                return count
            classify(db, case)
            count += 1


if __name__ == "__main__":
    with SessionLocal() as session:
        print(f"Updated {backfill(session)} completed cases to the active model.")
