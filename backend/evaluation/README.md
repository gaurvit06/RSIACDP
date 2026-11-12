# Reproducible evaluation

## Synthetic rehearsal requested by the project owner

From `backend`, run `python -m evaluation.generate_synthetic .test-runtime/synthetic-evaluation-v1` to create 108 fictional cases in a new, ignored directory. The generator refuses an existing output directory. Each simulated chronological split contains 36 cases; campaign identifiers are disjoint across splits. Only reserved `example.invalid` email identifiers are used. The adjacent manifest records the dataset hash, scope and limitations; the provenance file records generator-defined labels and email spans. No predictions or measured timings are fabricated.

Run `python -m evaluation.baseline_tfidf_logreg .test-runtime/synthetic-evaluation-v1/synthetic-input.jsonl .test-runtime/synthetic-evaluation-v1/tfidf-predictions.jsonl` for an actual baseline rehearsal. Save its stdout as a clearly labelled synthetic-only metrics artifact. These fixtures exercise the evaluation machinery, not real-world generalization: template overlap, simulated dates, email-only coverage and generator-defined labels make them unsuitable as evidence of deployment accuracy. Negative labels refer only to the complete fictional fixture universe. Do not import fictional source allegations into a production corpus. Full-pipeline and no-graph runs still require actual isolated application execution; an LLM/web-search comparison still requires a configured provider and traceable retrieval. This generator does not complete those comparisons.

### Recorded synthetic-only rehearsal

The generated `synthetic-evaluation-v1` artifact contains 108 cases (36 each in train, dev, and test); its input SHA-256 is `f458554cfd53ef57041047ff83f37e16904bad0a0348564fd9d3c4168d7c00f5`. The scorer was rerun against the saved TF-IDF/logistic-regression predictions on 2026-11-12 and reproduced these test-only values:

| Measure | Synthetic result | Interpretation |
| --- | ---: | --- |
| Entity micro-F1 | 0.00 (36 false negatives) | This baseline intentionally predicts no entities. |
| Campaign pairwise F1 | 0.00 (36 false negatives) | This baseline intentionally predicts no campaigns. |
| Evidence-support precision | Undefined; recall 0.00 (18 false negatives) | It predicts no supported claims, so precision has no denominator. |
| Narrow concern false-positive rate | 0/18 = 0.00 | Fictional labels only; this is not an estimate of real-world safety. |
| Per-test-case classifier time | Mean 0.0158 ms; p95 0.0250 ms | TF-IDF transform and logistic prediction only; excludes training, the API, worker, OCR, evidence retrieval, graph linking, and I/O. |

The scorer used 1,000 deterministic bootstrap resamples (seed `20261103`). Entity and campaign F1 intervals were `[0.00, 0.00]`; evidence-support precision had no valid resamples because there were no predicted support claims. The generated records use simulated dates, generator-defined labels, one email identifier type, and fictional `.invalid` addresses. These results show that the text-classifier comparator does not provide the investigation pipeline's extraction, provenance, or campaign-link capabilities; they are not evidence of product performance and must not be presented as a real-world metric.

Evaluation on independent, properly annotated recruitment-scam cases remains pending. Do not report synthetic or placeholder metrics as product performance. EMSCAD may be used as a separate baseline dataset, but it is not evidence of current performance on Indian recruitment scams.

Evaluation inputs and outputs can contain submitted text, personal identifiers, case labels, campaign labels, source references, and predictions. Use pseudonymous, non-identifying `case_id` and `campaign_id` values; keep any re-identification key outside the evaluation directory. Store input JSONL, prediction files, and provenance sidecars in access-controlled storage, exclude them from Git and container contexts, and delete them under the dataset's approved retention policy. The LLM/web-search runner writes only allowlisted provenance fields and standardized retrieval error codes, but operators must still ensure their metadata and source references contain no credentials, signed URLs, personal data, or confidential query text.

## Dataset format

