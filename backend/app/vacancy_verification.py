"""Corroborate a vacancy against a configured employer's public Greenhouse board."""
import hashlib
import html
import json
import math
import re
import time
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx
from sqlalchemy import select

from .config import settings
from .models import AuditEvent, Evidence

RULE = "official-board-tfidf-v1"
SOURCE = "official_employer_board"
LIMIT = "This confirms only that the employer published this role at retrieval time. The sender, terms, location, payment instructions and any individual offer remain unverified."
MIN_SIMILARITY = 0.50
MIN_SHARED = 12
_cache = {}


def configured_boards():
    boards = {}
    for entry in filter(None, settings.official_job_boards.split(",")):
        name, sep, slug = entry.partition("=")
        if not sep or not name.strip() or not re.fullmatch(r"[a-z0-9_-]{1,80}", slug):
            raise ValueError("OFFICIAL_JOB_BOARDS must contain employer=board-slug entries")
        boards[name.strip()] = slug
    return boards


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def phrases(text):
    words = re.findall(r"[^\W_]+", text.casefold())
    return Counter(zip(words, words[1:], words[2:]))


def index_jobs(payload):
    rows = payload["jobs"]
    if not isinstance(rows, list) or len(rows) > 5000:
        raise ValueError("Invalid board response")
    docs = []
    frequency = Counter()
    for row in rows:
        if type(row["id"]) != int or row["id"] <= 0 or not isinstance(row["title"], str) or not isinstance(row["content"], str):
            raise ValueError("Invalid vacancy record")
        if not 0 < len(row["title"]) <= 300:
            continue
        parser = PlainText()
        parser.feed(html.unescape(row["content"]))
        body = " ".join(" ".join(parser.parts).split())
        counts = phrases(body)
        frequency.update(counts.keys())
        docs.append((row["id"], row["title"], body, counts))
    idf = {p: math.log((1+len(rows))/(1+n))+1 for p,n in frequency.items()}
    return docs, idf, frequency


def board_index(slug):
    tick = time.monotonic()
    cached = _cache.get(slug)
    if cached and tick < cached[0]:
        return cached[1:]
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    now = datetime.now(timezone.utc)
    try:
        with httpx.stream("GET", url, timeout=8, follow_redirects=False, headers={"Accept-Encoding":"identity"}) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes(65536):
                if len(data)+len(chunk)>16_000_000 or time.monotonic()-tick>18:
                    raise ValueError("Board response exceeded limits")
                data.extend(chunk)
        index = index_jobs(json.loads(data))
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        index = None
    _cache[slug] = (tick + (1800 if index is not None else 60), index, now)
    return index, now


