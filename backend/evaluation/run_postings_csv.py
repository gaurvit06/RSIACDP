"""Offline labelled-CSV benchmark. Run either 'worker' or 'baseline' in a fresh process."""
import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


FIELDS = {
    "title": "Job title", "location": "Location", "industry": "Industry",
    "employment_type": "Employment type", "department": "Department",
    "required_experience": "Required experience", "requirements": "Requirements",
    "benefits": "Benefits", "description": "Job description", "salary_range": "Salary range",
    "company_profile": "Company profile", "required_education": "Required education", "function": "Function",
}
CONCERN = "Evidence supports concern"


def material(row):
    return "\n".join(f"{label}: {row[key].strip()}" for key, label in FIELDS.items() if row[key].strip())


def split(row):
    # Place all records with the same whitespace/case-normalized description in one fold.
    text = " ".join((row["description"].strip() or material(row)).casefold().split())
    group = hashlib.sha256(text.encode()).hexdigest()
    return "test" if int(group, 16) % 5 == 0 else "train"


def setup_worker():
    os.environ.update(APP_ENV="testing", DATABASE_URL="sqlite+pysqlite:///:memory:", RDAP_ENABLED="false")
    from app.db import Base, engine, SessionLocal
    from app.models import User
    from app import main  # Register models before schema creation.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(User(id=1, email="benchmark@example.invalid", password_hash="disabled", role="investigator"))
        db.commit()


def score_posting(task):
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.db import engine
    from app.main import create_case, current_consent_version
    from app.schemas import CaseCreate
    from app.models import Case, ProcessingJob, User
    from app.worker import process_job
    job_id, text = task
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            with Session(conn, join_transaction_mode="rollback_only", expire_on_commit=False) as db:
                body = CaseCreate(title=f"Benchmark posting {job_id}", input_kind="posting", submitted_text=text,
                                  consent_version=current_consent_version(), consent=True)
                created = create_case(body, db, db.get(User, 1))
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.case_id == created["id"]))
                process_job(db, job)
                if job.status != "completed":
                    raise RuntimeError(f"worker status {job.status}, error {job.last_error}")
                db.expire_all()
                case = db.get(Case, created["id"])
                return case.assessment, case.posting_prediction["label"], job.processing_ms, len(case.entities)
        finally:
            if transaction.is_active:
                transaction.rollback()


def metrics(rows):
    tp, fp, fn, tn = (sum(r["label"] == y and r["flag"] == flag for r in rows)
                      for y, flag in [(1, True), (0, True), (1, False), (0, False)])
    def ratio(n, d):
        return n / d if d else None
    return dict(n=len(rows), tp=tp, fp=fp, fn=fn, tn=tn, precision=ratio(tp, tp+fp),
                recall=ratio(tp, tp+fn), f1=ratio(2*tp, 2*tp+fp+fn), fpr=ratio(fp, fp+tn))


def run(args):
    with args.csv.open(encoding="utf-8-sig", newline="") as f:
        records = list(csv.DictReader(f))
    if len({r["job_id"] for r in records}) != len(records) or any(r["fraudulent"] not in {"0", "1"} for r in records):
        raise ValueError("Expected unique job_id and binary fraudulent labels")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    texts = []
    for r in records:
        rows.append(dict(job_id=r["job_id"], label=int(r["fraudulent"]), split=split(r),
                         india=r["location"].partition(",")[0].strip() == "IN"))
        texts.append(material(r))
    meta = dict(dataset_sha256=hashlib.sha256(args.csv.read_bytes()).hexdigest(),
                label_counts=dict(Counter(r["label"] for r in rows)))
    if args.mode == "worker":
        tasks = [(r["job_id"], t) for r, t in zip(rows, texts)]
        with ProcessPoolExecutor(max_workers=args.workers, initializer=setup_worker) as pool:
            results = pool.map(score_posting, tasks, chunksize=24)
            for i, (row, (assessment, decision, ms, n)) in enumerate(zip(rows, results), 1):
                row.update(assessment=assessment, model_decision=decision, flag=decision == "Higher fraud risk",
                           processing_ms=ms, entity_count=n)
                if i % 2000 == 0:
                    print(f"{i}/{len(rows)} completed", flush=True)
        times = sorted(r["processing_ms"] for r in rows)
        meta.update(all_rows=metrics(rows), india=metrics([r for r in rows if r["india"]]),
                    assessments=dict(Counter(r["assessment"] for r in rows)),
                    model_decisions=dict(Counter(r["model_decision"] for r in rows)),
                    total_entities=sum(r["entity_count"] for r in rows),
                    worker_ms_p50=statistics.median(times), worker_ms_p95=times[math.ceil(.95*len(times))-1])
    else:
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        train = [i for i, r in enumerate(rows) if r["split"] == "train"]
        test = [i for i, r in enumerate(rows) if r["split"] == "test"]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True)
        x_train = vectorizer.fit_transform(texts[i] for i in train)
        model = LogisticRegression(class_weight="balanced", solver="liblinear", random_state=42, max_iter=500)
        model.fit(x_train, [rows[i]["label"] for i in train])
        predicted = model.predict(vectorizer.transform(texts[i] for i in test))
        rows = [rows[i] for i in test]
        for r, pred in zip(rows, predicted):
            r["flag"] = bool(pred)
        meta.update(training_rows=len(train), sklearn_version=sklearn.__version__)
    meta["holdout"] = metrics([r for r in rows if r["split"] == "test"])
    with (args.output / f"{args.mode}-predictions.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (args.output / f"{args.mode}-metrics.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("worker", "baseline"))
    parser.add_argument("csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    run(parser.parse_args())