Use one UTF-8 JSON object per line. Dates must be timezone-aware ISO-8601 timestamps. Keep all records from the same campaign in one time split where possible; choose cutoff dates before inspecting test results, and record the cutoff dates and dataset hash in the run report. The scorer rejects train/test leakage by `campaign_id` when a campaign appears in multiple splits and rejects chronology that places a later split before an earlier split. The TF-IDF runner learns vocabulary, IDF and model weights only from training rows.

Required fields:

```json
{"case_id":"case-001","submitted_at":"2026-01-10T10:00:00Z","split":"test","campaign_id":"campaign-a","gold_entities":[{"type":"email","value":"hr@example.invalid"}],"predicted_entities":[{"type":"email","value":"hr@example.invalid"}],"gold_supported_entities":[{"type":"email","value":"hr@example.invalid"}],"predicted_supported_entities":[{"type":"email","value":"hr@example.invalid"}],"gold_adverse_verdict":false,"predicted_adverse_verdict":false,"processing_ms":42}
```

For records with no campaign label, set `campaign_id` to `null`. A campaign is an annotated cluster, not a conclusion of guilt. Entity values should be consistently normalized before scoring. `gold_supported_entities` lists the exact entity claims for which the adjudicated evidence supports the specific claim; each item must also occur in `gold_entities`. `predicted_supported_entities` lists claims the system says are supported. Support precision/recall is computed over `(case_id, entity type, normalized value)` tuples, so a supported claim cannot mask an unsupported claim in the same case. Evidence support does not mean the subject is guilty. The adverse-verdict field is for false-positive-rate evaluation only and must never be used as product wording.

### Binary adverse-assessment label

`gold_adverse_verdict` and `predicted_adverse_verdict` measure only whether a case meets the narrow assessment category **“Evidence supports concern.”** They do not label a person or company a scammer, do not establish that a reported allegation is true, and must never appear as a product decision or report verdict.

- Label `gold_adverse_verdict: true` only when independent adjudicators verify that at least one specific in-scope claim is matched by an exact identifier in a traceable, result-bearing, source-labeled unverified public report; record the source snapshot/reference and retrieval time. This means a report exists and makes the claim, not that the report is proven true.
- Label `false` only after the pre-registered review of the defined, documented evidence scope is complete and no claim meets that rule. A missing vacancy, empty/failed/unavailable lookup, lack of a report in an incomplete source set, or absence from the local corpus is not enough to label a case negative.
- Exclude cases from this binary metric when provenance, coverage, identity matching, or contradictory records leave the label indeterminate. The schema uses booleans, so do not coerce indeterminate cases to `false`; record their count and exclusion reason in the protected annotation/run record.
- Annotators must not use guilt, intent, complaint wording alone, repeated identifiers, or a campaign link as the target label. Report the metric as false-positive rate for the narrow concern category and publish its denominator and exclusions.

## Annotation guidance

1. Two annotators independently label entity type/value and source span, campaign membership, and whether a cited source supports the exact claim. Record the mapping from each supported `(type, normalized value)` claim to its supporting or contradicting source snapshot/reference in a separate protected provenance file. A third reviewer adjudicates disagreements.
2. Record source snapshots/IDs, retrieval times, annotation date, annotator IDs (pseudonymous), and adjudication rationale in that protected provenance file. Exclude records whose source provenance or consent/authorization cannot be established.
3. Treat repeated identifiers as a possible campaign link only when the underlying values match under documented normalization. Similar text alone is not a campaign label.
4. Label source results `result`, `no_result`, `unavailable`, `error`, or `not_checked` distinctly. Empty/unavailable/error outcomes cannot support an adverse assessment or establish a negative gold label; exclude an indeterminate case from the binary verdict metric.
5. Create chronological train/dev/test splits using fixed UTC cutoff dates. Keep linked cases and campaign groups together; document unavoidable overlap and remove duplicate content across splits.
6. Keep personal data out of the repository. Use synthetic or explicitly authorized, minimized data and document redactions.

## Metrics