def compare(text, titles, index):
    docs, idf, frequency = index
    query = phrases(text)
    unseen_weight = 1 + math.log(1 + len(docs))
    weights = {p: (1+math.log(n))*idf.get(p, unseen_weight) for p,n in query.items()}
    qnorm = math.sqrt(sum(v*v for v in weights.values()))
    matches = []
    for key,title,body,counts in docs:
        if title.strip().casefold() not in titles or not qnorm or not counts:
            continue
        shared = weights.keys() & counts.keys()
        informative = sum(frequency[p] <= max(1,len(docs)//5) for p in shared)
        if informative < MIN_SHARED:
            continue
        doc = {p:(1+math.log(n))*idf[p] for p,n in counts.items()}
        score = sum(weights[p]*doc[p] for p in sorted(shared))/(qnorm*math.sqrt(sum(w*w for w in doc.values())))
        if score >= MIN_SIMILARITY:
            matches.append((key,title,body,score,informative))
    return matches


def check_vacancy(db, case):
    boards = configured_boards()
    if not boards:
        return False
    existing = db.scalars(select(Evidence).where(Evidence.case_id==case.id, Evidence.source_type==SOURCE)
                          .order_by(Evidence.id.desc())).all()
    accepted = {(e.entity_type,e.raw_value.strip().casefold()) for e in case.entities if e.review_status!='rejected'}
    titles = {v for k,v in accepted if k=='job_title_claim'}
    targets = [(name,slug) for name,slug in boards.items() if ('company_claim',name.casefold()) in accepted]
    changed = False
    for name,slug in targets or [("", "")]:
        previous = next((e for e in existing if (e.details or {}).get("board")==slug),None)
        fingerprint = hashlib.sha256(json.dumps([RULE, slug, sorted(titles), case.submitted_text or ""], ensure_ascii=False).encode()).hexdigest()
        if previous and previous.outcome != "unavailable" and previous.details.get("input_sha256") == fingerprint:
            continue
        now = datetime.now(timezone.utc)
        details = {"board":slug, "rule":RULE, "input_sha256":fingerprint}
        ref = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs" if slug else "configured-employer-boards"
        outcome = "not_checked"
        claim = "Whether a configured employer published the submitted role."
        excerpt = "A recognized employer and extracted job title are required for automatic verification."
        if slug and titles:
            index, now = board_index(slug)
            matches = compare(case.submitted_text or "", titles, index) if index is not None else []
            outcome = "unavailable" if index is None else "no_result"
            excerpt = ("Employer board could not be retrieved." if index is None else
                       "No unique listing met the employer, title and wording requirements.")
            if len(matches)==1:
                key,title,body,score,shared = matches[0]
                ref = f"https://job-boards.greenhouse.io/{slug}/jobs/{key}"
                claim = f"{name} published the role {title}."
                excerpt = body[:360]
                details.update(company=name,title=title,similarity=round(score,6),shared_phrases=shared,
                               source_record_ref=ref,content_sha256=hashlib.sha256(body.encode()).hexdigest())
                outcome = "result"
        if previous and previous.outcome == outcome and previous.details.get("input_sha256") == fingerprint:
            continue
        db.add(Evidence(case_id=case.id, source_type=SOURCE, source_name=(name+" careers").strip() if name else "Employer board verification",
                        source_ref=ref, claim=claim, excerpt=excerpt, outcome=outcome, retrieved_at=now,
                        authority="authoritative_source" if outcome=="result" else "metadata", details=details))
        db.add(AuditEvent(case_id=case.id, action="official_vacancy_checked", detail={"rule_version": RULE, "outcome": outcome}))
        changed = True
    db.flush()
    return changed


def vacancy_decisions(entities, evidence):
    if not any(item.source_type == SOURCE and item.outcome == "result" for item in evidence):
        return
    original = next((item for item in evidence if item.source_type in {"submitted_material","uploaded_file"}
                     and item.outcome == "result" and item.review_status in {"unreviewed","relevant"}), None)
    if original is None:
        return
    accepted = {(e.entity_type,e.raw_value.strip().casefold()) for e in entities if e.review_status!='rejected'}
    latest = {}
    for item in evidence:
        if item.source_type == SOURCE:
            latest[(item.details or {}).get("board")] = item
    for item in latest.values():
        if item.outcome != "result":
            continue
        d = item.details or {}
        if d.get("rule") != RULE or ("company_claim",str(d.get("company","")).casefold()) not in accepted or (
                "job_title_claim",str(d.get("title","")).casefold()) not in accepted:
            continue
        if item.review_status not in {"unreviewed","relevant","contradicts"}:
            continue
        conflicts = [e.id for e in evidence if e.review_status == "contradicts"]
        conflict = bool(conflicts)
        yield dict(scope="vacancy",entity_id=None,claim=item.claim,rule=RULE,limitations=LIMIT,
                   assessment="Insufficient evidence" if conflict else "Confirmed by an authoritative source",
                   observation=("This listing match was disputed." if conflict else
                       f"Automatic employer-board match on {item.retrieved_at:%Y-%m-%d} UTC. Employer and title matched exactly; "
                       f"{d['shared_phrases']} distinctive three-word phrases matched (TF-IDF cosine {d['similarity']:.3f}). {LIMIT}"),
                   evidence_ids=sorted({original.id,item.id,*conflicts}),supporting_evidence_ids=[] if conflict else [item.id],
                   conflict_evidence_ids=conflicts,unreviewed_evidence_ids=[])
