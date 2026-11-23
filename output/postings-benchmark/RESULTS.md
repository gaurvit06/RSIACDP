# Job-posting benchmark · 22 November 2026

This historical run evaluated the evidence rules before Casework adopted the Hiring Market posting classifier. For the current model and evaluation instructions, see the [evaluation guide](../../backend/evaluation/README.md).

The automatic investigation returned **Insufficient evidence for all 17,880 postings**, including all **866** labelled fraudulent. No row failed to process. The system produced no fraud warnings on this dataset. An unflagged posting remains unresolved.

| Evaluation | Cases | Labelled fraudulent | Correct flags | False flags | Missed labelled fraud | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Investigation, all rows | 17,880 | 866 | 0 | 0 | 866 | Undefined | 0% | 0% | 0% |
| Investigation, held-out rows | 3,291 | 165 | 0 | 0 | 165 | Undefined | 0% | 0% | 0% |
| Text baseline, same held-out rows | 3,291 | 165 | 118 | 40 | 47 | 74.7% | 71.5% | 73.1% | 1.28% |

The text baseline trained on 14,589 other rows, using the fields available to the investigator. Identical normalized descriptions stayed in the same fold. The baseline could prioritize postings for review. Its score supplies no independent source for a claim.

## What the worker did

Each record passed through the case-creation handler and processing worker using an isolated in-memory database. The worker extracted 88,884 candidate entities and claims. Median worker processing time was 29.4 ms per posting, and the 95th percentile was 49.8 ms with six parallel processes. These times exclude queue wait, HTTP, user review and the completion commit.

The CSV supplies a binary label without supporting source records or investigator decisions. Several contact fields are masked in the posting text. For example, 5,621 rows contain a URL placeholder in the description, requirements, benefits or company profile. The benchmark used an empty local corpus with external lookups disabled. None of the 17,880 input texts matched the explicit recruitment-payment wording rule. Two separate controls verified that the worker flagged an explicit payment demand and left a no-fee advisory unresolved. These controls are excluded from all scores.

## Scope and reproducibility

- The India-location subset has 276 postings and just four labelled fraudulent. None were flagged. This sample is too small to establish performance on Indian recruitment scams.
- The file supplies no posting dates, campaign groupings, annotated entity spans or claim-level evidence judgments. Time-separated performance, campaign F1, extraction F1 and evidence-support precision remain unmeasured. Related templates or employers may cross the baseline split.
- Each posting was evaluated independently. This run measures automatic first-pass review from text. No postings were imported into the live workspace. No external services were contacted by the evaluation worker.
- Both outputs were independently reconciled against the source job IDs, labels, SHA-256 and held-out confusion matrices. The input SHA-256 was `59253295129d8b6a27607f9904f7d4ddf4dbb0ee35e079c7eb51b58b5e62bf60`. The sorted backend app Python source fingerprint was `ff6e814ee7e8fb8564d5ed82608787d8a1d4bfce16697837dd395ca9eaa07254`.
- The adjacent JSON files contain aggregate measures. The JSONL files contain per-posting results without the submitted text. See `backend/evaluation/README.md` for repeat commands and the split definition.