Run `python evaluate.py DATA.jsonl`. The script reports entity micro-precision/recall/F1, pairwise campaign-clustering precision/recall/F1, claim-level evidence-support precision/recall, adverse-verdict false-positive rate, and processing mean/p95. It also reports 95% percentile-bootstrap intervals for entity F1, campaign pairwise F1, evidence-support precision, verdict false-positive rate, processing mean and processing p95. The default is 1,000 deterministic resamples with seed `20261103`; the output records the seed, method and valid-resample count. Per-case metrics use case-level resampling. Campaign pairwise F1 resamples annotated gold campaign groups as clusters, treating unassigned cases as singleton groups, to avoid splitting a labeled group during interval estimation. An interval is `null` if fewer than 80% of its resamples define that metric; point estimates with undefined denominators are also `null`, never silently set to zero. These intervals describe sampling uncertainty on the provided test set and do not address annotation bias, source coverage, temporal drift or representativeness. The input can contain model output for one system at a time; use separate files with the same case IDs for each comparison. Each row is schema-checked: verdict fields must be JSON booleans, support fields must be type/value arrays contained in the corresponding entity arrays, timestamps must include a timezone, and processing times must be finite non-negative numbers. Invalid input is rejected instead of being silently coerced (for example, the string `"false"` is not treated as a Boolean false).

## Required comparisons

Use the exact same time-separated test IDs and evidence snapshots for: (1) TF-IDF plus logistic regression, (2) an LLM with web search, (3) this evidence pipeline with graph linking disabled, and (4) the full pipeline. Record model/provider/version, prompt and retrieval settings, corpus snapshot hash, code revision, and processing-time measurement boundary. The LLM/web-search comparison is an offline experimental baseline and is not a production decision-maker. Do not compare runs with different labels, retrieval access, or test windows as if they were controlled.

For application-worker measurements, `processing_jobs.processing_ms` stores the latest successful worker attempt duration. The timer starts after the job's transition to `processing` has been committed and stops immediately before the successful completion commit. It includes local parsing, OCR, configured source checks, and finding generation; it excludes queue wait and final database-commit time. A retry clears the previous value at the start of the new attempt, and failed attempts leave it null. Do not substitute `created_at`/`updated_at` differences for execution latency. In the full-pipeline export, `processing_ms` adds the measured duration of the latest investigator-triggered campaign-link recomputation after worker completion. That API duration is persisted in the `campaign_links_recomputed` audit event and includes deterministic identifier matching and database query/write preparation, but excludes the final transaction commit and asynchronous Neo4j projection. This makes the end-to-end evidence-plus-campaign-link measurement explicit without changing the persisted worker metric.

### Export the persisted investigation pipeline

`export_pipeline.py` joins the persisted application pipeline to a separately maintained annotation map. The input must be stored in access-controlled storage outside this repository and contain exactly the following fields per JSONL line; it must not contain submitted text:

```json
{"case_ref":"RC-1234ABCD","case_id":"pseudo-case-0001","split":"test","campaign_id":"campaign-group-a","gold_entities":[{"type":"phone","value":"+919876543210"}],"gold_supported_entities":[{"type":"phone","value":"+919876543210"}],"gold_adverse_verdict":false}
```

`case_ref` is the private join key and is never written to output. `case_id` and non-null `campaign_id` values must be pseudonymous. Gold entity values are still personal data, so protect the input, output and metadata sidecar. The exporter normalizes them using the same deterministic entity-type normalization as the application before producing scorer rows. Provide `EVALUATION_SNAPSHOT_HMAC_KEY` through the operator's secret store as a stable key of at least 32 bytes. Do not put it in Git, command history, or the metadata file. The exporter uses it to produce keyed hashes for the annotation file and local-corpus snapshot without publishing a hash that can be checked against guessed identifiers. Paired runs that need snapshot comparison must use the same protected key.

