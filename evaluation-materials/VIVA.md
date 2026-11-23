# Casework presentation and viva

**Recruitment Scam Investigation and Campaign Intelligence Platform** · Team DevThree

| Member | Roll number | Individual contribution | File, test or demo action the member can explain |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

Fill the table and the editable contribution slide together. Each person should be able to explain the whole case journey, then identify one decision they made, the alternative they considered and how they checked the result. Confirm the attribution with the rest of the team before submission.

## Two-minute presentation

Start signed in as an investigator. Open the [vacancy walkthrough](https://rsiacdp-frontend.vercel.app/#vacancy-demo) in one tab and a completed fictional scanned case in another. Prepare or reopen JL-204 before starting the clock. The public sample can introduce the idea to visitors. The investigator workspace demonstrates the persisted system.

| Time | What to say | What to show |
| --- | --- | --- |
| 0:00–0:18 | “We are DevThree: ____, ____ and ____. Our project is the Recruitment Scam Investigation and Campaign Intelligence Platform. Imagine receiving an offer for a vacancy that really exists. How would you check whether its contact details belong to that vacancy?” | Title slide, then the fictional JL-204 offer. |
| 0:18–0:40 | “Casework keeps the model prediction and the evidence finding separate. The model looks for patterns learned from job postings. For a claim about a mailbox, an investigator needs something they can inspect. Here is the original source and here is the detail it supports.” | Open the fictional employer register. Point to the vacancy and its mailbox. |
| 0:40–1:13 | “The worker extracted this address from the submitted email. The corpus contains a record for that address with a source reference. After review, the finding confirms the listed mailbox. A copied vacancy could still be sent by somebody else.” | Return to the walkthrough. Point to the source, retrieval time and reviewed finding. Select **Show case connections** or **Refresh graph**. |
| 1:13–1:38 | “This edge connects the evidence to the identifier it checked. Across different cases, a reused address can also create a campaign lead. Here’s a second input type: the scanned offer shows where OCR found the address. Its report masks the contact by default.” | Point to the graph edge, switch to the completed scan and download Markdown. |
| 1:38–2:00 | “React calls FastAPI. The worker handles slow extraction and PostgreSQL preserves the case history. We tested separate users’ access, processing, linking and report masking. The next evaluation needs independently labelled Indian offers. Our contributions were ____, ____ and ____.” | Show one source-backed result and finish on the case. |

If only 90 seconds are available, omit the scan and cover contributions while the graph is visible. If the network drops, switch to the prepared [local walkthrough](http://localhost:5175/#vacancy-demo). If both services are unavailable, identify the screenshot on slide 6 as a saved example.

## Ten-minute route

| Time | Slide or action | Discussion |
| --- | --- | --- |
| 0:00–0:45 | 1–2 · Opening and problem | Introduce the team, describe a copied advert, and define the three outputs: risk estimate, claim finding and investigative link. |
| 0:45–1:50 | 3 · Architecture | Follow a submitted case across browser, API, queue, worker and report. Explain the local and hosted graph options. |
| 1:50–2:50 | 4 · Model and evidence | Explain the 0.35 risk threshold, three-word coverage guard and why a score cannot authenticate a recruiter. |
| 2:50–5:20 | 5 · Live demonstration | Open the source register, review its match and trace the graph. Compare the scanned case, its page location and its masked report. |
| 5:20–6:10 | 6 · Cross-case investigation | Show the reason for an exact email match. Discuss shared mailboxes and false associations. |
| 6:10–7:15 | 7 · Validation | Explain the full/no-link comparison and why generated evidence makes the fixture easier than real investigations. |
| 7:15–8:05 | 8 · Trade-offs | Discuss OCR throughput, the single hosted instance, access boundaries, a failed lookup and recovery. |
| 8:05–9:00 | 9 · Contributions | Each member names their own work, points to the relevant code or test and explains one challenge. Fill the slide before use. |
| 9:00–10:00 | 10 · Limitations and next experiment | Describe how to evaluate unseen campaigns, how the gold labels would be assigned, and which false positives would matter to a user. |

## Viva questions and evidence to open

**Three design decisions to rehearse.** A classifier-only design could return a quick score, but it would leave the user unable to trace a claim to its source. A web-search chatbot would make outcomes depend on changing search results and model wording; the curated corpus and versioned rules give the evaluator a repeatable example without external credentials. Keeping the graph as the primary database would make graph availability a prerequisite for case reads and recovery. Storing the case, sources and reviews in PostgreSQL lets the team rebuild the graph and run the smaller hosted deployment. Explain the benefit and cost of each choice using an actual screen or record.

**One API trace to know.** Personal registration uses `POST /api/auth/register` with `account_kind=personal`. A text case uses `POST /api/cases`; a file uses `POST /api/cases/upload`. The browser polls `GET /api/processing-status`, opens `GET /api/cases/{id}` and downloads `GET /api/cases/{id}/report?format=markdown`. Staff can inspect `GET /api/graph` and `GET /api/campaigns`. Use the browser Network panel during rehearsal to see a real status and payload. Keep cookies, tokens and passwords out of screenshots.

| Examiner’s question | Answer to develop in your own words | Open |
| --- | --- | --- |
| Where does a new case start? | The React intake form collects consent and the input. The API checks the session, consent version, type and size. It persists the case and a processing job. The UI can show queued status while the worker runs. | [API handlers](../backend/app/main.py), [frontend](../frontend/src/App.tsx) |
| What does the database look like? | A user owns cases. A case has extracted entities, evidence, findings, a processing job and audit events. A link references two case IDs. A corpus record identifies a reusable source; a case evidence record captures what a check returned at that time. | [SQLAlchemy models](../backend/app/models.py), [migrations](../backend/migrations/versions/) |
| What is actually learned? | The bundled Hiring Market logistic regression combines TF-IDF text features with numeric posting features. The runtime loads the saved coefficients. Exact matching, evidence rules and human dispositions are separate. Credit the upstream work when introducing the model. | [Runtime predictor](../backend/app/posting_model.py), [attribution](../README.md#how-to-read-the-results) |
| Why can two outputs disagree? | A copied advert can contain familiar, low-risk wording while the message asks for money. Equally, a high-risk wording score alone cannot establish who sent an offer. Read the excerpt and identify the exact claim the source can support. | [Finding rules](../backend/app/findings.py), [vacancy walkthrough](../frontend/src/VacancyWalkthrough.tsx) |
| How can someone challenge a match? | Follow the entity back to the source span or OCR region. Investigators can correct or reject an extraction and review a link. Corrections and recalculation leave audit events. Stronger human dispositions require a separate reviewer. | [Case and correction routes](../backend/app/main.py), [acceptance test](../scripts/test-compose-e2e.ps1) |
| Why keep PostgreSQL alongside a graph? | Transactions, case ownership and auditable changes belong in one authoritative store. Local Neo4j supplies a relationship projection that can be rebuilt. The hosted graph reads those relationships from PostgreSQL to fit the free-tier configuration. | [Graph projection](../backend/app/graph_outbox.py), [rebuild](../backend/app/graph_rebuild.py), [deployment](../HOSTING.md) |
| How do integrations fail? | A retrieval result records source, time and outcome. Empty or unavailable checks leave uncertainty. Configured public employer boards cover a limited set of employers. RDAP requires configuration and consent. I4C automated access is outside the implemented workflow. | [Source adapters](../backend/app/source_adapters.py), [source access review](../SOURCE_ACCESS_REVIEW.md) |
| How do you prevent one user from guessing another case ID? | The API checks ownership on personal case reads and reports. Staff access is separately provisioned. Cookie-authenticated writes need a CSRF token. The two-user integration test exercises list, detail, processing and report visibility. | [Authentication](../backend/app/security.py), [API integration tests](../backend/tests/test_api_flow.py) |
| What happens when demand increases? | An OCR-heavy queue on the single hosted instance can delay other cases. Measure queue wait separately from worker time. A separate worker pool can consume jobs from PostgreSQL; row locks with skip-locked selection coordinate workers. Shared private storage lets multiple workers access uploaded files. Test database connections, memory and OCR latency before increasing capacity. | [Worker](../backend/app/worker.py), [hosted setup](../HOSTING.md) |
| How would you recover lost data? | Restore a consistent database and copies of encrypted uploads with the correct key, then rebuild the graph. Local backup/restore has a dedicated CI job. A cloud disaster-recovery exercise still needs a separate restore target and verification. | [Local recovery guide](../LOCALHOST.md), [CI](../.github/workflows/ci.yml) |
| Which results can you defend? | In the recorded synthetic v2 rerun there were 36 held-out cases. Pairwise campaign F1 changed from 0.00 without linking to 1.00 with linking. The generator supplied both repeated identifiers and gold groups. This tests implementation behaviour. Real accuracy needs independently labelled cases. The historical 17,880-posting CSV run used an earlier evidence pipeline. | [Evaluation, data split and scoring](../backend/evaluation/README.md), [historical benchmark](../output/postings-benchmark/RESULTS.md) |
| What would you improve first? | Collect consented examples from distinct campaigns, split chronologically, keep related material together, and have independent reviewers annotate claims and sources. Report extraction F1, pairwise clustering F1, evidence-support precision, false-positive rate and processing-time percentiles with denominators. | [Evaluation protocol](../backend/evaluation/README.md) |
