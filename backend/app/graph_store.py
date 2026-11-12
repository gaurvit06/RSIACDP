"""Neo4j projection store. PostgreSQL remains authoritative; these nodes are rebuildable."""
import hashlib
from datetime import timezone
from neo4j import GraphDatabase
from .config import settings
from .privacy import mask_identifier, redact_source_ref


def configured() -> bool:
    return bool(settings.effective_neo4j_uri and settings.neo4j_user and settings.effective_neo4j_password)


def _driver():
    if not configured():
        raise RuntimeError("Neo4j is not configured")
    return GraphDatabase.driver(settings.effective_neo4j_uri, auth=(settings.neo4j_user, settings.effective_neo4j_password), connection_timeout=5)


def display_identifier(entity_type: str, value: str) -> str:
    return mask_identifier(entity_type, value)


def entity_node_id(entity_key: str) -> str:
    """Stable graph node handle that does not expose the underlying identifier."""
    return "entity:" + hashlib.sha256(entity_key.encode("utf-8")).hexdigest()[:24]


def evidence_node_id(evidence_id: int) -> str:
    """Stable opaque evidence handle; do not expose sequential database IDs in the graph."""
    return "evidence:" + hashlib.sha256(f"evidence:{evidence_id}".encode("ascii")).hexdigest()[:24]


def serialize_evidence(evidence, entity_fingerprint_map: dict[str, str] | None = None) -> dict:
    """Build a graph-safe evidence node, preserving provenance without raw identifiers."""
    details = evidence.details or {}
    matched_type = details.get("matched_entity_type")
    matched_value = details.get("matched_normalized_value")
    matched_entity_key = f"{matched_type}:{matched_value}" if matched_type and matched_value else None
    if matched_entity_key is None and entity_fingerprint_map:
        matched_entity_key = entity_fingerprint_map.get(details.get("entity_fingerprint"))
    retrieved_at = evidence.retrieved_at
    if retrieved_at and retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    return {
        "evidence_key": evidence_node_id(evidence.id),
        "case_id": evidence.case_id,
        "source_type": evidence.source_type,
        "source_ref": redact_source_ref(evidence.source_ref),
        "outcome": evidence.outcome,
        "authority": evidence.authority,
        "retrieved_at": retrieved_at.isoformat() if retrieved_at else None,
        "review_status": evidence.review_status,
        "matched_entity_key": matched_entity_key,
    }


def sync_case(case_id: int, case_ref: str, created_at: str, entities: list[dict], evidence: list[dict], links: list[dict]) -> None:
    """Upsert one case and its current entity, evidence and campaign relationships."""
    with _driver() as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.run(
                "MERGE (c:CaseworkCase {case_id: $case_id}) "
                "SET c.case_ref = $case_ref, c.created_at = $created_at, c.updated_at = datetime() REMOVE c.title "
                "WITH c OPTIONAL MATCH (c)-[old:CASEWORK_CONTAINS]->() DELETE old "
                "WITH c OPTIONAL MATCH (c)-[:CASEWORK_HAS_EVIDENCE]->(old:CaseworkEvidence) DETACH DELETE old "
                "WITH c OPTIONAL MATCH (c)-[old:CASEWORK_POSSIBLE_CAMPAIGN]-() DELETE old "
                "WITH c UNWIND $entities AS item "
                "MERGE (e:CaseworkIdentifier {entity_key: item.entity_key}) "
                "SET e.entity_type = item.entity_type, e.normalized_value = item.normalized_value, e.display_value = item.display_value "
                "MERGE (c)-[r:CASEWORK_CONTAINS]->(e) SET r.review_status = item.review_status",
                case_id=case_id, case_ref=case_ref, created_at=created_at, entities=entities,
            ).consume()
            session.run(
                "MATCH (c:CaseworkCase {case_id: $case_id}) UNWIND $evidence AS item "
                "MERGE (v:CaseworkEvidence {evidence_key: item.evidence_key}) "
                "SET v.case_id = item.case_id, v.source_type = item.source_type, "
                "v.source_ref = item.source_ref, v.outcome = item.outcome, "
                "v.authority = item.authority, v.retrieved_at = item.retrieved_at, "
                "v.review_status = item.review_status REMOVE v.source_name, v.claim, v.excerpt, v.review_reason "
                "MERGE (c)-[r:CASEWORK_HAS_EVIDENCE]->(v) SET r.review_status = item.review_status",
                case_id=case_id, evidence=evidence,
            ).consume()
            session.run(
                "UNWIND $evidence AS item WITH item WHERE item.matched_entity_key IS NOT NULL "
                "MATCH (v:CaseworkEvidence {evidence_key: item.evidence_key}) "
                "MATCH (e:CaseworkIdentifier {entity_key: item.matched_entity_key}) "
                "MERGE (v)-[r:CASEWORK_CHECKS_IDENTIFIER]->(e) SET r.review_status = item.review_status",
                evidence=evidence,
            ).consume()
            for link in links:
                session.run(
                    "MATCH (a:CaseworkCase {case_id: $left_id}), (b:CaseworkCase {case_id: $right_id}) "
                    "MERGE (a)-[r:CASEWORK_POSSIBLE_CAMPAIGN {link_id: $link_id}]->(b) "
                    "SET r.rule_version = $rule_version, r.strength = $strength, r.reasons = $reasons, r.review_status = $review_status",
                    left_id=link["left_case_id"], right_id=link["right_case_id"], link_id=link["id"],
                    rule_version=link["rule_version"], strength=link["strength"], reasons=link["reasons"], review_status=link["review_status"],
                ).consume()


