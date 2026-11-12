"""Transactional outbox for the rebuildable Neo4j graph projection."""
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .db import SessionLocal
from .models import Case, GraphProjectionOutbox
from . import graph_store

log = logging.getLogger("casework.graph_outbox")
RUNNING_STALE_AFTER = timedelta(minutes=10)


def enqueue_graph_sync(db, case_id: int, operation: str = "upsert") -> bool:
    """Coalesce latest case state into a durable row in the caller's transaction."""
    if operation not in {"upsert", "delete"}:
        raise ValueError("Graph projection operation must be upsert or delete")
    if not graph_store.configured():
        return False
    now = datetime.now(timezone.utc)
    values = {
        "case_id": case_id,
        "operation": operation,
        "generation": 1,
        "status": "queued",
        "attempts": 0,
        "available_at": now,
        "last_error": "",
        "created_at": now,
        "updated_at": now,
    }
    table = GraphProjectionOutbox.__table__
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        statement = sqlite_insert(table).values(**values)
    elif dialect == "postgresql":
        statement = pg_insert(table).values(**values)
    else:
        existing = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id).with_for_update())
        if existing:
            existing.operation = operation
            existing.generation += 1
            existing.status = "queued"
            existing.attempts = 0
            existing.available_at = now
            existing.last_error = ""
            existing.updated_at = now
        else:
            db.add(GraphProjectionOutbox(**values))
        return True

    statement = statement.on_conflict_do_update(
        index_elements=[table.c.case_id],
        set_={
            "operation": statement.excluded.operation,
            "generation": table.c.generation + 1,
            "status": "queued",
            "attempts": 0,
            "available_at": now,
            "last_error": "",
            "updated_at": now,
        },
    )
    db.execute(statement)
    return True


def process_graph_projection_once() -> bool:
    """Claim and apply one outbox event; failures stay queued with backoff."""
    if not graph_store.configured():
        return False

    now = datetime.now(timezone.utc)
    stale_before = now - RUNNING_STALE_AFTER
    with SessionLocal() as db:
        with db.begin():
            job = db.scalar(
                select(GraphProjectionOutbox)
                .where(
                    or_(
                        and_(GraphProjectionOutbox.status == "queued", GraphProjectionOutbox.available_at <= now),
                        and_(GraphProjectionOutbox.status == "running", GraphProjectionOutbox.updated_at < stale_before),
                    )
                )
                .order_by(GraphProjectionOutbox.created_at, GraphProjectionOutbox.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return False
            job.status = "running"
            job.attempts += 1
            job.updated_at = now
            case_id = job.case_id
            generation = job.generation
            operation = job.operation
            attempts = job.attempts

    try:
        with SessionLocal() as db:
            case = db.get(Case, case_id)
            if operation == "delete" or case is None:
                graph_store.delete_case(case_id)
            else:
                graph_store.sync_from_db(db, case)
    except Exception as exc:
        log.error("Graph projection update failed for case id %s (%s)", case_id, type(exc).__name__)
        retry_now = datetime.now(timezone.utc)
        with SessionLocal() as db, db.begin():
            current = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id).with_for_update())
            if current is None:
                return True
            if current.generation == generation:
                delay_seconds = min(2 ** min(attempts, 8), 300)
                current.status = "queued"
                current.attempts = attempts
                current.available_at = retry_now + timedelta(seconds=delay_seconds)
                # Store only the exception type. User data or credentials can be
                # embedded in exception text; full tracebacks remain operator logs.
                current.last_error = type(exc).__name__[:80]
            else:
                current.status = "queued"
                current.available_at = retry_now
                current.last_error = ""
            current.updated_at = retry_now
        return True

    finished_at = datetime.now(timezone.utc)
    with SessionLocal() as db, db.begin():
        current = db.scalar(select(GraphProjectionOutbox).where(GraphProjectionOutbox.case_id == case_id).with_for_update())
        if current is not None:
            if current.generation == generation:
                current.status = "completed"
                current.last_error = ""
            else:
                # A newer change arrived during projection. Re-run the newest
                # PostgreSQL snapshot immediately instead of marking it complete.
                current.status = "queued"
                current.available_at = finished_at
                current.last_error = ""
            current.updated_at = finished_at
    return True
