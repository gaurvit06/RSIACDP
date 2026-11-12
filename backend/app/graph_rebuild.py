"""Rebuild the Neo4j projection from PostgreSQL. Run from a maintenance window."""
import logging
import hashlib
from sqlalchemy import select
from .db import SessionLocal
from .models import Case, Entity, Evidence, CaseLink
from . import graph_store

logging.basicConfig(level=logging.INFO)


def main():
    if not graph_store.configured():
        raise SystemExit("Neo4j credentials are required to rebuild the graph projection")
    with SessionLocal() as db:
        cases = db.scalars(select(Case).order_by(Case.id)).all()
        links = db.scalars(select(CaseLink)).all()
        entities_by_case = {}
        fingerprints_by_case = {}
        for entity in db.scalars(select(Entity)).all():
            key = f"{entity.entity_type}:{entity.normalized_value}"
            entities_by_case.setdefault(entity.case_id, []).append({
                "entity_key": key,
                "entity_type": entity.entity_type,
                "normalized_value": entity.normalized_value,
                "display_value": graph_store.display_identifier(entity.entity_type, entity.raw_value),
                "review_status": entity.review_status,
            })
            fingerprints_by_case.setdefault(entity.case_id, {})[hashlib.sha256(key.encode("utf-8")).hexdigest()] = key
        evidence_by_case = {}
        for evidence in db.scalars(select(Evidence)).all():
            evidence_by_case.setdefault(evidence.case_id, []).append(graph_store.serialize_evidence(evidence, fingerprints_by_case.get(evidence.case_id)))
        links_by_case = {}
        for link in links:
            data = {"id": link.id, "left_case_id": link.left_case_id, "right_case_id": link.right_case_id, "rule_version": link.rule_version, "strength": link.strength, "reasons": link.reasons, "review_status": link.review_status}
            links_by_case.setdefault(link.left_case_id, []).append(data)
            links_by_case.setdefault(link.right_case_id, []).append(data)
        case_rows = [{"id": case.id, "case_ref": case.case_ref, "created_at": case.created_at.isoformat() if case.created_at else ""} for case in cases]
        graph_store.rebuild(case_rows, entities_by_case, evidence_by_case, links_by_case)
    logging.info("Rebuilt Neo4j projection for %d cases", len(case_rows))


if __name__ == "__main__":
    main()