The full-pipeline exporter requires completed cases, a successful single-attempt worker duration, and a current-rule campaign-link recomputation after all mapped cases have completed processing and review. Trigger the endpoint once for each mapped case so link clusters are computed against the full evaluation set. It rejects corrected entity values, investigator link decisions, missing cases, retries, incomplete processing, stale/missing link timing, and invalid link durations. It retains all extracted candidates for entity-extraction scoring, including candidates an investigator later rejected; investigator confirmation/rejection and evidence relevance review may feed the end-to-end findings, but investigators must not see or author the gold labels. `gold_supported_entities` must be a subset of gold entities and is normalized using application rules. Current-rule proposed and low-signal campaign links are clustered only among cases present in the annotation map, matching the investigator campaign view. A low-signal group remains a weak lead, not a campaign finding or proof of wrongdoing. A claim is predicted supported only when that entity's active machine finding cites a result-bearing evidence record an investigator marked relevant. The metric compares exact `(case_id, entity type, normalized value)` claims; it does not count case-level positive status. The evaluation-only adverse flag is true when the case assessment or any active claim-level finding is `Evidence supports concern`; it does not mean a person or organization committed wrongdoing. These definitions are also included in the non-identifying metadata sidecar.

For a true graph-linking ablation, prepare a separate isolated database using the same application version, source corpus snapshot, worker settings, consented inputs, and independently produced investigator entity/evidence review. Do not call the campaign-link refresh endpoint in that run. Export it directly with `--without-graph-linking`; the exporter refuses cases with a link-recomputation audit record or any persisted case link, emits null campaign predictions, and uses the measured worker duration without adding campaign-link time. A regular export is full mode: after every mapped case has completed processing and review, recompute links once for every mapped case, then export. This includes recorded per-case link duration and derives campaign predictions from current-rule proposed/low-signal links. Pair both files using the same pseudonymous test IDs, gold labels, code revision, configuration, consent scope, and HMAC-matched evidence corpus. Do not compare runs if their evidence snapshot metadata differs. The ablation must rerun the evidence pipeline on its isolated copy; it is not valid to remove campaign predictions from full-pipeline output and reuse its timing.

Because the full application finding consumes investigator entity/evidence review, while the TF-IDF and LLM comparators are model-only runners, report those as system-level comparisons and disclose the human review input. They are not a controlled comparison of model components. A controlled comparison would need the same independently produced evidence-relevance inputs supplied to each system; this repository does not implement that shared-input harness. Never let the gold annotators author the investigator review consumed by the full pipeline.

From `backend`, configure `DATABASE_URL` for the evaluation database and set the HMAC key through a protected environment/secret manager, then run:

```powershell
python -m evaluation.export_pipeline C:\protected\annotations\pipeline-map.jsonl C:\protected\outputs\full-pipeline.jsonl
python evaluation/evaluate.py C:\protected\outputs\full-pipeline.jsonl
python -m evaluation.export_pipeline --without-graph-linking C:\protected\annotations\pipeline-map.jsonl C:\protected\outputs\no-graph.jsonl
python evaluation/evaluate.py C:\protected\outputs\no-graph.jsonl
```

The exporter refuses input or output paths inside the repository and refuses to overwrite either output file. On POSIX systems it creates output files with mode `0600`; on Windows, inherited directory ACLs must restrict access. Check the adjacent `.metadata.json` sidecar for rule versions, corpus snapshot HMAC, timing boundary, metric definitions, and annotation HMAC before comparing runs. Record the code revision and the independent evidence-review procedure in the run record. The exporter is a measurement tool, not a product report, and its adverse metric flag must never be shown to an investigated subject.

### TF-IDF + logistic regression baseline runner

`baseline_tfidf_logreg.py` is a deterministic, dependency-free implementation of the text-classifier baseline. Its input is JSONL with `case_id`, UTC `submitted_at`, `split`, `campaign_id`, `submitted_text`, `gold_entities`, `gold_supported_entities`, and `gold_adverse_verdict`. Training learns token vocabulary and IDF from `train` rows only; the binary classifier uses fixed full-batch logistic regression settings in the script. Campaign overlap between splits is rejected. It emits test predictions in the scorer format, and prints metrics and a SHA-256 of the exact input bytes.

From `backend`, run:

```powershell
python -m evaluation.baseline_tfidf_logreg evaluation/authorized-input.jsonl evaluation/output/tfidf-logreg.jsonl
python evaluation/evaluate.py evaluation/output/tfidf-logreg.jsonl
```