def delete_case(case_id: int) -> None:
    """Remove a projected case and identifiers no longer referenced by any case."""
    with _driver() as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.run(
                "MATCH (c:CaseworkCase {case_id: $case_id}) DETACH DELETE c",
                case_id=case_id,
            ).consume()
            session.run(
                "MATCH (e:CaseworkIdentifier) "
                "WHERE NOT EXISTS { MATCH (:CaseworkCase)-[:CASEWORK_CONTAINS]->(e) } "
                "DETACH DELETE e"
            ).consume()
            session.run(
                "MATCH (e:CaseworkEvidence) "
                "WHERE NOT EXISTS { MATCH (:CaseworkCase)-[:CASEWORK_HAS_EVIDENCE]->(e) } "
                "DETACH DELETE e"
            ).consume()


def sync_from_db(db, case) -> None:
    if not configured():
        return
    from sqlalchemy import select, or_
    from .models import CaseLink
    entities = [{"entity_key": f"{entity.entity_type}:{entity.normalized_value}", "entity_type": entity.entity_type, "normalized_value": entity.normalized_value, "display_value": display_identifier(entity.entity_type, entity.raw_value), "review_status": entity.review_status} for entity in case.entities]
    fingerprint_map = {
        hashlib.sha256(f"{entity.entity_type}:{entity.normalized_value}".encode("utf-8")).hexdigest():
            f"{entity.entity_type}:{entity.normalized_value}"
        for entity in case.entities
    }
    evidence = [serialize_evidence(item, fingerprint_map) for item in case.evidence]
    links = db.scalars(select(CaseLink).where(or_(CaseLink.left_case_id == case.id, CaseLink.right_case_id == case.id))).all()
    serialized = [{"id": link.id, "left_case_id": link.left_case_id, "right_case_id": link.right_case_id, "rule_version": link.rule_version, "strength": link.strength, "reasons": link.reasons, "review_status": link.review_status} for link in links]
    created_at = case.created_at.isoformat() if case.created_at else ""
    sync_case(case.id, case.case_ref, created_at, entities, evidence, serialized)


def graph_data(limit: int = 100):
    with _driver() as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            records = session.run(
                "MATCH (c:CaseworkCase) WITH c ORDER BY c.case_id DESC LIMIT $limit "
                "OPTIONAL MATCH (c)-[contains:CASEWORK_CONTAINS]->(e:CaseworkIdentifier) "
                "RETURN c.case_id AS case_id, c.case_ref AS case_ref, c.created_at AS created_at, "
                "collect(CASE WHEN e IS NULL THEN null ELSE {entity_key:e.entity_key, entity_type:e.entity_type, display_value:e.display_value, review_status:contains.review_status} END) AS entities",
                limit=limit,
            ).data()
            evidence_records = session.run(
                "MATCH (c:CaseworkCase)-[has:CASEWORK_HAS_EVIDENCE]->(v:CaseworkEvidence) "
                "WHERE c.case_id IN $case_ids "
                "RETURN c.case_id AS case_id, v.evidence_key AS evidence_key, "
                "v.source_type AS source_type, v.source_ref AS source_ref, "
                "v.outcome AS outcome, v.authority AS authority, "
                "v.retrieved_at AS retrieved_at, v.review_status AS review_status, "
                "has.review_status AS edge_review_status",
                case_ids=[row["case_id"] for row in records],
            ).data()
            evidence_links = session.run(
                "MATCH (v:CaseworkEvidence)-[r:CASEWORK_CHECKS_IDENTIFIER]->(e:CaseworkIdentifier) "
                "WHERE v.case_id IN $case_ids "
                "RETURN v.evidence_key AS evidence_key, e.entity_key AS entity_key, r.review_status AS review_status",
                case_ids=[row["case_id"] for row in records],
            ).data()
            links = session.run(
                "MATCH (a:CaseworkCase)-[r:CASEWORK_POSSIBLE_CAMPAIGN]->(b:CaseworkCase) "
                "WHERE a.case_id IN $case_ids AND b.case_id IN $case_ids "
                "RETURN a.case_id AS left_id, b.case_id AS right_id, r.review_status AS review_status, "
                "r.strength AS strength, r.rule_version AS rule_version, r.reasons AS reasons",
                case_ids=[row["case_id"] for row in records],
            ).data()
    nodes, edges, seen = [], [], set()
    for row in records:
        cid = row["case_id"]
        case_node = f"case:{cid}"
        nodes.append({"id": case_node, "type": "case", "label": row["case_ref"], "case_id": cid, "created_at": row.get("created_at")})
        for entity in row["entities"] or []:
            if not entity:
                continue
            node_id = entity_node_id(entity["entity_key"])
            if node_id not in seen:
                nodes.append({"id": node_id, "type": entity["entity_type"], "label": entity["display_value"], "review_status": entity["review_status"]})
                seen.add(node_id)
            edges.append({"from": case_node, "to": node_id, "kind": "contains_identifier", "review_status": entity["review_status"]})
    for evidence in evidence_records:
        case_node = f"case:{evidence['case_id']}"
        evidence_id = evidence["evidence_key"]
        node = {
            "id": evidence_id, "type": "evidence",
            "label": f"{evidence['source_type']} · {evidence['outcome']}",
            "case_id": evidence["case_id"],
            "source_type": evidence["source_type"], "source_ref": evidence["source_ref"],
            "outcome": evidence["outcome"], "authority": evidence["authority"],
            "retrieved_at": evidence["retrieved_at"], "review_status": evidence["review_status"],
        }
        nodes.append(node)
        edges.append({"from": case_node, "to": evidence_id, "kind": "has_evidence", "review_status": evidence["edge_review_status"]})
    entity_ids = {}
    for row in records:
        for entity in row["entities"] or []:
            if entity:
                entity_ids[entity["entity_key"]] = entity_node_id(entity["entity_key"])
    for link in evidence_links:
        entity_id = entity_ids.get(link["entity_key"])
        if entity_id:
            edges.append({"from": link["evidence_key"], "to": entity_id, "kind": "checks_identifier", "review_status": link["review_status"]})
    for link in links:
        edges.append({"from": f"case:{link['left_id']}", "to": f"case:{link['right_id']}", "kind": "proposed_campaign_link", "review_status": link["review_status"], "strength": link["strength"], "rule_version": link["rule_version"], "reasons": link["reasons"] or []})
    return {"nodes": nodes, "edges": edges}


def rebuild(cases: list[dict], entities_by_case: dict[int, list[dict]], evidence_by_case: dict[int, list[dict]], links_by_case: dict[int, list[dict]]) -> None:
    """Rebuild only the application's dedicated Neo4j labels from PostgreSQL snapshots."""
    with _driver() as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.run("MATCH (n:CaseworkCase) DETACH DELETE n").consume()
            session.run("MATCH (n:CaseworkIdentifier) DETACH DELETE n").consume()
            session.run("MATCH (n:CaseworkEvidence) DETACH DELETE n").consume()
    for case in cases:
        sync_case(case["id"], case["case_ref"], case.get("created_at", ""), entities_by_case.get(case["id"], []), evidence_by_case.get(case["id"], []), links_by_case.get(case["id"], []))