This comparator predicts only a text-level adverse label. It intentionally emits no entity, campaign, or evidence-support predictions, so those metrics are empty/false and will reflect the classifier’s missing capabilities. Its adverse output exists only for offline measurement and must never be surfaced as a product verdict. The scorer's processing time covers per-case vectorization and prediction, not training or disk I/O.

### LLM with web search and graph ablation

No paid LLM or search provider is included. `llm_web_search.py` is a provider-neutral runner for an operator-supplied adapter. Its input is the pre-prediction annotated experiment JSONL described for `baseline_tfidf_logreg.py` (`case_id`, `submitted_at`, `split`, `campaign_id`, `submitted_text`, `gold_entities`, `gold_supported_entities`, and `gold_adverse_verdict`); it is not scorer-format predictions. The runner validates the exact schema, chronological splits, and campaign separation before calling the adapter. The adapter module must expose a `metadata` dictionary (`provider`, `model_version`, `prompt_sha256`, `retrieval_policy`, and `lawful_access: true`) and a callable that accepts a case with only `case_id`, `submitted_at`, and `submitted_text`. It must return `predicted_entities` (`[{"type":"...","value":"..."}]`), `predicted_campaign_id`, `predicted_supported_entities` (`[{"type":"...","value":"...","source_references":["..." ]}]`), `predicted_adverse_verdict`, and a non-empty `sources` array whose entries contain `source`, `reference`, ISO `retrieved_at`, and a SHA-256 `content_sha256` for the retrieved snapshot. Each predicted supported claim must cite references present in `sources`; the sidecar preserves this claim-to-source mapping. Optional `retrieval_error` is retained in the provenance sidecar. The runner only invokes the adapter for `split=test`, does not give it gold labels, measures per-case elapsed time, validates outputs, and writes predictions plus `<output>.provenance.jsonl`.

Example invocation after the operator has installed/configured their experiment adapter in that environment:

```powershell
python -m evaluation.llm_web_search evaluation/authorized-input.jsonl evaluation/output/llm-web-search.jsonl --adapter my_experiment_adapter:run_case
```

The adapter must enforce the annotation protocol and its chosen provider/search service's lawful access and terms; `lawful_access: true` is an operator attestation, not something this generic runner can verify. Preserve source snapshots/retrieval metadata, errors, and model configuration. The runner processes only test rows and emits test predictions without submitted text; it does not copy training or development rows to the output. Do not include raw secrets in metadata. Exclude a run from reported metrics if provenance or lawful retrieval cannot be captured. These offline adverse predictions are for comparison only and must never be surfaced as product verdicts.

`export_pipeline.py --without-graph-linking` is the supported runtime-data ablation export. It produces the scorer rows directly from the isolated no-link application run using that run's own persisted worker timing and source outputs. `ablate_graph.py` remains a secondary utility for transforming the output of an independently measured no-link execution when a timing file from that execution must be joined to a compatible full-pipeline output; it is not the preferred method because it copies non-campaign predictions rather than independently exporting that run's persisted outputs.

After producing the four scorer-format files, compare them with:

```powershell
python -m evaluation.compare_runs evaluation/output/tfidf-logreg.jsonl evaluation/output/llm-web-search.jsonl evaluation/output/no-graph.jsonl evaluation/output/full-pipeline.jsonl
```

The comparison command rejects differing test case sets or mismatched gold labels/timestamps. When the LLM/web-search run is included, it also requires the adjacent `.provenance.jsonl` sidecar to cover exactly the same test IDs and validates lawful-access attestation, provider/model/prompt/retrieval metadata, timestamped source references, and source snapshot hashes before reporting metrics. Provenance identifiers and descriptive fields must be non-empty strings (not values coerced with `str()`), retrieval timestamps must be timezone-aware, and hashes must be SHA-256 hex digests. LLM output must be produced by an operator-configured experiment; there is deliberately no hidden provider credential or automatic web-search dependency in the application.

No result is published by this repository. Populate `results/` only after the annotation and split protocol is completed; include confidence intervals and disclose sample sizes, missing labels, and exclusions.
