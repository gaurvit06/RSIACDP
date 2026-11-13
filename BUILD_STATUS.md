# Build status

## 2026-11-03 20:17 (Asia/Calcutta) — Make keyboard focus visible across the interface

### Completed in this stage

- Continued the responsive/accessibility audit and found no explicit global focus-visible styling; the search input specifically suppressed its outline.
- Added high-contrast focus-visible rings to controls, a contrasting ring for controls in the dark sidebar, and a focus-within ring on the search wrapper.
- Added the rationale, computed color contrast and remaining manual-review limits to the engineering walkthrough and traceability matrix.

### Checks run and results

- In `frontend/`, `pnpm run build` passed.
- In `frontend/`, `pnpm run test:redaction` passed all 24 frontend tests.
- Calculated focus ring contrast ratios: dark green on white 6.53:1; light green on the sidebar background 11.69:1.
- Rebuilt the Compose web image; web healthcheck became healthy. The other four services remained healthy. `docker compose config -q` passed.
- No browser interaction was attempted. Ring placement/clipping and responsive layouts remain visually unverified because browser-origin approval remains declined.

### Files or components changed

- `frontend/src/style.css`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Focus colors meet the calculated contrast ratios against the selected backgrounds, but manual browser and assistive-technology review has not been performed.
- Hosted CI/deployment, production network/storage/security controls and authorized evaluation data remain pending external access.

### Exact next steps, in order

1. Continue the local requirements/security audit and address another concrete, verifiable gap.
2. Complete manual responsive, keyboard and assistive-technology review when browser-origin approval is granted.
3. Run hosted CI, operator deployment checks and authorized evaluation when their infrastructure/data are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `REQUIREMENTS_TRACEABILITY.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Full backend harness: `python run_ci_tests.py` in the dependency-pinned worker image with disposable SQLite and `/tmp` upload paths.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 20:15 (Asia/Calcutta) — Add reproducible confidence intervals to evaluation output

### Completed in this stage

- Compared the evaluation guide with the scorer and found it documented confidence intervals that the implementation did not produce.
- Added deterministic 95% percentile-bootstrap intervals for entity F1, campaign pairwise F1, evidence-support precision, verdict false-positive rate, processing mean and processing p95. Defaults are 1,000 resamples and seed `20261103`; output includes method, valid resample count, seed and minimum-defined-resample policy.
- Per-case metrics resample test cases; campaign pairwise F1 resamples gold campaign groups as clusters and keeps each sampled group together. Unlabeled cases are singleton groups. Undefined intervals stay null when fewer than 80% of resamples are valid.
- Reworked pairwise campaign counts to use contingency-count arithmetic instead of materializing every pair, avoiding quadratic set growth inside each bootstrap replicate.
- Verified `compare_runs.py` retains each system's confidence-interval metadata in the four-system comparison output, including the LLM/web-search run after its provenance checks.
- Updated evaluation instructions, requirements traceability and the engineering walkthrough. Actual evaluation results remain pending authorized data.

### Checks run and results

- Focused evaluation suite in the dependency-pinned worker image: all 13 tests passed after assertions for deterministic intervals, undefined intervals, invalid configuration and four-system interval propagation.
- Full backend CI harness in a disposable, network-isolated container: 224 unit tests ran (including 2 opt-in PostgreSQL skips), 15 API-flow tests and 2 proxy tests passed (exit code 0). The API suites used isolated test data. No production database or upload volume was mounted.
- The first full-harness invocation used a read-only source mount and two tests failed only because they write ignored baseline fixtures to `backend/.test-runtime`. Reran with a writable workspace mount; the complete harness passed. Confirmed the baseline fixtures were removed by test cleanup.
- No external provider, authorized dataset or real case data was used. No evaluation results were generated.

### Files or components changed

- `backend/evaluation/evaluate.py`
- `backend/evaluation/README.md`
- `backend/tests/test_evaluation.py`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The scorer now supports uncertainty intervals, but all actual metric results are pending an authorized, time-separated Indian recruitment-scam dataset and independently produced full/no-graph runs.
- Bootstrap intervals quantify resampling uncertainty only. They do not address annotation bias, source coverage, temporal drift or dataset representativeness.
- Hosted CI/deployment, operator security controls and manual browser/accessibility review remain unverified.

### Exact next steps, in order

1. Continue the local requirements audit and implement another concrete gap with focused checks.
2. Run the authorized time-separated evaluation once labels, lawful provider configuration and isolated application runs are available.
3. Run hosted CI/deployment and manual browser/accessibility review when a remote, operator environment and browser-origin approval are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `REQUIREMENTS_TRACEABILITY.md`, and inspect `git status --short`.
- Focused evaluation checks: in the dependency-pinned worker image, `python -m unittest discover -s tests -p test_evaluation.py -v`.
- Full backend harness: `python run_ci_tests.py` in the dependency-pinned worker image with a disposable SQLite database and `/tmp` upload path; allow its ignored baseline fixtures in `backend/.test-runtime` to be created and cleaned.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 20:10 (Asia/Calcutta) — Reflect the configured evidence-source mode in the UI

### Completed in this stage

- Continued the requirements audit and found that the signed-in header always claimed “LOCAL EVIDENCE MODE,” even when the operator enables optional RDAP lookups.
- Added a source-policy state derived from `/api/policy`. The UI now reports local-only, consent-gated RDAP, loading, or unavailable states, and does not claim local-only operation before policy is known.
- Added focused unit coverage for each source-mode label and documented the limitation in `ENGINEERING_WALKTHROUGH.md` and `REQUIREMENTS_TRACEABILITY.md`.

### Checks run and results

- In `frontend/`, `pnpm run build` passed (TypeScript and Vite).
- In `frontend/`, `pnpm run test:redaction` passed all 24 frontend tests, including 3 new source-mode tests.
- Rebuilt the Compose web image. All five services report healthy. `docker compose config -q` passed.
- Changed-file trailing-whitespace scan passed. No browser interaction or external RDAP request was made.

### Files or components changed

- `frontend/src/App.tsx`
- `frontend/src/evidence-mode.ts`
- `frontend/tests/evidence-mode.test.ts`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The source-mode label logic is unit-tested and bundled, but the browser-rendered header remains visually unreviewed due the declined browser-origin approval.
- RDAP is still default-off; production egress controls and live provider terms/behavior remain unverified. Continue auditing local requirements and security gaps.
- Hosted CI/deployment and authorized evaluation data remain external dependencies.

### Exact next steps, in order

1. Continue the local code audit against `REQUIREMENTS_TRACEABILITY.md` and implement another concrete gap with focused checks.
2. Complete hosted CI/deployment and evaluation when a remote, operator infrastructure, provider approval, and authorized dataset are available.
3. Complete manual browser, keyboard, assistive-technology, and responsive review only if browser-origin approval is granted.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `REQUIREMENTS_TRACEABILITY.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend check: run `backend/run_ci_tests.py` in the dependency-pinned worker image with `APP_ENV=testing`, a disposable SQLite database, and `/tmp` upload path.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 20:08 (Asia/Calcutta) — Add shared keyboard focus management to investigation dialogs

### Completed in this stage

- Audited custom overlays in case intake, evidence review, reviewer account actions, local evidence-record retirement, and public correction access. Several lacked focus containment, focus restoration, or dialog semantics.
- Added a reusable focus-management hook. It moves focus into an open dialog, contains Tab/Shift+Tab navigation, handles Escape through the dialog's current close action, and restores focus on close. Busy account/source operations cannot be dismissed by Escape.
- Applied accessible dialog semantics and labels to case intake and public correction access and shared focus handling with evidence review, account actions, and source retirement. The authenticated help guide from the preceding stage retains its own focus handling.
- Added the engineering rationale and manual-review limitation to `ENGINEERING_WALKTHROUGH.md`.

### Checks run and results

- In `frontend/`, `pnpm run build` passed with TypeScript and Vite; final bundle is 308.27 kB JS (90.50 kB gzip).
- In `frontend/`, `pnpm run test:redaction` passed all 21 frontend tests. There is no automated DOM/browser interaction test for dialog behavior in this repository.
- Rebuilt the Compose web image. API, database, Neo4j, worker and web all report healthy. `docker compose config -q` passed.
- Changed-file trailing-whitespace scan passed. No browser interaction was attempted; manual keyboard, visual and assistive-technology review remain pending due the declined browser-origin approval.

### Files or components changed

- `frontend/src/App.tsx`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The shared dialog behavior is bundled and type-checked but has not been manually verified with a browser or assistive technology. Browser-origin approval remains declined.
- Continue the local requirements/security audit. Hosted CI/deployment, operator security controls, and authorized time-separated evaluation data remain external dependencies.

### Exact next steps, in order

1. Continue auditing concrete locally addressable gaps against `REQUIREMENTS_TRACEABILITY.md`; run focused checks after each change.
2. Complete hosted CI/deployment and authorized evaluation when a remote, operator infrastructure, access approvals, and dataset are available.
3. Complete manual keyboard, screen-reader and responsive visual review only if browser-origin approval is granted.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `REQUIREMENTS_TRACEABILITY.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend check: run `backend/run_ci_tests.py` in the dependency-pinned worker image with `APP_ENV=testing`, a disposable SQLite database, and `/tmp` upload path.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 20:06 (Asia/Calcutta) — Make the investigator help control functional

### Completed in this stage

- Re-read current status, build plan, requirements matrix, and Git state. Confirmed the working tree remains untracked with no configured Git remote.
- Replaced the authenticated shell's inactive Help control with a workflow guide covering consented intake, extraction review, evidence results, campaign links, redacted sharing, and correction requests. Added safe-language reminders and accessible dialog semantics, keyboard close/trap behavior, and focus restoration.
- Recorded the implementation and its limits in `ENGINEERING_WALKTHROUGH.md`.

### Checks run and results

- In `frontend/`, `pnpm run build` passed (TypeScript and Vite production bundle).
- In `frontend/`, `pnpm run test:redaction` passed all 21 frontend tests.
- Existing disposable verification Compose project was inspected after the web image rebuild: API, database, Neo4j, worker, and web containers all reported healthy. No browser interaction was attempted; visual and manual keyboard review remain pending because browser-origin approval was declined.
- No backend source changed in this stage. No external provider or real data was queried.

### Files or components changed

- `frontend/src/App.tsx`
- `frontend/src/style.css`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The Help dialog has code-level focus management but has not received manual browser or assistive-technology review.
- Continue the local requirements/security audit for further addressable product gaps. Hosted CI/deployment, operator security controls, and an authorized evaluation dataset remain external dependencies.

### Exact next steps, in order

1. Continue auditing the current routes and UI against `REQUIREMENTS_TRACEABILITY.md`; prioritize a concrete local functional or security gap and add focused verification.
2. After local gaps are addressed, complete hosted CI/deployment and evidence-based evaluation when a remote, operator infrastructure, access approvals, and authorized annotations are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `REQUIREMENTS_TRACEABILITY.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend check: run `backend/run_ci_tests.py` in the dependency-pinned worker image with `APP_ENV=testing`, a disposable SQLite database, and `/tmp` upload path.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 20:00 (Asia/Calcutta) — Add measured campaign-link timing and a persisted no-link evaluation mode

### Completed in this stage

- Re-read the requirements matrix and evaluation tooling. The pipeline exporter used only worker duration, while campaign-link recomputation was investigator-triggered and had no persisted duration. The graph ablation utility required an externally produced timing file and did not export the isolated no-link pipeline's own persisted outputs.
- Added monotonic campaign-link timing to the `campaign_links_recomputed` audit event with duration, current rule version, threshold, and matched case count. Kept `ProcessingJob.processing_ms` as worker-only duration; no migration or prior-record rewrite was necessary.
- Updated the evaluation exporter: full mode requires a current-rule campaign-link recomputation after the successful worker run and adds that per-case duration to the scorer's processing time. It rejects missing/stale link timing, mismatched rule versions, and malformed durations.
- Added `--without-graph-linking` so an isolated no-link run exports its own persisted extraction/evidence/finding outputs and worker duration, clears campaign predictions, and refuses any campaign-link audit history or persisted case links. It does not copy full-pipeline predictions or link timings.
- Updated evaluation documentation to specify isolated matched databases, same authorized inputs/corpus/review scope, full link recomputation after all cases complete, direct ablation export, timing boundaries, and limitations. Added tests for timing aggregation, full-run guards, no-graph guards/outputs, and CLI selection.
- Rebuilt API/worker images and reran the full backend harness against the updated source.

### Checks run and results

- Backend CI harness inside the dependency-pinned worker image: 222 unit tests ran, 2 opt-in PostgreSQL tests skipped, 0 failures; 15 API-flow tests passed; 2 proxy-header tests passed; exit code 0.
- New and updated tests verify campaign-link duration in audit events, addition to full-pipeline measurement, rejection of missing/stale current-rule timings, UTC datetime freshness including sub-second boundaries, graph-off refusal when links/history exist, null campaign predictions, worker-only time in graph-off mode, and CLI option routing.
- API/worker images rebuilt. Final Compose status showed all five services healthy and API readiness returned HTTP 200. `docker compose config -q` passed. Removed the named temporary copied tests, SQLite DB, upload directory, and output log; verified all are absent. Changed-file trailing-whitespace scan and `git diff --check` passed.
- No external source, model provider, or real dataset was used. No browser/UI interaction was attempted.

### Files or components changed

- `backend/app/main.py`
- `backend/evaluation/export_pipeline.py`
- `backend/evaluation/README.md`
- `backend/tests/test_api_flow.py`
- `backend/tests/test_evaluation_export.py`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- No authorized time-separated Indian recruitment-scam dataset or actual baseline results are available. The LLM/web-search experiment remains an operator-configured adapter; the project has no hidden provider dependency.
- A full comparison requires an isolated authorized full-pipeline run with every mapped case processed/reviewed and campaign links refreshed, plus an otherwise matched isolated no-link run. The current local test fixtures verify exporter behavior but are not research evaluation results.
- Hosted CI/deployment, production network egress policy, operator TLS/storage/key custody, authorized evaluation data, and previously unreviewed visual browser flows remain pending external access. No commit was made; the working tree has no configured Git remote.

### Exact next steps, in order

1. Continue the local requirements/security audit from `REQUIREMENTS_TRACEABILITY.md` and address another concrete local gap.
2. Run hosted CI/deployment and evaluation once the remote, operator infrastructure, written access/retention terms, and authorized dataset are available. Complete browser review only if local-origin approval is granted.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Backend check: run `backend/run_ci_tests.py` in the dependency-pinned worker image with `APP_ENV=testing`, a disposable SQLite database, and `/tmp` upload path; test sources are not baked into the runtime images.
- Evaluation full export: `python -m evaluation.export_pipeline ANNOTATIONS.jsonl OUTPUT.jsonl`; true ablation export: `python -m evaluation.export_pipeline --without-graph-linking ANNOTATIONS.jsonl OUTPUT.jsonl` from `backend/` after preparing independent protected runs.
- Frontend checks: from `frontend/`, `pnpm run build` and `pnpm run test:redaction`.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 19:55 (Asia/Calcutta) — Pin optional RDAP requests to validated public DNS destinations

### Completed in this stage

- Re-read project instructions (no `AGENTS.md` files were present), `BUILD_STATUS.md`, `BUILD_PLAN.md`, requirements traceability, and Git status. The working tree is untracked and there is still no configured Git remote.
- Audited the optional RDAP adapter. It already required separate consent, rejected private IP literals and unsafe URL forms, disabled environment proxy inheritance, rejected redirects, and bounded response size/time. Found that the HTTP client performed hostname resolution after validation, so DNS answers were not pinned.
- Bumped the RDAP adapter version to `iana-rdap-domain-v2-dns-pinned`. Each lookup now resolves the registry hostname, rejects the entire answer set when any returned IPv4/IPv6 address is not globally routable, connects to a selected validated IP, and retains the original hostname for the HTTP `Host` header and TLS SNI/certificate verification. Proxies remain disabled; redirects and unsafe URL forms remain rejected.
- Tightened hostname label validation and added offline regression tests for public pinning, Host/SNI preservation, private and mixed DNS answers, malformed hosts, redirects, consent, and neutral empty outcomes.
- Updated README deployment guidance and the requirements traceability matrix to state that RDAP is default-off and production still needs outbound firewall policy blocking private, link-local, metadata, and internal destinations.
- Rebuilt the API and worker images. The final backend harness passed after the last adapter and test changes.

### Checks run and results

- Backend CI harness in the dependency-pinned worker image: 216 unit tests ran, 2 opt-in PostgreSQL tests skipped, 0 failures; 15 API-flow tests passed; 2 proxy-header tests passed; exit code 0.
- Final run included the RDAP pinning and hostile-DNS regression tests and ran with a temporary SQLite DB/upload path, no Neo4j or upload-key configuration, and a test-only JWT.
- API and worker images rebuilt successfully; API readiness returned HTTP 200.
- Removed only the temporary copied test sources, SQLite DB, upload directory, and test log from the worker container. A follow-up check confirmed all four named paths are absent; production volumes were not used for tests.
- `docker compose config -q`: passed. Final Compose status showed all five services healthy; API readiness was HTTP 200. Changed-file trailing-whitespace scan and `git diff --check` passed.
- The web image was not changed in this stage. No browser or UI interaction was attempted.

### Files or components changed

- `backend/app/source_adapters.py`
- `backend/tests/test_rdap_adapter.py`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Host DNS lookup uses the system resolver, which is not independently time-bounded by the adapter's HTTP connect timeout. Host-level outbound egress controls remain mandatory. RDAP stays disabled by default until deployment network policy and provider terms are verified.
- No external RDAP request was made during tests; live provider behavior, external logging/retention terms, and DNS behavior remain unverified.
- Hosted CI/deployment, operator TLS/storage/key custody, and authorized time-separated dataset evaluation remain external work. Browser visual review is still unavailable due the previously declined local-origin approval. No commit was made.

### Exact next steps, in order

1. Continue the local requirement and security audit from `REQUIREMENTS_TRACEABILITY.md`, prioritizing concrete gaps that can be verified in this environment.
2. Complete authenticated visual review only if local-origin approval is granted; perform hosted CI, deployment, egress-policy, and dataset evaluation when the required external access and authorized data are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Backend check: run `backend/run_ci_tests.py` in the dependency-pinned worker image with `APP_ENV=testing`, a disposable SQLite database and `/tmp` upload directory. Never use a production database for tests.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 19:51 (Asia/Calcutta) — Move the browser to CSRF-protected HttpOnly sessions

### Completed in this stage

- Continued from the 02:00 checkpoint and inspected the in-progress cookie-session implementation before making changes. The API already supported an HttpOnly cookie mode, CSRF checks for unsafe requests, bearer compatibility, and logout revocation; the frontend was still persisting and sending bearer tokens.
- Fixed the cookie API test isolation: the preceding registration-limit test intentionally throttles the shared integration-test client address, so the cookie test now clears only its isolated SQLite throttle rows before account creation.
- Preserved direct-call compatibility for the account-registration route while adding an HTTP `Response` for cookie setting. The first combined test run exposed this signature regression in two unit tests; route parameter order was corrected.
- Migrated frontend sign-in and registration to request `session_mode: cookie`; browser requests now use same-origin credentials, send the session-bound CSRF value only in `X-CSRF-Token` for unsafe methods, and keep that value only in React memory. The app restores an existing cookie session through `/api/auth/me`, removes sessionStorage bearer persistence, and retains the 401 session-reset behavior.
- Documented the browser cookie flow and bearer-only integration compatibility in README and requirements traceability. Added an engineering walkthrough entry for design, test findings, and deployment caveats.
- Rebuilt the local API, worker and web images. All five Compose services reported healthy after the web rebuild.

### Checks run and results

- Backend CI harness inside the dependency-pinned worker image: 214 unit tests passed, 2 opt-in PostgreSQL tests skipped; 15 API-flow tests passed; 2 proxy-header tests passed. The API flow includes cookie flags, no returned bearer token, `/me` CSRF retrieval, unsafe request rejection without CSRF and acceptance with CSRF, logout revocation, and cookie login.
- Frontend `pnpm run build`: passed.
- Frontend `pnpm run test:redaction`: 21 passed, 0 failed.
- Local Compose API, worker and web images rebuilt successfully. `docker compose ps` showed all five services healthy; API readiness returned HTTP 200.
- No UI/browser interaction was attempted. Visual authenticated-browser review is still unverified due the previously declined browser-origin approval.

### Files or components changed

- `backend/app/schemas.py`
- `backend/app/security.py`
- `backend/app/main.py`
- `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`
- `frontend/src/auth-session.ts`
- `frontend/tests/auth-session.test.ts`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The first test attempt failed because of the shared test-client registration throttle; after isolating the cookie test, it passed. The next complete run exposed two direct-handler tests depending on route parameter order; that compatibility was restored and the final 214 + 15 + 2 harness run passed. A subsequent harness attempt used root-owned copied test files and failed two file-creation tests; correcting container file ownership made the complete run pass. These were test harness setup/compatibility findings, not unresolved failing checks.
- The browser uses the cookie flow in built source, but end-to-end cookie behavior through the hosted browser has not been visually inspected. Deployment must set an HTTPS `WEB_ORIGIN` so the session cookie receives `Secure`; browser-origin approval is still pending.
- Hosted CI/deployment, operator TLS/storage/key custody, public-source integrations, and authorized time-separated dataset evaluation remain external work. No Git remote is configured; the local project remains uncommitted.

### Exact next steps, in order

1. Continue the local requirement/security audit from `REQUIREMENTS_TRACEABILITY.md`, addressing remaining verifiable gaps and documenting them.
2. Complete authenticated visual review only if local-origin approval is granted; run hosted CI/deployment/evaluation when the remote, operator infrastructure, and authorized dataset are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend check: use the dependency-pinned `worker` image with `backend/run_ci_tests.py`, `APP_ENV=testing`, temporary SQLite database and `/tmp` upload path; see README/CI for exact harness invocation.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 02:00 (Asia/Calcutta) — Expire the browser session after protected API 401 responses

### Completed in this stage

- Re-read the current status and verified the main local Compose stack was healthy and API readiness returned HTTP 200.
- Static security scan found no unsafe HTML/code execution sinks (`dangerouslySetInnerHTML`, `innerHTML`, `document.write`, `eval`, `new Function`) in the frontend sources reviewed. Checked the session path and found that an already-open tab could retain an expired/revoked bearer token after a later API 401.
- Added `frontend/src/auth-session.ts` and integrated it into the API wrapper and app state. Protected 401 responses now clear the tab token and investigator state and return to sign-in; the expected logout route, 403, 429, and 5xx do not trigger session expiry.
- Added focused frontend tests covering 401 classification, non-auth response boundaries, and token/state clearing.
- Rebuilt only the local web service. The served page and JS asset returned HTTP 200 and the asset contained the session-expiry handler/message. The web container became healthy; the other four services remained healthy and API readiness stayed HTTP 200.
- Updated the README, requirements traceability, and engineering walkthrough with behavior, tests, and the remaining storage/browser-security limitation.

### Checks run and results

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 21 passed, 0 failed.
- Served app page: HTTP 200; served bundle includes unauthorized-session event and user-facing expiry notice.
- Main Compose health: all five services healthy after web rebuild; API readiness HTTP 200.
- No browser interaction was attempted; visual session behavior remains unverified due the previously declined browser-origin approval.

### Files or components changed

- `frontend/src/auth-session.ts`
- `frontend/src/App.tsx`
- `frontend/tests/auth-session.test.ts`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Bearer tokens remain stored in tab-scoped `sessionStorage`, which is accessible to same-origin scripts. An HttpOnly cookie/session migration is not implemented; browser security review and deployment-specific CSRF/session design remain pending.
- Corrections/graph-filter visual review remains blocked by declined browser-origin access. Hosted CI/deployment and authorized evaluation remain pending external setup/data.

### Exact next steps, in order

1. Re-run documentation whitespace and Compose configuration checks after the documentary edits.
2. Continue the local security/privacy audit for additional actionable gaps.
3. Complete browser review only if local-origin approval becomes available; hosted deployment and evaluation require operator infrastructure and authorized data.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:57 (Asia/Calcutta) — Verify live correction propagation end to end

### Completed in this stage

- Re-read the correction and graph requirements. The E2E previously checked public request status transitions but not an actual case correction through all persisted downstream records.
- Extended `scripts/test-compose-e2e.ps1` to apply a synthetic correction to a confirmed extracted email. It checks corrected normalization/review state, resolved token-protected public status, correction and findings-recomputation timeline actions, redaction of both values in the report, and the updated Neo4j campaign edge.
- Ran the new test with the live Neo4j outage/recovery check in a separate disposable Compose project.
- The first run surfaced an overly strict assertion: because the old/new fabricated emails shared `example.com`, the rule correctly retained a 15-point `low_signal` domain link. Updated the assertion to require the exact-email match be gone and the remaining domain-only signal be below threshold. Reran from fresh disposable volumes; the complete flow passed.
- Cleaned the separate containers, network, PostgreSQL/Neo4j/upload volumes, environment file, and override. Main app API readiness remained HTTP 200.
- Updated `.github/workflows/ci.yml` so Compose E2E now exercises actual correction propagation before backup/restore; updated README, requirements traceability, and the engineering walkthrough.

### Checks run and results

- PowerShell parser for `scripts/test-compose-e2e.ps1`: passed.
- Prettier YAML parse for `.github/workflows/ci.yml`: passed.
- Disposable Compose configuration and all-five-service startup: passed.
- `scripts/test-compose-e2e.ps1 -BaseUrl http://127.0.0.1:18080 -EnvironmentFile backend/.test-runtime/correction-e2e-20261103.env -ComposeProjectName rsaicdp-correction-e2e-20261103 -ExerciseNeo4jOutage -AllowSyntheticWrites`: passed on a fresh isolated stack.
- Verified live result: correction persisted, audit/finding events present, original and corrected email masked in report, graph contained only below-threshold domain signal; Neo4j outage fallback/recovery also passed.
- Disposable cleanup check: containers/volumes/temp config removed; main API readiness HTTP 200.
- Post-documentation PowerShell parse, workflow YAML parse, main Compose configuration, and whitespace scan: passed.

### Files or components changed

- `scripts/test-compose-e2e.ps1`
- `.github/workflows/ci.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Corrections and graph-filter visual inspection remains pending because browser-origin approval was declined.
- Hosted CI/deployment, production storage/key custody/TLS/egress verification, and authorized time-separated evaluation remain unverified.

### Exact next steps, in order

1. Continue the requirement-by-requirement audit for remaining local workflows and security/privacy controls.
2. Keep Corrections/graph-filter visual inspection pending until browser-origin approval is granted.
3. Run hosted CI, deployment and labeled-data evaluation when the remote/runner, operator infrastructure and authorized dataset are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- Compose E2E needs `-AllowSyntheticWrites`; `-ExerciseNeo4jOutage` stops and restarts Neo4j for the explicitly selected Compose project, so only use a disposable named project/environment.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:52 (Asia/Calcutta) — Verify live graph fallback and Neo4j recovery

### Completed in this stage

- Re-read the requirement matrix and graph API implementation. PostgreSQL-derived fallback existed in code and unit tests, but live outage/recovery was still listed as unverified.
- Added opt-in `-ExerciseNeo4jOutage` to `scripts/test-compose-e2e.ps1`. The existing synthetic-write guard remains required. The script can target an explicit disposable Compose project/environment file, stops only that project's Neo4j, verifies PostgreSQL-backed API readiness and graph inclusion for both synthetic cases, restarts Neo4j in `finally`, and checks the recovered projection.
- Wired the live outage/recovery step into the Compose E2E GitHub Actions workflow before encrypted restore.
- Ran the updated end-to-end script successfully against a separate disposable project. API readiness stayed HTTP 200; graph switched to `postgresql-derived` while Neo4j was stopped; after restart the Neo4j projection contained both synthetic cases.
- Cleaned the disposable containers, network, database/Neo4j/upload volumes, generated environment file and port override. Main API readiness stayed HTTP 200; no main or unrelated volume was touched.
- Updated the requirements matrix, README CI description, and engineering walkthrough with actual outcome and limitations.

### Checks run and results

- PowerShell syntax parser for `scripts/test-compose-e2e.ps1`: passed.
- Prettier YAML parse for `.github/workflows/ci.yml`: passed.
- Disposable Compose config with separate ports/subnet: passed after correcting the temporary port override to replace, rather than append, mappings.
- `scripts/test-compose-e2e.ps1 -BaseUrl http://127.0.0.1:18080 -EnvironmentFile backend/.test-runtime/graph-outage-20261103.env -ComposeProjectName rsaicdp-graph-outage-20261103 -ExerciseNeo4jOutage -AllowSyntheticWrites`: passed.
- Disposable project cleanup: containers and volumes removed; generated environment/override files deleted.
- Main app readiness after cleanup: HTTP 200.
- Final PowerShell parse, workflow YAML parse, main Compose config, documentation whitespace scan, and disposable-resource cleanup checks: passed.

### Files or components changed

- `scripts/test-compose-e2e.ps1`
- `.github/workflows/ci.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Visual inspection of Corrections and graph filters remains pending; the browser approval gate declined local-origin access.
- Hosted CI/deployment, production storage/key custody/TLS/evidence-egress verification, and authorized time-separated evaluation remain unverified.

### Exact next steps, in order

1. Continue the local requirement audit for remaining workflows and privacy/security controls with current runnable code evidence.
2. Keep the visual review item pending; the browser origin gate must grant access before that inspection can proceed.
3. Run hosted CI and operator-owned deployment/evaluation checks when the required remote, hosting configuration and authorized dataset are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Main local app remains at `http://127.0.0.1:5173/`; API readiness is `http://127.0.0.1:8000/health/ready`.
- The outage test requires `-AllowSyntheticWrites`; pass an explicit disposable project name and environment file before allowing it to stop Neo4j.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:48 (Asia/Calcutta) — Re-run backend and frontend checks in the current worktree

### Completed in this stage

- Re-read the updated requirements matrix. `git remote -v` returned no configured remote; hosted CI cannot be triggered from this checkout.
- Built the frontend and ran its current test suite: build passed; all 18 tests passed.
- The host Python environment lacks FastAPI, so the backend suite could not run directly there. Used the healthy worker image with pinned dependencies and copied only test sources, evaluation modules, migrations and the harness into a temporary `/tmp/rsaicdp-test-runner` directory.
- The first container run inherited the worker's upload-encryption and Neo4j runtime settings, which did not match backend CI and caused environment-specific failures. Reran with a temporary SQLite database, `/tmp` upload path, blank optional upload key and Neo4j settings, and a test-only JWT. The corrected run passed 214 unit tests (2 opt-in PostgreSQL skips), 14 API-flow tests, and 2 proxy-header tests.
- Removed the test runner, SQLite database, temporary upload path and captured logs from the worker container's `/tmp`; verified the paths were absent afterward.
- Updated traceability and engineering walkthrough to reflect the current exact frontend test count, current backend run, unavailable Git remote, and declined browser-origin approval for the remaining visual inspection.

### Checks run and results

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 18 passed, 0 failed.
- `backend/run_ci_tests.py` in the worker image with isolated CI-like environment: 214 unit tests passed, 2 skipped; 14 API-flow tests passed; 2 proxy-header tests passed.
- Direct host backend run: did not start because host Python lacks FastAPI; the suite was run successfully in the dependency-pinned worker image instead.
- Test artifact cleanup check: runner directory, SQLite file and temporary upload directory absent.
- `docker compose ... config --quiet`: passed; API readiness HTTP 200; PostgreSQL, Neo4j, API, worker and web all healthy after the test run.
- Strict trailing-whitespace check across `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`, and `REQUIREMENTS_TRACEABILITY.md`: passed.
- No Git remote configured; hosted CI not run.

### Files or components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Corrections and graph-filter visual review remains incomplete because the browser origin approval gate declined access; no alternate browser or direct-HTTP route was attempted.
- CI on a hosted runner, hosted deployment/TLS/storage/key custody, and authorized evaluation labels/results remain unavailable.

### Exact next steps, in order

1. Continue a local requirement audit for implementation gaps that can be fixed and verified without browser-origin access.
2. Recheck current health and repository status before further code edits; preserve the main Compose data volumes.
3. Run hosted CI/deployment checks when a remote/runner and operator-owned host configuration are available; run evaluation only with authorized time-separated labels.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Main app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:45 (Asia/Calcutta) — Verify current-fingerprint live restore on disposable Compose

### Completed in this stage

- Re-read the checkpoint and checked the worktree and Docker state. The project remains untracked; no commit was created. The primary local Compose app and API remained healthy.
- Started an isolated disposable Compose project with its own ports, network, database volume, and upload volume. Corrected a static proxy-address mismatch in the temporary test override before the successful start.
- Ran the Compose E2E workflow with synthetic text and PDF intake; extraction/source spans, local corpus outcome, deterministic link, graph/report masking, and PDF page/span checks passed.
- Ran the actual encrypted backup/restore test against only the disposable project. The RSAICDPBK2 manifest fingerprint passed; restore rolled back the synthetic case-title change, restored the one private upload, returned API readiness HTTP 200, and rebuilt Neo4j from three synthetic cases.
- Removed the disposable project and its own volumes. Docker inspection found no remaining project containers or volumes; main app API readiness remains HTTP 200. No persistent or unrelated volume was restored or removed.
- Updated the engineering walkthrough and requirements matrix to record current live evidence and retain production/hosted limitations.

### Checks run and results

- Disposable live Compose E2E with synthetic PDF: passed.
- `scripts/test-compose-backup-restore.ps1 -AllowSyntheticWrites -RequirePrivateUpload` against disposable Compose: passed; title hash restored, upload count remained one, readiness 200, graph rebuild completed.
- Docker cleanup inspection for disposable project: no matching containers or named volumes remained.
- Main app API readiness: HTTP 200.
- PowerShell parser for `scripts/test-compose-backup-restore.ps1`: passed using its parser error collection. An initial validation wrapper incorrectly treated the returned syntax tree as an error list and stopped; the corrected parser invocation reported no syntax errors.
- Prettier YAML parse of `.github/workflows/ci.yml`: passed.
- `docker compose --project-name rsaicdp-verification-20261103 --env-file backend/.test-runtime/compose-20261103.env config --quiet`: passed.
- Trailing-whitespace scan of the three updated Markdown documents: passed.
- Removed only the generated disposable test override, wrapper, and synthetic PDF from `.test-runtime`; persistent project files and volumes were untouched.
- Attempted visual review using the in-app browser, but its origin approval gate explicitly reported that access to `http://127.0.0.1:5173` was declined. Did not retry via another browser or direct HTTP/UI workaround.

### Files or components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Corrections and graph-filter visual inspection remains incomplete because browser origin access was declined by the approval gate; prior desktop UI navigation also could not establish URL confidence. Hosted CI has no configured remote/runner, and production host/TLS/secret custody remain unverified.
- Authorized time-separated Indian recruitment-scam labels are unavailable, so evaluation metrics/results remain pending.
- Neo4j emitted an informational CartesianProduct notification during the successful rebuild; no failure occurred, but query efficiency should be revisited if graph size grows.

### Exact next steps, in order

1. Run documentation parser, Compose config, and whitespace checks; update this checkpoint with exact outcomes.
2. Continue the requirement-by-requirement local completion audit using code, API, and test evidence; UI inspection needs an approved browser origin and will not be attempted through an alternate path.
3. Run hosted CI/deployment checks when a remote/runner and operator-owned hosting configuration are available; run evaluation only with authorized time-separated labels.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Main local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- Disposable restore validation uses `scripts/test-compose-backup-restore.ps1 -AllowSyntheticWrites -RequirePrivateUpload` only inside a freshly created disposable Compose project; do not run it against persistent or production data.
- No commit. Leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:38 (Asia/Calcutta) — Add live encrypted restore to disposable Compose CI

### Completed in this stage

- Re-read the current checkpoint and inspected the Compose E2E workflow before editing. Repository files remain untracked; no commit was created.
- Added `scripts/test-compose-backup-restore.ps1`, guarded by `-AllowSyntheticWrites` and required disposable database environment variables. It creates an ephemeral backup key, runs the real encrypted backup, verifies the RSAICDPBK2 manifest key fingerprint, changes only a synthetic case title, restores database and private upload artifacts, and verifies the original title hash and API readiness.
- Wired the live restore regression into the Compose E2E GitHub Actions job after synthetic case/PDF intake and before final graph rebuild. The workflow tears down the disposable project/volumes in its existing `always()` cleanup.
- Updated README to describe this CI coverage and its still-pending hosted execution.
- Did not run this live restore against the current local database; an earlier direct live-restore command was rejected by execution policy. The new test is intended for the disposable CI project.

### Checks run and results

- PowerShell parser for `scripts/test-compose-backup-restore.ps1`: passed.
- Prettier YAML parse for `.github/workflows/ci.yml`: passed.
- `docker compose --project-name rsaicdp-verification-20261103 --env-file backend/.test-runtime/compose-20261103.env config --quiet`: passed.
- Strict whitespace scan across all six files changed in this stage: passed. All repository project files remain untracked; no tracked build artifact or commit was introduced.
- Live disposable backup/restore step: not run locally; it will run only in the CI Compose project. Hosted CI remains unavailable until a remote/runner is configured.

### Files or components changed

- `scripts/test-compose-backup-restore.ps1`
- `.github/workflows/ci.yml`
- `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The new live restore regression has syntax/config validation only; its runtime result is pending hosted CI. The previous live restore predates the manifest fingerprint change.
- Visual Corrections/graph-filter review, hosted CI/deployment, production key custody, and authorized evaluation results remain outstanding.

### Exact next steps, in order

1. Run hosted CI when a repository remote/runner is available; inspect the live backup/restore job output and fix any failure.
2. Continue the full completion audit for remaining local workflows, deployment and authorized evaluation requirements.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- CI script syntax: PowerShell parser or `pwsh -File scripts/test-compose-backup-restore.ps1 -AllowSyntheticWrites` only within disposable Compose E2E; do not run against persistent/production data.
- Current local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- No commit; leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:36 (Asia/Calcutta) — Recheck I4C public source access boundaries

### Completed in this stage

- Re-read the latest status and requirements matrix; the project remains untracked with no commit and no `AGENTS.md` found.
- Rechecked current official-domain public I4C materials. The indexed Suspect Repository still describes complaint-based entries, an authenticity/error warning and a correction channel; the page still displays a 2 February 2024 update date. The website/app suspect search remains a CAPTCHA-protected citizen form.
- No public API documentation, developer access flow, or automated-access authorization surfaced. The public pages are script-driven, and direct page retrieval yielded no readable lines; this check cannot establish that private or law-enforcement interfaces do not exist.
- Kept automated I4C access disabled and updated `SOURCE_ACCESS_REVIEW.md`, `REQUIREMENTS_TRACEABILITY.md`, and the engineering walkthrough with the recheck date and verification limits.

### Checks run and results

- Current official I4C public-source search/recheck: confirmed the repository's indexed complaint-based disclaimer, error/correction wording, CAPTCHA-based citizen form, and displayed 2024 update date.
- Direct retrieval of the official repository, homepage, and Website Policies pages returned no readable lines in the web tool; the review records this limitation and does not infer authorization or nonexistence of private APIs.
- No application code or external service was called; no I4C integration exists or was attempted.
- Attempted a live backup-and-restore smoke on the isolated synthetic Compose database to verify the current key-fingerprint manifest end to end. The execution policy rejected the shell command before a process started. No backup/restore action ran and no application data was changed by that attempt. A prior live encrypted restore is recorded, but it does not prove this latest manifest-fingerprint path.
- Strict trailing-whitespace scan across all four updated documentation files passed after removing intentional hard-break spaces from the source-review date lines.

### Files or components changed

- `SOURCE_ACCESS_REVIEW.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Public sources still do not establish permission for automated I4C access. Written operator authorization and terms would be required before implementing a connector.
- Live Compose restore with the key-fingerprint manifest remains unverified because the execution policy rejected the attempted command; fake-Docker restore and separate-process recovery tests pass.
- Visual review of Corrections/graph filters, hosted CI, operator deployment/security verification, and authorized evaluation data remain outstanding.

### Exact next steps, in order

1. Continue local verification and product fixes; do not automate I4C access without documented authorization.
2. Run hosted CI when a repository remote/runner is configured.
3. Verify hosting/security and recovery using operator-owned infrastructure, then run evaluations with authorized time-separated labels.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Local app remains at `http://127.0.0.1:5173/`; API readiness at `http://127.0.0.1:8000/health/ready`.
- Leave unrelated `rsiacdp-postgres` and `backend_postgres_data` untouched; no commit was created.

## 2026-11-03 01:34 (Asia/Calcutta) — Match correction actions to open-request state

### Completed in this stage

- Re-read the 01:32 checkpoint and revalidated the current files. All repository files remain untracked; no commit was created.
- Follow-up review found the Corrections queue offered case edits for closed (`resolved` or `rejected`) requests even though the API returns HTTP 409 for those changes.
- Added an explicit open-state rule: only `received` or `investigating` requests show case-change controls. Closed requests now explain that the request must be moved back to `investigating` before applying a case change. The handler independently checks request openness before sending.
- Added tests for open and closed request statuses alongside the rationale-length tests.
- Rebuilt the isolated Compose web image and confirmed the served production JavaScript contains the closed-request guidance.

### Checks run and results

- From `frontend/`: `pnpm run build` passed.
- From `frontend/`: `pnpm run test:redaction` passed, 19 tests / 0 failures.
- Isolated Compose web image rebuild and health check passed; no volumes were removed.
- Live smoke passed: app page 200, updated production JS bundle 200, same-origin `/api/policy` 200, API `/health/ready` 200.
- Engineering walkthrough and requirements traceability entries were updated; trailing-whitespace scan over the six changed source/document files passed.
- Visual review remains incomplete. Desktop computer-use previously stopped before navigation due URL verification; a separate headless Chrome launch was rejected by the execution policy. No policy barrier was bypassed.

### Files or components changed

- `frontend/src/review-rules.ts`
- `frontend/src/App.tsx`
- `frontend/tests/review-rules.test.ts`
- `BUILD_STATUS.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Corrections and graph-filter screens still need visual inspection in an approved browser method. Pure rules/tests and the served production bundle do not prove rendered layout or interactions.
- Hosted Actions, public deployment/TLS/network/storage controls, and real operator key custody/recovery remain unverified.
- Authorized time-separated evaluation data and measured metrics remain unavailable.

### Exact next steps, in order

1. Continue local workflow verification without bypassing the browser URL policy. The visible Corrections/graph-filter pages remain unreviewed; their focused frontend rules and API behavior are covered by automated tests.
2. Run hosted CI after a remote/runner is configured; then verify operator-owned deployment and obtain authorized evaluation data.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Frontend: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Local app: `http://127.0.0.1:5173/`; API readiness: `http://127.0.0.1:8000/health/ready`.
- Do not touch unrelated `rsiacdp-postgres` or `backend_postgres_data`; no commit was created.

## 2026-11-03 01:32 (Asia/Calcutta) — Fix correction form validation and refresh local web image

### Completed in this stage

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, the requirements traceability matrix, and Git status. All repo files are still untracked; no commit was created. No applicable `AGENTS.md` file was found.
- Rechecked the Corrections queue and found that it enabled update/apply buttons even when rationale values violated the backend schema, causing avoidable 422 responses.
- Added frontend validation that mirrors the API: request status updates need 5–4,000 non-space characters; applying a case record correction needs 10–4,000; a replacement value needs 2–1,000.
- Added user-facing rationale guidance and native length bounds. Invalid status updates and case changes stay disabled; client handlers also enforce the limits before sending requests.
- Added unit tests for lower/upper rationale and corrected-value bounds.
- Rebuilt the isolated Compose web image. Its served production JS contains the fix. HTML, JS bundle, same-origin policy endpoint and API readiness all returned HTTP 200.
- The prior desktop browser attempt had stopped before navigation because it could not verify the current browser URL. This stage used code-level rules/tests and the live served bundle; no desktop safety gate was bypassed.

### Checks run and results

- From `frontend/`: `pnpm run build` passed (`tsc -b` and Vite production bundle).
- From `frontend/`: `pnpm run test:redaction` passed, 17 tests / 0 failures.
- Isolated Compose web rebuild: passed and web health became healthy; no data volumes were deleted.
- Live web smoke: `/` 200; served production JavaScript 200 with the new validation copy; `/api/policy` through same-origin proxy 200; API `/health/ready` 200.
- Visual review of Corrections and graph filters remains incomplete. Existing pure graph-filter tests pass, but they do not prove rendered layout or interaction.

### Files or components changed

- `frontend/src/review-rules.ts`
- `frontend/src/App.tsx`
- `frontend/tests/review-rules.test.ts`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Corrections/graph-filter visual browser inspection remains incomplete; this turn's helper halted before navigation due URL-confidence policy. Functional graph filtering and correction API behavior have automated coverage, but not visual evidence.
- Hosted Actions, operator-owned public deployment/TLS/storage/egress and production key escrow remain unverified.
- Authorized time-separated recruitment-scam evaluation data and actual metrics remain unavailable.

### Exact next steps, in order

1. Continue verification of local end-to-end workflows, especially Corrections/graph UI behavior where a permitted browser method is available; do not use the ambient user tab if URL safety cannot be established.
2. Run the complete hosted CI workflow after a repository remote/runner is configured.
3. Verify deployment, TLS, storage, egress, backup custody/recovery on operator-owned infrastructure.
4. Obtain authorized time-separated labels and run the documented baseline/ablation comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Frontend checks: from `frontend/`, run `pnpm run build` and `pnpm run test:redaction`.
- Local web/API: `http://127.0.0.1:5173/` and `http://127.0.0.1:8000/health/ready`.
- No commit was created. Leave unrelated `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:28 (Asia/Calcutta) — Verify backup key identity, escrow recovery and rotation

### Completed in this stage

- Re-read this checkpoint and inspected the current working tree before editing. All project files remain untracked; no commit was created.
- Verified the existing backup manifest includes format `RSAICDPBK2` and a non-secret SHA-256 recovery-key fingerprint. Restore compares that fingerprint after ciphertext checksums and before plaintext staging or service shutdown.
- Updated backup and restore orchestration fixtures to require manifest format/key identity and to validate exactly two encrypted artifact checksum rows.
- Added `scripts/test-backup-recovery.ps1`: under a current-user-only temporary Windows ACL, it creates synthetic escrow key files and uses separate PowerShell processes with inherited key variables cleared. Key A recovers an A archive; key B is rejected for the A archive without plaintext output; a rotated B archive recovers with B; and the older A archive still recovers with A.
- Added the process-separated recovery/rotation test to the Windows CI operations job. README and engineering/requirements docs now explain the manifest fingerprint and the limits of the synthetic drill.
- The first recovery test run exposed a hashtable fixture-construction error. Fixed it and reran the drill successfully; no product encryption/restore defect was indicated.

### Checks run and results

- `scripts/test-backup-crypto.ps1`: passed.
- `scripts/test-backup.ps1`: passed with manifest format, key fingerprint, two ciphertext hashes, capture order, failure cleanup, and service restart assertions.
- `scripts/test-restore.ps1`: passed with key fingerprint preflight, no Docker calls on mismatch, operation ordering, graph rebuild and failure-safe behavior.
- `scripts/test-backup-recovery.ps1`: passed across separate `pwsh` processes; old and new synthetic archives recovered, wrong key was rejected before decryption, and no wrong-key plaintext was produced.
- `scripts/test-compose-config.ps1`: passed.
- `pnpm dlx prettier@3.5.3 --parser yaml .github/workflows/ci.yml`: passed; workflow parsed successfully.
- PowerShell parser pass for the six backup/restore scripts/modules: passed.
- Trailing-whitespace scan over all eight files changed in this stage: clean.
- Rechecked the local Compose project after tests: API, PostgreSQL, Neo4j, worker and web all report healthy; web remains on `127.0.0.1:5173` and API on `127.0.0.1:8000`.

### Files or components changed

- `scripts/test-backup-recovery.ps1`, `scripts/test-backup.ps1`, `scripts/test-restore.ps1`
- `scripts/backup-crypto.psm1`, `scripts/backup.ps1`, `scripts/restore.ps1` already contain the fingerprint implementation at the start of this stage; reviewed, not changed now.
- `.github/workflows/ci.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Backup-key workflow was verified with temporary local synthetic escrow files. Real operator secret-manager provisioning, custody, backup-target encryption, and disaster recovery remain unverified.
- Hosted Actions has not run because no Git remote/runner is configured. Public hosting/domain, TLS, egress boundaries and deployed operational controls remain unverified.
- Authorized, time-separated evaluation data and measured comparisons remain unavailable. Corrections and graph-filter visual review remain outstanding.

### Exact next steps, in order

1. Continue local review/verification of any remaining unverified user journeys without touching the separate `rsiacdp-postgres` project or its volume.
2. When a remote and runner are configured, run the complete hosted CI workflow and fix any failures.
3. Configure operator-owned deployment, run TLS/network/storage and restore checks, and obtain authorized evaluation data to run the four comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Run `./scripts/test-backup-crypto.ps1`, `./scripts/test-backup.ps1`, `./scripts/test-restore.ps1`, and `./scripts/test-backup-recovery.ps1`.
- Main synthetic stack, if still needed: `rsaicdp-verification-20261103`; env `backend/.test-runtime/compose-20261103.env`; UI `http://127.0.0.1:5173/`; API `http://127.0.0.1:8000/health/ready`.
- No commit was created. Leave unrelated `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:24 (Asia/Calcutta) — Verify PostgreSQL concurrency and finish local CI checks

### Completed in this stage

- Re-read the checkpoint and traceability matrix, then reviewed the two opt-in PostgreSQL tests before running them. Created two new databases ending `_test` inside the isolated verification PostgreSQL service and migrated both to `e7a91c0d4b62`. Did not use the main synthetic case database or the separate `rsiacdp-postgres` project.
- Ran privileged-investigator/reviewer provisioning race test on its empty disposable database: passed.
- Ran source-record retirement versus in-flight lookup lock-order test on a separate disposable database: passed. Both PostgreSQL tests previously skipped by the normal SQLite-focused harness are now verified against PostgreSQL.
- Ran the frontend production build and redaction/graph-review tests after the current changes: TypeScript/Vite build passed; all 15 frontend tests passed.
- Validated Caddyfile with `caddy validate` inside `caddy:2-alpine` using `PUBLIC_DOMAIN=example.invalid` and no network. Added the offline validation to the workflow's web-container job.
- Checked the live Compose web container from the host: `/` returned HTTP 200; same-origin `/api/policy` returned the persisted app policy; CSP, Permissions Policy, `nosniff`, no-referrer and frame-deny headers were present.
- Exercised retention against the live PostgreSQL/worker/Neo4j stack using one synthetic expired case, audit event and encrypted PDF upload. Retention deleted the case, case audit and private file, created a delete tombstone, and the Neo4j outbox status reached `completed`.
- Scanned all files changed in the current work for trailing whitespace. The scan was clean. `git diff --check` alone is not evidence for these files because this repository still has no tracked baseline and all project files are untracked.

### Checks actually run

- Alembic upgrade head on two new isolated PostgreSQL `_test` databases: passed for both.
- `test_postgres_account_provisioning.py`: 1 passed.
- `test_postgres_source_retirement.py`: 1 passed.
- `pnpm run build`: passed.
- `pnpm run test:redaction`: 15 passed, 0 failed.
- Caddy offline validation: passed; it parsed/adapted configuration without attempting certificate issuance.
- Live web-to-API same-origin proxy: passed, HTTP 200; expected campaign rule and consent version returned with all checked browser security headers.
- Live PostgreSQL retention: passed; expired synthetic case/audit and AES-GCM upload were removed, then the graph deletion tombstone completed.
- Previous same-stage results still apply: backend 214 unit tests, 14 API-flow tests, 2 proxy tests; Compose PDF E2E; OCR; encrypted backup/restore; backup crypto/fake-Docker scripts; workflow YAML parsing.

### Files/components changed

- `.github/workflows/ci.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`
- The two isolated PostgreSQL `_test` databases remain under the primary synthetic verification PostgreSQL volume.

### Known bugs or unfinished work

- The full hosted Actions workflow still cannot be run because the repository has no configured remote/runner. YAML parsing and local job-equivalent checks do not replace hosted execution.
- No public domain, hosting account, or operator-owned infrastructure is configured. DNS/TLS issuance, deployed access controls, egress boundaries, remote encrypted backup, logging/monitoring and disaster recovery remain unverified.
- Backup key escrow/rotation and real authorized evaluation labels/metrics remain open.
- Corrections and graph-filter interactions remain unreviewed in the browser after the prior origin-navigation gate; API workflows and unit coverage pass.

### Exact next steps, in order

1. Prepare a durable, separate test recovery key outside the repository and run a key escrow/recovery/rotation drill on synthetic encrypted backups.
2. When a remote and runner are configured, run the complete GitHub Actions workflow and fix any host-specific issues.
3. Configure operator-owned domain/hosting, verify TLS, network egress, storage and operational recovery.
4. Obtain authorized time-separated annotations and run all evaluation comparisons.
5. Finish remaining visual UI checks when browser navigation is available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Main synthetic stack: project `rsaicdp-verification-20261103`, env file `backend/.test-runtime/compose-20261103.env`, UI `http://127.0.0.1:5173/`, API `http://127.0.0.1:8000/health/ready`.
- Backup key must be a persistent distinct 32-byte base64 key in `.env` and escrowed outside the repository before production backup use.
- Run `scripts/test-backup-crypto.ps1`, `scripts/test-backup.ps1`, `scripts/test-restore.ps1`, `scripts/test-compose-config.ps1`, backend CI harness, both opt-in PostgreSQL tests on isolated `_test` DBs, `pnpm run build`, and `pnpm run test:redaction`.
- No commit was created; leave `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:19 (Asia/Calcutta) — Harden backup format and verify version 2 live restore

### Completed in this stage

- Reviewed the encrypted backup implementation for multi-backup nonce reuse risk. Replaced the initial per-file nonce-only separation with format version 2: each file gets a random 256-bit salt, derives its own AES key using HMAC-SHA256 extract/expand with a type-specific context, then uses a random nonce prefix and monotonic frame counter. AAD authenticates version, salt, prefix, type, sequence, frame length and final marker.
- Added explicit tests that backup encryption requires a key and rejects reuse of the upload key. Tampering test flips a payload byte. Multi-frame roundtrip, wrong-key, wrong-context, tamper, truncation, and partial-output cleanup checks pass.
- Updated encrypted backup/restore handling docs with format version, key escrow, temporary-file exposure, and recovery loss behavior.
- Repeated a live version 2 encrypted backup and restore on the isolated Compose stack. The two `.enc` artifacts and manifest were created; no plaintext output files remained. A synthetic title mutation was reverted, the encrypted PDF upload was restored/authenticated, the API and worker returned healthy, and Neo4j was rebuilt from PostgreSQL. The operation exited successfully.
- Re-ran crypto and fake-Docker backup/restore tests, Compose configuration, PowerShell parsing, YAML parsing, and `git diff --check`; all passed.
- Validated the production Caddyfile inside the pinned image family using `caddy validate` with the reserved `example.invalid` host and `--network none`; configuration passed without a certificate request or external network. Added this check to the `web-container` CI job.

### Checks actually run

- `scripts/test-backup-crypto.ps1`: passed, including required/distinct key validation, multi-frame roundtrip, wrong key/context, payload tampering, truncation and cleanup.
- `scripts/test-backup.ps1`: passed encrypted output, decryption fixture, checksum, capture order, cleanup and restart checks.
- `scripts/test-restore.ps1`: passed encrypted fixture, preflight checks, restore order, graph rebuild and safe-stop behavior.
- Live version 2 encrypted Compose backup/restore: passed with exit code 0; original case title restored, one encrypted PDF authenticated, API readiness passed, graph rebuild logged three cases, output directory held only two `.enc` files plus one manifest.
- `scripts/test-compose-config.ps1`, PowerShell parser for backup scripts, Prettier YAML parse for `.github/workflows/ci.yml`, and `git diff --check`: passed.
- `caddy validate` in `caddy:2-alpine` with `--network none`: passed. TLS certificate issuance remains untested and needs a real operator-owned domain.

### Files/components changed

- `scripts/backup-crypto.psm1`
- `scripts/test-backup-crypto.ps1`
- `scripts/backup.ps1`
- `scripts/restore.ps1`
- `scripts/test-backup.ps1`
- `scripts/test-restore.ps1`
- `.env.example`
- `.github/workflows/ci.yml`
- `scripts/test-compose-config.ps1`
- `Caddyfile`
- `README.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- No operator-owned Git remote or hosted CI runner is configured. Local tests/YAML parsing do not prove GitHub Actions execution.
- Backup key escrow/rotation/recovery remains an operator task. A random key was used only in this disposable verification process; do not treat the ignored synthetic artifacts as recoverable backups. For actual use, persist the separate key in an approved secret manager/recovery escrow before creating backups.
- Host temporary-storage encryption/access controls, remote backup target protections, hosted TLS/network/monitoring, and production restore are unverified.
- Authorized evaluation annotations/metrics and Corrections/graph-filter visual review remain outstanding.

### Exact next steps, in order

1. Add a planned key escrow and rotation/recovery drill for synthetic backups with a durable test-only key protected outside the repository.
2. Configure the repository remote/hosted runner and run the full CI workflow, including the new offline Caddy validation.
3. Verify deployment security and recovery on operator-owned infrastructure.
4. Complete authorized time-separated evaluation and remaining visual UI review.

### Resume commands

- Read this file and `BUILD_PLAN.md`; inspect `git status --short` before edits.
- Before real backup use, set a persistent, unique `BACKUP_ENCRYPTION_KEY` in `.env` and preserve it outside this checkout; losing it makes backups unrecoverable.
- Current primary synthetic stack: `rsaicdp-verification-20261103`; Compose env is `backend/.test-runtime/compose-20261103.env`; ports 8000/5173.
- Re-run `scripts/test-backup-crypto.ps1`, `scripts/test-backup.ps1`, `scripts/test-restore.ps1`, `scripts/test-compose-config.ps1`, backend CI harness, and YAML parse when resuming.
- No commit was created; keep unrelated `rsiacdp-postgres` and `backend_postgres_data` untouched.

## 2026-11-03 01:20 (Asia/Calcutta) — Encrypt backup artifacts and verify encrypted live recovery

### Completed in this stage

- Continued from the live backup/restore checkpoint and found an at-rest gap: backup scripts wrote sensitive PostgreSQL and upload archives as plaintext files. Implemented authenticated chunked AES-256-GCM encryption in `scripts/backup-crypto.psm1`, with a distinct context for PostgreSQL versus uploads, per-file nonce prefix, authenticated final frame, key validation and cleanup of partial plaintext/decryption outputs.
- Added a separate `BACKUP_ENCRYPTION_KEY` entry and setup instructions to `.env.example`. The helper rejects a backup key equal to the upload key. Backup and restore scripts read it from the process environment or `.env`; the key is not placed in backup files or manifests. Plaintext working files use a private OS temp directory and are removed by script cleanup.
- Updated `scripts/backup.ps1` to retain only encrypted artifacts plus a checksum manifest of ciphertext. Updated `scripts/restore.ps1` to check hashes and authenticate/decrypt both artifacts before stopping writes, then restore using protected temporary files.
- Added tests for multi-chunk round-trip, wrong-key and wrong-context rejection, tampering, truncation, partial-output cleanup, and encrypted fake-Docker backup/restore behavior. Added the crypto test to Windows CI and documented the new key and recovery limitations.
- Verified a live encrypted backup and restore on the isolated synthetic stack. Backup output contained two `.enc` files and one manifest, no plaintext output artifacts. Mutated a synthetic case title, restored it from the encrypted PostgreSQL dump, restored and authenticated/decrypted the encrypted PDF upload, confirmed API/worker health, and observed the restore script rebuild Neo4j.
- Independently ran the backup crypto, fake-Docker backup/restore, Compose config, PowerShell parser and CI YAML parser checks successfully.

### Checks actually run

- `scripts/test-backup-crypto.ps1`: passed multichunk encryption/decryption, wrong key, context substitution, tamper and truncation checks, and cleanup of failed plaintext output.
- `scripts/test-backup.ps1`: passed; produced encrypted database/upload outputs, verified they decrypt to synthetic inputs, checked capture order, checksum manifest, failure cleanup and service restart.
- `scripts/test-restore.ps1`: passed; checked confirmation, checksum rejection, authenticated decrypt, operation order, Neo4j rebuild and safe stop on simulated DB failure.
- `scripts/test-compose-config.ps1`: passed.
- Prettier 3.5.3 YAML parser: `.github/workflows/ci.yml` parsed successfully.
- Live encrypted `backup.ps1` / `restore.ps1`: passed on isolated Compose PostgreSQL, private-upload volume and Neo4j. PostgreSQL mutation reverted, AES-GCM PDF authenticated, API health returned, graph rebuilt, and the backup directory held encrypted artifacts only.
- Backend CI harness from previous checkpoint: 214 unit tests passed (2 opt-in PostgreSQL tests skipped), 14 API-flow tests passed and 2 proxy tests passed. An initial manual run inherited Compose Neo4j/upload keys and failed test assumptions; the successful run explicitly isolated `NEO4J_URI` and upload encryption settings.

### Files/components changed

- `scripts/backup-crypto.psm1` (new)
- `scripts/test-backup-crypto.ps1` (new)
- `scripts/backup.ps1`
- `scripts/restore.ps1`
- `scripts/test-backup.ps1`
- `scripts/test-restore.ps1`
- `.env.example`
- `.github/workflows/ci.yml`
- `scripts/test-compose-config.ps1`
- `README.md`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Encrypted backup/restore and key matching were exercised locally, but independent backup-key escrow, key-recovery/rotation drills, encrypted remote backup target and production host controls are not configured or verified. If the backup key is lost, data cannot be restored.
- The temporary working directory is private and cleaned by normal script completion; abrupt host power loss can leave temporary plaintext and requires operator cleanup. Protect host temp storage with disk encryption and access controls.
- Hosted CI has not run because no Git remote is configured. Hosted TLS, egress, monitoring, production restore, and authorized time-separated evaluation remain open.
- The visual Corrections page and graph-filter interaction remain unreviewed due the earlier browser-origin gate.

### Exact next steps, in order

1. Review the backup crypto format and operator key escrow/recovery instructions; perform a planned backup-key rotation/recovery drill using an encrypted synthetic archive.
2. Configure a Git remote/hosted runner, run the full workflow and fix any hosted-only failures.
3. Verify TLS, access control, storage, backup target, egress, monitoring and restoration on operator-owned production-like infrastructure.
4. Complete remaining UI visual checks when local browser navigation is permitted.
5. Obtain authorized time-separated annotations, execute the four evaluation comparisons and report actual measurements.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, then inspect `git status --short`.
- Set a separate, persistent `BACKUP_ENCRYPTION_KEY` in `.env` using the documented 32-byte base64 generation command. Preserve the key outside this repository and separately from backups before relying on them.
- Run `scripts/test-backup-crypto.ps1`, `scripts/test-backup.ps1`, `scripts/test-restore.ps1`, `scripts/test-compose-config.ps1`, and parse `.github/workflows/ci.yml`.
- The original Compose verification project remains `rsaicdp-verification-20261103`; keep the unrelated `rsiacdp-postgres` project and volume untouched. No commit was created.

## 2026-11-03 01:10 (Asia/Calcutta) — Verify the PDF E2E branch and parse hosted workflow YAML

### Completed in this stage

- Re-read the latest status/plan, confirmed the original Compose stack was healthy, and created a separate disposable Compose project using a different PostgreSQL database, private volumes, subnet and host ports. The original inspection stack and its data were left running.
- Parsed `.github/workflows/ci.yml` with Prettier's YAML parser (`pnpm dlx prettier@3.5.3 --parser yaml`); parsing succeeded. No YAML parser was previously installed in the host environment.
- Ran the exact updated Compose end-to-end script against the fresh secondary project with `-PdfPath`. It passed investigator registration/authentication, two consented text cases, worker extraction/source spans, neutral evidence outcomes, deterministic exact-email campaign link, Neo4j projection, redacted report, token-protected correction transitions, and PDF upload/processing with PDF page/span provenance and report redaction.
- Ran `python -m app.verify_ocr` inside the secondary worker container; real Tesseract image and scanned-PDF checks passed. Verified migration `e7a91c0d4b62` and graph rebuild from PostgreSQL.
- Stopped and removed only the secondary test containers and network without deleting their named volumes. The original `rsaicdp-verification-20261103` stack remains healthy on ports 8000/5173 for inspection.
- Re-ran `scripts/test-compose-config.ps1`; passed.

### Checks actually run

- `pnpm dlx prettier@3.5.3 --parser yaml .github/workflows/ci.yml`: parsed successfully.
- Full `scripts/test-compose-e2e.ps1` on a fresh isolated PostgreSQL/Neo4j stack with a generated synthetic PDF: passed, including PDF file upload.
- `docker compose exec worker python -m app.verify_ocr`: image and scanned-PDF OCR passed.
- PostgreSQL migration revision and Neo4j rebuild: passed.
- `scripts/test-compose-config.ps1`: passed.
- Original Compose stack health after secondary-stack teardown: all five services remained healthy.

### Files/components changed

- `BUILD_STATUS.md`
- Temporary ignored E2E configuration/artifacts under `backend/.test-runtime/`; no source changes in this stage.

### Known bugs or unfinished work

- Hosted CI has not run because no Git remote is configured. YAML parsing and local E2E execution do not prove GitHub Actions runner behavior.
- Backup/restore has been verified locally, but backup encryption/key recovery/rotation and operator-host storage controls remain open.
- Hosted domain/TLS, egress, monitoring, and recovery controls remain unverified. Authorized evaluation labels/metrics and visual Corrections/filter review remain outstanding.

### Exact next steps, in order

1. Decide whether to implement encrypted backup artifacts and separate recovery-key handling before documenting a deployment as secure.
2. Configure a repository remote/hosted runner, then run the full CI workflow and address any runner-specific failures.
3. Complete deployment verification on operator-owned infrastructure and obtain authorized time-separated evaluation data.
4. Complete remaining UI visual review when local browser navigation is permitted.

### Resume commands

- Re-read `BUILD_STATUS.md` and `BUILD_PLAN.md`, then check `git status --short`.
- The original verification project remains `rsaicdp-verification-20261103`, with ignored environment file `backend/.test-runtime/compose-20261103.env` and loopback ports 8000/5173.
- The isolated PDF E2E project was stopped (its named volumes and ignored synthetic configuration remain). Recreate only if needed using `rsaicdp-verification-pdf-e2e` and its `backend/.test-runtime/compose-e2e-20261103.*` files; do not use `down -v` unless explicitly discarding those synthetic volumes.
- No commit was created.

## 2026-11-03 01:08 (Asia/Calcutta) — Fix and verify live upload restore with rollback

### Completed in this stage

- Resumed from the current status and inspected the live isolated Compose services plus backup/restore scripts before acting. The project stack was healthy; repository files remain untracked and no commit was created.
- Ran the real backup script against the isolated synthetic PostgreSQL/Neo4j stack. It stopped API/worker writes, created a readable custom-format `pg_dump`, archived the private upload volume, wrote SHA-256 checksums, and restored service health. `pg_restore -l` successfully listed the database archive.
- Ran a live restore with a deliberate synthetic database title mutation. PostgreSQL restored, but private upload extraction failed with `OSError: [Errno 18] Invalid cross-device link`: `restore_uploads.py` staged files under `/app` and then moved them into the Docker named volume mounted at `/app/private_uploads`. The restore script kept API/worker stopped, as designed.
- Fixed `backend/app/restore_uploads.py` to stage on the upload volume itself and to preserve the previous upload set until all new files are installed. Added rollback of partially installed files if a move fails. Added a regression test proving source and destination are on the same filesystem and that a synthetic install failure restores the original file set.
- Rebuilt the API/worker images and ran the targeted upload-restore suite: all 7 tests passed.
- Re-ran the actual restore on the isolated synthetic stack. It restored the changed PostgreSQL row from the backup, restored 1 encrypted PDF, verified its AES-GCM authentication/decryption, restarted API/worker healthy, and rebuilt the Neo4j projection for 3 cases. Readiness returned successfully.
- Ran the full backend CI harness in a disposable container with testing-only SQLite, Neo4j disabled, and upload encryption disabled for the test process. The first manual invocation inherited production Compose settings and caused expected harness interference; after isolating test environment variables, all 214 unit tests passed (2 opt-in PostgreSQL tests skipped), all 14 API-flow tests passed, and both proxy tests passed.

### Checks actually run

- `scripts/backup.ps1` against live synthetic Compose services: passed; dump, upload tarball and manifest were created; `pg_restore -l` validated dump format.
- `scripts/restore.ps1 -ConfirmRestore` against the corresponding backup: passed after the fix; title mutation reverted, 1 encrypted PDF restored and authenticated, API/worker healthy, Neo4j rebuilt.
- `backend/tests/test_restore_uploads.py`: 7 passed, including same-filesystem staging and rollback regression.
- `backend/run_ci_tests.py`: 214 unit tests passed (2 opt-in PostgreSQL tests skipped), 14 API-flow tests passed, 2 proxy tests passed.
- The actual failure before the fix was reproduced and captured: `Invalid cross-device link` while moving staged upload into the Docker volume.

### Files/components changed

- `backend/app/restore_uploads.py`
- `backend/tests/test_restore_uploads.py`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Live recovery is now verified only on the isolated local synthetic stack. Backup confidentiality, key backup/rotation/recovery and production-host storage controls remain unverified.
- Hosted CI has not run; the workflow YAML has not yet been parsed with an installed YAML-aware tool. No Git remote is configured.
- The visual Corrections page and graph-filter interaction remain unreviewed. Authorized time-separated Indian recruitment-scam labels and real evaluation metrics remain unavailable.
- Hosted TLS, monitoring, egress restrictions, retention on deployment storage, and production security/recovery checks require operator-owned infrastructure.

### Exact next steps, in order

1. Validate `.github/workflows/ci.yml` with a YAML-aware parser, then run the complete hosted workflow once a remote and runner are configured.
2. Review backup privacy/key handling and test key recovery/rotation procedures separately from the synthetic application-data restore.
3. Verify the production Caddy/TLS path and network restrictions on an operator-owned host/domain.
4. Complete authorized visual review of Corrections and graph filters if local browser navigation becomes available.
5. Obtain authorized time-separated labels and run the specified evaluation comparisons; publish actual metrics only.

### Resume commands

- Re-read `BUILD_STATUS.md` and `BUILD_PLAN.md`; check `git status --short` before editing.
- The test stack is `rsaicdp-verification-20261103`, configured through ignored `backend/.test-runtime/compose-20261103.env`. Confirm its identity before use. Its live recovery artifacts are under ignored `backend/.test-runtime/real-backup-restore-20261103`.
- Targeted regression: mount `backend/tests` read-only into a one-off worker container and run `python -m unittest discover -s /tmp/tests -p test_restore_uploads.py -v`.
- Full backend CI harness: mount `backend` into a one-off worker container, set `APP_ENV=testing`, separate SQLite `DATABASE_URL` and `UPLOAD_DIR`, clear `UPLOAD_ENCRYPTION_KEY` and `NEO4J_URI`, then run `python run_ci_tests.py`.
- Do not operate on the separate existing `rsiacdp-postgres` service or `backend_postgres_data` volume. Do not commit unless requested.

## 2026-11-03 01:03 (Asia/Calcutta) — Recover Docker and exercise the real Compose stack

### Completed in this stage

- Resumed from the previous checkpoint and inspected repository status, build plan, status file, current CI workflow, and the partially completed Compose end-to-end script. All repository files remain untracked; no commit was created.
- Recovered Docker Desktop by upgrading the existing installation in place from 4.91.0 to 4.97.0. Verified the official installer SHA-256 against the published Winget manifest and verified the Docker Authenticode signer before running it. Docker Engine 29.9.2 now starts. The prior stale socket issue was resolved by the vendor update; no Docker data reset was performed.
- Built and started the isolated Compose project `rsaicdp-verification-20261103` with synthetic secrets and a dedicated database/network. PostgreSQL, Neo4j, API, worker, and web all reached healthy status. A separate existing project and its data volume were left untouched.
- Fixed a real Neo4j healthcheck configuration bug in `docker-compose.yml`: the healthcheck referenced variables that were not passed into the Neo4j container. It now reads both credentials from `NEO4J_AUTH`. Extended the Compose configuration check to catch this regression.
- Ran the real worker OCR verification for a synthetic image and scanned PDF. The isolated PostgreSQL database reports migration `e7a91c0d4b62`; graph rebuild from PostgreSQL completed, and a live graph query showed 15 nodes and 22 edges with personal identifiers masked.
- Ran live end-to-end API flows against PostgreSQL, the worker, and Neo4j: synthetic investigator registration/authentication; consented cases; persisted extraction spans; neutral local-corpus outcomes and assessment; deterministic exact-email campaign linking; masked graph; redacted reports; and correction status transitions. A separate synthetic PDF upload was processed; ciphertext was verified at rest and decrypted with the configured AES key inside the worker. The PDF case retained page/span provenance and a neutral assessment, and the report masked the address.
- Extended the Compose CI job to generate a synthetic PDF and run the same upload verification end to end. Adjusted its setup-code lookup so CI can use its environment variable without needing a repository `.env` file.

### Checks actually run

- Docker Compose build/start with `--wait`: all five services reported healthy.
- `scripts/test-compose-config.ps1`: passed after the Neo4j healthcheck fix.
- `docker compose exec -T worker python -m app.verify_ocr`: passed synthetic image and scanned-PDF OCR checks.
- Live Compose E2E PowerShell script on the isolated test stack: passed signup/auth, consented PostgreSQL intake, processing, source spans, local evidence, deterministic campaign link, Neo4j projection, redacted report, and correction workflow.
- Live synthetic PDF upload: passed asynchronous processing, PDF page and character spans, private opaque object name, AES-256-GCM ciphertext/decryption verification, neutral assessment, and report masking/provenance.
- Neo4j graph rebuild: passed; graph had 15 nodes and 22 edges, identifiers masked.
- PowerShell parser for `scripts/test-compose-e2e.ps1`: passed.
- `git diff --check`: passed.
- CI YAML parser attempt did not run because PyYAML is not installed in the host Python. This is a tooling gap, not a reported workflow pass; YAML syntax still needs validation by the hosted runner or an available parser.

### Files/components changed

- `docker-compose.yml`
- `scripts/test-compose-config.ps1`
- `scripts/test-compose-e2e.ps1`
- `.github/workflows/ci.yml`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Hosted CI has not run, so the new synthetic PDF workflow job remains unverified on GitHub Actions.
- No operator-owned host, domain, TLS deployment, backup destination, or external evidence provider is configured. Actual backup/restore, key recovery/rotation, retention deletion on a production-like store, egress controls, and hosted security checks remain open.
- The visual Corrections page and interactive graph filters remain unreviewed after a browser navigation gate declined access. API correction and graph behavior are verified.
- Authorized time-separated Indian recruitment-scam annotations and measured evaluation results are unavailable. Evaluation remains pending; no performance claims are made.
- The local Compose database contains synthetic verification accounts/cases only. It is isolated from the pre-existing `rsiacdp-postgres` container and volume. Leave the isolated stack running for inspection; do not run `down -v` unless intentionally discarding the synthetic verification data.

### Exact next steps, in order

1. Validate `.github/workflows/ci.yml` with a YAML-aware parser and run the hosted workflow after a remote/runner is configured; confirm the PDF upload job and every other CI job pass.
2. Inspect and exercise backup/restore plus retention/key recovery on disposable PostgreSQL/Neo4j data, recording exact results.
3. Complete the remaining visual Corrections and graph-filter review if local browser navigation becomes available.
4. Configure operator-owned deployment infrastructure and verify TLS, encrypted storage/backups, access controls, safe egress, logs, monitoring and recovery.
5. Obtain authorized time-separated annotations, run all evaluation comparisons, and report measured results only.

### Resume commands

- Re-read this file and `BUILD_PLAN.md`; inspect `git status --short` before editing.
- The isolated Compose project is `rsaicdp-verification-20261103`, using ignored secrets at `backend/.test-runtime/compose-20261103.env`, loopback API port 8000 and frontend port 5173. Confirm project identity and container status before operating on it.
- Repeat Compose checks with `scripts/test-compose-config.ps1` and `scripts/test-compose-e2e.ps1 -EnvironmentFile backend/.test-runtime/compose-20261103.env -AllowSyntheticWrites` only against an isolated/disposable database.
- Keep the unrelated `rsiacdp-postgres` container and `backend_postgres_data` volume untouched. Do not commit unless requested.

## 2026-11-03 00:29 (Asia/Calcutta) — Diagnose Docker startup and validate the local deployment configuration

### Completed in this stage

- Re-read the current checkpoint, plan, repository status, CI workflow and requirements matrix. No `AGENTS.md` file was found. Repository files remain untracked; no commits were created.
- Retried `docker desktop start`. Docker Desktop processes appeared, but `docker info` still could not connect to `npipe:////./pipe/dockerDesktopLinuxEngine`; `wsl --list --verbose` showed both `Ubuntu` and `docker-desktop` stopped.
- Inspected Docker Desktop's current log and found its backend failure: it cannot rename `C:\Users\gaurv\AppData\Local\Docker\run\sailor-ingest.sock` to `.stale` because Windows reports that the reparse-point socket cannot be accessed. The socket and a `.stale` sibling date from 15 September 2026. `fsutil reparsepoint query` and `Get-Acl` return error 1920 for this path. I did not remove either Docker runtime entry or reset Docker Desktop. `docker desktop stop` hung and was interrupted; this did not stop the still-running Desktop processes.
- Per Docker's official troubleshooting guidance, started `docker desktop diagnose` without its optional upload flag. The collector remained responsive but produced no diagnostic ID/archive after more than five minutes; stopped only that collector. No diagnostic was uploaded. A temporary diagnostic folder remains under the system temp directory; it was not inspected for content or removed.
- Verified the installed executable is Docker Desktop `4.91.0.239619`; the exact `sailor-ingest.sock` error is also reported against 4.91 in Docker's official feedback tracker. Docker's published release notes list 4.97.0 (26 October 2026). Started an in-place Winget upgrade to 4.97.0, but the transfer remained at a zero-byte Delivery Optimization temporary file with no active HTTPS connection or installer process. Interrupted that stalled Winget command. Docker remains at 4.91; no runtime/data directory was changed.
- Confirmed that the existing local API readiness endpoint and Vite frontend both returned HTTP 200.
- `scripts/test-compose-config.ps1` passed. Separately rendered the complete `docker-compose.yml` with `docker compose config --quiet`, supplying only temporary process-scoped synthetic secrets; configuration resolved successfully without writing a `.env` file.

### Checks actually run

- `scripts/test-compose-config.ps1`: passed.
- `docker compose config --quiet` with process-only synthetic values for all six required secrets: passed.
- `http://127.0.0.1:8001/health/ready`: HTTP 200; `http://127.0.0.1:5174/`: HTTP 200.
- `docker info`, after `docker desktop start`: failed because the Linux Engine named pipe is absent.
- `wsl --list --verbose`: both distributions were stopped at inspection time.
- Docker Desktop log inspection: identified the stale `sailor-ingest.sock` reparse-point rename failure; no socket was deleted or altered.
- `docker desktop diagnose`: no output or archive after more than five minutes while the collector process was confirmed live; collector interrupted, no upload.
- `winget upgrade --id Docker.DockerDesktop --exact --silent --accept-source-agreements --accept-package-agreements`: located 4.97.0 but hung downloading; canceled before installer launch. Installed version remains 4.91.0.239619.
- No application source code changed in this stage, so the previous backend, frontend and compile results remain the latest code verification.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Docker Desktop cannot start its Linux Engine while its runtime socket path raises Windows error 1920. Live Compose, PostgreSQL, Neo4j, OCR-container and actual backup/restore checks remain unavailable.
- The local service processes on ports 8001 and 5174 remain available for inspection. The existing synthetic SQLite data is not production data and does not verify PostgreSQL or Neo4j.
- Authenticated visual review of the Corrections page and graph filters remains incomplete after the prior browser gate declined navigation.
- Hosted CI/deployment, live recovery/key handling and measured evaluation on authorized time-separated data remain outstanding.

### Exact next steps, in order

1. Resolve Docker Desktop's stale runtime socket access problem. The installed version is 4.91.0.239619 and the official tracker reports the same failure on that version; official release notes list 4.97.0. Retry an official in-place update from a responsive Docker Desktop/Winget session, then confirm `docker info`. Preserve Docker data and do not factory-reset it.
2. With the Linux Engine available, use a disposable synthetic `.env` and run the Compose stack; verify migrations, worker, OCR, graph projection/rebuild, authenticated workflows and real backup/restore.
3. Complete the remaining browser review if local-origin navigation is permitted.
4. Run the configured hosted CI workflow and production-host security/recovery checks after an operator remote, domain and infrastructure are available.
5. Obtain authorized time-separated annotations and run the documented evaluation comparisons; report actual measurements only.

### Resume commands

- Re-read this file and `BUILD_PLAN.md`, then inspect `git status --short` before editing.
- Docker diagnosis: installed executable `4.91.0.239619`; `docker info`; `wsl --list --verbose`; inspect Docker Desktop's current log. The `winget` 4.97.0 upgrade attempt was canceled while stuck downloading; no installer ran, and no `.env` or Docker data was created by this stage.
- Existing local app: API readiness at `http://127.0.0.1:8001/health/ready`; Vite at `http://127.0.0.1:5174/`. Verify service ownership before reusing or stopping them.
- Once Docker works, generate a private temporary `.env` from `.env.example`, replace every placeholder, run `docker compose config --quiet`, then `docker compose up --build --wait --wait-timeout 180` against disposable synthetic data.
- Do not commit unless requested.

## 2026-11-03 00:18 (Asia/Calcutta) — Authenticated local UI review and extraction-card layout fix

### Completed in this stage

- Rechecked the project instructions and the latest build status. The existing SQLite test database contained one synthetic account, five cases, five completed jobs, and one synthetic correction request. Copied it and its two private test uploads to `backend/.test-runtime/browser-e2e-controlled-20261103` so the prior fixture remained untouched.
- Restarted the copied-database API at `127.0.0.1:8001`, Vite at `127.0.0.1:5174`, and the worker with local-only test settings and RDAP disabled. API readiness returned HTTP 200. The dashboard rendered five completed synthetic cases, all assessed as “Insufficient evidence.”
- Signed in to the existing synthetic investigator account and visually inspected the case dashboard, campaign page, evidence graph, and a synthetic PDF case. The campaign page showed a proposed two-case group at 55/100 under `campaign-signals-v3-threshold-40`, with investigative-lead warnings. The graph showed 35 nodes and 36 relationships, with identifiers masked. The case page showed PDF page/character provenance, source outcomes and retrieval times, findings, timeline, uncertainty, and conservative assessment.
- The PDF case screenshot exposed overlapping extraction location, confidence, review-status, and uncertainty text. Separated those items into a wrapping metadata layout in `frontend/src/App.tsx` and added `frontend/src/entity-review.css`. The refreshed screenshot shows each field on its own readable line without overlap.
- Downloaded the Markdown case report through the UI. Confirmed it includes “Insufficient evidence,” omits the raw synthetic email, and includes the Markdown-escaped masked form `d\\*\\*\\*@example.com`.
- Browser access to the Corrections screen was declined at the local-origin permission gate. Stopped browser interaction there; did not try another browser, raw browser interface, or indirect UI path. Correction request/review behavior remains covered by the passing API-flow tests.

### Checks actually run

- Backend `run_ci_tests.py` with a fresh synthetic SQLite environment and loopback access: 213 unit tests (211 passed, 2 PostgreSQL-only skipped), 14 API-flow tests passed, 2 proxy tests passed; exit code 0.
- `pnpm run build` after the extraction-card layout fix: passed; TypeScript and Vite production build completed.
- `pnpm run test:redaction`: 15 passed, 0 failed.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- `scripts/test-compose-config.ps1`: passed.
- `scripts/test-backup.ps1` and `scripts/test-restore.ps1`: fake-Docker orchestration checks passed; these do not verify a live backup or restore.
- Authenticated UI review: dashboard, campaign page, evidence graph, case detail and timeline rendered; PDF report downloaded and redaction checks passed. Corrections screen not inspected due the declined origin gate.
- Docker remains unavailable: `docker desktop status` and `docker info` report the missing Linux Engine named pipe. No Compose services or live PostgreSQL/Neo4j/OCR stack were started.

### Files/components changed

- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/entity-review.css` (new)
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The authenticated browser run used SQLite and the `APP_ENV=testing` mode; it does not verify PostgreSQL, Neo4j, encrypted upload storage, OCR container behavior, or deployment.
- The correction queue browser screen and graph filter interaction were not visually inspected. The origin permission gate declined the Corrections navigation; API tests cover correction behavior.
- PostgreSQL-only migration/concurrency tests, live backup/restore/key recovery, hosted CI/deployment security checks, and measured evaluation on authorized time-separated data remain outstanding.
- The local test stack is intended to remain available for user inspection: API PID 15168 on port 8001, Vite session 36678 on port 5174, and worker session 76395. Confirm service identity before reuse or stopping them.

### Exact next steps, in order

1. Run the documented app against Docker/PostgreSQL/Neo4j/OCR when the Docker Desktop Linux Engine can be started in a permitted user session; verify migration, projection rebuild, encrypted intake, and real recovery workflows.
2. Complete the remaining authenticated visual checks, including correction queue and graph filters, if the local-origin permission is granted in the browser.
3. Configure a hosted Git remote/runner and verify full CI, TLS, storage/backup encryption, access controls, egress, and recovery on operator-owned infrastructure.
4. Obtain authorized time-separated annotations and run all four evaluation comparisons; report actual results only.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- The isolated browser stack uses `backend/.test-runtime/browser-e2e-controlled-20261103/browser-e2e.db` and its sibling `uploads` directory. Current services were started from the bundled Python 3.12 runtime and Node/Vite against ports 8001 and 5174; verify them before reuse.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`. From `backend`, set `APP_ENV=testing`, use a new SQLite file under `.test-runtime`, set `PYTHONPATH` to bundled `Lib\site-packages` before `.pydeps`, and run `python run_ci_tests.py` with loopback enabled for the API/proxy suites.
- Do not commit unless requested.

## 2026-11-03 00:07 (Asia/Calcutta) — Re-run local verification; retry Docker Engine startup

### Completed in this stage

- Re-read the build status and plan. No `AGENTS.md` file was found in the workspace. The working tree still has the project as untracked files; no commits were created.
- Re-ran the backend CI harness in a fresh synthetic SQLite runtime. The non-HTTP suite passed 213 tests (211 passed, 2 PostgreSQL-only skipped); with loopback-enabled execution, the isolated API suite passed 14 tests and the proxy suite passed 2 tests. A first sandboxed attempt stalled after the unit suite at the HTTP integration stage; the successful run used the local loopback permission needed by `TestClient`.
- Re-ran `pnpm run build` and `pnpm run test:redaction`: production build succeeded and all 15 frontend tests passed.
- Re-ran `scripts/test-compose-config.ps1`: passed the Compose configuration checks for required secret wiring, database URLs, proxy trust, upload limits, health and headers.
- Re-ran fake-Docker `scripts/test-backup.ps1` and `scripts/test-restore.ps1`: both orchestration checks passed for capture/restore order, checksums, failure handling, and service restart/graph rebuild behavior. These do not start containers or restore a real database.
- Retried Docker startup via `docker desktop start` and the installed `Docker Desktop.exe`. The executable exists, but its process exited and both `docker desktop status` and `docker info` still report that the Linux Engine named pipe is unavailable. The Docker Desktop error log query returned no entries. No containers were started.

### Checks actually run

- Backend `run_ci_tests.py` with `APP_ENV=testing`, a fresh SQLite database, synthetic bootstrap secrets, and loopback access: 213 unit tests (211 passed, 2 skipped), 14 API-flow tests passed, and 2 proxy tests passed; exit code 0.
- `pnpm run build`: passed.
- `pnpm run test:redaction`: 15 passed, 0 failed.
- `scripts/test-compose-config.ps1`: passed.
- `scripts/test-backup.ps1`: passed fake-Docker orchestration checks.
- `scripts/test-restore.ps1`: passed fake-Docker orchestration checks.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- `docker desktop status` and `docker info`: failed because `npipe:////./pipe/dockerDesktopLinuxEngine` is absent; Docker Desktop did not remain running.
- `docker desktop logs --priority 2 --boot 0`: no error entries returned.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- PostgreSQL-only concurrency/migration tests remain skipped because no PostgreSQL service is reachable. Live PostgreSQL, Neo4j, OCR-in-container, encrypted-volume, graph-rebuild, and real backup/restore/key-recovery behavior remain unverified.
- Authenticated browser screens and the full visible intake-to-report workflow remain unverified. No browser credentials were entered during this stage.
- Hosted CI, operator-owned deployment security checks, and measured evaluation on authorized time-separated data remain outstanding.
- Docker Desktop cannot start in the current session; service-control inspection is also unavailable to this workspace process.

### Exact next steps, in order

1. Complete authenticated browser review using the synthetic investigator account, including intake, case/timeline, graph/campaign, correction review, and redacted report download.
2. Start Docker Desktop's Linux Engine in a user session with the required Windows service permissions, then run the Compose stack against disposable synthetic data and verify PostgreSQL migrations, Neo4j rebuild, OCR, encrypted uploads, and real backup/restore.
3. Configure a hosted Git remote/runner and run the full CI workflow; verify TLS, storage/backup encryption, access controls, egress, and recovery on operator-owned infrastructure.
4. Obtain authorized time-separated annotations and run all documented evaluation comparisons; report only measured results.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- From `backend`, use the bundled Python 3.12 runtime with `PYTHONPATH` set to bundled `Lib\site-packages` before `backend\.pydeps`, `APP_ENV=testing`, and a new SQLite database under `.test-runtime`; run `python run_ci_tests.py` with loopback enabled for the API/proxy suites.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`. From the repository root, run `scripts/test-compose-config.ps1`; from `scripts`, run `test-backup.ps1` and `test-restore.ps1`.
- Do not commit unless requested.

## 2026-10-28 23:23 (Asia/Kolkata) — Revalidate frontend and local runtime gates

### Completed in this stage

- Re-read the current build checkpoint, build plan and requirements traceability before continuing. The working tree still contains the project as untracked files; no edits from this stage have been committed.
- Confirmed the local in-app browser can reach the running frontend. It rendered the account-creation page and showed the secure-workspace and investigative-lead language. This was an unauthenticated landing-page check only; it did not verify authenticated workflows or their visual states.
- Re-ran the current frontend production build (`pnpm run build`): TypeScript compilation and Vite production build completed successfully.
- Re-ran the current frontend test suite (`pnpm run test:redaction`): 15 tests passed, 0 failed.
- Rechecked Docker availability. Docker CLI is installed, but the Docker Desktop Linux Engine pipe is absent, so live Compose/PostgreSQL/Neo4j/OCR and container-based checks remain unavailable in this session.

### Checks actually run

- `pnpm run build` from `frontend`: passed; Vite emitted production assets after `tsc -b`.
- `pnpm run test:redaction` from `frontend`: 15 passed, 0 failed.
- In-app browser opened `http://127.0.0.1:5174/`: signup landing page rendered; authenticated pages not inspected.
- `docker info`: failed to connect to `npipe:////./pipe/dockerDesktopLinuxEngine`; no container services were started.
- `git status --short`: project files remain untracked; no tracked modifications were reported.

### Files/components changed

- `BUILD_STATUS.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The local browser visual check is not an authenticated end-to-end review. No login, intake, graph/campaign filtering, correction queue, or report download was exercised in the browser.
- Docker's Linux Engine remains unavailable. PostgreSQL/Neo4j/OCR, live encrypted upload behavior, graph rebuild, and live backup/restore/key recovery are not verified.
- Hosted CI, hosted deployment controls, and authorized time-separated evaluation remain outstanding.

### Exact next steps, in order

1. Complete an authenticated browser review of intake, case review, timeline, graph/campaign, correction queue, and redacted report download.
2. Start Docker Desktop's Linux Engine and run the Compose deployment with synthetic data; verify PostgreSQL migrations, OCR, Neo4j projection/rebuild, encrypted uploads, and live backup/restore/key recovery.
3. Configure a hosted Git remote/runner and run the full CI workflow; verify TLS, storage/backup encryption, access controls, egress and recovery on operator-owned infrastructure.
4. Obtain authorized time-separated annotations and run all documented evaluation comparisons; report measured results only.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- The current frontend is reachable at `http://127.0.0.1:5174/`; the previous checkpoint also recorded API/worker services on loopback ports 8001 and the background worker. Confirm process ownership and health before reusing them.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`. From `backend`, use the documented Python 3.12 environment and run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-28 23:18 (Asia/Kolkata) — Verify PDF intake and correction handling; correct upload-storage provenance

### Completed in this stage

- Exercised multipart PDF intake through the live, refreshed loopback API and worker using a generated fictional PDF. The case completed, extracted email and location entities with `pdf_page_1` provenance, wrote the upload under an opaque filename in the configured private test directory, and did not return a public/download URL.
- Verified the downloaded report masks the PDF email and that machine assessment remains `Insufficient evidence`.
- Exercised public correction intake on a synthetic case, received a one-time status token, moved the request through investigator review (`investigating` then `resolved`), and confirmed the public token status reflects those transitions. The investigator documented that no change was made without contradictory source evidence.
- Found that the file-intake evidence excerpt always claimed encryption even when the isolated `APP_ENV=testing` mode intentionally permits plaintext fixtures. Updated the excerpt to identify this as test-only plaintext, required an encryption key whenever `APP_ENV` is not testing, and added regressions covering both encrypted and test-only storage descriptions plus fail-closed missing-key behavior.
- Restarted the local API and worker so the current app loads the updated upload behavior. A second live fictional PDF returned the accurate test-only storage disclosure at intake, then completed processing with PDF page provenance.
- Removed only the generated source PDF and temporary verification helper. Preserved the controlled app database and its synthetic records.

### Checks actually run

- `python -m unittest tests.test_upload_persistence -v`: 4 passed.
- Full `python run_ci_tests.py`: 213 unit tests (211 passed, 2 PostgreSQL-only skipped), 14 isolated API-flow tests, and 2 proxy-header tests passed; exit code 0.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- Live PDF intake and worker: passed; PDF email/location source locations were `pdf_page_1`, the private upload name was opaque, intake disclosed test-only plaintext accurately, and assessment remained `Insufficient evidence`.
- Live correction workflow: public request received, status token worked, investigator advanced it through `investigating` and `resolved`, and no source-unsupported record edit was made.
- Final app smoke check: API readiness, frontend root, and same-origin policy proxy all returned HTTP 200. With five synthetic cases, the SQLite-backed graph API returned 35 nodes and 36 edges, and one campaign group.

### Files/components changed

- `backend/app/main.py`
- `backend/tests/test_upload_persistence.py`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Current live uploads use `APP_ENV=testing` with plaintext synthetic files by design; this run does not verify encrypted-at-rest behavior on a deployed instance. Unit tests cover AES-GCM storage and fail-closed configuration, but production key handling and host encryption remain unverified.
- The controlled SQLite database has one synthetic account, five synthetic cases, five processing jobs, and one synthetic correction request. The local API/worker/Vite are loopback-only, not a production deployment.
- Authenticated visual browser review, PostgreSQL/Neo4j/Docker/OCR, backup/restore/key recovery, hosted CI, production controls, and authorized time-separated evaluation remain outstanding.

### Exact next steps, in order

1. Complete a visual authenticated review of intake, uploaded-file details, timeline, graph/campaign, correction queue, and report screens.
2. Start Docker Desktop's Linux Engine and verify the Compose/PostgreSQL/Neo4j/OCR stack, encrypted upload behavior, graph rebuild, and live backup/restore/key recovery with synthetic data.
3. Run hosted CI and verify TLS, storage/backup encryption, ACLs, egress, and recovery on operator-owned infrastructure.
4. Obtain authorized time-separated annotations and run the required evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- The controlled API is listening on 127.0.0.1:8001, the worker is a background process, and Vite listens on 127.0.0.1:5174; confirm process ownership before reusing or stopping them.
- From `backend`, use the documented Python 3.12 environment and run `python run_ci_tests.py`; frontend checks remain `pnpm run build` and `pnpm run test:redaction`.
- Do not commit unless requested.

## 2026-10-28 23:10 (Asia/Kolkata) — Fix UPI sentence-boundary extraction and verify worker persistence

### Completed in this stage

- Traced the missing fictional UPI entity to the extractor's trailing-token boundary: a final sentence period was treated as part of a possible provider suffix and caused the entire candidate to be discarded.
- Tightened the UPI pattern to require an alphanumeric final suffix character, permit ordinary sentence punctuation after the identifier, and reject a dot followed by a word character as a partial match. Added regressions for sentence-final UPI punctuation and dotted email/domain separation.
- Extended the database-backed worker pipeline check to assert the UPI value, normalized value, exact source span, review status, and neutral local-corpus `no_result` evidence persist.
- Restarted only the controlled loopback API and worker against their original test SQLite database so the live application loaded the updated parser. The existing synthetic account remained usable. A third fictional, consented case processed to `completed`; the UPI span, evidence outcome, conservative assessment, and masked report assertions all passed.

### Checks actually run

- `python -m unittest tests.test_extract -v`: 26 passed.
- `python -m unittest tests.test_worker_pipeline -v`: 2 passed, including encrypted PDF provenance and the new UPI persistence assertions.
- Full `python run_ci_tests.py`: 212 unit tests (210 passed, 2 PostgreSQL-only skipped), 14 isolated API-flow tests, and 2 proxy-header tests passed; exit code 0.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- Live API/worker UPI case: completed; exact `candidate.test@upi` source span persisted without the terminal period; local lookup persisted `no_result`; assessment remained `Insufficient evidence`; Markdown report omitted the identifier.
- After the API/worker refresh, rechecked API readiness, frontend root, and Vite `/api/policy` proxy: all returned HTTP 200. The graph response contained 18 nodes and 18 edges; one campaign group remained visible.
- Confirmed the controlled SQLite store has 1 synthetic account, 3 synthetic cases, and 3 processing jobs. API and Vite remain bound to loopback at ports 8001 and 5174. No PostgreSQL, Neo4j, Docker, external source, or real personal data was used.

### Files/components changed

- `backend/app/extract.py`
- `backend/tests/test_extract.py`
- `backend/tests/test_worker_pipeline.py`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- UPI extraction handles this verified punctuation case; provider-specific formats and ambiguous identifier/email overlaps still need broader authorized fixtures.
- Authenticated visual browser interaction, PostgreSQL/Neo4j/Docker/OCR, deployment and recovery, hosted CI, and authorized time-separated evaluation remain outstanding.

### Exact next steps, in order

1. Complete visual browser review of intake, case timeline, extraction review, campaign/graph, and report download on the loopback app.
2. Start Docker Desktop's Linux Engine and run Compose with synthetic data; verify PostgreSQL migration/concurrency, OCR, Neo4j projection/rebuild, encrypted upload handling, backup/restore and key recovery.
3. Run hosted CI and verify production TLS, storage/backup encryption, ACLs, egress, and operational recovery.
4. Obtain authorized time-separated annotations and run all documented evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- Local API/worker/Vite are running on loopback ports 8001/5174 with synthetic SQLite data; confirm process ownership before reuse or shutdown.
- From `backend`, use the documented Python 3.12 environment and run `python run_ci_tests.py`; frontend checks remain `pnpm run build` and `pnpm run test:redaction`.
- Do not commit unless requested.

## 2026-10-28 23:05 (Asia/Kolkata) — Verify the live isolated SQLite investigation workflow

### Completed in this stage

- Re-inspected the current runtime with elevated listener/process metadata. The controlled local test stack was still active despite the earlier checkpoint saying it had stopped: API PID 21412 (`uvicorn app.main:app` on 127.0.0.1:8001), Vite PID 5224 (127.0.0.1:5174), and worker PID 29872. Its active SQLite database is `backend/.test-runtime/browser-e2e-controlled-20261028.db`; aggregate counts show one synthetic user, two synthetic cases, and two processing jobs.
- Corrected the prior service-state assumption: the earlier non-elevated listener inspection returned no results, but it was not authoritative. No production credentials, database, or external providers were involved.
- Used the documented test-only bootstrap value to create a fictional investigator account, signed in, accepted the current consent version, and submitted two fictional recruitment messages that share the reserved `example.com` email identifier.
- Observed both jobs reach `completed`; extracted entities and local-corpus evidence outcomes persisted. The local corpus returned `no_result` for unmatched claims, and machine assessment stayed `Insufficient evidence`.
- Confirmed the investigator could review an extraction, refresh deterministic case links, and read the graph and campaign endpoints. The proposed relationship has strength 55, rule version `campaign-signals-v3-threshold-40`, and remains `proposed`; one campaign group is visible. This is an investigative lead, not a verdict.
- Downloaded the Markdown report and asserted it did not contain the submitted email or fictional UPI identifier. The API flow returned HTTP 200 for graph and campaign reads.
- Final read-only smoke check returned HTTP 200 for API readiness, frontend root, and same-origin `/api/policy`; the investigator graph response contained 14 nodes and 15 edges, with one campaign group. Both cases remained `Insufficient evidence`.
- Opened the local app in the Codex browser panel; the tab request is queued. A separate Edge/Computer Use launch timed out at the desktop app-approval step, so visual/authenticated browser interaction remains unverified.
- Removed only the empty duplicate SQLite file/logs created by this turn's failed duplicate startup attempt. Preserved the active controlled SQLite database and its synthetic records for local inspection.

### Checks actually run

- Live local HTTP workflow through API and worker: registration, login, consented case intake, two worker completions, case detail/evidence retrieval, entity review, link refresh, campaign and graph reads, and Markdown report masking all passed.
- Active frontend root and `/api/policy` proxy were previously verified on port 5174; current Vite listener is confirmed. Visual browser flow was not completed.
- These checks use SQLite and a local test stack. They do not verify PostgreSQL, Neo4j, OCR container behavior, TLS, production storage, deployment recovery, or hosted CI.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The controlled local app is running on loopback and contains only the synthetic investigator and two synthetic cases created for this check. It is not a hosted or production deployment.
- Authenticated visual browser E2E, PostgreSQL-only tests, live Docker/Neo4j/OCR, backup/restore/key recovery, hosted CI, production security controls, and authorized-data evaluation remain outstanding.
- The 22:29 status entry's statement that no services were running was contradicted by current process evidence and is superseded by this correction.

### Exact next steps, in order

1. If reviewing locally, open `http://127.0.0.1:5174/` and sign in with the local synthetic account described in this checkpoint's handoff; keep the app loopback-only.
2. Complete a visual authenticated browser walkthrough of the case, timeline, graph/campaign, review, and report screens.
3. Start Docker Desktop's Linux Engine and verify the Compose/PostgreSQL/Neo4j/OCR stack, real backup/restore, and graph rebuild with synthetic data.
4. Run hosted CI, complete deployment security/recovery checks, and obtain authorized time-separated annotations for the evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- The controlled local API is listening on 127.0.0.1:8001, Vite on 127.0.0.1:5174, and the worker is a background process; confirm process ownership before reusing or stopping them.
- Backend and frontend regression commands are listed in the prior checkpoint. Do not commit unless requested.

## 2026-10-28 22:31 (Asia/Kolkata) — Fail closed on missing deployment secrets

### Completed in this stage

- Removed Compose fallbacks for PostgreSQL and Neo4j passwords, JWT secret, upload-encryption key, and one-time investigator/reviewer setup codes. Compose now refuses to render/start when these values are unset instead of allowing known fallback credentials into service containers.
- Updated the hosted Compose configuration job and the PowerShell configuration check to supply synthetic-only values. The config check runs Compose with an empty environment and asserts that each of the six required secrets fails closed when omitted, then verifies the configured values and proxy wiring render correctly.
- Documented the new fail-closed behavior in the setup guide.

### Checks actually run

- `./scripts/test-compose-config.ps1`: passed, including six negative missing-secret checks and positive rendered-configuration checks. Docker Engine is not required for this command.
- Live service startup and PostgreSQL/Neo4j connection behavior remain unverified because Docker Desktop's Linux Engine is unavailable.

### Files/components changed

- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `scripts/test-compose-config.ps1`
- `README.md`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Compose secret presence now fails closed, while API startup performs further format/strength checks. The synthetic values used for the configuration-only CI job are never used to start the platform.
- Live PostgreSQL, Neo4j, OCR, browser E2E, deployment/recovery, hosted CI, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Re-run the full local checks and the Compose configuration test after this deployment change.
2. Once Docker Engine is available, run the full stack with a private `.env` and verify API/worker startup, PostgreSQL/Neo4j health, OCR, graph rebuild, and recovery procedures.
3. Complete browser E2E, hosted CI, deployment security/recovery checks, and the authorized time-separated evaluation.

### Resume commands

- From the repository root run `./scripts/test-compose-config.ps1`.
- Run the backend and frontend checks from `BUILD_STATUS.md` after reviewing the workspace status.
- Do not commit unless requested.

## 2026-10-28 22:29 (Asia/Kolkata) — Revalidate current backend and frontend checks

### Completed in this stage

- Rechecked the current checkout: project sources remain untracked, there is no configured Git remote, and no local API/frontend service is running.
- Re-ran the complete local backend harness. It passed 210 unit tests (208 passed; 2 PostgreSQL-only tests skipped), 14 isolated API-flow tests, and 2 proxy-header tests. The HTTP suites ran with loopback networking enabled.
- Re-ran the frontend production build and test suite: build passed and all 15 tests passed.
- Confirmed Docker CLI is installed, but Docker Desktop's Linux Engine is unavailable. Live Compose and hosted CI therefore remain unverified.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The local full backend/API/proxy, frontend build, and frontend tests pass. PostgreSQL-specific concurrency, live Docker/Neo4j/OCR, authenticated browser E2E, hosted CI/deployment security and recovery, and authorized-data evaluation remain unverified.
- There is no Git remote, so hosted CI has not run. Do not claim release readiness based on local tests.

### Exact next steps, in order

1. Start Docker Desktop's Linux Engine and verify the Compose stack with synthetic data, including PostgreSQL-specific tests, Neo4j projection/rebuild, OCR, retention, and live backup/restore.
2. Complete the authenticated browser journey from account setup through case intake, review, campaign/graph inspection and report download, using a synthetic investigator account.
3. Configure a repository remote and run all hosted CI jobs; confirm hosted TLS, storage/backup encryption, ACLs and recovery with operator-owned infrastructure.
4. Obtain authorized time-separated annotations and run the documented evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- From `backend`, use the documented Python 3.12 environment and run `python run_ci_tests.py`; frontend checks are `pnpm run build` and `pnpm run test:redaction` from `frontend`.
- Follow `README.md` only after Docker Engine is available. Do not commit unless requested.

## 2026-10-28 22:27 (Asia/Kolkata) — Verify location extraction through text and encrypted PDF processing

### Completed in this stage

- Extended the database-backed worker pipeline tests to check that workplace locations from submitted text and an encrypted PDF persist as reviewable entities with the correct source location and exact text span.
- The new worker check caught a trailing-period bug in location entity values parsed from PDF text (`Pune.` instead of `Pune`). Updated only the location boundary trimming so terminal sentence punctuation is excluded while the source span still points to the exact place name.

### Checks actually run

- `python -m unittest tests.test_worker_pipeline -v`: 2 passed, including encrypted-PDF-to-worker provenance and neutral-finding workflow.
- Full `run_ci_tests.py` with loopback-enabled API/proxy suites: 210 unit tests (208 passed, 2 PostgreSQL-only skipped), 14 API-flow tests passed, 2 proxy tests passed; overall exit code 0.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- Authenticated browser flow, PostgreSQL, Neo4j, Docker, OCR-in-container and deployment controls remain unverified.

### Files/components changed

- `backend/app/extract.py`
- `backend/tests/test_worker_pipeline.py`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Browser/account handoff is still pending; the isolated SQLite account and case counts were zero, and its services have stopped.
- PostgreSQL-only tests, live Docker/Neo4j/OCR, deployment security and recovery, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Continue the authenticated browser workflow after the operator starts a verified local or Compose instance and creates a synthetic investigator account directly in the browser.
2. Run hosted Linux CI with PostgreSQL and remaining container/Windows jobs.
3. Verify live Compose, OCR, Neo4j projection/rebuild, encrypted upload migration, backup/restore/key recovery, TLS and host ACL controls.
4. Obtain authorized time-separated annotations and execute the required evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- From `backend`, restore the documented Python runtime environment and run `python run_ci_tests.py`.
- Use `README.md` Local development instructions to start the app; do not assume the last synthetic test processes or browser state are still active.
- Do not commit unless requested.

## 2026-10-28 22:22 (Asia/Kolkata) — Extract locations from constrained workplace phrases

### Completed in this stage

- Added deterministic, low-confidence location candidates for explicit mixed-message constructions such as “based in Pune,” “office in New Delhi,” “work from Pune,” and “job location: Pune.”
- Preserved exact source spans and explanatory uncertainty; labeled locations continue to take precedence over inferred candidates. Generic home/remote/hybrid/anywhere terms and unrelated city mentions do not produce a location entity.
- A boundary probe exposed that “role in customer support” could be mistaken for a place. Removed ambiguous `job/role/position in ...` triggers, expanded stop words, and added a regression confirming job functions are not extracted as locations.
- Verified that the user handoff was not completed in the isolated SQLite database: read-only table counts show zero users, zero cases, and zero processing jobs. The API/frontend listeners and worker session have since stopped; no browser workflow data was created.

### Checks actually run

- `python -m unittest tests.test_extract -v`: 24 passed.
- Full backend `run_ci_tests.py` with loopback-enabled API/proxy execution: 210 unit tests (208 passed, 2 PostgreSQL-only skipped), 14 API-flow passed, 2 proxy tests passed; overall exit code 0.
- Python `compileall` for `app`, `tests`, `evaluation`, and `run_ci_tests.py`: passed.
- Earlier in this session: `pnpm run build`, `pnpm run test:redaction` (15 passed), Compose config validation, fake-Docker backup and restore checks, Python compileall, and controlled API/frontend/policy smoke checks all passed.
- No PostgreSQL, Neo4j, Docker, OCR-in-container, or authenticated browser workflow was verified.

### Files/components changed

- `backend/app/extract.py`
- `backend/tests/test_extract.py`
- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The location patterns are deliberately contextual and conservative; arbitrary recruiter names, locations, and job descriptions in unrestricted prose are not generally inferred.
- Authenticated browser workflow remains pending user credential handoff. The previous synthetic SQLite API/frontend processes and worker have stopped.
- PostgreSQL-only tests, live Docker/Neo4j/OCR, hosted deployment/security, live recovery, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Resume the browser workflow on a verified local test instance after the user creates a synthetic investigator account in the browser; do not handle or request their password.
2. Run hosted Linux CI with PostgreSQL and all container/Windows jobs.
3. Verify the live Compose stack, OCR, Neo4j projection/rebuild, encrypted uploads, backup/restore/key recovery, TLS and infrastructure access controls.
4. Obtain authorized time-separated annotations and run the required evaluation comparisons.

### Resume commands

- Re-read this file and `git status --short` before changing code.
- For a fresh deployment, follow `README.md` Local development steps after setting private `.env` values. The synthetic test setup code from the stopped test process must not be reused as a deployment credential.
- Run backend checks with the Python 3.12 `site-packages` before `backend/.pydeps` on `PYTHONPATH`, and direct `TEMP`/`TMP`/`TMPDIR` to `backend/.test-runtime`.
- Do not commit unless requested.

## 2026-10-28 22:16 (Asia/Kolkata) — Isolate the browser workflow on dedicated local ports

### Completed in this stage

- Found listeners already occupying the default development ports 8000 and 5173. Their configuration could not be verified, so no account or case was submitted to them.
- Started a controlled synthetic test stack on unused loopback ports 8001 and 5174 with a separate SQLite database, test-only bootstrap codes and encryption key, private upload directory, RDAP disabled, and no Neo4j connection.
- Waited for API migrations before starting the worker. An initial worker launch raced the migration and exited because `processing_jobs` did not yet exist; after restarting it against the migrated database, the worker stayed active.
- Opened the controlled frontend in the in-app browser and left it at the account-creation form. No credential or case has been submitted. The user must create the synthetic investigator account directly in the browser because credential entry requires handoff.

### Checks actually run

- API readiness on `http://127.0.0.1:8001/health/ready`: HTTP 200.
- Frontend root on `http://127.0.0.1:5174/`: HTTP 200.
- Vite same-origin `/api/policy` proxy on port 5174: HTTP 200; response shows `rdap_enabled=false` and the expected local consent disclosure.
- At the time of this checkpoint, verified the controlled API and Vite process IDs owned ports 8001 and 5174. That test instance is stopped in the newer 22:21 checkpoint above.
- Browser rendered the account-creation screen. Authenticated intake and review flow remains pending user credential handoff.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- No account or case has been created. The browser automation must stop at authentication credentials until the user completes the signup form.
- This controlled SQLite stack is for synthetic local workflow checks only; it is not the requested PostgreSQL/Neo4j deployed stack.
- Hosted PostgreSQL CI, Docker/Neo4j/OCR, full browser journey, live recovery/security verification, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. In the already-open browser at `http://127.0.0.1:5174/`, create a synthetic investigator account using a test email, a password chosen and entered privately by the user, and the local test-only setup code `synthetic-test-investigator-code-32chars`. This code is for the current isolated SQLite instance only; never reuse it for deployment. Do not send the password to chat.
2. After the account exists, continue the browser flow with synthetic case text and file intake, processing status, investigator review, campaign/graph, redacted report download, correction and retention checks.
3. Run hosted Linux CI with PostgreSQL, then verify live Compose, OCR, Neo4j projection/rebuild, encrypted uploads, backup/restore and key recovery.
4. Verify production TLS, storage/backup encryption and ACLs, RDAP egress, and recovery controls on operator-owned infrastructure.
5. Obtain authorized, time-separated annotations and run the required evaluation comparisons.

### Resume commands

- Inspect this file and `git status --short` before changing code.
- At the time of this checkpoint, the signup form was open on ports 8001/5174. Those listeners are now stopped; inspect current service state before continuing.
- The setup code `synthetic-test-investigator-code-32chars` applied only to that isolated test instance and is not a deployment credential.
- Do not commit unless requested.

## 2026-10-28 22:09 (Asia/Kolkata) — Inspect local account screens; default-port test isolation inconclusive

### Completed in this stage

- Attempted to start the API, worker, and Vite frontend with a synthetic disposable SQLite database, synthetic bootstrap codes, a test-only upload key, and private temporary upload storage.
- API liveness, frontend root, and same-origin `/api/policy` returned HTTP 200, but later process inspection found pre-existing listeners on the default ports. The responses cannot be attributed to the attempted synthetic API process and are not accepted as controlled-stack evidence. No writes were submitted.
- Opened the local application in the in-app browser and inspected the sign-in and account-creation screens. No account, case, or uploaded data was created.
- Stopped before entering or submitting a password. The applied computer-use skill requires a user handoff for creating or entering authentication credentials. The browser journey therefore still needs a user-created synthetic investigator account before I can continue its remaining non-credential steps.

### Checks actually run

- API `GET /health/live`: HTTP 200.
- Frontend `GET /`: HTTP 200.
- Same-origin proxy `GET /api/policy`: HTTP 200.
- In-app browser rendered the real sign-in form and the account setup form. Authenticated UI workflow was not completed.
- The complete backend runner passed earlier in this session: 207 unit tests (205 passed, 2 PostgreSQL-only skipped), 14 API-flow tests, and 2 proxy tests. Compose configuration and fake-Docker backup/restore scripts passed; frontend build and all 15 frontend tests passed.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- Authenticated browser flow, including intake through report/correction/retention, remains unverified because account creation requires a user credential handoff. The later controlled test instance now runs on ports 8001/5174; use its separate current checkpoint above rather than the earlier default-port attempt.
- PostgreSQL-only checks, live Docker/Neo4j/OCR, backup/restore/key recovery, hosted security controls, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Start the local services and let the operator create a synthetic investigator account in the browser; do not send the password into chat.
2. Continue the browser workflow with consented synthetic text/file intake, processing status, investigator entity/evidence review, case links/campaign/graph, redacted report download, correction and retention verification.
3. Run hosted Linux CI with PostgreSQL, then verify the full Docker Compose stack, OCR, Neo4j projection/rebuild, encrypted uploads and live recovery.
4. Verify TLS, at-rest encryption/ACLs, RDAP egress, and recovery controls on operator-owned infrastructure.
5. Obtain authorized, time-separated annotations and run the required evaluation comparisons.

### Resume commands

- Re-read this file, then inspect `git status --short`.
- Use the later controlled-test checkpoint above to continue the already-running isolated stack. If those processes have stopped by the time of resume, use `README.md`'s Local development steps for Docker Compose after verifying there are no port conflicts.
- At the sign-up form, use a synthetic address and `synthetic-test-investigator-code-32chars` only against the isolated SQLite instance; choose and enter the password directly in the browser and do not share it in chat. Do not use this code in a deployed environment.
- Do not commit unless requested.

## 2026-10-28 22:06 (Asia/Kolkata) — Restore a compatible local test runtime and rerun verification

### Completed in this stage

- Resolved the apparent backend test dependency block without changing application requirements: the bundled Python 3.12 runtime supplies compatible compiled Pydantic and cryptography packages, while `backend/.pydeps` supplies the application packages. Put the bundled runtime's `site-packages` before `.pydeps` on `PYTHONPATH` to avoid importing the incompatible CPython 3.14-only extension.
- Set `TEMP`, `TMP`, and `TMPDIR` to `backend/.test-runtime`; this avoids Windows sandbox temporary-directory cleanup permission errors.
- Reran the full backend runner and deployment-support checks. The previous stage's backend test blocker is resolved locally; PostgreSQL-only tests remain opt-in.

### Checks actually run

- `run_ci_tests.py --unit-only`: 207 tests run, 205 passed, 2 PostgreSQL-only tests skipped.
- Full `run_ci_tests.py` with loopback-enabled execution: same 207 unit tests (205 passed, 2 skipped), API-flow suite 14 passed, proxy suite 2 passed; overall exit code 0.
- Python compileall for `app`, `tests`, `evaluation`, and `run_ci_tests.py`: passed.
- `scripts/test-compose-config.ps1`: passed configuration checks for database URLs, upload key wiring, throttles, proxy trust, upload bounds, health/routing, security headers and build contexts.
- `scripts/test-backup.ps1` and `scripts/test-restore.ps1`: both passed fake-Docker orchestration checks. They do not constitute live database or volume recovery.
- `pnpm run build`: passed. `pnpm run test:redaction`: 15 passed.
- Docker Engine remains unavailable; no live PostgreSQL/Neo4j/container/browser/deployment verification was performed by these checks.

### Files/components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- `REQUIREMENTS_TRACEABILITY.md`

### Known bugs or unfinished work

- The two PostgreSQL-specific checks still require hosted PostgreSQL CI.
- Docker Engine and a completed browser journey remain unavailable; live OCR, graph projection/rebuild, backup/restore, TLS and infrastructure security are not verified.
- Authorized time-separated evaluation annotations and measured comparisons remain unavailable.

### Exact next steps, in order

1. Complete a real browser workflow against local API/frontend services if an in-app browser can reach the workspace; cover signup/login, consented case/file intake, processing state, investigator review, campaign/graph, report export, correction and retention.
2. Run hosted Linux CI with PostgreSQL, then run Docker Compose on an available Engine and verify OCR, Neo4j projection/rebuild, encrypted uploads and live backup/restore/key recovery.
3. Verify TLS, storage/backup encryption and ACLs, RDAP egress, and operational recovery on operator-owned infrastructure.
4. Obtain authorized, time-separated annotations and run all required evaluation comparisons.

### Resume commands

- Re-read this file and inspect `git status --short` before editing.
- For the current local Python runtime, from `backend`, set `PYTHONPATH` to the bundled Python 3.12 `Lib/site-packages` followed by `.pydeps`, set `APP_ENV=testing`, a disposable SQLite `DATABASE_URL`, and `TEMP`/`TMP`/`TMPDIR` to `.test-runtime`, then run `python run_ci_tests.py`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- Do not commit unless requested.

## 2026-10-28 22:00 (Asia/Kolkata) — Prevent salary amounts from becoming payment-request claims

### Completed in this stage

- Changed deterministic currency extraction so an amount becomes `payment_amount_claim` only when nearby explicit payment wording supports that meaning. Nearby salary/compensation language becomes `compensation_amount_claim`; unrelated or ambiguous amounts are omitted instead of receiving an unsupported semantic label.
- Preserved exact character spans, source context and uncertainty statements for extracted amounts. The new claim type remains outside deterministic campaign-matchable identifiers.
- Added regression cases for payment, salary, LPA, unrelated amounts and ambiguous mixed context.
- Updated the requirements matrix and step-by-step engineering walkthrough.

### Checks actually run

- `python -m unittest tests.test_extract -v`: 21 passed, including the final LPA-specific regression.
- `pnpm run build`: passed; TypeScript and production Vite bundle generated.
- `pnpm run test:redaction`: 15 passed.
- Full backend `run_ci_tests.py --unit-only`: not completed. The project-local `.pydeps` is missing `cryptography`; the bundled Python 3.12 runtime cannot load the Python 3.14-only compiled `pydantic_core` extension from `.pydeps`. A local pip restore of pinned `cryptography==50.0.2` failed because DNS/network access to the package index is unavailable. Do not treat these attempts as a pass.
- Docker Engine remains unavailable, so PostgreSQL, Neo4j, containers and deployed browser journeys remain unverified.

### Files/components changed

- `backend/app/extract.py`
- `backend/tests/test_extract.py`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- General free-form recruiter/location extraction remains intentionally limited to explicit labels and constrained hiring phrases.
- Restore a Python 3.14-compatible backend dependency environment (including `cryptography==50.0.2`) before rerunning the full backend suite. This workspace currently has no package-index network access; provide an approved cached wheel or run the suite on hosted CI. The local failures above are dependency/runtime setup errors, not evidence about suite outcomes.
- PostgreSQL-specific tests, live Docker/Neo4j/OCR, actual browser workflows, hosted operational security and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Restore the Python 3.14-compatible backend dependencies from an approved wheel/cache or hosted CI, then rerun unit, API-flow and proxy suites; use hosted Linux CI for PostgreSQL-only cases.
2. Complete authenticated browser workflows through intake, evidence review, campaigns/graph, reports, corrections and retention.
3. Run Compose on Docker Engine and verify PostgreSQL, Neo4j projection/rebuild, worker OCR, encrypted uploads, backup/restore and key recovery.
4. Verify host TLS, storage/backup encryption and ACLs, RDAP egress and recovery controls.
5. Obtain authorized, time-separated annotations and run the required baseline and ablation comparisons.

### Resume commands

- Re-read this file and the repository instructions, then inspect `git status --short`.
- From `backend`, restore dependencies matching Python 3.14 (`requirements.txt` pins `cryptography==50.0.2`) from an approved wheel/cache or hosted CI before running `python run_ci_tests.py`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- Do not commit unless requested.

## 2026-10-28 21:55 (Asia/Kolkata) — Smoke-test the local frontend and API proxy

### Completed in this stage

- Started the API using a disposable `APP_ENV=testing` SQLite database and temporary upload directory, then started the existing Vite frontend on loopback.
- Confirmed API liveness returned HTTP 200, the frontend root returned HTTP 200 with title `Casework | Recruitment investigation`, and the frontend's same-origin `/api/policy` proxy returned the expected consent and configuration response.
- Checked that the temporary API/worker/Vite listeners were no longer running after the browser attempt; this smoke data is under `.test-sandbox-tmp/browser-smoke` and is synthetic only.
- Attempted a desktop-browser workflow, but the Chrome launch request timed out at the app-approval step. No user account, case, or browser interaction was performed in Chrome; UI end-to-end verification remains pending.

### Checks actually run

- Disposable API `/health/live`: HTTP 200.
- Vite `/`: HTTP 200, correct application title.
- Vite same-origin `/api/policy`: HTTP 200 with current local consent/config response.
- Port check after the attempt found no listeners on 8000 or 5173.
- The complete backend runner previously passed in this session: unit suite 202 run, 200 passed, 2 opt-in PostgreSQL skipped; API-flow 14 passed; proxy 2 passed.

### Files/components changed

- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The browser journey did not run because Chrome launch approval timed out. Docker Engine/Neo4j/PostgreSQL deployment, OCR in the container, live backup/restore, host security, and authorized-data evaluation remain unverified.
- The API/proxy suites used SQLite/mocked RDAP; the two PostgreSQL-only checks remain skipped.

### Exact next steps, in order

1. Run the full GitHub CI workflow or equivalent hosted Linux job with PostgreSQL; capture database migration/concurrency results and every container/script job.
2. With an approved browser launch or a browser-test runtime, complete signup/login, consented text and file intake, status refresh, investigator review, campaign/graph views, report download, correction, and retention flows through the frontend.
3. Start Compose on an available Docker Engine, verify OCR/container behavior and Neo4j projection/rebuild, then perform the encrypted-upload migration and live backup/restore/key-recovery drill.
4. Verify host TLS, PostgreSQL/storage/backup encryption and ACLs, RDAP egress, and operational recovery.
5. Obtain authorized, time-separated annotations and run the required comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py` in an execution context with loopback access and the CI environment configured.
- For offline build and script checks, run `python -m compileall -q app tests evaluation run_ci_tests.py`, `./scripts/test-compose-config.ps1`, `./scripts/test-backup.ps1`, and `./scripts/test-restore.ps1`.
- Do not commit unless requested.

## 2026-10-28 21:31 (Asia/Kolkata) — Run API and proxy integration suites

### Completed in this stage

- Diagnosed why the API-flow integration suite had appeared to hang: Python 3.14 was blocked while asyncio created its Windows loopback self-pipe inside the restricted sandbox. With an approved loopback-enabled execution, the async test client ran normally.
- Fixed missing bearer credentials returning HTTP 403 instead of HTTP 401 by making the bearer dependency optional and returning a deliberate 401 with `WWW-Authenticate: Bearer`. The API-flow regression now verifies this behavior.
- Made correction rate-limit integration test clean up its deliberately exhausted synthetic test-client throttle row, preventing state leakage into the following correction workflow test.
- Corrected stale API-flow expectations: the investigator must leave a request in `investigating` before applying a record correction, and case creation returns HTTP 200. The RDAP audit assertion now uses an investigator login so it can inspect the unredacted authorized timeline.

### Checks actually run

- `python run_ci_tests.py` with loopback enabled: unit suite 202 ran, 200 passed, 2 opt-in PostgreSQL tests skipped; isolated API-flow suite 14 passed; proxy-header suite 2 passed. Overall command exit code 0.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- These API-flow tests use disposable SQLite and mocked RDAP; they do not verify PostgreSQL concurrency, Neo4j, container proxy, or a live browser deployment.

### Files/components changed

- `backend/app/security.py`
- `backend/tests/test_api_flow.py`
- `BUILD_STATUS.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API and proxy integration now pass locally when loopback is permitted, but PostgreSQL-only tests remain skipped. Docker Engine never became available, so container, Neo4j, OCR-image, browser, live backup/restore, TLS and host-security checks remain outstanding.
- Authorized time-separated evaluation data/results remain unavailable; current evaluation results are pending.

### Exact next steps, in order

1. Run the hosted Linux CI workflow with its PostgreSQL service; capture results for migration/concurrency and all CI jobs.
2. Start the Compose stack with a generated upload key and complete investigator/reviewer browser workflows, including OCR, campaigns, reports, corrections and retention.
3. Perform a live encrypted upload migration, PostgreSQL backup/restore, key recovery and Neo4j rebuild drill.
4. Verify operator TLS, PostgreSQL/storage/backup encryption and ACLs, RDAP egress policy, and operational recovery.
5. Obtain authorized, time-separated annotations and execute the required comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py` in a runtime that permits the local async test client's loopback socket pair; run `python -m compileall -q app tests evaluation run_ci_tests.py`.
- In Linux CI, use the configured PostgreSQL test database URLs from `.github/workflows/ci.yml` to exercise the two skipped database tests.
- Do not commit unless requested.

## 2026-10-28 21:26 (Asia/Kolkata) — Verify encrypted file-to-finding workflow offline

### Completed in this stage

- Added a database-backed synthetic workflow test that creates a text-bearing PDF, submits it through the actual `persist_uploaded_case` transaction with consent metadata, confirms ciphertext is saved and the plaintext digest remains in provenance, then runs the real worker against the stored encrypted file.
- Verified that PDF parsing yields a persisted email entity with page location and deterministic extraction method, a curated local-corpus result with source reference and retrieval time, and an active finding that remains “Insufficient evidence” until investigator confirmation/relevance review.
- Kept the fixture isolated in SQLite and a temporary upload directory; no real identifiers or live external provider were used.

### Checks actually run

- `python -m unittest tests.test_worker_pipeline -v`: 2 passed, including the new encrypted upload-to-evidence workflow.
- `python run_ci_tests.py --unit-only`: 202 ran, 200 passed, 2 opt-in PostgreSQL tests skipped.
- This exercises the persistence/worker logic with SQLite, but does not replace the HTTP API, browser, PostgreSQL, Neo4j, or Docker deployment journeys.

### Files/components changed

- `backend/tests/test_worker_pipeline.py`
- `BUILD_STATUS.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- HTTP API-flow and proxy suites, live PostgreSQL/Neo4j, OCR binary inside the deployment image, browser workflows, actual backup/restore, key-manager/host security, and authorized-data evaluation remain unverified.
- A quiet Docker Desktop launch was attempted; no running Docker Desktop process or Linux Engine became available. WSL access is denied in this Windows workspace, and API async tests have stalled under the available local Python runtimes. Hosted Linux CI or an operator-enabled local engine is required for the pending integration checks.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Build and start Compose with a generated upload key; exercise case intake, worker/OCR, investigator/reviewer UI, campaigns, reports, corrections and retention in a browser.
3. Run a disposable live migration, PostgreSQL/Neo4j, encrypted backup/restore and key recovery drill.
4. Verify operator-host TLS, PostgreSQL/storage/backup encryption and ACLs, RDAP egress, and recovery controls.
5. Obtain authorized, time-separated annotations and run all required comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only` and `python -m compileall -q app tests evaluation run_ci_tests.py`.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:22 (Asia/Kolkata) — Encrypt private upload originals

### Completed in this stage

- Added versioned AES-256-GCM encryption for private uploads before they are written to disk. Each upload gets a fresh random nonce; the version marker and opaque filename are authenticated as associated data. The worker decrypts in memory, checks the original plaintext digest, and parses only the authenticated bytes.
- Made a canonical base64 encoding of 32 random bytes mandatory as `UPLOAD_ENCRYPTION_KEY` for API/worker startup outside test mode. Added the setting to Compose for API and worker and included a safe placeholder plus generation instructions in `.env.example`.
- Made read paths reject missing/wrong keys, corrupted authentication tags, unencrypted downgrade, invalid formats and oversized plaintext. Restore now accounts for encryption overhead and authenticates staged encrypted files before replacing the current upload set.
- Added `python -m app.encrypt_existing_uploads`, which defaults to dry-run counts and supports an explicit `--apply` for atomic conversion of earlier plaintext files. Added configuration, encrypted storage, worker decrypt-and-parse, filename binding, migration and restore tests.
- Updated README, traceability and step-by-step engineering documentation. PostgreSQL data and backup archives still rely on operator-managed encrypted storage; key rotation is manual and requires a maintenance window.

### Checks actually run

- `python run_ci_tests.py --unit-only`: 201 ran, 199 passed, 2 opt-in PostgreSQL tests skipped. This includes encrypted intake, worker decryption, key validation, legacy conversion, restore authentication, and downgrade regressions.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- `./scripts/test-compose-config.ps1`: passed, including API/worker encryption-key wiring.
- `./scripts/test-backup.ps1` and `./scripts/test-restore.ps1`: passed using fake Docker and synthetic artifacts; they do not prove live encrypted-volume backup/restore.
- Tests use synthetic/local data. No Docker Engine, live PostgreSQL/Neo4j, hosted deployment, or key-manager integration was available.

### Files/components changed

- `backend/app/private_storage.py`, `config.py`, `main.py`, `worker.py`, `restore_uploads.py`, new `encrypt_existing_uploads.py`
- `backend/requirements.txt`, related storage/config/upload/restore tests
- `docker-compose.yml`, `.env.example`, `scripts/test-compose-config.ps1`
- `README.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- PostgreSQL case/evidence records and backup archives are not application-encrypted; deployment must use managed encrypted storage and encrypted backup targets. Upload-key secret storage, backup, and recovery must be verified by the operator. Automatic key rotation is absent.
- The migration command and restore validator are covered with synthetic tests only; they need a real maintenance-window recovery drill. API/proxy integration, live PostgreSQL/Neo4j, Docker Compose/browser journeys, hosted security controls, and authorized-data evaluation remain outstanding.
- Local backend API tests still stall on the Windows async runtime; Docker Engine is unreachable and WSL access is denied in this workspace. Hosted Linux CI is needed for those suites.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Build and start Compose with a generated secret key; complete browser journeys for intake, worker/OCR, evidence review, campaigns, reports, corrections and retention.
3. Exercise encrypted upload migration, backup, restore and key recovery against disposable live services; verify Neo4j rebuild and failure recovery.
4. Verify operator-host TLS, PostgreSQL/storage/backup encryption and ACLs, RDAP egress, and recovery controls.
5. Obtain authorized, time-separated annotations and run all required comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only` and `python -m compileall -q app tests evaluation run_ci_tests.py`.
- Before API/worker/restore in any non-test environment, configure the same protected `UPLOAD_ENCRYPTION_KEY` for all processes.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:15 (Asia/Kolkata) — Add constrained narrative hiring extraction

### Completed in this stage

- Added two narrowly scoped deterministic patterns for common hiring statements (for example, “We are hiring Data Analysts at Example Ltd” and “Opening for a Data Analyst at Example Ltd”). They yield company and role candidates only; they do not infer recruiter identity, location, or claims from unrelated prose.
- Stored these candidates with exact source spans, 0.55 parser confidence, and explicit uncertainty saying the wording, employer identity, and vacancy remain unverified and require investigator review. Existing explicit-label candidates keep precedence.
- Added regressions for both phrase forms, article trimming, exact span preservation, low confidence/uncertainty, and unrelated-prose non-matches.
- Updated the step-by-step engineering walkthrough and requirement matrix to describe the narrow capability and its remaining free-form extraction limits.

### Checks actually run

- `python -m unittest discover -s tests -p 'test_extract.py' -v`: 16 passed.
- `python run_ci_tests.py --unit-only`: 190 ran, 188 passed, 2 opt-in PostgreSQL tests skipped.
- The suite uses synthetic fixtures; it does not establish real-world extraction quality. Live database/API, browser, OCR-container, and deployment behavior remain unverified.

### Files/components changed

- `backend/app/extract.py`, `backend/tests/test_extract.py`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Narrative extraction remains deliberately narrow and has no authorized annotated dataset to measure precision/recall. Recruiter and location extraction still requires explicit labels or later investigator correction.
- API/proxy integration, live PostgreSQL/Neo4j, Docker Compose/browser journeys, actual backup/restore, deployment security, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including OCR, graph rebuild, reports, retention, and actual backup/restore.
3. Obtain authorized, time-separated annotations and run all four comparisons.
4. Verify operator-host TLS, storage/backup encryption and ACLs, RDAP egress, and recovery controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only` for the local deterministic suite.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:11 (Asia/Kolkata) — Refresh official I4C access review

### Completed in this stage

- Rechecked the official I4C Suspect Search and Report Suspect pages, the portal's Website Policies page, and available MHA material.
- The Suspect Search page still presents a CAPTCHA and states that records derive from public complaints, are not certified by I4C, can contain errors, and are incomplete; the page itself displays a 2 February 2024 update date.
- The public Website Policies page says prior permission is required before an external site links to the portal. Confirmed the application code contains no I4C links.
- An MHA search-indexed report excerpt mentions stakeholder API integrations separately from citizen Suspect Search; the linked report PDF could not be fetched in this review, so it is not treated as API documentation or authorization.
- Kept I4C automated access disabled and updated the source access review, README, requirements matrix, and engineering walkthrough.

### Checks actually run

- Reviewed current official-source search results for the repository form, website form, report-suspect form, website policy, and MHA annual-report excerpt.
- `rg -ni "I4C|cybercrime\.gov\.in" frontend/src backend/app`: no matches; no application URL or I4C integration exists.
- No application code changed; no code test was required for this documentation/access-review update.

### Files/components changed

- `SOURCE_ACCESS_REVIEW.md`, `README.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Public materials still do not document a Suspect Search API or automated-access permission. This does not establish that private or law-enforcement APIs do not exist; obtain written authorization and terms before considering an integration.
- API/proxy integration, live PostgreSQL/Neo4j, Docker Compose/browser journeys, actual backup/restore, deployment security, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including OCR, graph rebuild, reports, retention, and actual backup/restore.
3. Obtain authorized, time-separated annotations and run all four comparisons.
4. Verify operator-host TLS, storage/backup encryption and ACLs, RDAP egress, and recovery controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `SOURCE_ACCESS_REVIEW.md`, and `git status --short`.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:07 (Asia/Kolkata) — Clarify evaluation labels and false-positive denominator

### Completed in this stage

- Audited the scorer, persisted-pipeline exporter, TF-IDF baseline, LLM/web-search adapter runner, graph ablation, and matched-run comparator against the requested metrics and comparison protocol.
- Defined the gold binary target as the narrow “Evidence supports concern” category, which means a traceable unverified report contains an exact in-scope identifier claim; it does not mean the report is proven true or anyone is guilty.
- Specified that binary-negative labels require the pre-registered evidence scope to have been reviewed, and that incomplete or indeterminate records must be excluded and counted rather than treated as negatives.
- Confirmed no authorized annotated dataset or actual comparison results exist; none were generated or reported.

### Checks actually run

- Evaluation scorer/export/comparison/LLM adapter modules: 35 tests passed.
- TF-IDF/logistic-regression baseline tests: 3 tests passed.
- These tests exercise synthetic fixtures and script behavior only; they are not model-performance results.

### Files/components changed

- `backend/evaluation/README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`
- No application or evaluation code changed in this stage.

### Known bugs or unfinished work

- Evaluation requires authorized time-separated Indian recruitment-scam annotations, source snapshots, configured lawful LLM/search adapter, and measured application/no-graph runs. All result metrics remain pending.
- API/proxy integration, live PostgreSQL/Neo4j, Docker Compose/browser journeys, actual backup/restore, and hosted deployment security remain unverified.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including OCR, graph rebuild, reports, retention, and actual backup/restore.
3. Obtain and label authorized, time-separated data using the new narrow binary target; run all four comparisons and disclose exclusions/denominators.
4. Verify operator-host TLS, storage and backup encryption/ACLs, RDAP egress, and recovery controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python -m unittest discover -s tests -p 'test_*eval*.py' -v` and `python -m unittest discover -s tests -p 'test_baseline_tfidf_logreg.py' -v`.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:05 (Asia/Kolkata) — Reverify Compose and recovery orchestration offline

### Completed in this stage

- Re-read the current stage notes and rechecked which operational gates can run without a live container engine.
- Re-ran the Compose configuration validator. It invoked `docker compose ... config --format json` and verified the production-profile configuration, derived database URLs, correction throttles, proxy trust, upload limits, web health, same-origin routes, browser headers, and private build contexts.
- Re-ran backup orchestration with a fake Docker command. The test verified consistent capture order, checksums, cleanup after simulated archive failure, and health-checked service restart.
- Re-ran restore orchestration with synthetic artifacts and fake Docker. The test verified confirmation and checksum gates, operation ordering, graph rebuild, failure handling, and that services remain stopped after a simulated database restore failure.

### Checks actually run

- `./scripts/test-compose-config.ps1`: passed.
- `./scripts/test-backup.ps1`: passed.
- `./scripts/test-restore.ps1`: passed.
- These are configuration and orchestration tests; they do not verify a live PostgreSQL backup/restore, Docker deployment, or service recovery.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`
- No application code changed in this stage.

### Known bugs or unfinished work

- API/proxy integration still needs a Linux asyncio runner. Live PostgreSQL/Neo4j, Compose startup, browser journeys, actual backup/restore, hosted security controls, and authorized-data evaluation remain unverified.
- Docker CLI can parse Compose, but the Docker Engine is unreachable. No local PostgreSQL server, Git remote, or `gh` CLI is available. The project is not release-ready.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including OCR, graph rebuild, reports, retention, and actual backup/restore.
3. Verify operator-host TLS, storage and backup encryption/ACLs, RDAP egress, and recovery controls.
4. Obtain authorized time-separated labels, run all required comparisons, and report measured metrics.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From the repository root, run `./scripts/test-compose-config.ps1`, `./scripts/test-backup.ps1`, and `./scripts/test-restore.ps1` for offline operational checks.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 21:04 (Asia/Kolkata) — Make shared-identifier graph review state relationship-specific

### Completed in this stage

- Fixed graph review-status filtering so shared identifier nodes are included based on matching case-to-identifier/evidence relationships, rather than a single arbitrary node status.
- The graph inspector now derives identifier labels only from case-to-identifier review relationships, displays “varies by case” for mixed states, and does not fall back to a stale node-level status when no such relationship is available.
- Improved source and retrieval-date filtering to keep the selected evidence and its matching case/identifier path visible while excluding unrelated identifier paths.
- Added frontend unit tests for mixed review states on a shared identifier, entity/source/date filtering, and evidence without a retrieval timestamp.

### Checks actually run

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 15 tests passed, including 4 graph filter/status regressions, 7 review-rule/selection tests, and 4 redaction tests.
- Backend was unchanged in this stage; its latest unit-only run remains 188 tests, 186 passed and 2 PostgreSQL-only tests skipped.
- Graph behavior is covered at the frontend rule level only. Live PostgreSQL-derived/Neo4j graph API and browser rendering remain unverified.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/src/graph-filters.ts`, `frontend/tests/graph-filters.test.ts`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- API/proxy route integration still requires a working Linux asyncio runner. PostgreSQL concurrency, live Neo4j, Docker Compose/browser journeys, deployment security controls, and authorized-data evaluation remain unverified.
- No Docker Engine, local PostgreSQL server/CLI, Git remote, or `gh` CLI is available in this workspace. The project is not release-ready.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including graph filtering, OCR, graph rebuild, reports, retention, and backup/restore.
3. Verify operator-host TLS, storage and backup encryption/ACLs, RDAP egress, and recovery controls.
4. Obtain authorized time-separated labels, run all required comparisons, and report measured metrics.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- From `backend`, run `python run_ci_tests.py --unit-only` and `python -m compileall -q app tests evaluation run_ci_tests.py`.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 20:58 (Asia/Kolkata) — Recheck API integration and local migration gates

### Completed in this stage

- Re-read the build plan, current status, README and worktree status before continuing.
- Confirmed Docker Engine is unreachable and there is no local `psql`, PostgreSQL server command, GitHub CLI, or configured Git remote available for the hosted integration gates.
- Re-ran the isolated API-flow suite. It produced no output and remained blocked for about a minute. A minimal FastAPI `TestClient` request and a plain `asyncio.run(asyncio.sleep(...))` probe also stalled in this Windows Python runtime, identifying the local limitation as the async test runtime rather than a demonstrated application failure. The API-flow attempt was interrupted and is not a pass.
- Ran the complete Alembic migration chain against a disposable SQLite test database; it upgraded through the current head successfully.

### Checks actually run

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 11 tests passed.
- `python run_ci_tests.py --unit-only`: 188 tests ran, 186 passed and 2 opt-in PostgreSQL tests skipped.
- `python -m compileall -q app tests evaluation run_ci_tests.py`: passed.
- `python -m alembic upgrade head` with a disposable SQLite test URL: passed.
- API-flow, `TestClient`, and basic asyncio probes stalled in the local Windows runtime and were interrupted; none is reported as passing.
- Docker Compose, live PostgreSQL, Neo4j, browser, and hosted deployment checks remain unrun.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`
- No application code changed in this verification stage.

### Known bugs or unfinished work

- API/proxy route integration still requires a working Linux asyncio runner. PostgreSQL concurrency, live Neo4j, Docker Compose/browser journeys, deployment security controls, and authorized-data evaluation remain unverified.
- No Docker Engine, local PostgreSQL server/CLI, Git remote, or `gh` CLI is available in this workspace. The project is not release-ready.

### Exact next steps, in order

1. On a hosted Linux runner, run `python run_ci_tests.py` with the configured isolated PostgreSQL service; inspect API-flow, proxy, and concurrency outcomes.
2. Start Compose and complete end-to-end investigator/reviewer browser workflows, including OCR, graph rebuild, reports, retention, and backup/restore.
3. Verify operator-host TLS, storage and backup encryption/ACLs, RDAP egress, and recovery controls.
4. Obtain authorized time-separated labels, run all required comparisons, and report measured metrics.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- From `backend`, run `python run_ci_tests.py --unit-only` and `python -m compileall -q app tests evaluation run_ci_tests.py`.
- In Linux CI, run `python run_ci_tests.py` with PostgreSQL test database URLs set as in `.github/workflows/ci.yml`.
- Do not commit unless requested.

## 2026-10-28 20:52 (Asia/Kolkata) — Keep withdrawn evidence historical in correction requests

### Completed in this stage

- Updated the investigator correction queue to label withdrawn local-corpus evidence as historical and offer only “Mark evidence irrelevant” or “Needs further review.”
- Made the action fallback consistent with the displayed eligible options if evidence becomes withdrawn after it was selected.
- Added a pure frontend rule and regression covering available correction actions for withdrawn and current evidence.

### Checks actually run

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 11 tests passed (7 review-rule/selection tests and 4 text-redaction tests).
- `python run_ci_tests.py --unit-only` was rerun from `backend`: 188 tests ran, 186 passed and 2 opt-in PostgreSQL tests were skipped.
- No API, browser, Docker, PostgreSQL or Neo4j integration result is claimed.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/src/review-rules.ts`, `frontend/tests/review-rules.test.ts`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- API/proxy route integration, PostgreSQL migration/concurrency, live Neo4j, Docker Compose/browser journeys, deployment security controls, and authorized-data evaluation remain unverified.
- Docker cannot reach the Linux Engine, no Git remote or `gh` CLI is configured, and WSL access failed on the previous check. The project is not release-ready.

### Exact next steps, in order

1. Continue the offline release audit and fix any reproducible defects found in implemented flows.
2. When a hosted Linux runner is available, run `python run_ci_tests.py` and inspect API/proxy and PostgreSQL results.
3. Start Compose and complete end-to-end investigator/reviewer browser workflows and operational recovery checks.
4. Run the authorized, time-separated evaluation and verify operator-host deployment controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-28 20:48 (Asia/Kolkata) — Clear stale disposition evidence selections

### Completed in this stage

- Reset the human disposition form when a user opens a different case, preventing stale selected IDs or rationale from carrying into another case.
- Added a typed rule to retain only currently relevant, result-bearing, non-withdrawn evidence IDs after case data refreshes.
- Added a frontend regression for removal of withdrawn, irrelevant, and no-result selections.

### Checks actually run

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 10 tests passed (6 reviewer approval/selection rules and 4 text-redaction tests).
- Backend was unchanged in this stage; latest recorded unit-only suite remains 188 tests, 186 passed and 2 opt-in PostgreSQL tests skipped.
- No API, browser, Docker, PostgreSQL or Neo4j integration result is claimed.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/src/review-rules.ts`, `frontend/tests/review-rules.test.ts`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- API/proxy route integration, PostgreSQL migration/concurrency, live Neo4j, Docker Compose/browser journeys, deployment security controls, and authorized-data evaluation remain unverified.
- Docker cannot reach the Linux Engine, no Git remote or `gh` CLI is configured, and WSL access failed on the previous check. The project is not release-ready.

### Exact next steps, in order

1. Continue the offline release audit; add fixes only when backed by reproducible evidence.
2. When a hosted Linux runner is available, run `python run_ci_tests.py` and inspect API/proxy and PostgreSQL results.
3. Start Compose and complete end-to-end investigator/reviewer browser workflows and operational recovery checks.
4. Run authorized, time-separated evaluation and verify operator-host deployment controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-28 20:46 (Asia/Kolkata) — Verify reviewer approval eligibility in the UI

### Completed in this stage

- Extracted the reviewer approval eligibility rule into `frontend/src/review-rules.ts`, so the queue disables approval when cited evidence is absent, withdrawn, no longer relevant, not result-bearing, or insufficiently authoritative.
- Kept reviewer rejection available when approval is blocked, and displayed the reason in the queue.
- Added five frontend unit tests for valid source evidence, withdrawn evidence, stale/non-result evidence, authoritative-source requirements, and weaker dispositions.
- Re-read the current operational gates: Docker still cannot connect to its Linux Engine; there is no configured Git remote and no `gh` CLI.

### Checks actually run

- `pnpm run build`: passed.
- `pnpm run test:redaction`: 9 tests passed (4 redaction and 5 reviewer-approval eligibility tests).
- Backend was unchanged in this stage; latest recorded `python run_ci_tests.py --unit-only` remains 188 tests, 186 passed, 2 opt-in PostgreSQL tests skipped. Latest Python compilation result remains passed.
- No HTTP API-flow, browser, PostgreSQL, Neo4j, or Docker integration result is claimed.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/src/review-rules.ts`, `frontend/tests/review-rules.test.ts`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- API/proxy route integration, PostgreSQL migration/concurrency, live Neo4j, Compose/browser journeys, deployment security controls, and authorized-data evaluation remain unverified.
- Docker's Linux Engine is unavailable, WSL returned `Wsl/E_ACCESSDENIED` previously, and no Git remote or `gh` CLI is configured. The project is not release-ready.

### Exact next steps, in order

1. Continue the offline release audit and add only fixes backed by reproducible evidence.
2. When a Linux runner is available, run `python run_ci_tests.py` and inspect API/proxy and PostgreSQL retirement/provisioning results.
3. Start Compose with PostgreSQL and Neo4j; complete browser workflows for intake, evidence review, dispositions, graph/campaign, reports, retention, and restore.
4. Complete operator-host TLS, encryption/ACL, backups, and egress checks; obtain authorized time-split data and run measured comparisons.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 11:20 (Asia/Kolkata) — Give reviewers the evidence needed for second review

### Completed in this stage

- Changed the reviewer-only pending disposition queue to include the cited source excerpts, references, claims, and investigator rationale. Analysts remain denied access by the endpoint role guard; reviewer queue reads continue to create an audit event.
- Added a database-backed regression for reviewer visibility and extended the API-flow test to assert the reviewer sees the cited material.
- Continued hardening retired evidence: it cannot support stronger human dispositions, withdrawn evidence is excluded from the picker, and historical items marked irrelevant no longer remain in the pending-review IDs.

### Checks actually run

- Focused reviewer queue and correction tests: 11 passed.
- `python run_ci_tests.py --unit-only`: 188 tests ran, 186 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed in the same implementation session.
- HTTP API-flow suite remains unverified because the local Windows test runtime stalled; Docker Linux Engine, WSL, hosted CI, and PostgreSQL concurrency are unavailable in this workspace.

### Files/components changed

- `backend/app/main.py`, `backend/app/findings.py`
- `backend/tests/test_sensitive_read_audit.py`, `test_correction_application.py`, `test_findings.py`, `test_api_flow.py`
- `frontend/src/App.tsx`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Route/middleware E2E, PostgreSQL migration/concurrency, Neo4j, Compose/browser workflows, hosted security controls, and authorized-data evaluation still need runtime evidence.
- Docker's Linux Engine is unavailable, WSL returns `Wsl/E_ACCESSDENIED`, and no Git remote or `gh` CLI is configured. The project is not release-ready.

### Exact next steps, in order

1. Run the default workflow on a hosted Linux runner and inspect API/proxy, PostgreSQL migration, and source-retirement concurrency results.
2. Start Compose and verify the full investigator and reviewer journeys, including source retirement and second review, then verify graph projection/rebuild and operational recovery.
3. Verify TLS, storage ACL/encryption, encrypted backups, and egress policy on operator-controlled infrastructure.
4. Obtain authorized time-separated annotations and run the required evaluation comparisons; report measured results only.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 11:18 (Asia/Kolkata) — Keep retired evidence out of disposition workflows

### Completed in this stage

- Updated investigator evidence controls to display withdrawn source records as historical, hide unsupported “relevant” and “contradicts” actions, and retain the allowed “irrelevant” action. The stronger-disposition picker now excludes withdrawn records.
- Added API handler protections so withdrawn evidence cannot be cited to propose or approve a stronger human disposition, even if its old review status is stale.
- Adjusted finding review state so withdrawn items explicitly marked irrelevant no longer remain in the pending-review IDs, while still never generating a current negative assessment.
- Added direct-handler tests and isolated HTTP-flow assertions; updated traceability and engineering documentation.

### Checks actually run

- Focused findings, disposition/correction, and corpus tests: 28 passed during the first pass; focused disposition and finding regressions: 20 passed after the stronger-disposition guard.
- `python run_ci_tests.py --unit-only`: 187 tests ran, 185 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.
- The HTTP API-flow suite is still not verified in this Windows sandbox; Docker Linux Engine, WSL, hosted CI, and PostgreSQL concurrency are unavailable here.

### Files/components changed

- `backend/app/findings.py`, `backend/app/main.py`
- `backend/tests/test_findings.py`, `test_correction_application.py`, `test_api_flow.py`
- `frontend/src/App.tsx`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Route/middleware E2E, PostgreSQL concurrency and migration, live Neo4j, Compose/browser journeys, hosted security controls, and authorized-data evaluation still need their required runtime evidence.
- Docker's Linux Engine is unavailable, WSL returns `Wsl/E_ACCESSDENIED`, and there is no Git remote or `gh` CLI in this workspace. The project is not release-ready.

### Exact next steps, in order

1. Run the default workflow on a hosted Linux runner and inspect API/proxy, PostgreSQL migration, and source-retirement concurrency results.
2. Start the full Compose deployment and verify intake, retired-source review, stronger dispositions, graph projection/rebuild, redacted reports, retention, and backup/restore through the browser.
3. Verify TLS, storage ACL/encryption, encrypted backups, and network egress policy on an operator-controlled host.
4. Obtain authorized time-separated labels and run all required evaluation comparisons; report only measured results.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 11:14 (Asia/Kolkata) — Verify worker evidence flow and email boundary

### Completed in this stage

- Added a database-backed offline worker-to-evidence regression using synthetic SQLite records. It checks processing completion, deterministic extraction with source offsets, persisted local-corpus provenance, review gating, and the resulting authoritative-source finding after investigator review.
- Fixed email extraction at sentence boundaries: a valid address followed by a period was previously dropped. Added a parser regression and validated the full worker path against an address at end of sentence.
- Attempted the isolated HTTP API-flow suite locally; it stalled without output and was interrupted. Windows Subsystem for Linux also returned `Wsl/E_ACCESSDENIED`; neither provides an alternate local Linux integration runner.
- Updated the requirement matrix and engineering walkthrough.

### Checks actually run

- Focused extraction and worker pipeline tests: 15 passed.
- `python run_ci_tests.py --unit-only`: 185 tests ran, 183 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- Prior in this session: `pnpm run build` passed; `pnpm run test:redaction` passed all 4 tests.
- The API-flow suite did not pass or complete locally. Docker/Linux container integration, hosted CI and PostgreSQL concurrency remain unverified.

### Files/components changed

- `backend/app/extract.py`
- `backend/tests/test_extract.py`, `test_worker_pipeline.py`
- `.gitignore`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Full HTTP routes, proxy middleware, PostgreSQL concurrency, Neo4j projection, Docker Compose/browser flows, hosted deployment, and authorized-data evaluation still need their required runtime evidence.
- Docker's Linux Engine is unavailable; WSL returns access denied; no Git remote or `gh` CLI is configured. The project is not release-ready.

### Exact next steps, in order

1. Run the default workflow on a hosted Linux runner; inspect API/proxy, PostgreSQL migration, and source-retirement concurrency results.
2. Start Compose with PostgreSQL and Neo4j; verify intake, reviewer retirement, graph projection/rebuild, report downloads, retention, and backup/restore through the browser.
3. Complete hosted TLS, storage ACL/encryption, backup encryption, and egress-policy checks on operator-controlled infrastructure.
4. Obtain authorized time-separated labels and run the required evaluation comparisons; publish only measured results.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 11:08 (Asia/Kolkata) — Prevent withdrawn evidence from re-entering findings

### Completed in this stage

- Excluded withdrawn source evidence from current relevant results and conflict resolution even if its stored review status is stale. Withdrawn evidence remains included in the finding's unreviewed IDs. Added regressions for withdrawn-only and withdrawn-plus-active evidence.
- Rejected attempts through evidence review and correction application to mark withdrawn records `relevant` or `contradicts`. Added direct-handler regressions and an HTTP API-flow assertion for the 409 response.
- Added per-evidence retirement audit records containing the old review status/reviewer/time and the invalidation status.
- Updated the engineering walkthrough and requirement traceability checklist.

### Checks actually run

- Focused findings, local corpus, correction, and route-authorization tests: 29 passed.
- `python run_ci_tests.py --unit-only`: 183 tests ran, 181 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.
- `docker info` could not connect to the Docker Desktop Linux Engine. `git remote -v` returned no configured remote and the `gh` CLI is unavailable, so hosted CI cannot be triggered from this checkout as configured.
- The API-flow test was updated and imported by the unit-only runner's isolation checks, but the HTTP API-flow suite itself was not executed. No route-level or browser pass is claimed.

### Files/components changed

- `backend/app/findings.py`, `backend/app/main.py`
- `backend/tests/test_findings.py`, `test_local_evidence_corpus.py`, `test_correction_application.py`, `test_api_flow.py`
- `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- HTTP route/middleware, PostgreSQL concurrency, live Neo4j, Compose/browser workflows, hosted deployment controls, and authorized-data evaluation remain unverified. Local asyncio stalls before a no-op coroutine starts, so hosted Linux CI is needed for HTTP integration. Docker Engine, a Git remote/hosted-runner connection, and `gh` are not currently available in this workspace.
- The project remains under active implementation and is not release-ready.

### Exact next steps, in order

1. Run the default workflow on a hosted Linux runner and inspect API/proxy, PostgreSQL migration, and source-retirement concurrency results.
2. Run Compose with PostgreSQL and Neo4j, then verify reviewer retirement and graph projection behavior through the browser.
3. Continue the release audit, including deployment security and backup/restore on an operator-controlled host.
4. Obtain authorized, time-separated labels and run the required evaluation comparisons; report results without inventing metrics.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 11:03 (Asia/Kolkata) — Preserve conflicts after corpus retirement

### Completed in this stage

- Fixed finding-rule precedence so withdrawing a source record cannot hide a separately investigator-recorded conflict. Added a regression that requires the conflict evidence ID and explanation to remain visible.
- Tried to exercise native HTTP startup with an isolated synthetic SQLite database. App import succeeds, but a minimal `asyncio.run(asyncio.sleep(0))` stalls on this Windows sandbox before entering the coroutine; the Uvicorn process never opened a listener. This points to the local asyncio runtime restriction, not a result for the app's HTTP route behavior.
- Stopped the test processes and removed the temporary startup script and logs.

### Checks actually run

- `python run_ci_tests.py --unit-only`: 180 tests ran, 178 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- Native HTTP health check did not connect; no route-level or browser pass is claimed.

### Files/components changed

- `backend/app/findings.py`, `backend/tests/test_findings.py`
- `BUILD_STATUS.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Route-level HTTP and PostgreSQL concurrency checks remain pending hosted Linux CI. The local sandbox stalls even on a no-op asyncio run, so local Uvicorn is not a usable substitute here.
- Live Neo4j, browser workflows, deployment controls and authorized-data evaluation remain unverified. The project is not release-ready.

### Exact next steps, in order

1. Run the default workflow on hosted Linux CI and inspect API, PostgreSQL migration/provisioning, and source-retirement concurrency results.
2. Verify the reviewer retirement UI and graph projection in a running Compose environment.
3. Continue the full release audit and run comparative evaluation with authorized time-separated data.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:56 (Asia/Kolkata) — Add reviewer-controlled corpus record retirement

### Completed in this stage

- Added persisted active/retired state, retirement timestamp, reviewer, and rationale for database-curated source records, with migration `e7a91c0d4b62` chained after the current duration migration.
- Added a reviewer-only retirement endpoint and UI action. Retirement keeps source history, stops future local matches, marks linked evidence for review, recalculates findings, reopens approved stronger human dispositions that cited it, records audits, and queues graph sync in the same transaction.
- Updated findings so a withdrawn source record cannot continue to support an active strong assessment or a current no-adverse result.
- Added row locking to serialize source lookups with retirement and an opt-in PostgreSQL race regression; configured the existing CI PostgreSQL service to run it after migrations.
- Added focused handler, finding-boundary, and route-access tests; updated the README, traceability matrix, and engineering walkthrough.
- Extended the isolated full API-flow test with investigator/analyst denial checks, reviewer retirement, prior finding/disposition updates, and repeated-retirement rejection. This route-level suite could not be run in this Windows environment.

### Checks actually run

- Focused corpus, findings, authorization-contract, and correction suites: 25 passed; the new opt-in PostgreSQL concurrency test skipped because no PostgreSQL URL was configured locally.
- `python run_ci_tests.py --unit-only`: 179 tests ran, 177 passed, 2 opt-in PostgreSQL tests skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.
- Alembic reported one head; full migration chain upgraded a disposable SQLite database and schema inspection confirmed the four new fields and index.
- `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.

### Files/components changed

- `backend/app/models.py`, `schemas.py`, `source_adapters.py`, `findings.py`, `main.py`
- `backend/migrations/versions/e7a91c0d4b62_retire_evidence_corpus_records.py`
- `backend/tests/test_local_evidence_corpus.py`, `test_findings.py`, `test_route_authorization.py`, `test_postgres_source_retirement.py`, `test_api_flow.py`
- `.github/workflows/ci.yml`, `frontend/src/App.tsx`, `README.md`, `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Reviewer retirement handler checks use SQLite; the PostgreSQL concurrency regression is configured for CI but has not run yet. HTTP authentication/middleware and PostgreSQL runtime effects remain unverified in this environment.
- Live Neo4j outbox processing, full browser UI, and concurrent retire/worker behavior still need integration checks.
- The project remains under active implementation and is not release-ready. Hosted CI, live deployment verification, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Run the default test workflow on hosted Linux CI and inspect API integration, the PostgreSQL retirement race, and provisioning results.
2. Verify reviewer retirement in the browser against PostgreSQL and confirm graph projection changes in Neo4j.
3. Continue the remaining full-scope release checks and authorized-data evaluation.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:45 (Asia/Kolkata) — Verify local corpus curation handlers

### Completed in this stage

- Extended `backend/tests/test_local_evidence_corpus.py` to call the investigator corpus create/list handlers against disposable SQLite storage.
- Covered identifier normalization, authority/source-category and traceability requirements, duplicate rejection across phone formatting, returned source provenance, and minimized audit details.
- Updated the traceability matrix and engineering walkthrough with the added coverage.

### Checks actually run

- Focused local corpus test module: 7 passed.
- `python run_ci_tests.py --unit-only`: 175 tests ran, 174 passed, 1 opt-in PostgreSQL test skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.

### Files/components changed

- `backend/tests/test_local_evidence_corpus.py`
- `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- These tests exercise handler behavior with an investigator object supplied directly; they do not verify HTTP authentication, middleware, or browser behavior.
- Local corpus behavior is verified with synthetic fixtures; the bundled corpus remains empty and no real external source was queried.
- The project remains under active implementation and is not release-ready. Hosted CI, live service/browser/deployment verification, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Continue offline security and requirements review, prioritizing fixes with clear code evidence.
2. Run the default test workflow on hosted Linux CI when a remote runner is configured; inspect HTTP integration and PostgreSQL results.
3. Verify Compose services, browser workflows, and backup/restore against a running Docker Engine with synthetic data.
4. Obtain authorized time-separated labels and run the specified baseline comparisons; verify the actual hosted deployment and operational controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:42 (Asia/Kolkata) — Verify the local evidence adapter

### Completed in this stage

- Added `backend/tests/test_local_evidence_corpus.py` covering the empty-corpus neutral result, an exact match against a persisted investigator-curated `SourceRecord`, and validation that bundled records carry a stable record identifier.
- Updated the requirement matrix and engineering walkthrough with the new coverage and current check count.

### Checks actually run

- Focused Python 3.12.14 tests: 3 passed.
- `python run_ci_tests.py --unit-only`: 171 tests ran, 170 passed, 1 opt-in PostgreSQL test skipped because no test database URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py`: passed.

### Files/components changed

- `backend/tests/test_local_evidence_corpus.py`
- `REQUIREMENTS_TRACEABILITY.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- Adapter behavior against the empty local corpus and a synthetic persisted record is tested. The shipped corpus still has no records, and no external source was queried.
- The project remains under active implementation and is not release-ready. Hosted CI, live service/browser/deployment verification, and authorized-data evaluation remain outstanding.

### Exact next steps, in order

1. Continue offline security and requirements review, adding a narrowly scoped test or fix where evidence supports it.
2. Run the default test workflow on hosted Linux CI when a remote runner is configured; inspect HTTP integration and PostgreSQL results.
3. Verify Compose services, browser workflows, and backup/restore against a running Docker Engine with synthetic data.
4. Obtain authorized time-separated labels and run the specified baseline comparisons; verify the actual hosted deployment and operational controls.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:42 (Asia/Kolkata) — Add requirement-to-evidence release-readiness matrix

### Completed in this stage

- Created `REQUIREMENTS_TRACEABILITY.md` to map product purpose, intake, extraction, evidence, matching, campaigns, human review, reports, privacy, deployment, evaluation and documentation requirements to their code/tests and remaining proof.
- Explicitly marks local-unit evidence separately from unverified live HTTP, PostgreSQL/Neo4j, Docker, browser, hosted CI/TLS, and authorized-data evaluation.
- Linked the matrix from README and verified the new file and its required sections are present.

### Checks actually run

- PowerShell file-presence and heading checks for `REQUIREMENTS_TRACEABILITY.md` — passed.
- Confirmed README links to the new matrix.
- No application tests were run; this was a documentation-only increment.

### Files/components changed

- `REQUIREMENTS_TRACEABILITY.md`, `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The matrix is a traceability guide, not proof of acceptance. Hosted CI, live Docker services, browser journeys, production storage/TLS, and authorized evaluation still need actual evidence.
- The project remains active and is not release-ready.

### Exact next steps, in order

1. Continue offline review for product/security issues and keep the traceability statuses aligned with evidence.
2. When a remote runner is available, run default `python run_ci_tests.py` and inspect API-flow/proxy/PostgreSQL results.
3. When Docker Engine is available, verify full services and end-to-end flows using disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `REQUIREMENTS_TRACEABILITY.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:40 (Asia/Kolkata) — Add regression tests for CI runner isolation

### Completed in this stage

- Added three unit tests for the CI runner: API/proxy suites remain explicitly isolated, the API suite is invoked through a fresh interpreter with the expected discovery command, and subprocess failures propagate as failures.
- Re-ran the isolated unit/handler suite after adding the runner tests.

### Checks actually run

- `tests.test_ci_runner` under Python 3.12.14 — 3 passed.
- `python run_ci_tests.py --unit-only` under Python 3.12.14 — 168 tests ran, 167 passed, 1 opt-in PostgreSQL test skipped because no test PostgreSQL URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py` — passed.
- No API/proxy integration subprocess was launched on this Windows host; their local event-loop startup stall remains known.

### Files/components changed

- `backend/tests/test_ci_runner.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Runner behavior and unit suite are verified locally; the two HTTP suites still need an Ubuntu CI execution to establish their actual pass/fail status.
- No Git remote/`gh` or running Docker Engine is available for hosted or container verification.
- Live databases, OCR, browser E2E, backup/restore, hosted TLS, RDAP egress controls, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Run the default CI runner on Ubuntu when a remote runner is available and inspect API-flow/proxy results.
2. Run full Docker service and end-to-end checks when Docker Engine is available.
3. Complete authorized-data comparative evaluation and hosted deployment/security verification.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; in Linux CI run `python run_ci_tests.py`.
- Do not commit unless requested.

## 2026-10-26 10:38 (Asia/Kolkata) — Isolate API-flow tests from shared import-time settings

### Completed in this stage

- Followed up the CI bootstrap-code fix and found API-flow integration tests also set `DATABASE_URL` and `UPLOAD_DIR` before app import. In normal unittest discovery, prior modules can import the app first, making those paths ineffective and breaking test cleanup/isolation.
- Added `backend/run_ci_tests.py`: it dynamically runs every unit/handler module except API-flow/proxy modules in the parent process, then runs each HTTP integration module in a fresh Python subprocess. Added a `--unit-only` mode for this Windows environment.
- Updated CI and README so the supported test boundaries and required API-flow process isolation are explicit.

### Checks actually run

- `python run_ci_tests.py --unit-only` under Python 3.12.14 — 165 tests ran, 164 passed, 1 opt-in PostgreSQL test skipped because no test PostgreSQL URL was configured.
- Python 3.12 `compileall -q app tests evaluation run_ci_tests.py` — passed.
- Updated CI YAML parsed and asserted to call `python run_ci_tests.py`; runner help output verified `--unit-only` and default isolated-suite behavior.
- Scanned the test modules and confirmed no relative imports depend on package-style test discovery; both isolated modules are excluded from the parent importer.
- Did not run default mode because it starts the known-stalling local TestClient suites; hosted Ubuntu CI remains the intended verifier.

### Files/components changed

- `backend/run_ci_tests.py`, `.github/workflows/ci.yml`, `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The runner's unit mode passed locally, but subprocess API-flow/proxy execution is still unverified on Ubuntu; no hosted runner or Git remote is configured.
- Live Docker services, databases, OCR, browser, backup/restore, hosted TLS, RDAP egress restrictions, and authorized evaluation remain unverified.

### Exact next steps, in order

1. When a remote runner is available, execute default `python run_ci_tests.py` on Ubuntu and inspect the API-flow and proxy results.
2. When Docker Engine is available, verify service startup and end-to-end flows using disposable synthetic data.
3. Complete authorized-data comparative evaluation and hosted deployment/security verification.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, run `python run_ci_tests.py --unit-only`; on Linux CI run `python run_ci_tests.py` to include isolated API/proxy suites.
- Do not commit unless requested.

## 2026-10-26 10:36 (Asia/Kolkata) — Fix CI bootstrap configuration for discovery import order

### Completed in this stage

- Reviewed backend test import ordering and found `test_account_provisioning` imports the app settings before `test_api_flow` sets its process environment. In a discovery run, the API app could therefore start without its required investigator/reviewer bootstrap codes.
- Added matching synthetic investigator and reviewer bootstrap codes to the backend CI job environment. They match `test_api_flow` fixtures and satisfy the application startup validator; they are CI-only test values.
- Simulated the discovery import order (`test_account_provisioning` then `test_api_flow`) and verified the already-created settings object has valid matching bootstrap codes.

### Checks actually run

- Python 3.12 import-order simulation and `validate_bootstrap_codes(settings)` — passed.
- Parsed CI YAML and asserted both CI bootstrap-code values — passed.
- No TestClient/API startup or hosted workflow was run; local asyncio startup remains unavailable.

### Files/components changed

- `.github/workflows/ci.yml`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The import-order fix is verified statically and by settings validation, but the API-flow suite must run on Ubuntu hosted CI to prove lifespan startup and routes work there.
- Docker Desktop launch still exits without an engine; no Git remote/`gh` means neither hosted CI nor live Compose can be run here.
- Live databases, OCR, browser E2E, backup/restore, hosted TLS, RDAP egress, and authorized comparative evaluation remain unverified.

### Exact next steps, in order

1. Continue independent offline configuration and privacy review.
2. When a remote runner is available, execute CI and fix any test, migration, container or PowerShell failures.
3. When Docker Engine is available, verify full services and end-to-end flows with synthetic data.
4. Complete authorized-data evaluation and hosted deployment/security verification.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, rerun the import-order check with Python 3.12 and the documented test dependency path; run the full API suite on a Linux runner.
- Do not commit unless requested.

## 2026-10-26 10:34 (Asia/Kolkata) — Validate Compose statically and recheck Docker startup

### Completed in this stage

- Ran `docker compose config --quiet` and the repository's detailed `scripts/test-compose-config.ps1`; both passed. They verify Compose structure, derived DB URLs, proxy trust addresses, upload ceilings, same-origin routing, headers, and build-context exclusions.
- Confirmed Docker Desktop is installed but not running. Attempted a hidden background start; the process exited immediately and the Linux Engine named pipe remained unavailable. No container or service was started.
- Reconfirmed current Git has no remote, so hosted CI cannot be triggered from this checkout.

### Checks actually run

- `docker compose config --quiet` — passed.
- `scripts/test-compose-config.ps1` — passed.
- Hidden Docker Desktop start followed by process/engine check — engine remained unavailable; no long-lived Docker process was present.
- No database/container operation was attempted after the daemon check failed.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Docker Desktop requires an interactive/environment-level repair or startup change before live services can be verified; automated hidden startup did not establish the engine.
- No Git remote/`gh` means hosted CI results are still unavailable. The new PostgreSQL and operations CI jobs remain unexecuted.
- Live API/proxy, PostgreSQL/Neo4j, browser, OCR, backup/restore, TLS, RDAP egress and authorized evaluation remain unverified.

### Exact next steps, in order

1. Continue independent code and documentation checks that do not require container or hosted services.
2. When Docker Desktop's engine is available, run Compose startup and end-to-end flows on disposable synthetic data.
3. When a Git remote is configured, run the CI workflow and inspect every job result.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From the repository root, run `docker compose config --quiet` and `./scripts/test-compose-config.ps1`; these are static checks and do not need the Docker daemon.
- Do not commit unless requested.

## 2026-10-26 10:32 (Asia/Kolkata) — Recheck frontend and current deployment access

### Completed in this stage

- Re-read the latest checkpoint, plan, CI workflow, and Git status before continuing.
- Expanded the CI workflow to run PostgreSQL-backed account-provisioning concurrency and Windows fake-Docker backup/restore checks; locally parsed the YAML and verified its expected jobs/service.
- Re-ran the production frontend build and redaction tests successfully.
- Rechecked deployment access: no Git remote or GitHub CLI is configured, and Docker Desktop's Linux Engine named pipe is missing. Hosted CI and container services cannot be exercised from this workspace currently.

### Checks actually run

- `pnpm run build` — passed; TypeScript compilation and Vite production build completed.
- `pnpm run test:redaction` — 4 passed.
- PyYAML CI workflow parse and job assertions — passed.
- Docker server probe failed with `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`; no container was started.
- `git remote -v` returned no remotes; `gh` is not installed.

### Files/components changed

- `.github/workflows/ci.yml`, `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- CI edits have not been exercised on GitHub. PostgreSQL service/migrations, API/proxy integration, container smoke, and Windows operations job require hosted results.
- Docker Engine is unavailable locally, so the app cannot currently be launched as its intended service stack here.
- Live PostgreSQL/Neo4j, OCR, backup/restore, hosted TLS, RDAP egress restrictions, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Continue offline review and checks; preserve this workspace until a Git remote/runner or Docker Engine becomes available.
2. Once hosted CI is available, run the configured workflow and resolve any failing jobs, especially full API/proxy and PostgreSQL concurrency.
3. Once Docker Engine is available, execute full service, OCR, graph rebuild/outage, retention, and backup/restore flows on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- Frontend checks: from `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend checks: from `backend`, use Python 3.12 and `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; use the 32-module supported suite recorded in the 10:29 checkpoint.
- Do not commit unless requested.

## 2026-10-26 10:31 (Asia/Kolkata) — Expand hosted CI coverage for PostgreSQL and operations scripts

### Completed in this stage

- Added a disposable PostgreSQL 16 service to the backend CI job, migrates its dedicated database, and provides the opt-in PostgreSQL URL so the account-provisioning concurrency test runs instead of skipping.
- Added a Windows CI job to run fake-Docker backup and restore orchestration checks.
- Updated README to describe the hosted checks and their scope. The existing Ubuntu CI job continues to include the full API-flow/proxy integration tests that stall on this local Windows runtime.

### Checks actually run

- Parsed `.github/workflows/ci.yml` with PyYAML and asserted the PostgreSQL service and all five jobs are present — passed.
- Inspected `backend/migrations/env.py` and confirmed the migration step reads the step-level PostgreSQL `DATABASE_URL`.
- Local fake-Docker backup and restore checks passed earlier in this session. No hosted workflow was triggered and no PostgreSQL service was started locally.

### Files/components changed

- `.github/workflows/ci.yml`, `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The workflow has not run on GitHub; service health, migrations, PostgreSQL concurrency test, Ubuntu API/proxy tests, container build/smoke, and Windows PowerShell job still require hosted CI evidence.
- Live Docker/Neo4j deployment, backup/restore, OCR, hosted TLS, RDAP egress controls, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Inspect Compose and deployment workflow assumptions; verify local static build and syntax checks that do not need Docker.
2. Run the configured GitHub workflow after a remote/CI route is available and inspect each job result.
3. When Docker Engine is available, run service, graph rebuild, OCR, retention, and full backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- Parse `.github/workflows/ci.yml` and, when connected to its remote runner, inspect the `CI` workflow's backend, frontend, compose-config, web-container, and operations-scripts jobs.
- Do not commit unless requested.

## 2026-10-26 10:30 (Asia/Kolkata) — Exercise restore orchestration with a fake Docker CLI

### Completed in this stage

- Added `scripts/test-restore.ps1`, a synthetic restore-orchestration check that never contacts a real Docker daemon or mutates a live database/upload volume.
- The check proves missing `-ConfirmRestore` and checksum mismatch fail before Docker is called; successful orchestration stops writes, runs PostgreSQL restore, restores the private upload archive, waits for API/worker health, then rebuilds Neo4j.
- A simulated `pg_restore` failure is reported, temporary dump cleanup is attempted, and services are deliberately left stopped for operator inspection rather than automatically reopening potentially partial data.
- Documented the check in README.

### Checks actually run

- `scripts/test-restore.ps1` — passed all synthetic orchestration assertions.
- PowerShell parser on `scripts/backup.ps1` and `scripts/restore.ps1` — passed.
- The earlier `scripts/test-backup.ps1` fake-CLI backup checks passed in this session.
- No real Docker, database, archive restore, or Neo4j rebuild was run.

### Files/components changed

- `scripts/test-restore.ps1`, `README.md`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Live restore remains unverified. On failure, API and worker intentionally remain stopped; the operator must inspect the restored database/backup and explicitly restart services after recovery.
- Service health, real GNU tar container compatibility, database restore integrity, private upload volume restore, and Neo4j rebuild need a Docker-enabled disposable environment.
- API/proxy runtime tests, browser E2E, hosted TLS/CI, RDAP network restrictions, and authorized-data evaluation remain unverified.

### Exact next steps, in order

1. Continue source-level security review; review CI/deployment workflow and check for any syntax/configuration gaps.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, run full deployment, OCR, retention, backup/restore, graph rebuild, and outage recovery on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From the repository root, run `./scripts/test-restore.ps1` and `./scripts/test-backup.ps1`; these use a fake Docker CLI only.
- Do not commit unless requested.

## 2026-10-26 10:29 (Asia/Kolkata) — Re-run supported backend suite after security increments

### Completed in this stage

- Re-ran the full locally supported backend unit/handler suite after adding the password-reset, sensitive-read audit, graph outbox, and correction/outbox regressions.
- The suite includes the prior 29 supported modules plus `test_graph_outbox`, `test_password_reset`, and `test_sensitive_read_audit`. It excludes `test_api_flow.py` and `test_proxy_headers.py` because they stall during local TestClient/asyncio startup.

### Checks actually run

- Python 3.12.14 supported backend suite — 165 tests ran, 164 passed, 1 opt-in PostgreSQL test skipped because no test PostgreSQL URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- One expected synthetic graph-outage error-class-only log line was emitted. The evaluation test printed its synthetic metadata filename; no measured performance result was produced.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The two TestClient-stalling modules, live PostgreSQL/Neo4j, browser E2E, Docker OCR/deployment, backup/restore, hosted TLS/CI, and RDAP network egress controls remain unverified.
- Authorized recruitment-scam evaluation labels and controlled comparative metrics remain unavailable.

### Exact next steps, in order

1. Continue source-level security review and inspect restore/deployment operations and graph rebuild invocation.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify PostgreSQL/Neo4j rebuild, outage recovery, OCR, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; the supported suite is the 32-module command recorded at this checkpoint, followed by `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:28 (Asia/Kolkata) — Verify graph deletion tombstones and retention integration

### Completed in this stage

- Reviewed graph rebuild and retention code paths. PostgreSQL remains the rebuild source; rebuild deletes only the application's dedicated Neo4j labels and recreates their projection. Retention enqueues graph deletion in the same database transaction before deleting the relational case, and the outbox row intentionally has no case foreign key so the tombstone survives.
- Added an offline test that deletes a case row, processes the retained graph delete tombstone, verifies the graph deletion call, and confirms the tombstone becomes completed.
- Rechecked graph retry and concurrent-generation behavior alongside correction and retention tests.

### Checks actually run

- `tests.test_graph_outbox tests.test_correction_application tests.test_retention_uploads` under Python 3.12.14 — 14 passed. The simulated outage emitted one expected error-class-only log line.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- No live Neo4j, Docker, or PostgreSQL service was available or contacted. This verifies relational semantics only.

### Files/components changed

- `backend/tests/test_graph_outbox.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Full graph rebuild and graph deletion behavior against a real Neo4j instance remain unverified, as do PostgreSQL locking and concurrent worker semantics.
- API/proxy runtime checks, browser E2E, Docker/hosted deployment, OCR, live backup/restore, RDAP resolver/egress restrictions, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Continue source-level security review and inspect deployment/restore rebuild workflow.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify PostgreSQL/Neo4j rebuild, outage recovery, OCR, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_graph_outbox tests.test_correction_application tests.test_retention_uploads -q`.
- Do not commit unless requested.

## 2026-10-26 10:27 (Asia/Kolkata) — Test graph projection retry and update races offline

### Completed in this stage

- Added isolated SQLite tests for the graph outbox worker so retry behavior can be checked without Neo4j or the stalled API TestClient module.
- Verified a simulated Neo4j projection outage returns the durable row to `queued`, increments attempts, applies backoff, and persists only the exception class rather than private exception text.
- Verified a newer case update arriving during an in-flight projection increments the generation and remains queued for an immediate follow-up projection instead of being incorrectly marked complete.

### Checks actually run

- `tests.test_graph_outbox tests.test_correction_application` under Python 3.12.14 — 9 passed. One expected synthetic outage log line was emitted; the error text was not persisted.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- No live Neo4j service was contacted.

### Files/components changed

- `backend/tests/test_graph_outbox.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- These checks cover relational outbox retry/generation behavior, not Neo4j transaction semantics, service restart behavior, complete graph rebuild, or consistency under live concurrent PostgreSQL workers.
- API/proxy runtime checks, browser E2E, Docker/hosted deployment, OCR, backups, RDAP egress controls, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Continue source-level and unit privacy/security review; inspect graph rebuild data flow and retention-driven graph deletion semantics.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify PostgreSQL/Neo4j, OCR, retention, outage recovery, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_graph_outbox tests.test_correction_application -q`.
- Do not commit unless requested.

## 2026-10-26 10:26 (Asia/Kolkata) — Verify correction propagation to findings, reports, and graph outbox

### Completed in this stage

- Audited correction application: only open requests can change a record; a request targets exactly one entity or evidence item in its referenced case; duplicate application is rejected; corrections update the selected record, reopen stronger dispositions whose support changed, recompute findings and exact-identifier links, and preserve audit history.
- Confirmed the graph is an asynchronous projection: correction-triggered link refresh schedules an upsert in the transactional outbox when graph projection is configured. Added a SQLite regression test proving the corrected entity and queued projection row persist together.
- Reviewed report/redaction regressions: JSON and Markdown report tests assert corrected/replaced contact identifiers and requester email do not leak into default exports; graph view tests assert source URL paths and personal identifiers are masked.

### Checks actually run

- `tests.test_correction_application tests.test_findings tests.test_reporting tests.test_privacy tests.test_sensitive_read_audit` under Python 3.12.14 — 27 passed.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- Correction/outbox checks used isolated SQLite and synthetic values. No live Neo4j service was available or contacted.

### Files/components changed

- `backend/tests/test_correction_application.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The database-to-Neo4j outbox enqueue is now directly tested, but Neo4j delivery, restart/retry behavior, and full graph rebuild remain unverified without Docker/Neo4j.
- Corrections still require full HTTP route/middleware verification in an environment where TestClient can start; these direct tests do not establish browser-level access behavior.
- API/proxy integration, browser E2E, hosted TLS/CI, backup/restore, real OCR, resolver/egress restrictions, and authorized evaluation remain unverified.

### Exact next steps, in order

1. Continue source-level and unit privacy/security review; verify graph projection rebuild and worker retry semantics when possible.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify PostgreSQL/Neo4j, OCR, retention, outage recovery, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_correction_application tests.test_findings tests.test_reporting tests.test_privacy tests.test_sensitive_read_audit -q`.
- Do not commit unless requested.

## 2026-10-26 10:25 (Asia/Kolkata) — Audit reviewer access to pending decisions

### Completed in this stage

- Reviewed persisted access and change audit events across case, report, campaign, graph, correction, account, and disposition routes.
- Found reviewer reads of the pending human-disposition queue were not logged. Added a minimized event containing actor, action, and result count; it excludes case contents, evidence excerpts, rationale, and disposition text.
- Added a persisted SQLite regression test proving the queue read commits its audit event.

### Checks actually run

- `tests.test_sensitive_read_audit tests.test_route_authorization tests.test_password_reset` under Python 3.12.14 — 5 passed.
- Python 3.12 `compileall -q app tests evaluation` — passed.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_sensitive_read_audit.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Full API route execution remains unverified because the local TestClient startup stalls; the new test directly exercises the persisted handler.
- The processing-status endpoint intentionally emits no audit event for each frequent poll and returns only case IDs, states, attempt counts, and generic errors. If access auditing must include every status poll, add a bounded/aggregated audit design rather than producing an unbounded event per poll.
- Bearer token browser storage, manual account-recovery delivery, RDAP resolver/egress boundaries, Docker/service verification, hosted checks, and authorized evaluation remain as noted in earlier checkpoints.

### Exact next steps, in order

1. Continue correction/redaction propagation review and verify audit coverage without recording raw source content or excessive polling events.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify OCR, deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_sensitive_read_audit tests.test_route_authorization tests.test_password_reset -q`.
- Do not commit unless requested.

## 2026-10-26 10:24 (Asia/Kolkata) — Add direct persistence checks for password recovery

### Completed in this stage

- Reviewed authentication/session behavior: bearer access tokens have a bounded lifetime and a persisted token-version revocation check; logout, password reset, and account suspension revoke prior sessions. The frontend keeps the bearer token in tab-scoped `sessionStorage`; CORS is limited to the configured web origin and the edge applies a restrictive CSP.
- Confirmed password recovery is reviewer-issued and requires a rationale. Only an HMAC digest is persisted; the raw one-time token is returned once with `no-store`, expires after the configured interval, replacement invalidates the old token, redemption is rate-limited, and successful recovery revokes prior sessions. The documented delivery channel is manual/out-of-band; no email, SMS, verified-email, or self-service identity recovery exists.
- Added database-backed direct-handler tests for token hashing, expiry, replacement, single use, audit minimization, password change, and session-version revocation. This exercises persisted behavior without triggering the known local TestClient startup stall.

### Checks actually run

- `tests.test_password_reset tests.test_rdap_adapter tests.test_route_authorization` under Python 3.12.14 — 13 passed.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- Tests use isolated SQLite and synthetic credentials; no external request or user data was used.

### Files/components changed

- `backend/tests/test_password_reset.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The API-level reset workflow remains unverified because the local TestClient runtime stalls; direct handler tests do not prove the full HTTP routing/middleware flow.
- Bearer tokens remain accessible to same-origin JavaScript through `sessionStorage`; the CSP and same-origin design reduce exposure but do not eliminate XSS impact. A hosted browser security review is still required.
- Recovery token delivery depends on an operator-verified secure out-of-band channel. No automated delivery or self-service account recovery is implemented.
- Resolver-level pinning and production network egress controls for optional RDAP remain unverified; see the 10:23 checkpoint.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS/CI, and authorized-data evaluation remain unverified.

### Exact next steps, in order

1. Continue source-level privacy/security review, prioritizing audit-event coverage and correction/redaction propagation.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify OCR, deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment/security verification when resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_password_reset tests.test_rdap_adapter tests.test_route_authorization -q`.
- Do not commit unless requested.

## 2026-10-26 10:23 (Asia/Kolkata) — Bound and test external source fetch behavior

### Completed in this stage

- Audited outbound source fetching. The submitted URL itself is not fetched. The optional RDAP adapter only accepts extracted domain entities, requires explicit case consent, starts from the fixed IANA bootstrap endpoint, accepts only HTTPS service bases without credentials, literal IP hosts, nonstandard ports, queries, or fragments, disables environment proxies and redirects, and bounds response size and timeout.
- Added regressions proving URL/email/phone entities do not trigger RDAP requests, domain lookup sends only the normalized domain to the mapped registry, and unsafe registry base URLs are rejected.
- Confirmed empty local-corpus and evaluation-data audit findings are recorded in this status and the engineering walkthrough.

### Checks actually run

- `tests.test_rdap_adapter` under Python 3.12.14 — 9 passed, including the new no-submitted-URL-fetch and unsafe-base cases.
- `tests.test_route_authorization` under Python 3.12.14 — 8 passed.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- No live registry requests were made; RDAP adapter tests are offline.

### Files/components changed

- `backend/tests/test_rdap_adapter.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Resolver-level destination pinning/public-address validation and production network egress restrictions are not verified. The application does not fetch submitted URLs, but the optional RDAP integration makes outbound requests to IANA and its mapped registry hostnames; deployment network policy must be reviewed before enabling it.
- The bundled local evidence corpus is empty by design; operators must add source records before positive local matches are possible.
- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue the source-level privacy/security review, prioritizing session/account recovery, audit completeness, and cross-origin/session hardening.
2. Resolve or explicitly constrain RDAP resolver/egress behavior before enabling it in a hosted environment.
3. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
4. When Docker Engine is available, verify OCR, deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
5. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, run Python 3.12 with `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; focused command: `python -m unittest tests.test_rdap_adapter tests.test_route_authorization -q`.
- Do not commit unless requested.

## 2026-10-26 10:21 (Asia/Kolkata) — Audit local corpus and evaluation data safety

### Completed in this stage

- Inspected the bundled local evidence corpus. It contains schema/version metadata and zero evidence records; the README accurately says the operator must populate it with sources they are permitted to retain and cite. No person or organization is labeled in bundled evidence data.
- Inspected `backend/evaluation` for JSON, JSONL, CSV, and TSV datasets. No evaluation dataset or prediction fixture is present, so no personal identifiers or unsupported real-world labels are bundled as evaluation data.
- Reviewed evaluation guidance: it explicitly requires pseudonymous IDs, protected provenance, authorized/minimized data, campaign-aware time splits, and says pending data must not be represented as measured product performance.
- Identifier and allegation-pattern search hits in this scope were in source code, documentation, or test fixtures rather than bundled corpus/evaluation datasets. No personal values were copied into this checkpoint.

### Checks actually run

- File inventory and bounded-content inspection of `backend/app/evidence_corpus.json` — confirmed an empty `records` array.
- Evaluation data-file inventory for `.json`, `.jsonl`, `.csv`, and `.tsv` under `backend/evaluation` — zero files.
- Pattern search over the bundled corpus and evaluation directory — hits were limited to code/docs, not data files.
- No tests or runtime checks were needed or run for this read-only data audit.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The bundled corpus is intentionally empty, so operators must add reviewed source records before local lookups can return positive evidence. This is documented; no real personal identifiers or unsupported seed allegations are included.
- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify OCR, deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- Continue from the privacy/security source audit; use Python 3.12 and the documented isolated dependency path for applicable backend checks.
- Do not commit unless requested.

## 2026-10-26 10:19 (Asia/Kolkata) — Verify upload integrity before worker parsing

### Completed in this stage

- Found that worker processing trusted the stored path but did not compare its content with the SHA-256 recorded when the upload was accepted.
- Worker now rejects malformed/missing digest references, symlink paths, oversized files, and content whose digest differs from intake. It parses the same bounded in-memory bytes it hashed, avoiding a hash-then-reopen substitution window; PDF documents are closed through a context manager.
- Updated the OCR smoke fixture and PDF region fixture with intake digests, and added regressions for modified content, missing hashes, and file-size limits.
- Documented the upload integrity check in README.

### Checks actually run

- Focused upload-integrity and OCR fixture checks under Python 3.12: 9 passed.
- Selected 29-module backend suite under Python 3.12.14: 155 tests ran, 154 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- Host Tesseract is not installed; Docker Engine remains unavailable, so the real OCR binary/container smoke check was not run.

### Files/components changed

- `backend/app/worker.py`, `backend/app/verify_ocr.py`
- `backend/tests/test_upload_integrity.py`, `backend/tests/test_ocr_regions.py`
- `README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify OCR, deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 and `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; run the 29-module command in the 10:17 checkpoint with `tests.test_upload_integrity` added, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:17 (Asia/Kolkata) — Align OCR deployment smoke fixture with upload policy

### Completed in this stage

- Audited the container OCR smoke command after tightening upload-name validation and found its synthetic PDF name (`scanned-fixture.pdf`) would be rejected by the worker.
- Changed the smoke fixture to use the app-generated opaque filename format and added an offline test that runs its image-to-scanned-PDF flow with synthetic OCR output.
- Confirmed Tesseract is not installed on the host, so the actual OCR binary/container smoke test remains pending Docker availability.

### Checks actually run

- OCR region and smoke-fixture checks under Python 3.12: 6 passed.
- Selected 28-module backend suite under Python 3.12.14: 152 tests ran, 151 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- The actual Docker/Tesseract smoke command was not run.

### Files/components changed

- `backend/app/verify_ocr.py`
- `backend/tests/test_ocr_regions.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, real OCR container, backup/restore, hosted TLS and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, run the OCR command and verify deployment, PostgreSQL/Neo4j outage/rebuild, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use Python 3.12 and `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; run the 28-module command in the 10:15 checkpoint, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:15 (Asia/Kolkata) — Compensate failed upload storage and database writes

### Completed in this stage

- Audited upload intake transaction ordering and found that the private file was written before the case/evidence/job transaction. A database failure could therefore leave submitted personal material orphaned until its normal retention age.
- Extracted persistence into `persist_uploaded_case()`: it ensures the private directory exists, writes the opaque file, commits case/evidence/job/audit records, and on transaction failure rolls back and immediately removes the just-created file. Cleanup failures log only the exception class; they never include file paths or upload content.
- Hardened the lower-level file write as well: if creating the stream or writing bytes fails after exclusive file creation, the descriptor is closed and the partial file is immediately removed.
- Added success and synthetic commit-failure tests proving persisted references match the generated upload and failed persistence leaves neither database case records nor the private file.

### Checks actually run

- Focused upload persistence/private storage/retention tests under Python 3.12: 10 passed.
- Selected 28-module backend suite under Python 3.12.14: 151 tests ran, 150 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- API-flow/proxy, browser, Docker, live database, and deployment checks remain unverified.

### Files/components changed

- `backend/app/main.py`, `backend/app/private_storage.py`
- `backend/tests/test_upload_persistence.py`, `backend/tests/test_private_storage.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify deployment, PostgreSQL/Neo4j outage/rebuild, OCR, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, use the Python 3.12 executable and `.test-sandbox-tmp/py312-deps;.` `PYTHONPATH`; run the 28-module command from the 10:13 checkpoint with `tests.test_upload_persistence` added, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:13 (Asia/Kolkata) — Constrain retention cleanup to application uploads

### Completed in this stage

- Audited retention and found the orphan sweep deleted every old unreferenced regular file in the private upload directory, regardless of whether the application created it.
- Added one shared validator for the 48-character lowercase hex name and supported suffixes generated by the upload endpoint. Upload writes and worker reads now reject malformed stored names; retention only collects and prunes validated upload names; archive restore uses the same validator.
- Added regression coverage proving old unrelated files are preserved. Updated the OCR and API-flow fixtures to use valid generated-style names.
- Updated README operational documentation with the cleanup rule.

### Checks actually run

- Focused private-storage, retention, and restore tests under Python 3.12: 11 passed.
- Selected 27-module backend suite under Python 3.12.14: 148 tests ran, 147 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- An initial full-suite attempt found the OCR test's synthetic filename did not match the strengthened validator; the fixture was corrected and the rerun passed.
- API-flow/proxy, browser, Docker, live database, and deployment checks remain unverified.

### Files/components changed

- `backend/app/private_storage.py`, `backend/app/worker.py`, `backend/app/restore_uploads.py`
- `backend/tests/test_private_storage.py`, `backend/tests/test_retention_uploads.py`, `backend/tests/test_ocr_regions.py`, `backend/tests/test_api_flow.py`
- `README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API-flow and proxy runtime checks still stall during local asyncio/TestClient startup; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, verify deployment, PostgreSQL/Neo4j outage/rebuild, OCR, retention, and backup/restore on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the 27-module command in the 10:10 checkpoint (with `test_private_storage` and `test_retention_uploads` each containing the new regression), then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:10 (Asia/Kolkata) — Run selected backend suite on Python 3.12

### Completed in this stage

- Ran the selected 27-module backend suite under the repository target Python 3.12 runtime, using the exact pinned dependencies and an isolated temporary SQLite URL.
- Added an exact `.gitignore` entry for the generated Python 3.12 dependency directory and verified it with `git check-ignore`; other test artifacts were not added to the ignore rule.
- Rechecked the unauthenticated correction status response and investigator-only request queue source path; existing tests cover omission of investigator notes and invalid status tokens.

### Checks actually run

- Selected 27-module backend suite on Python 3.12.14: 146 tests ran, 145 passed, and 1 opt-in PostgreSQL test was skipped because no PostgreSQL test URL is configured.
- Python 3.12 `compileall -q app tests evaluation` — passed.
- `git check-ignore -v .test-sandbox-tmp/py312-deps/fastapi/__init__.py` — confirmed the dependency install is ignored.
- The TestClient/asyncio startup stall from the prior checkpoint remains; API-flow and proxy tests were excluded from this successful suite.

### Files/components changed

- `.gitignore`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- API-flow/proxy runtime behavior remains unverified because TestClient and even a minimal asyncio loop stall in this environment; WSL access is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS, and hosted CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect actual job output.
3. When Docker Engine is available, run deployment, PostgreSQL/Neo4j outage/rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- The selected Python 3.12 run used `C:\Users\gaurv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` with `PYTHONPATH` set to `.test-sandbox-tmp/py312-deps;.` from the backend directory; rerun the 27-module command shown in the 10:03/10:02 checkpoints if needed.
- Do not commit unless requested.

## 2026-10-26 10:06 (Asia/Kolkata) — Retry HTTP integration checks under Python 3.12

### Completed in this stage

- Re-read the current checkpoint and Git state; all application files remain uncommitted and untracked.
- Located the desktop-bundled Python 3.12 runtime and, after the sandbox denied PyPI access, provisioned the repository's pinned requirements into the ignored `.test-sandbox-tmp/py312-deps` directory.
- Retried the proxy `TestClient` test under Python 3.12. Verbose output identified the first trusted-proxy test, which remained stalled with no further output for over 80 seconds; interrupted that run. A minimal `asyncio.run(asyncio.sleep(0))` probe also stalled during event-loop startup. `wsl.exe --status` returned `Wsl/ E_ACCESSDENIED`.
- No API/proxy integration result is claimed. This confirms the local limitation is not specific to Python 3.14; the configured Ubuntu CI remains the available supported route, but there is no Git remote to trigger it from this workspace.

### Checks actually run

- Python 3.12 dependency installation to the ignored temporary directory — completed using pinned `backend/requirements.txt`.
- Python 3.12 API/proxy integration retry — stalled and was interrupted; not a pass or a functional failure result.
- Minimal Python 3.12 asyncio loop probe — stalled; not a pass.
- No source code changed in this attempt; the last selected backend suite remains 146 tests run, 145 passed, 1 PostgreSQL-only skip.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`
- Ignored temporary dependency installation: `.test-sandbox-tmp/py312-deps`

### Known bugs or unfinished work

- Actual API-flow and proxy behavior remains unverified because local event-loop initialization stalls across both available Python runtimes; the WSL Linux path is denied.
- Docker Engine, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, hosted TLS and CI results remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue source-level and unit-level privacy/security checks that do not require an event loop or live services.
2. Run the API-flow/proxy tests on an accessible Linux runner when a remote/CI route is available; inspect the actual job output.
3. When Docker Engine is available, run the deployment, PostgreSQL/Neo4j outage/rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- Available Python 3.12 runtime: `C:\Users\gaurv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Its temporary project dependencies are in `.test-sandbox-tmp/py312-deps`; source and other selected tests continue to use the existing `backend/.pydeps` environment.
- Do not commit unless requested.

## 2026-10-26 10:03 (Asia/Kolkata) — Verify analyst campaign redaction

### Completed in this stage

- Added a database-backed serializer regression for the analyst campaign view using two synthetic cases sharing a phone identifier and related source evidence.
- Verified the campaign response masks the shared identifier, source title and claim, and URL path/query while preserving the source origin and campaign-link explanation.
- No production code change was needed for this path; the test guards the existing redaction behavior against regression.
- Rechecked external execution options: Docker CLI is present but the Docker Desktop Linux Engine named pipe is unavailable; `git remote -v` has no configured remote, so hosted CI cannot be triggered from this checkout.

### Checks actually run

- Focused analyst campaign redaction test: 1 passed.
- Selected 27-module backend suite: 146 tests ran, 145 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- `python -m compileall -q app tests evaluation` — passed.
- API-flow/proxy, browser, live service, Docker, and deployment checks were not run.

### Files/components changed

- `backend/tests/test_correction_application.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Route dependency checks are declaration-level only; API-flow and proxy runtime authorization remain unverified in this Windows sandbox.
- Docker Engine, hosted CI access, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, and hosted TLS remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue the privacy review for remaining analyst-facing outputs and inspect correction-status and source-reference handling.
2. Run API-flow and proxy integration tests in a supported Linux runtime and inspect actual results.
3. When Docker Engine is available, run the container, Postgres/Neo4j outage and rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the 26-module command in the 09:50 checkpoint with `tests.test_route_authorization` added, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:02 (Asia/Kolkata) — Whitelist historical finding snapshots

### Completed in this stage

- Continued the analyst-output audit and found that the finding serializer copied every key in persisted historical evidence snapshots.
- Changed finding serialization to emit only the defined provenance fields (`evidence_id`, source name/type/reference, claim, outcome, authority, and retrieval time). Analyst views still mask source name, claim, and URL path/query.
- Added a synthetic regression fixture with a future/private field and a phone number in a source URL; neither is exposed in the analyst snapshot.

### Checks actually run

- Focused report/privacy/route-contract checks: 15 passed.
- Selected 27-module backend suite: 145 tests ran, 144 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- `python -m compileall -q app tests evaluation` — passed.
- API-flow/proxy routes, browser, live services, Docker and hosted deployment were not verified in this stage.

### Files/components changed

- `backend/app/main.py`
- `backend/tests/test_reporting.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The route contract verifies declared dependencies, not HTTP execution. API-flow and proxy integration remain unverified in this Windows sandbox.
- Docker Engine, hosted CI access, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, and hosted TLS remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue the privacy review for analyst-facing case, campaign, graph, and report serializers, adding targeted regressions where gaps are found.
2. Run API-flow and proxy integration tests in a supported Linux runtime and inspect actual results.
3. When Docker Engine is available, run the container, Postgres/Neo4j outage and rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the 26-module command in the 09:50 checkpoint with `tests.test_route_authorization` added, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 10:01 (Asia/Kolkata) — Lock API route access classes

### Completed in this stage

- Re-read the current status and verified the workspace remains an uncommitted, untracked tree with no AGENTS.md files.
- Audited every FastAPI `/api/` route dependency. Public routes are explicitly enumerated (policy, authentication/reset, public correction intake/status); case and campaign reads require a signed-in user; investigation writes and sensitive graph/correction operations require investigator access; account and disposition review operations require reviewer access.
- Added a route-policy contract test that fails when a new API route is unclassified or when its dependency no longer matches its access class.

### Checks actually run

- New route authorization contract: 2 passed.
- Selected 27-module backend suite: 144 tests ran, 143 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- `python -m compileall -q app tests evaluation` — passed.
- This checks declared route dependencies. The API-flow and proxy tests were not run here, so this is not a runtime authorization verification.

### Files/components changed

- `backend/tests/test_route_authorization.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Runtime API-flow and proxy integration checks remain unverified in this Windows sandbox.
- Docker Engine, hosted CI access, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore, and hosted TLS remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue the privacy review for analyst-facing case, campaign, graph, and report serializers, adding targeted regressions where gaps are found.
2. Run API-flow and proxy integration tests in a supported Linux runtime and inspect actual results.
3. When Docker Engine is available, run the container, Postgres/Neo4j outage and rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
4. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the 26-module command in the 09:50 checkpoint with `tests.test_route_authorization` added, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 09:58 (Asia/Kolkata) — Fail closed on unknown analyst audit fields

### Completed in this stage

- Re-read the current build plan, status, and Git state. The workspace is still an uncommitted, untracked project tree; no AGENTS.md is present at the workspace root.
- Closed a privacy review gap in analyst case timelines and downloaded report audit details: only explicitly approved metadata fields are retained. Arbitrary and future unknown fields are omitted, while known private fields remain explicitly redacted.
- Added a regression case with an unexpected nested free-text field containing a synthetic person name and details; safe status metadata remains visible.

### Checks actually run

- `python -m unittest tests.test_privacy tests.test_reporting -q` — 12 passed.
- Re-ran the documented 26-module selected backend suite — 142 tests ran, 141 passed, and 1 opt-in PostgreSQL test was skipped because no test PostgreSQL URL is configured.
- `python -m compileall -q app tests evaluation` — passed.
- No full API router, browser, live database, Docker, or deployment check was run in this stage.

### Files/components changed

- `backend/app/privacy.py`
- `backend/tests/test_privacy.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Existing selected-suite result remains 141 passed and 1 PostgreSQL-only test skipped; API-flow and proxy integration modules are still unverified in this environment.
- Docker Engine, hosted CI access, browser E2E, live PostgreSQL/Neo4j, OCR container, backup/restore and hosted TLS remain unverified.
- Authorized time-separated evaluation labels and measured provider comparisons remain unavailable.

### Exact next steps, in order

1. Continue route-level authorization and redaction checks, then execute API-flow and proxy tests on a supported Linux runtime.
2. When Docker Engine is available, run the container, Postgres/Neo4j outage and rebuild, OCR, retention, and backup/restore checks on disposable synthetic data.
3. Complete authorized-data comparative evaluation and hosted deployment verification when those resources are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the selected-suite command in the 09:50 checkpoint, then `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-26 09:50 (Asia/Kolkata) — Enforce correction-request state before case changes

### Completed in this stage

- Audited API route gates: case/report routes require a signed-in user; source-corpus, correction-queue, graph, entity/evidence review and link decisions require investigator-level access; pending disposition review and account administration require reviewer-level access. Analyst case/campaign views use redacted serializers.
- Confirmed the Docker CLI/Compose remain installed but the Docker Desktop Linux Engine named pipe is unavailable, so live service checks cannot run here.
- Fixed an authorization-adjacent workflow gap in correction application: only requests in `received` or `investigating` state can change case records. Resolved and rejected requests now return 409 before any record mutation or audit event.
- Added regression coverage for rejected/resolved request states and documented the open-request rule in `README.md`.

### Checks actually run

- Selected backend suite: 142 tests; 141 passed and 1 opt-in PostgreSQL account-provisioning test skipped because no PostgreSQL test database is configured. `test_api_flow.py` and `test_proxy_headers.py` were excluded because of the recorded Windows TestClient startup issue.
- Focused correction/public-status/privacy/report checks: 17 passed, including a PostgreSQL-fallback graph redaction regression test.
- `python -m compileall -q app tests evaluation` — passed.
- Frontend `pnpm run build` — passed (`tsc -b` and Vite production bundle).
- Frontend `pnpm run test:redaction` — 4 passed, 0 failed.
- `docker version` confirmed the daemon is unavailable; `docker compose version` is available. No live service or browser check ran.

### Files/components changed

- `backend/app/main.py`
- `backend/tests/test_correction_application.py` (closed-request, disposition-propagation, and PostgreSQL-fallback graph redaction coverage)
- `README.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- API-router and proxy integration checks remain unverified locally; CI is configured to run them on Ubuntu, but no Git remote is configured here to trigger or inspect a hosted run.
- Live PostgreSQL, Neo4j, OCR container behavior, backup/restore, hosted TLS, and browser interaction remain unverified.
- Authorized evaluation data and real provider comparisons remain unavailable; no performance claims are made.

### Exact next steps, in order

1. Run the existing full API/proxy suite in its configured Linux CI environment or resolve the Windows TestClient issue, then inspect actual results; the repository has no configured Git remote here.
2. Continue report and graph access/redaction review with synthetic personal identifiers; frontend type-check/build and redaction helper tests now pass.
3. Verify PostgreSQL migration/export transaction behavior and complete the live deployment, Neo4j rebuild, OCR, and backup/restore checks when a Docker runtime is available.
4. Keep comparative evaluation pending until authorized time-split labels and lawful adapters are configured.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- Frontend checks: from `frontend`, run `pnpm run build` and `pnpm run test:redaction`.
- Backend: from `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; use the 26-module command in the 09:47 checkpoint, then compile.
- Do not commit unless requested.

## 2026-10-26 09:47 (Asia/Kolkata) — Reopen dispositions when their linked entity claim changes

### Completed in this stage

- Extended disposition invalidation beyond direct evidence-review corrections. Before correcting or rejecting an entity, the application finds evidence explicitly linked to that original normalized identifier; approved stronger dispositions citing that evidence are reopened for independent review.
- Reused the same audit-preserving reopening path for evidence-status changes and entity-claim changes. Reopened dispositions clear the active reviewer fields and retain previous status/reviewer/time in an audit event.
- Added reviewer IDs to private audit fields so the newly preserved reviewer identity is shown to authorized reviewers but redacted from analyst timeline/report details.
- Added a regression test for correcting an entity whose old identifier evidence was cited by an approved disposition.

### Checks actually run

- Selected backend suite: 140 tests; 139 passed and 1 opt-in PostgreSQL account-provisioning test skipped because a PostgreSQL test database is not configured. The run excluded only `test_api_flow.py` and `test_proxy_headers.py`.
- Focused correction tests: 3 passed.
- Focused report/privacy/correction check after reviewer-ID redaction: 15 passed.
- `python -m compileall -q app tests evaluation` — passed.
- No browser, API-router, live PostgreSQL, or Neo4j check was run.

### Files/components changed

- `backend/app/main.py`
- `backend/tests/test_correction_application.py`
- `backend/app/privacy.py`, `backend/tests/test_privacy.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Evidence and entity corrections now reopen approved stronger dispositions when cited evidence was tied to an invalidated claim. Browser interaction remains unverified, and API-router tests still have the recorded Windows TestClient startup issue.
- Access-control and output-redaction review remains ongoing. Live PostgreSQL, Neo4j, deployment, OCR, backup/restore, and authorized comparative evaluation remain unverified or unavailable.

### Exact next steps, in order

1. Continue the report and access-control audit using synthetic secret-shaped values, focusing on route-specific authorization and personal identifiers in report URLs, source refs, audit details, and graph fallbacks.
2. Resolve and run API-flow/proxy tests in a supported runtime; verify correction endpoints through the actual ASGI app.
3. Run PostgreSQL migrations/export locking and the live Compose/Neo4j/OCR/backup/restore/deployment checks when Docker is available.
4. Keep real performance evaluation pending authorized data and configured lawful comparison services.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./all-unit-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the selected-suite command and `python -m compileall -q app tests evaluation`:

```powershell
python -m unittest tests.test_account_provisioning tests.test_baseline_tfidf_logreg tests.test_campaign_rules tests.test_config tests.test_correction_application tests.test_correction_throttle tests.test_evaluation tests.test_evaluation_export tests.test_extract tests.test_file_validation tests.test_findings tests.test_llm_web_search_eval tests.test_migration_graph tests.test_ocr_regions tests.test_postgres_account_provisioning tests.test_privacy tests.test_private_storage tests.test_processing_timing tests.test_public_correction_status tests.test_rdap_adapter tests.test_reporting tests.test_request_body_limit tests.test_restore_uploads tests.test_retention_uploads tests.test_schema_limits tests.test_validation_privacy -q
python -m compileall -q app tests evaluation
```
- Do not commit unless requested.

## 2026-10-26 09:45 (Asia/Kolkata) — Reopen human dispositions after supporting evidence corrections

### Completed in this stage

- Rechecked current UI and found that evidence-target correction controls already exist in `frontend/src/App.tsx`; the previous top-level checkpoint's step to implement those controls was stale.
- Closed a more consequential correction-propagation gap: when an evidence correction removes the relevant/result state required by an approved stronger human disposition, the correction transaction reopens that disposition as `pending_review`.
- Reopened records clear current reviewer fields but preserve the prior reviewer identity/status/time in a case audit event. Reports and the reviewer queue therefore stop presenting the disposition as approved until a separate authorized reviewer reviews it again.
- Added a database-backed regression test covering an approved concern disposition, evidence marked irrelevant through correction, preserved audit history, and report state.

### Checks actually run

- Selected backend suite: 139 tests passed; 1 opt-in PostgreSQL account-provisioning test skipped because no PostgreSQL test database is configured. The command excluded only `test_api_flow.py` and `test_proxy_headers.py`.
- `python -m compileall -q app tests evaluation` — passed.
- A focused command including `test_correction_application.py` twice ran 16 cases and passed; the broader selected suite above is the canonical run for this stage.
- No browser, API-router, PostgreSQL, or live Neo4j test was run in this stage.

### Files/components changed

- `backend/app/main.py`
- `backend/tests/test_correction_application.py`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Evidence correction invalidates affected approved stronger dispositions when their recorded evidence no longer meets review criteria. Entity-value corrections do not yet reassess whether an already approved case-level disposition still refers to the corrected identifier.
- Evidence-target correction controls are present but their browser interaction remains unverified.
- API-flow and proxy-header suites, live PostgreSQL, Neo4j, hosted deployment, OCR, and backup/restore remain unverified.
- Evaluation still needs authorized labeled data, a lawful configured LLM/search adapter, and a matched graph-disabled run.

### Exact next steps, in order

1. Extend correction propagation to entity-value/rejection changes when those changes invalidate evidence referenced by a stronger human disposition; add a regression test.
2. Continue access-control and report-redaction audit, then get the API/proxy tests running in a supported runtime.
3. Verify PostgreSQL transaction behavior and complete live Compose, Neo4j, OCR, backup/restore, and deployment checks when Docker is available.
4. Keep real evaluation results pending until authorized data and comparison adapters are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `README.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./correction-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the selected 26-module suite recorded in this checkpoint and `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-25 01:14 (Asia/Kolkata) — Score evidence support at claim level

### Completed in this stage

- Replaced the case-level evidence-support boolean with gold and predicted supported-claim arrays keyed by entity type and normalized value. A supported-claim set must be a subset of the corresponding entity set.
- Updated the persisted pipeline exporter to identify supported claims from each active entity finding and its relevant, result-bearing evidence records. Normalization applies to both gold and predicted claims.
- Added claim-level evidence-support precision, recall, and TP/FP/FN counts so a supported finding cannot mask an unsupported claim in the same case.
- Updated the LLM experiment adapter contract to require source references for every supported-claim prediction; the provenance sidecar preserves claim-to-source mappings and validates that references exist.
- Updated the TF-IDF baseline, four-run comparator, annotation format, evaluation README, metadata version, and engineering walkthrough to use the claim-level definition.

### Checks actually run

- Focused evaluation tests: 38 passed across scorer, pipeline exporter, TF-IDF baseline, and LLM/web-search runner.
- Selected broader backend suite: 132 tests passed across 23 named modules (campaign rules, config, corrections, evaluation, extraction, uploads, findings, OCR, privacy, retention, reports, and related checks).
- Account provisioning checks: 2 passed; the opt-in PostgreSQL-specific test was skipped because no PostgreSQL test database is configured.
- `python -m compileall -q app tests evaluation` — passed.
- An unfiltered discovery attempt stalled without further output after two tests and was interrupted. The named supported modules above were then run successfully. API-flow and proxy-header modules remain excluded due the recorded Windows TestClient issue.

### Files/components changed

- `backend/evaluation/evaluate.py`, `export_pipeline.py`, `baseline_tfidf_logreg.py`, `llm_web_search.py`, `compare_runs.py`
- Evaluation tests and `backend/evaluation/README.md`
- `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- No authorized annotation set, live LLM/search adapter, real PostgreSQL exporter run, matched graph-off execution, or measured system comparison exists. Evaluation results remain pending.
- Claim-level gold provenance must be maintained by independent annotators in protected storage; this repository does not hold or generate gold labels.
- API-flow and proxy-header checks, Docker services, hosted deployment, OCR service behavior, and backup/restore remain unverified.

### Exact next steps, in order

1. Run the focused evaluation tests and supported suite again after any follow-on changes; resolve the API/proxy test startup issue in a Linux CI/runtime.
2. Continue the correction propagation and privacy/security audit, particularly evidence-target correction UI, full report/source URL redaction, and access-control coverage.
3. Verify exporter transaction behavior on PostgreSQL, then verify Compose startup, Neo4j rebuild, OCR, backup/restore, and deployment when a usable Docker runtime is available.
4. Keep the four-system evaluation pending until authorized data and configured comparison providers are available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `backend/evaluation/README.md`, `ENGINEERING_WALKTHROUGH.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:APP_ENV='testing'`, `$env:DATABASE_URL='sqlite:///./evaluation-tests.db'`, and workspace-local `$env:TEMP`/`$env:TMP`; run the four focused evaluation test modules and `python -m compileall -q app tests evaluation`.
- Do not commit unless requested.

## 2026-10-25 01:08 (Asia/Kolkata) — Make the documented LLM evaluation input runnable

### Completed in this stage

- Fixed a mismatch between the documented LLM/web-search baseline input and its CLI: it had been validating the pre-prediction annotated dataset with the scorer's post-prediction schema, making the documented command unusable.
- Added a strict input reader for the experiment dataset. It validates the exact fields, entity shapes, booleans, unique case IDs, chronological split order, campaign separation, and presence of a held-out test set.
- Kept gold labels out of adapter arguments and limited adapter calls to test cases. Updated evaluation documentation and added regression tests for successful documented input, extra fields, and campaign leakage.

### Checks actually run

- From `backend`, `python -m unittest tests.test_llm_web_search_eval tests.test_evaluation -v` — 21 tests passed.
- `python -m compileall -q evaluation tests` — passed.
- The first test attempt used the sandbox's protected default temporary directory and failed before exercising code. Re-running with `TEMP` and `TMP` set to `backend/.test-tmp` resolved the filesystem restriction; this is an environment constraint, not a test or product failure.
- No real LLM/search adapter was configured or invoked; no evaluation data or performance result is claimed.

### Files/components changed

- `backend/evaluation/llm_web_search.py`
- `backend/tests/test_llm_web_search_eval.py`
- `backend/evaluation/README.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- A provider-specific lawful adapter and authorized time-separated data are still required for a real LLM/web-search comparison.
- Evidence-support remains currently represented as a case-level boolean, while system findings are claim-level; the annotation definition and metric granularity still need a final audit before data collection.
- PostgreSQL repeatable-read export, live API/proxy tests, Docker services, hosted deployment, OCR, and backup/restore remain unverified.

### Exact next steps, in order

1. Resolve evidence-support evaluation granularity and align annotation, persisted findings, comparison runner, and documentation; add focused tests.
2. Verify the evaluation exporter against disposable PostgreSQL when an accessible runtime exists.
3. Continue correction propagation, security/privacy verification, API/proxy tests, live service checks, and deployment/restore work as recorded below.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `backend/evaluation/README.md`, and `git status --short`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:TEMP` and `$env:TMP` to a writable workspace-local temporary directory; run `python -m unittest tests.test_llm_web_search_eval tests.test_evaluation -v` and `python -m compileall -q evaluation tests`.
- Do not commit unless requested.

## 2026-10-25 01:06 (Asia/Kolkata) — Count claim-level concerns in evaluation false-positive metric

### Completed in this stage

- Reviewed the adverse-assessment metric and found that a case-level authoritative-source label could mask a separate active claim-level “Evidence supports concern” finding.
- Updated the evaluation-only adverse flag to count either the overall case concern or any active claim-level concern. Authoritative-source confirmation alone remains non-adverse.
- Documented the field as an evaluation metric only; it is not a verdict about a person or organization.

### Checks actually run

- Focused evaluation-export suite: 11 passed, including the mixed case/claim assessment regression.
- Full supported backend suite excluding the Windows-blocked API/proxy modules: 132 tests ran, 131 passed, and 1 opt-in PostgreSQL concurrency test skipped.
- Python compilation of app, tests, and evaluation modules passed.
- Daemon-free deployment checks: docker compose config --quiet and scripts/test-compose-config.ps1 passed; live engine checks remain unavailable.
- Runtime availability rechecked: Docker CLI/Compose are installed, but Docker cannot connect to its Linux engine named pipe; WSL returns E_ACCESSDENIED; the Python launcher has no registered Python installations; this repository has no configured Git remote.

### Files/components changed

- backend/evaluation/export_pipeline.py, backend/evaluation/README.md
- backend/tests/test_evaluation_export.py, BUILD_STATUS.md

### Known bugs or unfinished work

- Evaluation remains pending authorized time-separated labels, a matched graph-off runtime, and real provider/data comparisons. The model-only versus human-in-the-loop comparison limitation remains documented.
- Live PostgreSQL execution, API/proxy CI, Docker services, hosted deployment, OCR, and backup/restore remain unverified.

### Exact next steps, in order

1. Finish auditing metric/annotation definitions and confirm the independent investigator review procedure before any authorized data run.
2. Verify the exporter on disposable PostgreSQL, including its repeatable-read transaction and non-overwriting private output files.
3. Continue end-to-end API, proxy, container, and deployment verification when the required runtime is available.

### Resume commands

- Re-read BUILD_STATUS.md, BUILD_PLAN.md, and git status --short.
- From backend, run python -m unittest tests.test_evaluation_export -v with the isolated environment, then the supported backend suite excluding test_api_flow and test_proxy_headers.
- Do not commit unless requested.

## 2026-10-25 01:04 (Asia/Kolkata) — Align campaign evaluation with investigator groups

### Completed in this stage

- Rechecked the campaign-view query and found that the UI groups both current-rule proposed and low-signal links, while evaluation previously measured only proposed links.
- Updated the exporter to include both current-rule states in predicted candidate clusters; links from historical rule versions remain excluded. Metadata explicitly describes these clusters as investigative leads.
- Updated evaluation documentation and added a regression test for low-signal groups.

### Checks actually run

- Focused exporter suite: 10 passed.
- Full supported backend suite excluding the Windows-blocked API/proxy modules: 131 tests ran, 130 passed, and 1 opt-in PostgreSQL concurrency test skipped because no test database was configured.
- Python compilation of app, tests, and evaluation modules passed.

### Files/components changed

- backend/evaluation/export_pipeline.py, backend/evaluation/README.md
- backend/tests/test_evaluation_export.py, BUILD_STATUS.md, ENGINEERING_WALKTHROUGH.md

### Known bugs or unfinished work

- No authorized time-separated evaluation data or real comparative run exists; no performance results are claimed.
- PostgreSQL repeatable-read behavior, API/proxy integration, live services, and deployment checks remain unverified because Docker and a Git remote are unavailable.

### Exact next steps, in order

1. Continue the requirements audit around evidence-support semantics, adverse assessment semantics, and comparison fairness before using an authorized dataset.
2. Run the exporter against a disposable PostgreSQL service and inspect its repeatable-read, read-only behavior and protected file output when a database runtime is available.
3. Run the actual API/proxy suites in Linux CI and complete the remaining live deployment, OCR, Neo4j, and backup/restore checks.

### Resume commands

- Re-read BUILD_STATUS.md, BUILD_PLAN.md, and git status --short.
- Evaluation exporter: from backend, run python -m unittest tests.test_evaluation_export -v; see backend/evaluation/README.md for the operator-data command and protected key requirements.
- Do not commit unless requested.

## 2026-10-25 01:00 (Asia/Kolkata) — Export persisted full-pipeline evaluation records

### Completed in this stage

- Added `backend/evaluation/export_pipeline.py`. It joins protected annotation maps to persisted case results and measured worker timing, emits only pseudonymous case IDs, and never exports case references or submitted text.
- Enforced a strict annotation schema, unique/pseudonymous IDs, complete successful single-attempt processing, campaign/time-split validation, and rejection of corrected values, human link decisions, retries, and incomplete cases.
- Defined reproducible evaluation outputs: extraction includes original candidate records (including candidates later rejected), evidence support requires an active finding that cites a relevant result, campaign clusters use current-rule proposed and low-signal links among mapped cases, and the adverse metric flag covers case-level and active claim-level “Evidence supports concern” findings.
- Added an operator-held HMAC key for corpus/evidence snapshot and annotation hashes; the key is never written. PostgreSQL reads use a repeatable-read, read-only transaction. Export files are created exclusively (no overwrite) with POSIX mode 0600; Windows inherits directory ACLs.
- Documented the exact input format, workflow review boundary, privacy limits, and command in `backend/evaluation/README.md`; updated the engineering walkthrough to distinguish implemented tooling from still-missing real evaluation results.

### Checks actually run

- Full supported backend suite (excluding `test_api_flow.py` and `test_proxy_headers.py`): 130 tests ran, 129 passed, and the opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL URL was configured.
- New evaluation-export tests: 9 passed. They exercise the scorer-schema join, candidate/evidence/campaign outcomes, HMAC metadata, privacy exclusions, refusal of corrected/retried cases, strict annotation IDs, repository path guard, exclusive output creation, and required HMAC key.
- `python -m compileall -q app tests evaluation`: passed.
- The exporter logic was verified with synthetic SQLite records; the CLI file-write path was exercised with a mocked database session. No authorized data or live PostgreSQL export was run.

### Files/components changed

- `backend/evaluation/export_pipeline.py`, `backend/evaluation/README.md`
- `backend/tests/test_evaluation_export.py`
- `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- No authorized time-separated annotation set, real full-pipeline measurement, configured LLM/web-search provider, or matched graph-disabled run exists; no performance results are claimed.
- Evidence-support and adverse assessment scoring are human-in-the-loop outputs. Gold-label annotators must remain independent of investigators who review entities/evidence, and the output’s adverse flag is evaluation-only, never a guilt verdict.
- Live PostgreSQL transaction behavior, API/proxy integration suites, Docker/Neo4j/OCR, hosted deployment/TLS, and backup/restore remain unverified in this environment.
- The project files still appear untracked in Git; no commit was made.

### Exact next steps, in order

1. Review the export metric definitions against the approved annotation guidance before using real data.
2. When lawful authorized data and an operator-controlled PostgreSQL environment are available, run the exporter, inspect the metadata and privacy boundary, then score only the time-separated test set.
3. Execute a real matched graph-disabled run and the configured LLM/web-search comparator under the same test cases and evidence snapshots; compare four runs.
4. Resolve the Windows TestClient hang in Linux CI and continue live service, security, deployment, and restore verification.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and `git status --short`.
- See `backend/evaluation/README.md` for the protected annotation-map format, `EVALUATION_SNAPSHOT_HMAC_KEY` requirement, exporter command, scorer command, and graph-ablation procedure.
- From `backend`, run `python -m unittest tests.test_evaluation_export -v` with the isolated test environment described above; then run the supported suite excluding `test_api_flow` and `test_proxy_headers`.
- Do not commit unless requested.

## 2026-10-25 00:51 (Asia/Kolkata) — Persist successful worker processing duration

### Completed in this stage

- Added nullable `processing_jobs.processing_ms`, populated on successful processing attempts using a monotonic timer. The measurement starts after the queued-to-processing transition commits and ends just before the completion commit; queue wait is excluded.
- Clear prior duration when an attempt starts, so failed/retried work cannot expose a stale successful duration as the latest attempt result.
- Added migration `c28f4e6a1b93_capture_processing_duration.py` and documented the exact timing boundary. The pseudonymous annotation-to-prediction export/join utility remains the next evaluation task.

### Checks actually run

- New isolated worker timing test: 1 passed.
- Full supported backend suite (excluding `test_api_flow.py` and `test_proxy_headers.py`): 121 tests ran, 120 passed, 1 opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL URL was configured.
- Fresh disposable SQLite `alembic upgrade head` and `alembic check`: passed; no schema drift detected.

### Files/components changed

- `backend/app/models.py`, `backend/app/worker.py`
- `backend/migrations/versions/c28f4e6a1b93_capture_processing_duration.py`
- `backend/tests/test_processing_timing.py`, `backend/evaluation/README.md`
- `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- The duration currently captures only the latest attempt, not an immutable per-attempt history. It is suitable for successful-run evaluation if the first/only completed attempt is measured; retries should be excluded or separately labeled until per-attempt records exist.
- No exporter yet joins pseudonymous labels to persisted predictions/timing. Evaluation remains pending authorized data and real baseline runs.
- API/proxy integration, live Docker services, PostgreSQL/Neo4j/OCR, hosted TLS, and backup/restore remain unverified in this environment.

### Exact next steps, in order

1. Implement an evaluation export path that takes an access-controlled annotation-to-case-reference mapping, emits only pseudonymous IDs, and rejects cases whose predictions were altered by human review.
2. Export persisted extraction, evidence-support, assessment, campaign-link outputs and worker timing under documented reproducible definitions; test with synthetic database records.
3. Re-run the full supported backend suite and migration checks after export implementation.
4. Continue API/proxy, live-service, security, and deployment verification when a suitable runtime is available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short`.
- Backend tests: from `backend`, set `PYTHONPATH=.pydeps`, `APP_ENV=testing`, workspace-local `TEMP`/`TMP`, and a unique disposable SQLite `DATABASE_URL`; run `python -m unittest tests.test_processing_timing -v`, then the supported suite excluding `test_api_flow` and `test_proxy_headers`.
- Migration: from `backend`, with a new disposable SQLite URL, run `python -m alembic upgrade head` and `python -m alembic check`.
- Do not commit unless requested.

## 2026-10-25 00:49 (Asia/Kolkata) — Reconcile engineering walkthrough with current evaluation and report implementation

### Completed in this stage

- Corrected stale walkthrough statements: the provider-neutral LLM/web-search baseline runner and Markdown report export are implemented; the earlier text incorrectly described the runner as absent and reports as JSON-only.
- Replaced an obsolete 100-test verification snapshot with the current 120-test result and clearly retained exclusions and operational verification gaps.

### Checks actually run

- Searched `ENGINEERING_WALKTHROUGH.md` for the obsolete claims and confirmed the current implementation status is now described consistently.
- `git diff --check` was invoked, but this workspace currently reports all project files as untracked, so Git cannot show/check their contents as a tracked diff.
- No runtime tests were needed for this documentation-only correction.

### Files/components changed

- `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- The walkthrough still documents real environment blockers: API/proxy TestClient suites, hosted browser flow, Docker/PostgreSQL/Neo4j/OCR/backup checks, and authorized-data evaluation are unverified.
- `git status --short` reports the whole implementation as untracked. No commit was made; preserve this state until the repository ownership/baseline is understood.

### Exact next steps, in order

1. Implement a reproducible export of persisted full-pipeline predictions and per-case processing durations for authorized time-separated evaluation.
2. Verify that export using synthetic SQLite-backed cases and ensure it contains only pseudonymous identifiers and evaluation fields.
3. Continue API/proxy, live-service, security, and deployment verification when an appropriate runtime is available.

### Resume commands

- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and inspect `git status --short` before the next change.
- Resume evaluation work by inspecting `backend/app/worker.py`, `backend/app/models.py`, `backend/evaluation/README.md`, and existing evaluation export/scorer schemas.
- Do not commit unless requested.

## 2026-10-25 00:48 (Asia/Kolkata) — Expand explicit recruitment-claim extraction labels

### Completed in this stage

- Extended deterministic claim parsing for common labeled variants: company name/hiring company, designation/vacancy/opening, HR or recruiter name, and office/posting location.
- Kept extraction conservative: claims still require an explicit field label, retain exact source spans, and remain marked as unverified. Added a negative test confirming unlabeled narrative text does not cause company, role, recruiter, or location claims to be inferred.

### Checks actually run

- Full supported backend suite (excluding `test_api_flow` and `test_proxy_headers`): 120 tests ran, 119 passed, and 1 opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL URL was configured.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/app/extract.py`, `backend/tests/test_extract.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- Free-form narrative extraction remains intentionally limited; it needs authorized annotated examples and evaluation before introducing inference beyond explicit labels.
- OCR/container verification and API-flow/proxy CI are still unavailable in this workspace. PostgreSQL/Neo4j, deployment, backup/restore, and real-data evaluation remain unverified.

### Exact next steps, in order

1. Run API-flow and proxy-header suites on Linux CI, including the new Markdown report assertions.
2. Verify browser report downloads and responsive layout on a running deployment.
3. Run the disposable Docker/PostgreSQL/Neo4j, OCR, retention, and backup/restore drills when an engine is available.
4. Continue authorized-data and security review; preserve the current explicit-label boundary unless evaluation supports a broader parser.

### Resume commands

- From `backend/`, run `.venv/Scripts/python.exe -m unittest tests.test_extract -v` with `PYTHONPATH=.pydeps`, `APP_ENV=testing`, workspace-local `TEMP`/`TMP`, and a disposable SQLite `DATABASE_URL`.
- Re-read this file and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 00:46 (Asia/Kolkata) — Add a human-readable redacted report export

### Completed in this stage

- Added a Markdown renderer over the same persisted, redacted report document used by JSON. It includes case scope, masked entities and source locations, evidence outcomes/retrieval provenance, active and superseded machine findings, campaign-link review state, human dispositions, audit timeline, rule versions, timestamps, and limitations.
- Escaped source-controlled text so it cannot inject Markdown headings or links. The API keeps JSON as the default and supports `?format=markdown`; both formats write an audited export event with the selected format.
- Added separate JSON and Markdown download controls to the investigator case view and documented both report formats.
- Added unit coverage for required report sections, provenance, safe outcome language, identifier masking, and Markdown injection resistance; extended correction/report handler coverage and added HTTP assertions to the Linux API-flow test.

### Checks actually run

- Focused report and correction-handler suite: 3 passed.
- Full supported backend suite (excluding `test_api_flow` and `test_proxy_headers`): 118 tests ran, 117 passed, and 1 opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL URL was configured.
- `python -m compileall -q app tests evaluation`: passed.
- Frontend `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.
- The API-flow HTTP assertions for Markdown content type/attachment headers are added but remain unrun in this Windows environment.

### Files/components changed

- `backend/app/reporting.py`, `backend/app/main.py`
- `backend/tests/test_reporting.py`, `backend/tests/test_correction_application.py`, `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known bugs or unfinished work

- The actual `/api/cases/{id}/report?format=markdown` request/response and browser download flow still need API-flow CI and browser verification.
- Linux API/proxy CI, live PostgreSQL/Neo4j, Docker/OCR, TLS deployment, and backup/restore remain unverified; authorized evaluation data is still unavailable.

### Exact next steps, in order

1. Run API-flow and proxy-header suites on Linux CI, including the new Markdown response assertions.
2. Verify JSON/Markdown downloads in the browser and check narrow/mobile header layout.
3. With Docker available, run the documented service health, PostgreSQL/Neo4j, OCR, retention, and backup/restore drills on disposable data.
4. Continue security/privacy review and wait for authorized time-separated data before reporting evaluation results.

### Resume commands

- Backend: from `backend/`, use workspace-local `TEMP`/`TMP`, `PYTHONPATH=.pydeps`, `APP_ENV=testing`, and disposable SQLite `DATABASE_URL`; run `tests.test_reporting tests.test_correction_application`, then the supported suite excluding the known Windows-blocked API/proxy modules.
- Frontend: from `frontend/`, run `pnpm run build; pnpm run test:redaction`.
- Re-read this file and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 00:41 (Asia/Kolkata) — Revalidate local deployment configuration and CI access

### Completed in this stage

- Rechecked the current Compose deployment configuration and daemon-free assertions after the privacy/API hardening changes.
- Confirmed the workspace still has no configured Git remote or `gh` CLI, no available Podman/nerdctl runner, and WSL access is denied. This environment therefore cannot dispatch/inspect GitHub Actions or substitute a local Linux runtime for the blocked Windows HTTP/proxy tests.
- Reconfirmed the Docker CLI cannot reach the Docker Desktop Linux engine pipe; live service, container, backup/restore, and OCR checks remain pending.

### Checks actually run

- `docker compose config --quiet`: passed.
- `scripts/test-compose-config.ps1`: passed for database URL derivation, correction throttles, proxy trust, upload limits, web health, same-origin routes, security headers, and private Docker build contexts.
- `docker version`: failed to connect because `//./pipe/dockerDesktopLinuxEngine` is unavailable.
- `wsl --list --quiet`: failed with `Wsl/E_ACCESSDENIED`.

### Files/components changed

- `BUILD_STATUS.md`

### Known bugs or unfinished work

- API-flow/proxy-header test modules and Linux-only runtime verification remain unrun. No remote is configured to publish the branch or inspect hosted CI results.
- PostgreSQL/Neo4j integration, container OCR, actual TLS deployment, and backup/restore drill remain unverified.

### Exact next steps, in order

1. When a Linux CI runner or repository remote becomes available, run and inspect the existing CI workflow, including API-flow, proxy, image-build, and Nginx smoke jobs.
2. On a Docker host, run the documented disposable Compose verification for API/worker health, PostgreSQL, Neo4j outage/rebuild, OCR, retention, and backup/restore.
3. Continue independent privacy, browser, and evaluation work in the meantime; keep performance results pending until authorized data exists.

### Resume commands

- From the repository root: `docker compose config --quiet; ./scripts/test-compose-config.ps1`.
- Inspect `git remote -v`, Docker Engine availability, and WSL/CI access before attempting the excluded integration checks again.
- Re-read `BUILD_STATUS.md` and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 00:39 (Asia/Kolkata) — Keep rejected request values out of validation responses

### Completed in this stage

- Added a FastAPI request-validation handler that returns at most 50 errors with fixed, safe messages and allowlisted field locations/types. It excludes Pydantic's rejected `input`, context, and raw error message, which can include submitted text, identifiers, or secrets.
- Added a regression test using a synthetic phone number and token in all rejected-value fields; verified neither value appears in the response representation while a useful field location and validation hint remain.

### Checks actually run

- Focused `tests.test_validation_privacy`: 1 passed.
- Full supported backend suite (excluding only `test_api_flow` and `test_proxy_headers`, which remain blocked by the known Windows TestClient socketpair issue): 116 tests ran, 115 passed, and 1 opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL test URL was configured.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_validation_privacy.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The API-flow and proxy integration tests still need Linux CI execution. This helper test verifies safe response construction and registration, not an HTTP request through the live ASGI middleware stack.
- Docker Engine, live PostgreSQL/Neo4j, hosted CI, TLS deployment, OCR-in-container, and backup/restore remain unverified. Authorized evaluation data is still unavailable.

### Exact next steps, in order

1. Run API-flow and proxy-header suites in Linux CI and inspect actual results.
2. Run Docker Compose health, graph rebuild/outage, OCR, retention, and backup/restore checks on disposable data when a Docker Engine is available.
3. Continue browser, security/privacy, and authorized evaluation work.

### Resume commands

- From `backend/`, use workspace-local `TEMP`/`TMP`, `PYTHONPATH=.pydeps`, `APP_ENV=testing`, and a disposable SQLite `DATABASE_URL`; run supported `tests.test_*` modules except `test_api_flow` and `test_proxy_headers`, then `.venv/Scripts/python.exe -m compileall -q app tests evaluation`.
- Re-read status/plan and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 00:36 (Asia/Kolkata) — Reduce evaluation and retention data leakage

### Completed in this stage

- Restricted the operator-supplied LLM/web-search evaluation sidecar to allowlisted provenance fields, validates source hashes/timestamps, drops arbitrary metadata keys, and converts free-form provider errors to standardized codes. Provider exceptions and comparison/ablation validation errors no longer echo case IDs or sensitive exception text.
- Limited the LLM/web-search runner output to held-out test predictions only; train/dev source text is no longer copied into prediction artifacts.
- Added evaluation handling guidance requiring pseudonymous case/campaign IDs, access-controlled artifacts, no raw secrets or signed URLs in provenance, and off-repository retention controls.
- Changed retention filesystem failure logs to report only the exception class, without exception strings or tracebacks.
- Fixed a retention ordering bug: deletion of expired cases is now flushed before active upload references are collected, so files belonging only to deleted cases are no longer incorrectly protected as active. Kept files referenced by surviving cases protected.
- Added regression coverage for the retention ordering/privacy behavior and evaluation artifact leakage controls.

### Checks actually run

- Backend focused evaluation and retention suite: 24 tests passed across `test_evaluation`, `test_baseline_tfidf_logreg`, `test_llm_web_search_eval`, and `test_retention_uploads`.
- Full supported backend suite (excluding only the known Windows-blocked `test_api_flow` and `test_proxy_headers` modules): 115 tests ran, 114 passed, and 1 opt-in PostgreSQL concurrency test skipped because no disposable PostgreSQL test URL was configured.
- `python -m compileall -q app tests evaluation`: passed.
- Frontend `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.
- Tests ran with the backend virtual-environment interpreter, workspace-local dependency path, isolated SQLite configuration, and workspace-local temp directory. No external dataset or provider was used.

### Files/components changed

- `backend/app/worker.py`, `backend/evaluation/README.md`, `backend/tests/test_retention_uploads.py`
- `backend/tests/test_llm_web_search_eval.py`, `backend/tests/test_baseline_tfidf_logreg.py`
- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Known bugs or unfinished work

- The API-flow and proxy integration test modules still cannot be verified in this restricted Windows runtime; run them in Linux CI.
- Docker Engine, live PostgreSQL/Neo4j, hosted CI, TLS deployment, OCR-in-container, and backup/restore drill remain unverified.
- Authorized evaluation data and provider-specific LLM/web-search adapter are not configured; real performance results remain pending.

### Exact next steps, in order

1. Run API-flow and proxy-header suites in Linux CI, then inspect actual CI results.
2. With Docker Engine available, run Compose health/readiness, expired-upload purge, PostgreSQL/Neo4j outage and graph-rebuild, OCR, and backup/restore checks on disposable data.
3. Continue the security/privacy and browser end-to-end audit, then obtain authorized time-separated data before evaluation.

### Resume commands

- Backend focused suite (from `backend/`): set `PYTHONPATH=.pydeps`, `APP_ENV=testing`, a disposable SQLite `DATABASE_URL`, and `TEMP`/`TMP` to a workspace-local directory, then run `.venv/Scripts/python.exe -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval tests.test_retention_uploads -v`.
- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, and current Git status before continuing. Do not commit unless requested.

## 2026-10-25 (Asia/Kolkata) — Restrict browser connections to the same origin

### Completed in this stage

- Changed the production app to call relative `/api` routes by default; added a Vite development proxy and an Nginx API proxy so local and hosted deployments use the same origin.
- Added Nginx Content Security Policy, Permissions Policy, frame, MIME and referrer headers. The static asset location repeats the security-header include because Nginx stops inheriting parent `add_header` directives when a child location defines its own cache header.
- Added stable Caddy and Nginx proxy addresses to the API's explicit forwarded-header trust list. Added a web-container health check, made Caddy wait for web health, and documented the proxy address/subnet configuration.
- Added a Linux CI container smoke job that will build and run Nginx, check security headers, and exercise `/api` through a synthetic local HTTP fixture.

### Checks actually run

- `frontend/pnpm run build`: passed.
- `frontend/pnpm run test:redaction`: 4 passed.
- `scripts/test-compose-config.ps1`: passed with assertions for same-origin routes, proxy IP trust, security headers, and web health check.
- `docker compose config --quiet`: passed, including Compose syntax/interpolation validation.
- The new hosted Nginx container smoke job has not run. Local Docker Engine is unavailable, so no live Nginx/API proxy result is claimed.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/vite.config.ts`, `frontend/Dockerfile`, `frontend/nginx.conf.template`, `frontend/nginx-entrypoint.sh`, `frontend/security-headers.conf`
- `docker-compose.yml`, `Caddyfile`, `.env.example`, `.github/workflows/ci.yml`
- `scripts/test-compose-config.ps1`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known limitations and next steps

1. Run the hosted CI workflow, including the Nginx container smoke test and backend HTTP/proxy suites.
2. On a Docker host, start the Compose stack and verify browser headers, Nginx forwarded client addresses, Caddy TLS routing, and upload-size handling end to end.
3. Continue live PostgreSQL/Neo4j, backup/restore, security/privacy, and authorized evaluation verification.

### Resume commands

- Frontend: `cd frontend; pnpm run build; pnpm run test:redaction`.
- Compose: `./scripts/test-compose-config.ps1; docker compose config --quiet`.
- Re-read this file and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 (Asia/Kolkata) — Keep upload limits and Docker contexts aligned

### Completed in this stage

- Bounded `MAX_UPLOAD_BYTES` to 1 byte–50 MiB in API startup validation and exposed focused configuration tests.
- Changed the Nginx configuration into an entrypoint template. The container computes its accepted request size from the configured file limit plus 64 KiB multipart overhead, rounded up to KiB, so proxy and API limits agree. Values above the supported cap fail closed at startup.
- Passed the upload limit to the web container and added a hosted smoke assertion for a 2 MiB configuration (2,112 KiB request cap).
- Added backend and frontend `.dockerignore` files to keep test databases, virtual environments, dependency caches, uploads, local environment files and build artifacts out of container build contexts. CI now builds the API/worker image as well as running the web container smoke test.

### Checks actually run

- `python -m unittest tests.test_config -v`: 9 passed.
- `python -m compileall -q app tests evaluation`: passed.
- Re-ran supported backend modules excluding the socketpair-blocked API-flow/proxy suites: 110 ran, 109 passed, 1 skipped for absent disposable PostgreSQL concurrency configuration.
- `pnpm run build`: passed; `pnpm run test:redaction`: 4 passed.
- `scripts/test-compose-config.ps1`: passed with checks for the upload limit propagation and private Docker contexts.
- `docker compose config --quiet`: passed.
- CI workflow YAML parsed and includes the API/web container build and web smoke job. Docker builds and actual Nginx template rendering remain unrun locally because Docker Engine is unavailable.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_config.py`, `backend/.dockerignore`
- `frontend/.dockerignore`, `frontend/Dockerfile`, `frontend/nginx.conf.template`, `frontend/nginx-entrypoint.sh`
- `docker-compose.yml`, `.github/workflows/ci.yml`, `scripts/test-compose-config.ps1`, `.env.example`, `README.md`, `BUILD_STATUS.md`

### Next steps

1. Run the hosted CI workflow and inspect both container builds and Nginx runtime smoke results.
2. Verify Nginx request limits and trusted client-address forwarding through the complete Docker Compose stack.
3. Continue live Postgres/Neo4j, backup/restore, deployment, privacy/security, and authorized evaluation checks.

### Resume commands

- Backend config: `cd backend; python -m unittest tests.test_config -v; python -m compileall -q app tests evaluation`.
- Frontend and Compose: `cd frontend; pnpm run build; pnpm run test:redaction`; from root run `./scripts/test-compose-config.ps1; docker compose config --quiet`.
- Do not commit unless requested.

## 2026-10-25 (Asia/Kolkata) — Make system assessments and rule provenance explicit in the investigator UI

### Completed in this stage

- Renamed the case-list column to “System assessment” to distinguish automated categories from the separate human-disposition workflow.
- Added each machine finding's rule name beside its scope and version so investigators can see which named rule produced the finding.
- Recorded this UI clarification and its verification in the engineering walkthrough.

### Checks actually run

- From `frontend/`, `pnpm run build`: passed (`tsc -b` and Vite production build).
- From `frontend/`, `pnpm run test:redaction`: 4 passed.
- From `backend/`, the supported unittest modules excluding `test_api_flow` and `test_proxy_headers`: 109 run, 108 passed, 1 skipped because an isolated PostgreSQL test URL was not configured. This confirms unit and handler-level behavior but does not replace the excluded HTTP/proxy flow suite or live PostgreSQL checks.

### Files/components changed

- `frontend/src/App.tsx`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known limitations and next steps

1. Continue the full application verification: Linux API-flow suite, live PostgreSQL and Neo4j behavior, graph rebuild, worker retry, retention and backup/restore.
2. Complete security/privacy review and controlled deployment checks; Docker Engine is unavailable in this workspace.
3. Run evaluation only with authorized time-separated data; no performance results exist yet.

### Resume commands

- Frontend: `cd frontend; pnpm run build; pnpm run test:redaction`.
- Re-read this file and inspect Git status before continuing. Do not commit unless requested.

## 2026-10-25 (Asia/Kolkata) — Recheck daemon-free deployment operations

### Completed in this stage

- Revalidated the backup orchestration script with its fake Docker CLI, including consistent database/upload capture order, manifest generation, failure cleanup and service restart behavior.
- Revalidated the rendered Compose settings for PostgreSQL-derived API/worker database URLs and API correction-throttle wiring.
- Confirmed Docker CLI is present but the Docker Desktop Linux engine pipe is absent, so no live Compose service or backup/restore drill can be run in this workspace.

### Checks actually run

- `scripts/test-backup.ps1`: passed.
- `scripts/test-compose-config.ps1`: passed.
- `docker version`: failed to reach `//./pipe/dockerDesktopLinuxEngine` because the engine is not running/available; this is an environment check, not a passing deployment check.

### Known limitations and next steps

1. Run the API-flow and proxy-header integration suites on the configured Linux CI runner and inspect their actual job results.
2. With Docker Engine available, start Compose and verify PostgreSQL, worker, Neo4j outbox/rebuild, OCR smoke test, health checks, and backup/restore on disposable data.
3. Complete hosted deployment and security/privacy verification; obtain authorized evaluation data before reporting model metrics.

### Additional environment verification

- A temporary in-process `httpx.ASGITransport` adapter was evaluated for Windows API tests, but its proxy test request stalled in this sandbox and had to be interrupted. The adapter was removed and the original test setup restored; no API-flow or proxy test result is claimed from that attempt.
- `git remote -v` returned no configured remote, and `gh` is not installed, so this workspace cannot dispatch or inspect the configured GitHub Actions workflow. Hosted CI remains a required next verification step.

### Resume commands

- From the repository root: `./scripts/test-backup.ps1; ./scripts/test-compose-config.ps1`.
- Live: `docker compose up --build --wait --wait-timeout 180`, then follow README health, OCR and backup/restore procedures with disposable test data.
- Re-read this file and inspect Git status. Do not commit unless requested.

## 2026-10-25 (Asia/Kolkata) — Verify corrected report provenance and privacy

### Completed in this stage

- Extended the isolated persisted-data correction test to invoke report generation after an entity correction and campaign relinking.
- Verified the exported report contains the current proposed campaign link and its rule version while masking both the superseded and corrected phone values, and excluding the correction requester email.
- This directly exercises report serialization and audit redaction from SQLite-backed records but does not test HTTP auth/cache middleware or live PostgreSQL behavior.

### Checks actually run

- `python -m unittest tests.test_correction_application -v`: 1 passed.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/tests/test_correction_application.py`, `BUILD_STATUS.md`

### Next steps

1. Run API report route tests in hosted Linux CI, including response headers, and verify correction history remains safely redacted.
2. Verify report fields against PostgreSQL-persisted evidence and link state after a correction.
3. Continue live deployment, graph, security/privacy, backup/restore and authorized evaluation work.

### Resume commands

- Backend: `python -m unittest tests.test_correction_application -v` with isolated SQLite settings.
- Hosted CI: inspect report assertions in `tests.test_api_flow`; HTTP route/auth behavior still needs CI execution.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Include redacted campaign links in downloadable reports

### Completed in this stage

- Report review showed exports included campaign rule versions but omitted the actual linked case pairs and their current review states. Added a `campaign_links` report field using the existing redacting link serializer, plus explicit lead-language explaining that connections are not proof of wrongdoing.
- Added an API-flow regression assertion that reports include campaign links/rule versions while keeping direct phone identifiers out of link explanations.
- Updated the engineering walkthrough report contents.

### Checks actually run

- `python -m compileall -q app tests evaluation`: passed.
- `python -m unittest tests.test_campaign_rules tests.test_privacy tests.test_correction_application -v`: 18 passed.
- The endpoint-level report assertion is in `tests.test_api_flow`; it remains pending Linux CI execution because Windows TestClient initialization hangs in socketpair fallback.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Verify report export on hosted Linux CI, including link redaction and correction-updated report contents.
2. Verify report content against live persisted PostgreSQL findings and campaign links after corrections.
3. Continue live deployment, privacy/security, graph, backup/restore and authorized evaluation work.

### Resume commands

- Backend focused checks: `python -m unittest tests.test_campaign_rules tests.test_privacy tests.test_correction_application -v`.
- Hosted Linux CI: inspect `tests.test_api_flow` report assertions after pushing; local compilation is not route-level proof.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Protect active uploads during orphan retention sweep

### Completed in this stage

- Fixed an orphan cleanup data-loss edge case: the age-based private-file sweep could delete a file still referenced by a nonexpired evidence record if the file had an old modification time (for example after restore/copy).
- Retention now builds a protected set of opaque filenames from surviving `uploaded_file` evidence, excludes them from both expired-upload unlinking and the age-based orphan sweep, and still removes files belonging only to expired cases.
- Added a database-backed regression test using a recent case with a 400-day-old upload mtime. The test exercises real SQLite persistence and the purge function without HTTP/TestClient.
- Updated the engineering walkthrough retention description.

### Checks actually run

- `python -m unittest tests.test_retention_uploads -v`: 1 passed.
- `python -m compileall -q app tests evaluation`: passed.
- Live PostgreSQL retention and Docker volume behavior remain unverified.

### Files/components changed

- `backend/app/worker.py`, `backend/tests/test_retention_uploads.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Verify the full retention flow in the Linux API integration suite and PostgreSQL-backed deployment.
2. Exercise backup/restore with live Docker volumes and ensure recovered active upload references remain present.
3. Complete remaining deployment, graph, security/privacy, and authorized evaluation work.

### Resume commands

- Backend: `python -m unittest tests.test_retention_uploads -v` with `APP_ENV=testing` and isolated SQLite settings.
- Live verification: use disposable PostgreSQL and upload volumes; inspect active and expired files after purge and restore.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Exercise correction logic without HTTP event loop

### Completed in this stage

- Added a database-backed isolated SQLite test that invokes the correction handler directly, bypassing the Windows-only TestClient socketpair hang while retaining real persistence and SQL behavior.
- Verified a corrected phone identifier creates a proposed link to another case containing that value, and verified a repeat application is rejected with HTTP 409.
- This covers handler persistence and linking but does not test HTTP authentication/middleware or PostgreSQL row-lock concurrency; those remain in the API-flow/PostgreSQL checks.

### Checks actually run

- `python -m unittest tests.test_correction_application -v`: 1 passed.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/tests/test_correction_application.py`, `BUILD_STATUS.md`

### Next steps

1. Run the full backend CI suite on Linux/Python 3.12, including API-level correction relinking and replay assertions.
2. Verify row-lock race behavior against PostgreSQL and graph outbox delivery against Neo4j.
3. Complete deployment/backup/restore, privacy/security and authorized evaluation verification.

### Resume commands

- Backend: `python -m unittest tests.test_correction_application -v` with test dependencies installed.
- Hosted Linux CI: review the complete workflow results; PostgreSQL concurrency and Neo4j require configured services.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Prevent correction request replay

### Completed in this stage

- Added a row lock while applying a correction request and a check against the durable `correction_applied` audit event. Reapplying an already applied request now returns HTTP 409 rather than repeating mutations/recomputation; serialized requests prevent concurrent duplicate application on PostgreSQL.
- Added an API-flow regression assertion for replay rejection.

### Checks actually run

- `python -m compileall -q app tests evaluation`: passed.
- Verified the JSON audit-detail lookup on SQLite with an isolated in-memory database: passed.
- `python -m unittest tests.test_correction_throttle tests.test_public_correction_status tests.test_account_provisioning -v`: 8 passed.
- The endpoint replay assertion itself is in `tests.test_api_flow` and remains pending Linux/Python 3.12 CI execution. PostgreSQL row-lock behavior is not live-verified in this environment.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `BUILD_STATUS.md`

### Next steps

1. Run API-flow tests on hosted Linux CI, including correction replay and corrected-identifier relinking.
2. Verify concurrent correction application and row locking on PostgreSQL.
3. Complete live Neo4j, deployment, retention, backup/restore, privacy/security and authorized evaluation work.

### Resume commands

- Backend focused checks: `python -m unittest tests.test_correction_throttle tests.test_public_correction_status tests.test_account_provisioning -v`.
- Hosted Linux: run `tests.test_api_flow`; PostgreSQL concurrency requires a disposable PostgreSQL database.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Review correction link decision preservation

### Completed in this stage

- Inspected the correction-triggered campaign recomputation for investigator-decision handling. Rejected links remain rejected; confirmed links remain confirmed while their evidence still shares identifiers; links that lose all shared identifiers are marked stale; newly supported matches are proposed/low-signal under the current versioned rule.
- Existing API-flow regression now covers a corrected identifier that should produce a new candidate link; it remains pending Linux execution.

### Checks actually run

- `python -m compileall -q app tests evaluation`: passed.
- `python -m unittest tests.test_campaign_rules tests.test_findings tests.test_account_provisioning tests.test_migration_graph -v`: 17 passed.
- These focused tests do not execute the new correction endpoint path; `tests.test_api_flow` still requires Linux/Python 3.12 or another working asyncio socketpair runtime.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run the full API-flow suite on hosted Linux CI and confirm correction relinking and investigator decision preservation.
2. Verify Neo4j outbox projection after correction and graph rebuild in a live deployment.
3. Continue PostgreSQL, privacy/security, backup/restore and authorized evaluation verification.

### Resume commands

- Backend: `python -m unittest tests.test_campaign_rules tests.test_findings tests.test_account_provisioning tests.test_migration_graph -v`.
- Hosted: inspect `.github/workflows/ci.yml` run; specifically verify `tests.test_api_flow` after push.
- Re-read status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Recompute campaign links after record corrections

### Completed in this stage

- Found that correction application recalculated findings and withdrew existing links that lost their shared identifiers, but did not discover new exact-identifier links made possible by a corrected value.
- Changed correction application to run current-version campaign-link recomputation before its commit. Its response now includes the refreshed links; the shared refresh path updates the graph projection outbox in the same transaction.
- Expanded the API-flow regression test: it prepares a synthetic case containing the corrected identifier and asserts that applying the correction discovers a new lead link.
- Updated the engineering walkthrough to describe both stale-link withdrawal and new-link discovery.

### Checks actually run

- `python -m compileall -q app tests evaluation`: passed.
- `python -m unittest tests.test_campaign_rules tests.test_findings tests.test_evaluation -v`: 22 passed.
- The new end-to-end correction relinking assertion is in `tests.test_api_flow`; it could not be executed in this Windows Python 3.14 environment because TestClient event-loop startup blocks in socketpair fallback. Hosted CI has not run yet.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run `tests.test_api_flow` on Linux/Python 3.12 via hosted CI; verify corrected records produce new links and old links become stale.
2. Verify graph outbox application against Neo4j in a live deployment.
3. Continue PostgreSQL, security/privacy, backup/restore and authorized evaluation completion.

### Resume commands

- Backend focused checks: `python -m unittest tests.test_campaign_rules tests.test_findings tests.test_evaluation -v`.
- Hosted CI: inspect `tests.test_api_flow` result after pushing; do not count compilation or rules tests as end-to-end proof.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Reject coerced LLM provenance values

### Completed in this stage

- Tightened four-way comparison provenance validation: case IDs, provider/model/prompt/retrieval metadata, and source fields must have the documented string types instead of being accepted through string coercion. Existing checks continue to require explicit lawful-access attestation, timezone-aware retrieval times, matching test IDs, and valid SHA-256 hashes.
- Added tests showing numeric provider and source-reference values are rejected. Updated evaluation guidance.

### Checks actually run

- `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v`: 18 passed.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/evaluation/compare_runs.py`, `backend/tests/test_evaluation.py`, `backend/evaluation/README.md`, `BUILD_STATUS.md`

### Next steps

1. Run hosted CI on Python 3.12 and fix any failures from the full Linux suite.
2. Obtain authorized annotated data and execute the prescribed comparisons; no model performance results are available.
3. Complete live deployment, PostgreSQL/Neo4j, privacy/security, retention and backup/restore verification.

### Resume commands

- Backend: `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v` with writable temp paths.
- Review `.github/workflows/ci.yml` results after a hosted run; local checks do not prove CI passes.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Validate evaluation input instead of coercing labels

### Completed in this stage

- Tightened the scorer's JSONL loader. It now rejects malformed record roots, empty case IDs, invalid split/campaign identifiers, non-Boolean evidence/verdict labels, malformed entity records, naive timestamps, and negative/non-finite processing times.
- This prevents values such as the string `"false"` from being silently interpreted as true during evidence-support or false-positive calculations.
- Added regression tests and documented the accepted row constraints.

### Checks actually run

- `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v`: 17 passed.
- `python -m compileall -q app tests evaluation`: passed.
- The first test attempt inherited a restricted Windows temp directory and errored in `tempfile`; reran with the workspace test temp directory and all checks passed.

### Files/components changed

- `backend/evaluation/evaluate.py`, `backend/tests/test_evaluation.py`, `backend/evaluation/README.md`, `BUILD_STATUS.md`

### Next steps

1. Run hosted CI and confirm all integration tests on Linux/Python 3.12.
2. Obtain authorized annotated time-separated data and run comparisons; no model performance results are available.
3. Complete live PostgreSQL/Neo4j, backup/restore, security/privacy and deployment verification.

### Resume commands

- Backend: `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v` with a writable `TEMP`/`TMPDIR`.
- Re-read current status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Recheck RDAP outbound controls and request bounds

### Completed in this stage

- Reviewed optional RDAP destination construction. Submitted URLs are never fetched; RDAP requests only use an HTTPS base from the IANA bootstrap response, reject credentials/nonstandard ports/IP literals, disable environment proxies, do not follow redirects, and bound response size and timeout. The adapter remains disabled unless configured and separately consented.
- Re-ran RDAP adapter and request-body-boundary tests. They use mocked external responses; no public registry request was made.
- No new defect was established in this focused review. A full network-level security review, including runtime DNS/egress behavior, remains outstanding.

### Checks actually run

- `python -m unittest tests.test_rdap_adapter tests.test_request_body_limit -v`: 13 passed.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run hosted CI and address actual Linux/Python 3.12 failures.
2. Verify deployment with PostgreSQL and Neo4j, including SSRF/egress controls, migrations, API flow, retention, backup/restore, and graph rebuild.
3. Complete independent security/privacy review and authorized time-separated evaluation.

### Resume commands

- Backend: set `APP_ENV=testing` and an isolated SQLite `DATABASE_URL`, then run `python -m unittest tests.test_rdap_adapter tests.test_request_body_limit -v`.
- For live verification, use a Docker/Linux host; do not enable RDAP without explicit consent and validated network egress policy.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Fix CI test upload isolation configuration

### Completed in this stage

- Reviewed the CI workflow against test module import order. Added an explicit workspace-local `UPLOAD_DIR` alongside the dedicated SQLite database path so settings initialized by earlier test imports still use the runner's disposable upload directory when `test_api_flow` is imported later.
- This CI setup detail reduces dependence on the integration test module's later environment mutation; the end-to-end suite still must run on the hosted runner to validate behavior.

### Checks actually run

- Parsed `.github/workflows/ci.yml` with PyYAML and asserted the backend, frontend, and Compose jobs plus the upload directory setting: passed.
- `docker compose config --quiet`: passed.
- GitHub-hosted workflow has not run; the CI tests are not yet verified on Linux.

### Files/components changed

- `.github/workflows/ci.yml`, `BUILD_STATUS.md`

### Next steps

1. Push the workflow and inspect hosted backend results, especially API-flow and proxy tests.
2. Add/run PostgreSQL-backed integration coverage for migrations and concurrency.
3. Complete live Compose/Neo4j, backup/restore, retention, security/privacy, and authorized-data evaluation checks.

### Resume commands

- From repository root, parse `.github/workflows/ci.yml` and run `docker compose config --quiet`.
- Hosted verification requires pushing to GitHub and reviewing Actions output; do not infer success from local parsing.
- Re-read this status and inspect Git status; do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Add Linux CI coverage for blocked integration tests

### Completed in this stage

- Added GitHub Actions CI jobs for the complete backend unittest suite on Python 3.12 (including API-flow and proxy-header tests), frontend production build and redaction tests on Node.js 22, and Compose configuration validation.
- Backend CI uses an isolated SQLite test database with `APP_ENV=testing`; it does not claim to verify PostgreSQL integration. The opt-in PostgreSQL provisioning test remains skipped unless separately configured.
- Documented the workflow and its status in README.

### Checks actually run

- Parsed `.github/workflows/ci.yml` locally with PyYAML: passed.
- `docker compose config --quiet`: passed.
- `./scripts/test-compose-config.ps1`: passed.
- Hosted GitHub Actions jobs have not run because no push/CI execution was initiated; no hosted results are claimed.

### Files/components changed

- `.github/workflows/ci.yml`, `README.md`, `BUILD_STATUS.md`

### Next steps

1. Push to a GitHub repository and inspect the workflow run; fix any Linux/Python 3.12 failures, especially API-flow and proxy tests.
2. Add or run a separate disposable PostgreSQL service integration job to verify migrations and concurrency against PostgreSQL.
3. Run Compose/Neo4j, backup/restore, retention and security reviews in a Docker-enabled environment; authorized evaluation data is still required.

### Resume commands

- Local preflight: parse `.github/workflows/ci.yml`, run supported backend tests, `pnpm run build`, `pnpm run test:redaction`, `docker compose config --quiet`.
- Hosted verification: push the workflow to GitHub and inspect its CI result; do not treat YAML parsing as a successful CI run.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Add offline migration history integrity checks

### Completed in this stage

- Inspected the Alembic configuration and migrations. Added offline tests that require exactly one deployment head, a reachable base, unique revision identifiers, and valid parent references.
- Confirmed current history has one head: `f19c7b2a8d45`.
- PostgreSQL offline SQL generation could not be checked in this local environment because the test dependency environment lacks the `psycopg` driver. No migration was applied and no PostgreSQL compatibility claim is made by the new graph tests.

### Checks actually run

- `python -m unittest tests.test_migration_graph -v`: 2 passed.
- `alembic heads`: one head reported.
- `alembic history --verbose`: history printed successfully.
- `alembic upgrade head --sql` with a PostgreSQL URL: failed before migration generation because `psycopg` is not installed in the local dependency cache. This environment is distinct from the Docker image, which pins backend requirements.
- `python -m compileall -q app tests evaluation`: passed.

### Files/components changed

- `backend/tests/test_migration_graph.py`, `BUILD_STATUS.md`

### Next steps

1. Generate/execute migrations against PostgreSQL in the Docker-enabled integration environment; validate upgrade on an empty DB and upgrade from the prior schema.
2. Run API-flow/proxy tests and full Compose health checks on a supported Linux/Python 3.12 host.
3. Continue live operations, authorized dataset evaluation, and independent security/privacy review.

### Resume commands

- Backend: `python -m unittest tests.test_migration_graph -v`.
- With Docker/PostgreSQL: bring up the stack and verify API migrations, then run the opt-in PostgreSQL migration/integration checks against a disposable database.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Recheck account provisioning and correction access controls

### Completed in this stage

- Reviewed the account/session security path: one-time investigator/reviewer provisioning is serialized through a database gate; JWT sessions bind to a persisted token version and active-account state; reviewer account changes revoke existing sessions.
- Re-ran focused tests for one-time role provisioning, correction request throttling and public correction status privacy. Public status responses use fixed neutral wording and do not disclose investigator notes.
- No defect was found in this focused review. It is not a substitute for the blocked end-to-end/API security review or external penetration testing.

### Checks actually run

- `python -m unittest tests.test_account_provisioning tests.test_correction_throttle tests.test_public_correction_status -v`: 8 passed.
- Compose configuration was rechecked after the README deployment instructions change: `docker compose config --quiet` passed.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run API-flow/proxy tests and live deployment checks from Linux/Python 3.12 with a Docker Engine.
2. Verify PostgreSQL/Neo4j integration, account/session flows, retention, graph rebuild, and backup/restore in a disposable environment.
3. Complete independent security/privacy review and authorized evaluation; no real-world evaluation metrics are available yet.

### Resume commands

- Backend: set `APP_ENV=testing` and isolated SQLite `DATABASE_URL`, then run `python -m unittest tests.test_account_provisioning tests.test_correction_throttle tests.test_public_correction_status -v`.
- Root: `docker compose config --quiet`; live checks require a Docker-enabled host.
- Re-read this status and inspect Git status; do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Clarify deployment readiness and troubleshooting steps

### Completed in this stage

- Updated local deployment instructions to wait for Compose health checks rather than opening the app immediately after build/start.
- Added explicit API liveness and PostgreSQL-backed readiness commands and clarified that Neo4j is a projection, not an API readiness dependency.
- Added service-log troubleshooting guidance and a warning not to remove named volumes as a diagnostic step.

### Checks actually run

- `docker compose config --quiet`: passed.
- `./scripts/test-compose-config.ps1`: passed.
- Live health endpoints were not called because Docker Engine is unavailable in this host environment.

### Files/components changed

- `README.md`, `BUILD_STATUS.md`

### Next steps

1. Run documented `docker compose up --build --wait --wait-timeout 180` and verify health on a Docker-enabled host.
2. Run API-flow/proxy tests in Linux/Python 3.12 and complete live PostgreSQL/Neo4j, retention, and backup/restore drills.
3. Complete independent security/privacy review and authorized dataset evaluation.

### Resume commands

- Repository root: `docker compose config --quiet`, `./scripts/test-compose-config.ps1`.
- Docker-enabled host: configure `.env`, run Compose wait command in README, inspect `docker compose ps` and service logs.
- Re-read this file and inspect Git status; do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Reconfirm supported suite and assess live-runtime availability

### Completed in this stage

- Re-read the latest status and checked available runtimes. Docker CLI is installed but cannot connect to `dockerDesktopLinuxEngine`; WSL returns `E_ACCESSDENIED`; no system Python installations are registered. Live Compose or Linux integration checks cannot be run from this host state.
- Re-ran the supported backend suite, production frontend build/redaction tests, and Compose configuration parser after recent changes.
- Confirmed remaining live verification and authorized-data requirements are environmental/data gates; no claims of end-to-end or production readiness are made.

### Checks actually run

- Supported backend suite excluding `test_api_flow` and `test_proxy_headers`: 102 passed, 1 opt-in PostgreSQL test skipped.
- `python -m compileall -q app tests evaluation`: passed.
- `pnpm run build`: passed.
- `pnpm run test:redaction`: 4 passed.
- `docker compose config --quiet`: passed.
- Runtime availability: Docker daemon unavailable; WSL denied; `py -0p` reported no installed Pythons.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run API-flow/proxy integration tests and live Compose service checks from an authorized Linux/Python 3.12 and Docker-enabled environment.
2. Complete live PostgreSQL/Neo4j workflows, restore drill, retention observation, and security/privacy review.
3. Obtain authorized time-separated dataset and run all prescribed comparisons; metrics remain pending.

### Resume commands

- Backend supported suite: set `APP_ENV=testing` and isolated SQLite `DATABASE_URL`, then run all test modules except `test_api_flow` and `test_proxy_headers`.
- Frontend: `pnpm run build` and `pnpm run test:redaction`.
- Docker-enabled host: `docker compose config --quiet`, then `docker compose up --build` with configured secrets and inspect health.
- Re-read this file and inspect Git status; do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Retry failed retention sweeps sooner

### Completed in this stage

- The worker previously updated its retention timer even after a failed purge, delaying the next cleanup attempt for 24 hours. Changed the schedule so successful sweeps remain daily and failed sweeps retry after one hour.
- Existing retention behavior deletes expired case content and associated audit rows, removes original private upload files, purges expired correction/source/reset/throttle records, and queues graph tombstones for deletion. The integration coverage for this workflow remains in `test_api_flow` and cannot currently execute in the local Windows Python 3.14 TestClient environment.

### Checks actually run

- `python -m compileall -q app tests evaluation`: passed.
- `python -m unittest tests.test_findings tests.test_restore_uploads -v`: 10 passed.
- No live retention sweep was run against PostgreSQL/Neo4j; the retention interval adjustment is source-verified but still needs runtime observation.

### Files/components changed

- `backend/app/worker.py`, `BUILD_STATUS.md`

### Next steps

1. Run `tests.test_api_flow` and verify retention in a Linux/Python 3.12 environment with isolated database fixtures.
2. Run Compose on Docker-enabled host and verify PostgreSQL/Neo4j, API/worker, graph tombstones, and backup/restore.
3. Complete authorized time-separated evaluation and independent security/privacy review.

### Resume commands

- Backend: `python -m unittest tests.test_findings tests.test_restore_uploads -v`.
- On supported Linux test host: `python -m unittest tests.test_api_flow -v`.
- Re-read current status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Recheck request limits, upload validation and privacy masking

### Completed in this stage

- Reviewed URL-fetch handling: arbitrary submitted job URLs are not automatically fetched. Optional RDAP is limited to extracted domains, disabled by default, consent-gated, and uses bounded HTTPS requests with redirects and ambient proxy configuration disabled.
- Re-ran focused security tests for request body limits, upload validation and privacy masking. The first invocation omitted the test-only SQLite environment and failed while loading the default PostgreSQL driver; rerunning with the documented test environment passed.
- No new security defect was established in this focused review. This source review and unit suite do not replace a live penetration test or deployment security review.

### Checks actually run

- `python -m unittest tests.test_request_body_limit tests.test_file_validation tests.test_privacy -v` with `APP_ENV=testing` and isolated SQLite URL: 26 passed.
- The same command without the test environment failed during module initialization because psycopg was unavailable locally; no tests ran successfully in that attempt.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run API flow and proxy tests in Linux/Python 3.12; Windows Python 3.14 blocks asyncio loop setup in the socketpair fallback.
2. Run a live Compose security/operations drill with PostgreSQL, Neo4j, API, worker and frontend, including backup/restore and graph rebuild.
3. Complete external security/privacy review and obtain authorized time-separated evaluation data; performance results remain pending.

### Resume commands

- Backend focused checks: set `APP_ENV=testing`, an isolated SQLite `DATABASE_URL`, and run `python -m unittest tests.test_request_body_limit tests.test_file_validation tests.test_privacy -v`.
- Re-read `BUILD_STATUS.md` and inspect Git status before continuing. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Verify backup orchestration and upload restore validation

### Completed in this stage

- Exercised the PowerShell backup orchestration harness. It verifies writes are stopped before capture, DB and private-upload artifacts receive a SHA-256 manifest, incomplete artifacts are removed on a simulated upload archive failure, and API/worker restart plus health wait is attempted in the finally path.
- Exercised the upload archive restore validator and private storage tests. These cover accepted opaque regular files, rejection paths, and restricted storage permissions.
- These checks use a fake Docker CLI and synthetic archive data; a real PostgreSQL dump, Docker volume restore, API/worker recovery, and Neo4j rebuild are still not verified.

### Checks actually run

- `./scripts/test-backup.ps1`: passed orchestration and failure-cleanup checks with fake Docker.
- `python -m unittest tests.test_restore_uploads tests.test_private_storage -v`: 6 passed.
- One initial test invocation from repository root used the backend-relative venv path and did not run; reran successfully from `backend`.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. On Docker-enabled host, execute a full backup and restore drill on disposable deployment data and verify API/worker health and Neo4j graph rebuild.
2. Run API flow and proxy tests in Linux/Python 3.12; current Windows Python 3.14 blocks event-loop creation in socketpair fallback.
3. Complete live security/privacy review and authorized evaluation data collection; evaluation metrics remain pending.

### Resume commands

- Repository root: `./scripts/test-backup.ps1`.
- Backend: `python -m unittest tests.test_restore_uploads tests.test_private_storage -v`.
- Live drill only on disposable data: follow README backup/restore commands after configuring Compose secrets and starting Docker Engine.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Verify reproducible evaluation tooling

### Completed in this stage

- Exercised the time-separated scorer, TF-IDF/logistic baseline, and LLM/web-search adapter runner/comparator through their automated tests. Coverage verifies train-only fitting, prediction schema, lawful-access attestation, source snapshot provenance, missing-provenance rejection, test-only adapter calls, measured latency recording, and four-way comparison validation.
- Evaluation tooling is usable for an appropriately authorized dataset, but there is no authorized real-world Indian recruitment-scam corpus in the workspace; no performance result is claimed.

### Checks actually run

- `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v`: 15 passed.
- Existing wider supported suite remains 102 passed and one opt-in PostgreSQL check skipped (see prior entry); not rerun in this stage.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Obtain or prepare an authorized, consented, redacted, annotated time-separated dataset under the documented protocol; run four comparisons and report confidence intervals and exclusions.
2. Verify API flow and proxy-header tests in a Linux/Python 3.12 runtime; Windows Python 3.14 blocks asyncio event-loop creation in socketpair fallback.
3. Run full Compose deployment and operational exercises when Docker Engine is available, including PostgreSQL/Neo4j health, graph rebuild, retention, and backup/restore.
4. Close remaining security/privacy review items described in `ENGINEERING_WALKTHROUGH.md`.

### Resume commands

- From `backend`, run `python -m unittest tests.test_evaluation tests.test_baseline_tfidf_logreg tests.test_llm_web_search_eval -v`.
- For real evaluation, follow `backend/evaluation/README.md`; keep authorized dataset material out of Git.
- Re-read this file and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Identify Windows asyncio socket-pair test blocker

### Completed in this stage

- Ran the proxy-header test under `faulthandler.dump_traceback_later`. The hang occurs during `asyncio.run()` event-loop construction in Python 3.14 on Windows, at `socket._fallback_socketpair()` waiting in `socket.accept()`, before ASGI middleware or endpoint code is invoked.
- Tried HTTPX `ASGITransport` and an async endpoint; the same event-loop constructor hang occurred. Reverted that unsuccessful test rewrite, preserving the original TestClient test logic.
- This is an environment-specific inability to execute the async test here, not evidence the proxy behavior passes or fails.

### Checks actually run

- `tests.test_proxy_headers` with faulthandler: confirmed stack location in Windows Proactor event-loop socket-pair fallback; test did not execute and was interrupted.
- No proxy-header pass is claimed.

### Files/components changed

- `BUILD_STATUS.md`

### Next steps

1. Run `tests.test_proxy_headers` and `tests.test_api_flow` in Linux/Python 3.12 or another supported socketpair-capable environment.
2. Resume operational verification with a running Docker Engine: Compose health, PostgreSQL and Neo4j connectivity, worker retries, graph rebuild, retention, backup/restore.
3. Finish authorized time-separated evaluation and remaining security/privacy review listed in `ENGINEERING_WALKTHROUGH.md`.

### Resume commands

- Backend: `python -m unittest tests.test_proxy_headers -v` and `python -m unittest tests.test_api_flow -v` in a Linux/Python 3.12 environment with the test dependencies installed.
- Root: `docker compose config --quiet`; with Docker and `.env` configured, `docker compose up --build` and check health endpoints.
- Re-read this status and inspect Git status. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Rework proxy-header test transport

### Completed in this stage

- Replaced Starlette `TestClient` in `backend/tests/test_proxy_headers.py` with HTTPX `ASGITransport` to avoid the TestClient portal socket-pair startup path that hangs on this Windows Python 3.14 environment.
- Changed the small test endpoint to async to avoid AnyIO thread-pool startup in that platform-sensitive test.
- The test still hangs on its first request under the current runtime; interrupting it exits cleanly. This means the proposed transport change did not resolve the environment-specific issue and is not accepted as verified.

### Checks actually run

- `python -m unittest tests.test_proxy_headers -v` before the edit: stalled on first test; interrupted after 30 seconds.
- Same command after switching to HTTPX ASGITransport and async endpoint: also stalled on first test; interrupted after 10 seconds.
- No successful proxy-header check is claimed. The supported backend suite and config results are in the prior entry.

### Files/components changed

- `backend/tests/test_proxy_headers.py`, `BUILD_STATUS.md`

### Next steps

1. Diagnose the ASGITransport hang with faulthandler / minimal repro; either fix the test mechanism or restore the original test and document the platform block.
2. Run API flow and proxy tests on Linux/Docker or another supported Python runtime when available.
3. Continue deployment, backup/restore, privacy/security and authorized time-separated evaluation work.

### Resume commands

- From backend, run `python -m unittest tests.test_proxy_headers -v` with the configured test environment; currently it hangs on this Windows Python 3.14 runtime.
- Inspect `backend/tests/test_proxy_headers.py` and `BUILD_STATUS.md` before changing the harness further. Do not commit unless requested.
## 2026-10-25 (Asia/Kolkata) — Enforce PostgreSQL for runtime services

### Completed in this stage

- Added a database backend guard to API startup and worker startup: PostgreSQL is required for runtime; SQLite is accepted only under `APP_ENV=testing` for the test harness.
- Added configuration coverage for PostgreSQL acceptance, test-only SQLite, non-PostgreSQL rejection and safe error text.
- The first test run exposed a malformed `validate_web_origin` function: its URL rejection conditions were accidentally located in `validate_database_url`, causing 14 origin assertions to fail and the SQLite test path to crash. Restored the origin validation to its own function and reran checks successfully.
- Documented the runtime database requirement in README.

### Checks actually run

- `python -m unittest tests.test_config -v`: 8 passed.
- Supported backend suite excluding `test_api_flow` and `test_proxy_headers`: 102 passed, 1 opt-in PostgreSQL test skipped.
- `python -m compileall -q app tests evaluation`: passed.
- `docker compose config --quiet`: passed.
- `./scripts/test-compose-config.ps1`: passed from the repository root.
- API startup, worker startup, API-flow and proxy-header checks remain unverified against a live PostgreSQL service; Docker Engine is unavailable here.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/app/worker.py`, `backend/tests/test_config.py`, `backend/tests/test_api_flow.py`, `README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. On a Docker-enabled host, run the Compose stack with valid secrets and verify PostgreSQL, Neo4j, API, worker and frontend health.
2. Run `tests.test_api_flow` and `tests.test_proxy_headers` in a socketpair-capable runtime against an isolated test database; the Windows Python 3.14 TestClient startup currently hangs before lifespan.
3. Continue the outstanding deployment, backup/restore, privacy/security and authorized time-separated evaluation work listed in `ENGINEERING_WALKTHROUGH.md`.

### Resume commands

- From the backend directory, run `python -m unittest tests.test_config -v`, then run the supported suite excluding `test_api_flow` and `test_proxy_headers` as described in this entry.
- From the repository root, run `docker compose config --quiet` and `./scripts/test-compose-config.ps1`.
- Re-read this file and `BUILD_PLAN.md`, inspect Git status, and do not commit unless requested.
## 2026-10-23 (Asia/Kolkata) — Add repeatable Compose environment regression check

### Completed in this stage

- Added `scripts/test-compose-config.ps1`, which temporarily overrides and restores process-level synthetic environment values, renders Compose without requiring a daemon, checks that API and worker database URLs derive from `POSTGRES_*`, and verifies the API receives all three correction throttle overrides.
- The script also prevents regression to a hard-coded `DATABASE_URL` in `.env.example`.
- Documented the command in README and the engineering walkthrough.

### Checks actually run

- `./scripts/test-compose-config.ps1` passed with deliberately conflicting inherited values; it rendered the expected synthetic configuration and restored the original process environment. It uses no temporary files.
- This verifies rendered configuration only; it does not verify container startup, health or database connectivity.

### Files/components changed

- `scripts/test-compose-config.ps1`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the Compose stack on a host with an active Docker Engine and verify API, worker, PostgreSQL, Neo4j and web health.
2. Run API-flow and proxy-header tests in a socketpair-capable runtime.

### Resume commands

- From the repository root, run `./scripts/test-compose-config.ps1`; then, on a Docker-enabled host with `.env` configured, run `docker compose up --build` and inspect health/logs.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Pass correction throttle settings to the API container

### Completed in this stage

- Added `CORRECTION_MAX_REQUESTS`, `CORRECTION_WINDOW_SECONDS`, and `CORRECTION_LOCKOUT_SECONDS` to the API service environment in Compose. These values were documented in `.env.example` and read by the API, but were not previously passed into the container, so deployment overrides silently fell back to defaults.

### Checks actually run

- Rendered Compose using synthetic throttle values and verified the API container receives all three configured values.
- `docker compose config --quiet` passed.
- Docker Engine remains unavailable; service startup and the effective runtime throttle could not be exercised.

### Files/components changed

- `docker-compose.yml`, `BUILD_STATUS.md`

### Next steps

1. Run Compose on a host with a working Docker Engine and verify environment values inside the API container plus service health.
2. Continue API-flow, PostgreSQL/Neo4j, backup/restore, hosted deployment, and authorized evaluation checks.

### Resume commands

- From the repository root, copy `.env.example` to `.env`, set secrets and any `CORRECTION_*` overrides, then run `docker compose config --quiet` and `docker compose up --build`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Let Compose derive DATABASE_URL from database settings

### Completed in this stage

- Removed the redundant placeholder `DATABASE_URL` from `.env.example`. Previously, it overrode Compose's fallback, so changing only `POSTGRES_PASSWORD` left API and worker credentials stale.
- Clarified README guidance: leave `DATABASE_URL` unset for the normal Compose network; set it explicitly only for a different target or a URL-encoded password containing reserved characters.

### Checks actually run

- Rendered Compose config with `.env.example` plus synthetic `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values. Verified both API and worker receive the exact derived URL.
- `docker compose config --quiet` passed.
- Docker Engine remains unavailable, so no containers were started and database connectivity was not checked.

### Files/components changed

- `.env.example`, `README.md`, `BUILD_STATUS.md`

### Next steps

1. Start Docker Desktop/Engine in a runtime that allows the daemon to run; then bring up Compose and verify API, worker, PostgreSQL, Neo4j and frontend health.
2. Run API-flow and proxy-header tests in a socketpair-capable runtime.

### Resume commands

- From the repository root, copy `.env.example` to `.env`, fill the secrets and distinct bootstrap codes, leave `DATABASE_URL` unset, then run `docker compose config --quiet` and `docker compose up --build`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Validate access-token lifetime and web origin

### Completed in this stage

- Added startup validation that access-token lifetime is between 1 and 1,440 minutes.
- Added canonical-origin validation for `WEB_ORIGIN`: only lowercase HTTP(S) origins with an ASCII hostname and without credentials, a path (including a trailing slash), query, fragment, wildcard, explicit default port or invalid port are accepted. This avoids CORS configuration that appears valid but cannot match browser Origin headers.
- Added configuration tests covering supported values and representative invalid values.
- Documented both requirements in README and the engineering walkthrough.

### Checks actually run

- Supported non-`TestClient` suite: **100 tests ran, 99 passed, one opt-in PostgreSQL test skipped as designed**, across 18 modules.
- `tests.test_config`: **6 tests passed**.
- `python -m compileall -q app tests evaluation` passed.
- `pnpm run build` passed; `pnpm run test:redaction` passed all **4 tests**; `docker compose config --quiet` passed.
- Refreshed focused backend run: **12 configuration/correction tests passed**. Full suite count above is from this checkpoint.
- Docker Desktop reported not running. `docker desktop start` did not create a Docker process or the `dockerDesktopLinuxEngine` pipe and remained silent for over 85 seconds; the stalled CLI command was interrupted. Live containers remain unavailable.
- API lifespan startup remains unverified due to the local Windows socket-pair startup failure.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_config.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the API-flow and proxy-header suites in a socketpair-capable runtime.
2. Continue live PostgreSQL/Neo4j, backup/restore, hosted deployment, and authorized evaluation checks.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated `DATABASE_URL`, `JWT_SECRET`, distinct 32-character bootstrap codes, a valid `WEB_ORIGIN`, and workspace-local `TEMP`/`TMP`; run `python -m unittest tests.test_config -v`, the supported suite, then `python -m compileall -q app tests evaluation`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Require distinct strong bootstrap codes

### Completed in this stage

- Added startup validation requiring investigator and reviewer bootstrap codes to be different and at least 32 characters each. This closes a role-separation gap where one secret could provision both privileged roles.
- Updated the API-flow fixture to use distinct synthetic codes meeting the startup policy.
- Documented the code requirements in README and the engineering walkthrough.

### Checks actually run

- Supported non-`TestClient` suite: **98 tests ran, 97 passed, and one opt-in PostgreSQL test skipped as designed**, across 18 modules.
- `tests.test_config`: **4 tests passed**, including distinctness and minimum-length cases.
- `python -m compileall -q app tests evaluation` passed.
- API lifespan startup and the full API-flow suite remain unverified because the Windows socket-pair fallback prevents TestClient from entering the app lifespan.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_config.py`, `backend/tests/test_api_flow.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the API-flow and proxy suites in a socketpair-capable environment to verify startup and routing.
2. Continue live PostgreSQL/Neo4j, backup/restore, hosted deployment, and authorized evaluation checks.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated `DATABASE_URL`, `JWT_SECRET`, distinct 32-character bootstrap codes, and workspace-local `TEMP`/`TMP`; run `python -m unittest tests.test_config -v`, the supported suite, then `python -m compileall -q app tests evaluation`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Validate correction throttling settings before API startup

### Completed in this stage

- Added startup validation for the new correction request count, time window and lockout duration. Nonpositive values now fail API startup with a clear configuration error rather than silently disabling or inverting the throttle.
- Added config unit tests for valid defaults and every nonpositive field.
- Re-ran the supported suite after the new handler tests and configuration checks.

### Checks actually run

- Supported non-`TestClient` suite: **96 tests ran, 95 passed, one opt-in PostgreSQL test skipped as designed**, across 18 modules.
- Eight focused correction-handler, privacy, throttle and configuration tests passed.
- `python -m compileall -q app tests evaluation` passed.
- Full HTTP transport remains unverified. The faulthandler trace shows the test runtime blocks before application startup in the Windows socket-pair fallback.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_config.py`, `backend/tests/test_correction_throttle.py`, `backend/tests/test_public_correction_status.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run API-flow and proxy-header tests in a socketpair-capable runtime.
2. Continue isolated PostgreSQL/Neo4j verification, hosted deployment checks, and authorized evaluation.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated `DATABASE_URL`, `JWT_SECRET`, and workspace-local `TEMP`/`TMP`; run the supported test set (all `tests.test_*` modules except `test_api_flow` and `test_proxy_headers`), then compile with `python -m compileall -q app tests evaluation`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Diagnose API test transport and cover correction handlers directly

### Completed in this stage

- Reproduced the correction TestClient hang with `faulthandler`. The stack is blocked before FastAPI lifespan or request handling: Starlette enters AnyIO's blocking portal, Python 3.14 creates the Windows Proactor loop, and `_fallback_socketpair()` blocks in `socket.accept()`.
- Confirmed that switching to Windows `SelectorEventLoop` does not bypass this workspace limitation; its self-pipe setup calls the same blocked `socket.socketpair()` fallback.
- Added direct handler tests that bypass the failing HTTP test transport. They exercise correction intake persistence and 429 rejection, token validation, and omission of investigator free-text notes from the public status response.
- Updated the engineering record to distinguish direct handler coverage from unverified ASGI/HTTP transport behavior.

### Checks actually run

- Supported non-`TestClient` suite: **94 tests ran, 93 passed, one opt-in PostgreSQL test skipped as designed**, across 17 modules.
- Six focused correction handler/privacy/throttle tests passed.
- `python -m compileall -q app tests evaluation` passed.
- A 12-second `faulthandler` diagnostic produced the Windows event-loop stack above. The test was then interrupted; no HTTP endpoint result is claimed.

### Files/components changed

- `backend/tests/test_correction_throttle.py`, `backend/tests/test_public_correction_status.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run `test_api_flow.py` and `test_proxy_headers.py` on Linux or another runtime with a functioning socket-pair implementation to verify ASGI routing and middleware.
2. Continue isolated PostgreSQL/Neo4j integration and deployment checks; local SQLite handler tests do not establish PostgreSQL locking or production behavior.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated `DATABASE_URL`, `JWT_SECRET`, and workspace-local `TEMP`/`TMP`; run `python -m unittest tests.test_correction_throttle tests.test_public_correction_status -v` and the supported suite. Use a socketpair-capable runtime for `python -m unittest -v tests.test_api_flow tests.test_proxy_headers`.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Throttle public correction submissions

### Completed in this stage

- Added a configurable persisted per-client throttle to public correction intake using the existing `login_throttles` table. The HMAC fingerprint includes a separate correction scope; raw client addresses are not persisted.
- Default limit is 10 submission attempts per 15-minute window followed by a 15-minute lockout. Added `CORRECTION_MAX_REQUESTS`, `CORRECTION_WINDOW_SECONDS`, and `CORRECTION_LOCKOUT_SECONDS` settings to the environment example and operating documentation.
- Added SQLite unit coverage for allowed submissions, lockout duration, window reset, and hashed address storage. Added an API-flow regression assertion for 429 behavior; that suite remains unverified in this runtime.

### Checks actually run

- Supported non-`TestClient` suite at this checkpoint: **92 tests ran, 91 passed, and one opt-in PostgreSQL test skipped as designed**, across 17 modules.
- Four focused tests for public status privacy and correction throttling passed at this checkpoint; direct route-handler assertions were added in the following checkpoint.
- `python -m compileall -q app tests evaluation` passed.
- The API-flow assertion and live PostgreSQL throttle behavior were not run; Docker Engine is unavailable, and the TestClient correction flow previously stalled in this Windows workspace.

### Files/components changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_correction_throttle.py`, `backend/tests/test_api_flow.py`, `.env.example`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the API-flow and proxy-header suites in a socketpair-capable runtime, including the public correction 429 regression.
2. Verify concurrent throttle updates against PostgreSQL using isolated integration tests.
3. Continue live graph, OCR, backup/restore, hosted deployment, and authorized evaluation checks listed in the walkthrough.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated SQLite `DATABASE_URL`, `JWT_SECRET`, and workspace-local `TEMP`/`TMP`; run `python -m unittest tests.test_correction_throttle tests.test_public_correction_status -v` and the supported suite. In a socketpair-capable runtime run `python -m unittest -v tests.test_api_flow tests.test_proxy_headers`.
- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Keep investigator resolution notes out of public appeal status

### Completed in this stage

- Changed public correction-status lookup to serialize only an allowlisted status and fixed status-specific message. Investigator-authored resolution notes are not included; pattern masking cannot safely detect arbitrary names or copied evidence.
- Updated the requester UI, correction-flow regression assertions, README privacy note, and engineering walkthrough.
- Added focused unit tests for the public response contract, including names and identifier-like values in private notes and an unknown legacy status value.

### Checks actually run

- `tests.test_public_correction_status`: **2 tests passed**.
- `python -m compileall -q app tests evaluation` passed.
- `pnpm run build` passed, including the requester status UI.
- The targeted end-to-end correction TestClient test produced no output for about two minutes and was interrupted. It is **not verified**; no API routing result is claimed.

### Files/components changed

- `backend/app/main.py`, `backend/app/public_status.py`, `backend/tests/test_public_correction_status.py`, `backend/tests/test_api_flow.py`, `frontend/src/App.tsx`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known gaps and exact next steps

1. Run `tests.test_api_flow.CaseFlowTests.test_public_correction_request_can_be_reviewed_by_investigator` in a Linux/socketpair-capable test runtime and confirm the public status response omits the private resolution field.
2. Run the supported backend suite including the new unit module, then the full API-flow/proxy suites in that runtime.
3. Continue the pending live PostgreSQL/Neo4j, OCR, backup/restore, hosted deployment, and authorized evaluation checks listed in `ENGINEERING_WALKTHROUGH.md`.

### Resume commands

- From `backend`, configure the isolated SQLite test environment described in the preceding status entry and run `python -m unittest tests.test_public_correction_status -v` plus the supported suite. In a socketpair-capable runtime, run `python -m unittest tests.test_api_flow.CaseFlowTests.test_public_correction_request_can_be_reviewed_by_investigator -v`.
- Re-read `BUILD_STATUS.md`, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add opt-in PostgreSQL provisioning race check

### Completed in this stage

- Added an opt-in PostgreSQL-only concurrency test for simultaneous first-investigator claims and simultaneous one-time reviewer claims.
- The check refuses a database name without `_test`, requires an empty `users` table and the migrated provisioning gate, uses synthetic accounts and distinct client addresses, and removes its test accounts/throttle rows afterward. The provisioning generation counter remains advanced as documented.
- Documented setup and cleanup behavior in README so operators can run the check against an isolated database.

### Checks actually run

- Supported suite: **88 tests ran, 87 passed and the opt-in PostgreSQL concurrency test skipped as designed**, across 16 modules. The API-flow and proxy-header modules remain excluded because of the local socketpair restriction.
- `python -m compileall -q app tests evaluation` passed.
- The opt-in test was not executed against PostgreSQL because Docker Engine and an isolated PostgreSQL test database are unavailable here.

### Files/components changed

- `backend/tests/test_postgres_account_provisioning.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the opt-in concurrency check against an empty, migrated PostgreSQL database whose name ends in `_test`.
2. Continue live API, graph, OCR, backup/restore, hosted deployment and authorized evaluation verification.

### Resume commands

- From `backend`, set `RSAICDP_PROVISIONING_TEST_DATABASE_URL` and `DATABASE_URL` to the same isolated PostgreSQL test database, run `python -m alembic upgrade head`, then `python -m unittest tests.test_postgres_account_provisioning -v`.
- Re-read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Serialize privileged account setup

### Completed in this stage

- Added a singleton database provisioning gate. Registration increments it inside the same transaction before deciding whether to create the initial investigator or one-time reviewer; row updates serialize concurrent registrations. Duplicate email is rechecked after acquiring the gate.
- Added migration `f19c7b2a8d45` to create and seed the singleton row. Registration fails closed with 503 if the required row is absent.
- Added direct route tests for one-time investigator/reviewer setup, rejection of a second reviewer, generation updates and missing-gate behavior.

### Checks actually run

- **87 supported backend tests passed** across 15 test modules. `test_api_flow.py` and `test_proxy_headers.py` remain excluded because their TestClient/event-loop setup cannot create the required socketpair in this workspace.
- A fresh SQLite migration reached the single head `f19c7b2a8d45`; the migration seeded row `(id=1, generation=0)`, and `alembic check` reported no schema drift.
- `python -m compileall -q app tests evaluation` passed.
- Live PostgreSQL concurrent-registration behavior was not exercised; Docker Engine remains unavailable.

### Files/components changed

- `backend/app/models.py`, `backend/app/main.py`, `backend/migrations/versions/f19c7b2a8d45_account_provisioning_gate.py`, `backend/tests/test_account_provisioning.py`, `README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run concurrent signup tests against PostgreSQL to verify simultaneous first-investigator and reviewer provisioning attempts serialize correctly.
2. Run the API-flow/proxy integration suites and live end-to-end workflows in a Docker/Linux or socketpair-capable runtime.
3. Continue remaining graph, privacy/security, OCR, backup/restore, hosted deployment and authorized evaluation verification.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, isolated `DATABASE_URL`, `JWT_SECRET`, and workspace-local `UPLOAD_DIR`; run `python -m unittest tests.test_account_provisioning -v`, the supported suite, and `python -m alembic upgrade head` plus `python -m alembic check` against a fresh disposable SQLite database.
- Re-read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add pre-submission text redaction control

### Completed in this stage

- Added a pasted-text redaction action to the case intake form. A submitter selects a text span and replaces it with `[REDACTED BY SUBMITTER]` before submission.
- Cleared the saved selection range when the source text changes, disabled the action until a non-empty range is selected, and explained that redacted material cannot be extracted.
- Extracted the replacement operation into a pure helper and added dependency-free Node tests for middle/start/end selection, supplementary Unicode characters, and invalid or empty ranges.
- Documented that image and PDF redaction must happen locally before upload because the intake does not edit binary files.

### Checks actually run

- `pnpm run build` passed (`tsc -b && vite build`).
- `pnpm run test:redaction` passed: **4 tests passed** using Node's built-in test runner.
- Started Vite, but the in-app browser timed out on `http://localhost:5173`; a direct `Invoke-WebRequest` to `127.0.0.1:5173` was denied by workspace socket permissions. Stopped the Vite process after confirming the restriction.
- The selection event wiring and API submission behavior have not been exercised in a browser. Unit tests prove replacement logic; they do not prove the UI event flow or submitted payload.
- Backend code was not changed in this stage. Earlier supported-backend test results remain recorded below; they were not rerun for this frontend-only change.

### Files/components changed

- `frontend/src/App.tsx`, `frontend/src/style.css`, `frontend/src/text-redaction.ts`, `frontend/tests/text-redaction.test.ts`, `frontend/package.json`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. In a browser runtime with local network access, verify keyboard and mouse selection, replacement of middle/start/end spans, and that the API receives only the redacted text.
2. Continue the graph live-infrastructure and remaining privacy/security, OCR, backup/restore, hosted deployment and authorized evaluation checks below.

### Resume commands

- From `frontend`, run `pnpm run test:redaction` and `pnpm run build` (the test script uses Node.js 22.6+ built-in TypeScript stripping).
- Re-read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add evidence provenance and explainable campaign edges to graph

### Completed in this stage

- Extended the graph projection and PostgreSQL fallback with evidence nodes, case-to-evidence links, and evidence-to-identifier links. Evidence nodes retain source category, minimized source reference, outcome, authority, retrieval timestamp and review status; stable evidence handles are hashed.
- Added investigator graph filters for entity type, source category, evidence retrieval date and review status, plus node inspectors that show graph relationships and open the authoritative case view for full evidence inspection.
- Preserved campaign link strength and rule version in both Neo4j and PostgreSQL-derived graph edges. The graph now names connected nodes using their masked display labels and shows score, review state, rule version and redacted reasons in the relationship inspector.
- Removed free-text source names, claims, excerpts, review rationales and case titles from graph responses and Neo4j projection. Incremental case synchronization explicitly removes legacy text properties and recreates evidence nodes from safe metadata.
- Updated README and the point-by-point engineering walkthrough to describe the current graph scope and privacy boundary.

### Checks actually run

- `python -m unittest tests.test_file_validation -v`: **9 tests passed**, including graph evidence provenance, campaign-edge score/version, fingerprint linking, masked references, PostgreSQL-fallback graph payload privacy and assertions that projection Cypher omits free-text properties.
- **85 supported backend tests passed** across 14 test modules. The API-flow and proxy-header integration suites were excluded because this workspace's Windows socketpair limitation prevents their TestClient/event-loop setup.
- `python -m compileall -q app tests evaluation` passed.
- `pnpm run build` passed (`tsc -b && vite build`).
- `docker compose config --quiet` passed; a trailing-whitespace scan passed for the eight stage files.
- Docker CLI could not connect to the Docker Desktop Linux engine. Live Neo4j projection, hosted PostgreSQL fallback API route, graph browser interaction, and end-to-end case navigation remain unverified; local API sockets are restricted.

### Files/components changed

- `backend/app/graph_store.py`, `backend/app/graph_rebuild.py`, `backend/app/main.py`, `backend/tests/test_file_validation.py`, `frontend/src/App.tsx`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. In a Docker/Linux or socketpair-capable runtime, run the API-flow and proxy-header suites and verify graph filters, masked edge evidence and case navigation against persisted synthetic records.
2. Exercise Neo4j graph projection, legacy-field removal, graph rebuild and PostgreSQL fallback with live PostgreSQL and Neo4j services.
3. Continue the outstanding privacy/security, OCR, backup/restore, hosted deployment and authorized evaluation checks listed below.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, an isolated SQLite `DATABASE_URL`, `JWT_SECRET`, and workspace-local `UPLOAD_DIR`; run `python -m unittest tests.test_file_validation -v`, `python -m compileall -q app tests evaluation`, then the remaining supported test modules. API flow and proxy-header integration tests require a runtime with socketpair support.
- From `frontend`, run `pnpm run build`.
- Re-read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add bank/payment identifier extraction and safe campaign linking

### Completed in this stage

- Added deterministic IFSC-shape extraction and bank-account extraction only when a clear account label is present. Account identifiers are normalized to digits; the phone parser skips overlapping labeled account spans to avoid creating a duplicate phone candidate.
- Added both identifier types to the local-corpus intake schema and investigator UI. Bank accounts can support exact source checks and exact-reuse campaign links; IFSC codes remain evidence candidates but are excluded from campaign matching because they identify shared branches.
- Added bank-account reuse as a 40-point exact campaign signal and advanced the campaign rule version to `campaign-signals-v3`; historical v2 links retain their stored rule versions. Updated the API integration assertions for the new version.
- Confirmed the existing fail-closed identifier masking covers both bank account and IFSC in graph/report displays; added explicit regression coverage.
- Updated README and engineering documentation to explain the extraction constraints, sensitivity and linking policy.

### Checks actually run

- **31 focused tests passed** across extraction, campaign rules, privacy and request schemas.
- **81 supported backend tests passed**; this excludes `test_api_flow.py` and `test_proxy_headers.py`, whose `TestClient`/asyncio setup is blocked by this workspace's socketpair restriction.
- `python -m compileall -q app tests evaluation` passed.
- Frontend production build passed (`tsc -b && vite build`, via pnpm 11.25.0).
- PowerShell parsing, `docker compose config --quiet`, and `git diff --check` passed.
- No live PostgreSQL, Neo4j, browser, OCR, or deployment checks were possible; no production or real-person data was used.

### Files/components changed

- `backend/app/extract.py`, `backend/app/campaign_rules.py`, `backend/app/schemas.py`, extraction/campaign/privacy/schema tests, `backend/tests/test_api_flow.py`, `frontend/src/App.tsx`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the API workflow and proxy tests in a runtime with socketpair support; verify saved corpus records and campaign v3 links end to end.
2. Verify bank-account masking in an actual browser/report and graph projection on PostgreSQL/Neo4j.
3. Continue live infrastructure, privacy/security and authorized evaluation checks listed below.

### Resume commands

- From `backend`, use a new workspace-local temp directory, `PYTHONPATH=.pydeps`, isolated SQLite `DATABASE_URL`, and the documented test environment; run all 81 supported tests (excluding the two socket-dependent suites), then `python -m compileall -q app tests evaluation`.
- From `frontend`, run `pnpm run build`.
- Re-read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Document dependency baseline and diagnose ASGI test stall

### Completed in this stage

- Documented the repository's configured runtime targets: Python 3.12 and pinned backend requirements; Node.js 22 and pnpm 11.25.0 with a frozen lockfile; PostgreSQL 16, Neo4j 5, Nginx 1.27, and Caddy 2.
- Clarified that service image tags permit upstream patch updates and that production operators should pin reviewed image digests.
- Diagnosed the local API integration-test stall with `faulthandler`: the Python 3.14 Windows Proactor event loop blocks while creating its internal self-pipe through `socket._fallback_socketpair`/`socket.accept`, before entering FastAPI lifespan. This workspace denies local socket access, so the in-process ASGI attempt cannot execute here either.

### Checks actually run

- `python -c "import app.main"` passed with the configured isolated SQLite environment.
- A fresh SQLite `python -m alembic upgrade head` passed.
- API/ASGI integration did not pass: the focused run stalled before lifespan/request dispatch and was stopped after the traceback established the sandbox socketpair block. No API journey pass is claimed.
- Documentation changes passed `git diff --check`.

### Files/components changed

- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run `test_api_flow.py` and `test_proxy_headers.py` in a runtime that permits Windows event-loop socketpair operations or a Docker/Linux test environment.
2. Perform live PostgreSQL/Neo4j, browser, OCR, TLS, and backup/restore verification when Docker Engine or another permitted deployment runtime is available.
3. Continue the privacy/security and operational review; run authorized time-separated evaluation only after approved data is available.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, workspace-local `TEMP`/`TMP`, a fresh SQLite `DATABASE_URL`, `JWT_SECRET`, and upload path; run the 81 supported backend tests. The API-flow and proxy-header suites require a runtime with socketpair support.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status before editing.

## 2026-10-23 (Asia/Kolkata) — Make paired backups consistent and failure-recoverable

### Completed in this stage

- Backup now stops API and worker writes before creating the PostgreSQL dump and upload archive, so the pair is captured within one maintenance window.
- Captures upload files in a uniquely named one-off worker container sharing the private volume; it writes the checksum manifest only after both artifacts are present.
- Uses collision-resistant timestamped output names, removes incomplete local artifacts on failure, and restarts API/worker in `finally` with a 120-second health wait.
- Restore now also waits up to 120 seconds for API/worker health before rebuilding Neo4j.
- Added `scripts/test-backup.ps1`, a repeatable fake-Docker orchestration check for capture order, checksum rows, cleanup after a simulated failure, and service restart.
- Documented the brief backup maintenance window and separated mock orchestration evidence from the still-required live Docker drill.

### Checks actually run

- `scripts/test-backup.ps1` passed, including a successful mocked backup and an injected archive-command failure.
- PowerShell parser accepted `scripts/backup.ps1`, `scripts/restore.ps1`, and `scripts/test-backup.ps1`.
- `docker compose config --quiet` and `git diff --check` passed.
- Docker Compose CLI is v5.5.1, but Docker Engine is unavailable; no real service stop/start, PostgreSQL dump, named-volume archive, or restore ran.

### Files/components changed

- `scripts/backup.ps1`, `scripts/restore.ps1`, `scripts/test-backup.ps1`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run the live Compose backup/restore drill with disposable cases and uploads when Docker Engine is available; verify checksums, linked file recovery, health checks, and graph rebuild.
2. Run PostgreSQL persistence/migration tests and API/worker end-to-end workflows on a permitted runtime.
3. Continue outstanding deployment, security, OCR, Neo4j, and authorized evaluation verification from the prior checkpoints.

### Resume commands

- Without Docker, rerun `./scripts/test-backup.ps1`, PowerShell parse checks, and `docker compose config --quiet` to validate script flow/configuration only.
- With Docker Engine, run `./scripts/backup.ps1` to a protected scratch location, then restore the same dump/archive/manifest with `-ConfirmRestore`; verify API/worker health, case-to-upload links, and `python -m app.graph_rebuild`.
- Read this status file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Harden private-upload restore archive handling

### Completed in this stage

- Replaced direct GNU tar extraction in `restore.ps1` with `app.restore_uploads`, which stages and validates archive members before replacing the active upload set.
- Verified that Windows `bsdtar` running `tar -czf archive -C source .` emits the expected `./` root plus `./<opaque-file>` layout, and that the restore validator restores a synthetic upload from that actual archive with matching bytes. The host has `bsdtar`, not GNU tar; the worker-container GNU tar output is therefore not directly verified here.
- Renamed the synthetic tar-layout test so it does not imply that Python's `tarfile` generated a GNU tar archive.
- Restore accepts only regular flat files with the 48-hex-character opaque names generated by case intake and supported file extensions; it rejects traversal paths, symlinks/special entries, duplicate names, empty entries, and files above `MAX_UPLOAD_BYTES`.
- Restored files are created with owner-only mode, the upload directory is set to `0700` on POSIX, and services stay in maintenance mode until the restore script restarts them.
- Added synthetic archive tests confirming safe restore behavior and rejection without deleting existing files when an archive fails validation.

### Checks actually run

- A real local `bsdtar` archive compatibility check passed (`./` directory and prefixed opaque file; restored byte-for-byte). This is not a Docker backup/restore drill.
- **75 tests passed** across backend modules excluding `test_api_flow.py` and `test_proxy_headers.py`, which use `TestClient`; the command used a fresh workspace-local `TEMP`/`TMP`, `PYTHONPATH=.pydeps`, and an isolated SQLite `DATABASE_URL`. Four restore-upload tests passed separately after renaming the tar-layout test.
- `python -m compileall -q app tests evaluation` passed.
- Frontend production build passed with the workspace bundled pnpm runtime: `pnpm run build` (TypeScript project build and Vite production bundle).
- PowerShell parser accepted both `scripts/backup.ps1` and `scripts/restore.ps1`; `docker compose config --quiet` and `git diff --check` passed.
- A focused `TestClient` readiness integration test stalled for 40 seconds and was stopped. Attempting to verify via a local Uvicorn listener was blocked by this workspace's loopback socket permissions. These are environment limitations, not passing API integration evidence.
- Live restore against Docker/PostgreSQL and the named upload volume remains unverified because Docker Engine is unavailable.

### Files/components changed

- `backend/app/restore_uploads.py`, `backend/tests/test_restore_uploads.py`, `scripts/restore.ps1`, `README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run a real backup/restore drill with disposable Compose PostgreSQL and upload data, then verify case-to-upload links and graph rebuild; Docker Engine is unavailable in this environment.
2. Run migrations and persistence tests against PostgreSQL; verify API/worker restart and health behavior when a PostgreSQL-capable runtime is available.
3. Resolve the Windows/Python 3.14 `TestClient` hang or verify the same journeys in a permitted local/Compose browser runtime; continue OCR, Neo4j, TLS, and authorized evaluation checks.

### Resume commands

- With Docker Engine running, create synthetic cases/uploads, run `scripts/backup.ps1` to a protected scratch directory, then restore that matching dump/archive/manifest with `-ConfirmRestore`; verify service health and `python -m app.graph_rebuild` completion.
- From `backend`, set `PYTHONPATH=.pydeps`, fresh workspace temp paths, and unique SQLite `DATABASE_URL`; run all test modules except `test_api_flow.py` and `test_proxy_headers.py` (both use `TestClient`) and compile check. Parse-check both scripts with PowerShell.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Revalidate migration chain and schema metadata

### Completed in this stage

- Applied the complete Alembic migration chain to a newly created, isolated SQLite database and ran Alembic's model/schema consistency check.
- Confirmed `alembic heads` reports a single head revision. This is SQLite validation only; it does not prove PostgreSQL-specific DDL or concurrency behavior.

### Checks actually run

- `python -m alembic upgrade head` — passed on fresh SQLite.
- `python -m alembic check` — passed, “No new upgrade operations detected.”
- `python -m alembic heads` — exactly one head (`a7b13c9e4d20`).
- `git diff --check` — passed.

### Files/components changed

- `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run migrations and all persistence tests against real PostgreSQL when Docker is available; check startup and restart behavior.
2. Continue API/browser integration and operational deployment checks.
3. Run the real OCR smoke check, Neo4j rebuild/outage checks, TLS, backup/restore, and authorized evaluation.

### Resume commands

- From `backend`, use a new workspace-local SQLite database path and run `python -m alembic upgrade head`, `python -m alembic check`, and `python -m alembic heads`. For release verification, repeat migration checks against Compose PostgreSQL.
- Re-read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Require LLM provenance in matched comparisons

### Completed in this stage

- The four-run comparison now refuses to report metrics for an LLM/web-search run unless its adjacent provenance sidecar exactly covers the held-out case IDs.
- Validates operator lawful-access attestation, provider/model/prompt/retrieval metadata, timezone-bearing retrieval timestamps, source references, and SHA-256 source snapshot hashes.
- Added comparison tests for valid sidecar matching and missing-sidecar rejection. Added a runner-to-comparator round-trip test that writes the generated prediction/provenance JSONL files and consumes them through the actual four-way compare function.

### Checks actually run

- **71 tests passed** across all supported non-`TestClient` backend modules.
- `python -m compileall -q app tests evaluation` passed.
- `git diff --check` passed.
- No real model/search provider or authorized dataset was used; the validation tests use synthetic metadata and sources only.

### Files/components changed

- `backend/evaluation/compare_runs.py`, `backend/tests/test_evaluation.py`, `backend/tests/test_llm_web_search_eval.py`, `backend/evaluation/README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run an authorized adapter and time-separated data through the LLM runner and matched four-way comparison; do not report results until real provenance is reviewed.
2. Continue API/browser integration and live deployment checks on a runtime with Windows socket and Docker support.
3. Run real OCR smoke check, Postgres/Neo4j, TLS, and backup/restore verification when Docker is available.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, fresh workspace temp paths, and unique SQLite `DATABASE_URL`; run all supported non-`TestClient` modules and `python -m compileall -q app tests evaluation`.
- Follow `backend/evaluation/README.md` for producing a provenance sidecar and comparing four matched runs. The comparison command intentionally rejects missing or mismatched LLM provenance.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add operator-configured LLM/web-search evaluation runner

### Completed in this stage

- Added a provider-neutral held-out evaluation runner. Operators supply an adapter module explicitly; no model/search SDK, paid service, or credential is added to the product.
- The runner passes only case ID, timestamp, and submitted text to the adapter for `test` rows; it withholds gold labels and does not call the adapter for train/dev rows.
- Validates structured entity/evidence/verdict output, requires operator lawful-access attestation and per-case source references/timestamps, measures per-case latency, and writes a separate provenance JSONL sidecar.
- Provider exceptions are converted to diagnostics containing only case ID and exception class, avoiding echoing prompt or secret text. Documented the adapter contract and offline-only role.

### Checks actually run

- **69 tests passed** across all supported non-`TestClient` backend modules, including five LLM/web-search runner tests (held-out-only behavior, timing/provenance, missing-source and missing-snapshot rejection, and privacy-safe provider errors).
- `python -m compileall -q app tests evaluation` passed.
- No provider was invoked and no evaluation result was generated; authorized data, adapter configuration, and source terms are still required before a real comparison.

### Files/components changed

- `backend/evaluation/llm_web_search.py`, `backend/tests/test_llm_web_search_eval.py`, `backend/evaluation/README.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Connect an operator-approved adapter and authorized time-separated dataset; capture model/search versions and source snapshots, then run the comparison without publishing unsupported performance claims.
2. Run API/proxy tests on a runtime supporting the integration suite and verify production deployment flows.
3. Run the documented OCR smoke check, Postgres/Neo4j checks, TLS deployment, and backup/restore drill when Docker is available.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, fresh workspace temp paths, and a unique SQLite `DATABASE_URL`; run the documented non-`TestClient` suite and `python -m compileall -q app tests evaluation`.
- Follow `backend/evaluation/README.md` for the explicit LLM adapter contract; do not supply production user data unless the evaluation set is authorized.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Add container-side real OCR smoke check

### Completed in this stage

- Added `python -m app.verify_ocr`, a deployment-side command that creates synthetic image and scanned-PDF fixtures, invokes the real Tesseract executable, extracts the synthetic phone identifier, and requires image and page region coordinates.
- Documented the command for operators. It writes no user case data and uses a temporary scanned-PDF fixture.

### Checks actually run

- **64 tests passed** across all non-`TestClient` backend unit modules.
- `python -m compileall -q app tests evaluation` passed, including the new smoke-check module.
- The smoke check itself was not run because this host has no Tesseract executable and Docker Engine is unavailable. It is intended to run inside the worker image, which installs Tesseract.

### Files/components changed

- `backend/app/verify_ocr.py`, `README.md`, `BUILD_STATUS.md`

### Next steps

1. Run the OCR smoke command in the Docker worker image and fix any compatibility or OCR-recognition issue it exposes.
2. Run API/proxy tests on a runtime that supports the existing TestClient suite; verify exported OCR region fields end to end.
3. Continue PostgreSQL/Neo4j, TLS, backup/restore, hosted deployment, and authorized evaluation checks.

### Resume commands

- With Docker Engine running and Compose services healthy, run `docker compose exec worker python -m app.verify_ocr` from the repository root.
- From `backend`, set `PYTHONPATH=.pydeps`, a fresh workspace-local temp directory, and unique SQLite `DATABASE_URL`, then run the listed 64 non-`TestClient` tests and `python -m compileall -q app tests evaluation`.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Persist OCR image-region locations

### Completed in this stage

- OCR extraction now uses Tesseract word-level data to map text offsets to bounding boxes for uploaded images and scanned PDF pages.
- When a deterministic entity span overlaps OCR words, its persisted `source_location` includes the union box in OCR pixels, alongside the existing text offsets. PDF text-native pages remain page-relative without fabricated image coordinates.
- Investigator case and campaign-link views now render the stored OCR region token as a readable image/PDF page label with x/y/width/height pixel values.
- Added tests for mocked Tesseract word-data conversion, overlapping word-box union, non-overlap, and the current 80-character database column limit.
- Added a synthetic two-page PDF test that exercises the real PDF text/page segmentation path with mocked OCR on the scanned page, verifying page-local spans map to correctly shifted document offsets and retain the page-specific region prefix.

### Checks actually run

- **64 tests passed** across all non-`TestClient` backend unit modules, including five OCR-region tests and a synthetic scanned-PDF page/offset test.
- `python -m compileall -q app tests evaluation` passed.
- The report API integration test asserts `source_location` is included for exported entities; that TestClient integration test remains unrun here.
- `pnpm run build` passed (`tsc -b && vite build`).
- Frontend production build passed again after adding readable OCR region labels.
- `docker compose config --quiet` and `git diff --check` passed.
- OCR word conversion and scanned-PDF page/offset mapping are unit-tested with synthetic Tesseract data; an actual Tesseract binary run and real scanned deployment fixtures remain unverified. API/browser integration and live Postgres/Neo4j checks remain outstanding.

### Files/components changed

- `backend/app/worker.py`, `backend/tests/test_ocr_regions.py`, `frontend/src/App.tsx`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Add an OCR fixture verification using the actual deployment image and confirm stored region locations against rendered source pixels.
2. Run API/proxy tests on a permitted runtime and verify the new locations appear correctly in investigator case details and reports.
3. Continue remaining production verification: Docker services, migrations, graph rebuild, TLS, backup/restore, and authorized-data evaluation.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, use a fresh workspace-local temp directory and unique SQLite `DATABASE_URL`; run the listed non-`TestClient` unit modules and `python -m compileall -q app tests evaluation`. Build the UI with `pnpm run build` from `frontend` and check Compose with `docker compose config --quiet` at the root.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Redact public correction status text

### Completed in this stage

- The requester-facing correction status endpoint returned investigator-written resolution text without applying privacy redaction. Since those notes can quote copied evidence, it now applies the shared text redactor before returning them.
- Extended the API flow regression test to place a phone number and dotless UPI handle in an investigator resolution and assert they are masked in the status-token response.

### Checks actually run

- **59 tests passed** across all non-`TestClient` backend unit modules, including privacy, campaign rules, request-body limits, extraction, findings, storage, source adapters, and evaluation.
- `python -m compileall -q app tests evaluation` passed after the privacy and endpoint changes.
- A direct call to the correction-status handler with a synthetic session verified phone, UPI, and private URL-path/query masking end to end through that handler.
- `pnpm run build` passed (`tsc -b && vite build`; Vite produced the production assets).
- `git diff --check` passed. The API-flow assertion is added but not executable in the current Windows sandbox because Starlette `TestClient` socket setup is blocked; the full API integration result is therefore unverified.
- `docker compose config --quiet` passed. This validates Compose syntax and interpolation only; it does not prove that the services start.
- Docker Engine is unavailable (`docker info` could not connect to the Docker Desktop Linux engine), so container startup and live service checks remain unrun.
- Tried an in-process `httpx.ASGITransport` request to `/health/live` with an isolated SQLite URL as an alternative to Starlette `TestClient`; the request produced no response after roughly 15 seconds and the specific process was terminated. This path is not currently a viable integration-test workaround in this sandbox.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Continue checking requester-visible responses and other redacted API serializers for copied personal data.
2. Run API/proxy tests on a permitted runtime; both Starlette `TestClient` and the attempted `httpx.ASGITransport` request are blocked/hanging in this sandbox.
3. Verify the full browser workflows and production services as recorded below.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, a fresh workspace-local temp path, and a unique SQLite `DATABASE_URL`; run non-`TestClient` modules plus `python -m compileall -q app tests evaluation`. Run API/proxy integration tests on a runtime that permits Starlette's socketpair setup.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-23 (Asia/Kolkata) — Mask dotless UPI handles in free text

### Completed in this stage

- Route-by-route review found UPI values embedded in free text could bypass the email masker when their payment-provider suffix had no dot (for example `candidate@okaxis`).
- Added a dedicated dotless-handle pattern to shared text redaction, used by analyst/audit text serializers, and a regression test for two common handle shapes.

### Checks actually run

- **15 targeted tests passed** across privacy redaction and campaign-rule modules.
- `python -m compileall -q app tests evaluation` passed.
- Full unit suite was not rerun in this increment; API/proxy integration, browser, and live deployment checks remain outstanding.

### Files/components changed

- `backend/app/privacy.py`, `backend/tests/test_privacy.py`, `BUILD_STATUS.md`, `README.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Continue reviewing API serialization and report fields for personal-data leakage, including source corpus and correction responses.
2. Run the complete non-`TestClient` unit suite, then API/proxy tests on a permitted runtime.
3. Verify rendered intake, investigator, graph, timeline, campaign, and report workflows.
4. Verify PostgreSQL/Neo4j, TLS, backup/restore, OCR deployment behavior, and authorized-data evaluation.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, use a fresh workspace-local temp directory for `TEMP`/`TMP`/`TMPDIR`, and a fresh SQLite `DATABASE_URL`. Run the non-`TestClient` modules and `python -m compileall -q app tests evaluation`; run full discovery on a permitted runtime.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (current session) — Mask additional financial and national identifiers in redacted output

### Completed in this stage

- Expanded shared free-text redaction to mask labeled 9–18 digit bank account numbers, PAN-shaped identifiers, and 12-digit identifiers (including Aadhaar-style grouped values) in analyst-facing text and recursively serialized audit values.
- Added focused regression coverage for the new patterns. This is display redaction only; original source material remains available only to roles authorized to inspect case evidence.

### Checks actually run

- **58 tests passed** across non-`TestClient` backend unit modules.
- `python -m compileall -q app tests evaluation` passed.
- The full API/proxy integration tests, browser rendering, and live Postgres/Neo4j behavior remain unverified in this Windows sandbox.

### Files/components changed

- `backend/app/privacy.py`, `backend/app/main.py`, `backend/tests/test_privacy.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Continue the route-by-route privacy review, focusing on all redacted API response serializers and report paths.
2. Run API/proxy integration tests on a permitted runtime and POSIX upload-mode checks on Linux.
3. Verify rendered intake, investigator, graph, timeline, campaign, and report workflows.
4. Verify PostgreSQL/Neo4j, TLS, backup/restore, and authorized-data evaluation with available dependencies/data.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, use a fresh workspace-local temp directory for `TEMP`/`TMP`/`TMPDIR`, and a fresh SQLite `DATABASE_URL`. Run the non-`TestClient` unit modules, then `python -m compileall -q app tests evaluation`. Run full discovery on a permitted runtime.
- Read this file, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `README.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:38 Asia/Kolkata / 12:08 UTC) — Centralize source-reference and audit redaction

### Completed in this stage

- Moved source-reference and recursive audit redaction into the shared `privacy.py` module so both API serialization and focused unit tests use the same implementation.
- Redacted source references now retain a safe HTTP(S) origin while replacing user-controlled paths, queries, and fragments. Contact-shaped values embedded in hostnames are masked; URL credentials and unrecognized references are withheld.
- Free text passed through analyst/audit serializers now redacts embedded URLs and their paths/queries as well as recruiter labels, phones, emails, and UPI-shaped values. Known private audit keys remain replaced with `[redacted]`.
- Added tests for source provenance retention, sensitive host values, credential-bearing URLs, arbitrary nested text, and private audit fields.

### Checks actually run

- **57 tests passed** across non-`TestClient` unit modules; `python -m compileall -q app tests evaluation` passed.
- Full API/proxy tests, visual reports, and live provider/deployment behavior remain unverified here.

### Files/components changed

- `backend/app/privacy.py`, `backend/app/main.py`, `backend/tests/test_privacy.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Continue privacy review across every route and inspect redacted API payloads through the integration harness when available.
2. Run API/proxy integration tests on a permitted runtime and POSIX upload-mode checks on Linux.
3. Verify rendered intake, investigator, graph, timeline, campaign, and report workflows.
4. Verify PostgreSQL/Neo4j, TLS, backup/restore, and authorized-data evaluation with available dependencies/data.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, use a fresh workspace-local temp directory for `TEMP`/`TMP`/`TMPDIR`, and a fresh SQLite `DATABASE_URL`. Run all unit modules except `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. Run full discovery on a permitted runtime.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:35 Asia/Kolkata / 12:05 UTC) — Fail closed on free-text graph labels

### Completed in this stage

- Extended the shared display privacy utility to mask location and payment-request excerpts and to mask unknown entity types by default.
- Retained company/job/date/payment-amount claims for graph context but scrubbed embedded recruiter labels, phone numbers, emails, and UPI-like values before display.
- Documented the current shared-workspace authorization boundary: analyst-wide case visibility is redacted; investigator/reviewer roles can inspect originals; deployment is not multi-tenant or case-owner isolated.
- Added tests for free-text contact scrubbing, location/payment masking, safe-claim preservation, and unknown-type fail-closed behavior.

### Checks actually run

- **55 tests passed** across non-`TestClient` unit modules, including privacy, graph, body-size, schema, extraction, evidence, and evaluation checks.
- `python -m compileall -q app tests evaluation` — passed.
- API/proxy integration tests, rendered UI, and live Neo4j projection remain unverified in this environment.

### Files/components changed

- `backend/app/privacy.py`, `backend/app/main.py`, `backend/tests/test_privacy.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run API/proxy integration modules on a permitted runtime; run POSIX storage mode assertions on Linux.
2. Continue route-by-route privacy and authorization review; verify graph, case, and report redaction in the rendered application.
3. Exercise intake, review, timeline, campaign, and report flows against a reachable deployment.
4. Verify PostgreSQL/Neo4j, TLS, backup/restore, and authorized evaluation when dependencies and data are available.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, point `TEMP`/`TMP`/`TMPDIR` to a fresh workspace-local test directory, and set `DATABASE_URL` to a fresh SQLite file. Run all unit modules except `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. On a permitted runtime, run full discovery.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:32 Asia/Kolkata / 12:02 UTC) — Mask web identifiers in graph node labels

### Completed in this stage

- Centralized entity display masking in `backend/app/privacy.py` and reused it from API serialization and the Neo4j projection helper.
- Graph labels now mask URLs and domains as well as phone, email, UPI, and recruiter-claim values. This prevents personal data embedded in URL paths or query strings from appearing in the investigator graph by default.
- The API re-masks Neo4j node labels when reading them, preventing legacy projection display values from bypassing current masking rules. PostgreSQL graph fallback uses the same helper.
- Added privacy utility and graph-projection regression tests.
- Documented the current authorization boundary: one shared workspace, with redacted analyst-wide case access and investigator/reviewer source access; it is not multi-tenant or per-case ownership isolated.

### Checks actually run

- **53 tests passed** across the non-`TestClient` unit modules, including graph redaction, web-identifier masking, request-body limits, schema boundaries, and private storage.
- `python -m compileall -q app tests evaluation` — passed.
- Full API/proxy integration modules and visual graph review remain unverified in this Windows sandbox.

### Files/components changed

- `backend/app/privacy.py`, `backend/app/main.py`, `backend/app/graph_store.py`, `backend/tests/test_privacy.py`, `backend/tests/test_file_validation.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Next steps

1. Run API and proxy integration modules on a permitted runtime; run POSIX storage mode assertions on Linux.
2. Continue arbitrary-text privacy and authorization-scope audit, then verify redaction in rendered graph, case, and report views.
3. Run visual intake/review/report workflows on a reachable local deployment.
4. Run Docker/PostgreSQL/Neo4j/TLS/backup checks and authorized-data evaluation when dependencies and data are available.

### Resume commands

- From `backend`, use `PYTHONPATH=.pydeps`, a fresh workspace-local `TEMP`/`TMP`/`TMPDIR`, and a fresh SQLite `DATABASE_URL`. Run all unit modules except `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. On a permitted runtime, run full test discovery.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:30 Asia/Kolkata / 12:00 UTC) — Bound credential and email fields

### Completed in this stage

- Login password input now has the same 128-character ceiling as registration/reset passwords, avoiding unnecessarily expensive verification of oversized values.
- Registration, login, and public correction email fields are capped at the database column size (320 characters) to prevent values that pass input validation but fail at persistence time.
- Added boundary tests for maximum accepted login password and overlong credential/correction email addresses.

### Checks actually run

- **50 tests passed** across the non-`TestClient` unit modules; this includes request-body protections, graph redaction, schema limits, and the existing deterministic/evidence evaluation tests.
- `python -m compileall -q app tests evaluation` — passed.
- Actual FastAPI middleware stack returned 413 for declared oversized upload/auth/case bodies and for an oversized streamed multipart request lacking `Content-Length`.

### Files/components changed

- `backend/app/schemas.py`, `backend/tests/test_schema_limits.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run API and proxy integration modules on a permitted runtime; run POSIX mode assertions on Linux.
2. Continue route-by-route privacy review, focusing on arbitrary text and authorization scope.
3. Visually verify intake polling, review dialogs, graph masking, and report download when browser-to-local-app networking is available.
4. Run container/PostgreSQL/Neo4j/TLS/backup checks and authorized-data evaluation when dependencies and data are available.

### Resume commands

- From `backend`, use `PYTHONPATH=.pydeps`, fresh workspace-local `TEMP`/`TMP`/`TMPDIR`, and a fresh SQLite `DATABASE_URL`. Run all unit modules except `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. On a permitted runtime, run `python -m unittest discover -s tests -v`.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:29 Asia/Kolkata / 11:59 UTC) — Preserve 413 on streamed multipart overflow

### Completed in this stage

- Real-stack streaming verification found FastAPI's multipart parser was converting the custom overflow exception into a generic HTTP 400 before the middleware could return its intended 413.
- The middleware now detects that parser response after an overflow and replaces it with the bounded-size HTTP 413 response, while suppressing the parser's body. Unknown-length and inaccurate declared-length bodies both remain covered.
- Added a regression test simulating a framework parser that catches the overflow and tries to emit 400.

### Checks actually run

- **48 tests passed** across the non-`TestClient` unit modules, including seven request-body tests, graph-link redaction, and private-storage tests.
- `python -m compileall -q app tests evaluation` — passed.
- Actual FastAPI middleware stack: declared oversize checks for upload, authentication, and case JSON passed; a streamed multipart request with no `Content-Length` also returned 413 before parsing, with no-store and connection-close headers.

### Files/components changed

- `backend/app/middleware.py`, `backend/tests/test_request_body_limit.py`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`

### Next steps

1. Run the excluded API and proxy integration modules on a permitted runtime; run POSIX mode assertions on Linux.
2. Continue route-by-route privacy review, focusing on arbitrary text and authorization scope.
3. Visually verify intake polling, review dialogs, graph masking, and report download when browser-to-local-app networking is available.
4. Run container/PostgreSQL/Neo4j/TLS/backup checks and authorized-data evaluation when dependencies and data are available.

### Resume commands

- From `backend`, set `PYTHONPATH=.pydeps`, point `TEMP`/`TMP`/`TMPDIR` at a fresh workspace-local test directory, and set `DATABASE_URL` to a fresh SQLite file. Run the 48-test subset excluding `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. On a permitted runtime, run `python -m unittest discover -s tests -v`.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:27 Asia/Kolkata / 11:57 UTC) — Mask identifiers in graph-link explanations

### Completed in this stage

- Campaign-link explanations shown in redacted analyst views and graph views now preserve the matched identifier type and deterministic signal weight while masking exact values, URLs, and shared web hosts.
- PostgreSQL-derived graph case titles now receive the same conservative text redaction applied to Neo4j-derived titles.
- Added regression coverage for UPI IDs without a dotted email domain, phone numbers, email addresses, URLs, and shared hosts.

### Checks actually run

- **47 tests passed** across evaluation baselines, campaign rules/redaction, evaluation metrics, extraction, file validation/graph projection, findings, private storage, RDAP, and request-body middleware. `test_api_flow` and `test_proxy_headers` remain excluded due to the sandbox's TestClient socket restriction.
- `python -m compileall -q app tests evaluation` — passed.
- The actual FastAPI middleware stack was checked in memory for oversized upload, authentication JSON, and case JSON requests; all returned 413 before body reads with CORS, no-store, and connection-close headers.
- Windows run does not verify POSIX filesystem mode bits. No UI/browser or hosted deployment checks were run in this increment.

### Files/components changed

- `backend/app/campaign_rules.py`, `backend/app/main.py`, `backend/tests/test_campaign_rules.py`, `backend/app/middleware.py`, `backend/tests/test_request_body_limit.py`, `.gitignore`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known issue and next steps, in order

1. Run API and proxy integration modules on a runtime where Starlette's Windows asyncio socketpair is permitted; run the POSIX mode-bit tests on Linux.
2. Continue route-by-route privacy review, focusing on arbitrary text and authorization scope.
3. Visually verify live intake polling, review dialogs, graph masking, and report download in a browser connected to a local deployment.
4. Run Docker/PostgreSQL/Neo4j/TLS/backup checks and authorized-data evaluation when those dependencies and data are available.

### Resume commands

- From `backend`, set `PYTHONPATH` to `.pydeps`; point `TEMP`, `TMP`, and `TMPDIR` to a fresh workspace-local test directory; set `DATABASE_URL` to a fresh SQLite file there. Run all unit modules except `test_api_flow` and `test_proxy_headers`, then `python -m compileall -q app tests evaluation`. On a permitted runtime, run full discovery.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:26 Asia/Kolkata / 11:56 UTC) — Bound intake request bodies before parsing

### Completed in this stage

- Added pure ASGI request-size enforcement for all API `POST`, `PATCH`, and `PUT` requests. Oversized declared bodies are rejected before FastAPI reads/parses them; missing or dishonest lengths are checked as chunks arrive.
- Upload request cap is `MAX_UPLOAD_BYTES + 64 KiB` for multipart boundaries and consent/title fields; the endpoint still enforces the actual file byte limit. Text-case JSON is capped at 512 KiB, above the worst-case UTF-8 size of the 100,000-character schema limit plus metadata.
- Oversize responses are JSON 413, no-store, and close the connection; CORS and no-store middleware remain outside the size guard.
- Added socket-free ASGI regression tests for declared length, streaming overflow, exact limit, API default cap, route scope, and malformed length. Added the isolated test temp folder to `.gitignore`.

### Checks actually run

- **45 tests passed** across evaluation baselines, campaign rules, evaluation metrics, extraction, file validation/graph projection, findings, private storage, RDAP, and request-body middleware. This includes a declared-length mismatch test. The run excluded `test_api_flow` and `test_proxy_headers`, whose Starlette `TestClient`/Windows socket setup is environment-sensitive.
- `python -m compileall -q app tests evaluation` — passed.
- Built the actual FastAPI middleware stack without starting lifespan and drove oversized upload, login JSON, and case JSON requests through it with in-memory ASGI receive/send functions — confirmed rejection before body reads and HTTP 413, CORS, no-store, and connection-close headers.

### Files/components changed

- `backend/app/middleware.py`, `backend/app/main.py`, `backend/tests/test_request_body_limit.py`, `.gitignore`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known issue and next steps, in order

1. Rerun integration tests on a permitted runtime; run POSIX storage mode tests on Linux.
2. Continue authorization/redaction review and assess other API request surfaces for appropriate body limits.
3. Visually verify intake polling, review dialogs and report download when browser-to-local-app networking is available.
4. Run container/PostgreSQL/Neo4j/TLS/backup integration checks and authorized-data evaluation when dependencies and data are available.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'`, create `backend/.test-sandbox-tmp`, and point `$env:TEMP`, `$env:TMP`, and `$env:TMPDIR` there. Set `DATABASE_URL` to a fresh SQLite file in that directory before importing modules that construct the SQLAlchemy engine. Run the 44-test subset (all unit modules except `test_api_flow` and `test_proxy_headers`) and `python -m compileall -q app tests evaluation`. On a runtime where Starlette's Windows socketpair works, then run `python -m unittest discover -s tests -v`.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:20 Asia/Kolkata / 11:50 UTC) — Restrict local upload storage permissions

### Completed in this stage

- Added reusable private-storage helpers. On POSIX, startup and worker retention set the upload directory to `0700`; new uploads are opened exclusively with `0600`, so a collision fails instead of overwriting a file.
- Documented the Windows ACL responsibility and clarified that filesystem permissions do not encrypt stored uploads.
- Added unit coverage for directory creation, file content, exclusive creation and POSIX mode bits (the mode assertions are conditional on a POSIX runner).

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest tests.test_private_storage -v` — **2 tests passed** on Windows; POSIX mode-bit assertions were skipped by platform condition.
- `python -m compileall -q app tests evaluation` — passed.
- Full API/backend suite — **not verified in this environment**. Starlette `TestClient` setup blocks while creating the Windows asyncio self-pipe (`socket.accept`) under the sandbox, before the first API test runs. The existing prior checkpoint's 52-test result predates this change and does not verify it.

### Files/components changed

- `backend/app/private_storage.py`, `backend/app/main.py`, `backend/app/worker.py`, `backend/tests/test_private_storage.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known issue and next steps, in order

1. Run `backend/tests` on a permitted host/runtime; also exercise POSIX mode-bit assertions on Linux CI. Use a fresh unique test directory under the workspace or a permitted temporary root; do not inspect, reuse, or delete the pre-existing `.test-runtime` database.
2. Continue authorization/redaction review, multipart request-body limits and data-at-rest controls.
3. Visually verify intake polling, review dialogs and report download when browser-to-local-app networking is available.
4. Run container/PostgreSQL/Neo4j/TLS/backup integration checks and authorized-data evaluation when those dependencies and data are available.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'` and a unique permitted temporary directory for `$env:TEMP`, `$env:TMP`, and `$env:TMPDIR`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Read this file, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

### Test data isolation note

- While diagnosing the sandbox's blocked default temporary path, the suite's unique temporary children were placed under the ignored `.test-runtime` parent. The pre-existing database at that parent was not opened, inspected, modified or deleted. One interrupted API-test attempt may have left a uniquely named temporary child; it is not the pre-existing database and must not be mistaken for it.

## 2026-10-21 (17:13 Asia/Kolkata / 11:43 UTC) — Disable caching for private API responses

### Completed in this stage

- Added pure ASGI `ApiNoStoreMiddleware` that applies `Cache-Control: no-store, private` and `Pragma: no-cache` to all `/api/*` responses, including authentication and downloaded case reports.
- Added assertions for auth registration and report headers; updated README and security section of the walkthrough.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **52 tests passed** in 3.390 seconds.
- `python -m compileall -q app tests evaluation` — passed.

### Files/components changed

- `backend/app/middleware.py`, `backend/app/main.py`, `backend/tests/test_api_flow.py`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Continue privacy/security review for authorization scope, uploaded request-body limits and data-at-rest controls.
2. Visually exercise intake, evidence review, reviewer dialogs, automatic processing refresh, and report download when local browser-to-server networking is available.
3. Run real container/host/backup checks and authorized evaluation.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run full unittest discovery and `python -m compileall -q app tests evaluation`.
- Read the latest checkpoint, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect Git status. Do not commit unless requested.

## 2026-10-21 (17:11 Asia/Kolkata / 11:41 UTC) — Validated upload policy in intake

### Completed in this stage

- `/api/policy` now publishes `MAX_UPLOAD_BYTES` and accepted upload media types; application startup rejects a nonpositive limit.
- The intake form uses that server policy to validate selected file type and size before submitting and displays an actionable inline error. The API retains independent size, declared media type, and signature enforcement.
- Added API integration assertions for the returned upload policy, unsupported MIME rejection, and an over-limit upload response. Updated README and the role-by-role engineering walkthrough.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **52 tests passed** in 3.381 seconds.
- `python -m compileall -q app tests evaluation` — passed.
- `pnpm run build` (`tsc -b && vite build`) — passed after the intake and in-page review dialog changes.
- Browser interaction remains pending because the environment denied local browser-to-server sockets in the previous isolated attempt.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `frontend/src/App.tsx`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Continue authorization, upload, source provenance, and data-retention security review.
2. Visually exercise intake and review flows in a browser when local app networking is permitted.
3. Run real Postgres/Neo4j/container/host/TLS/backup checks with Docker and a controlled deployment environment; run authorized-data evaluation.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run full unittest discovery and `python -m compileall -q app tests evaluation`.
- From `frontend`, run `pnpm run build`.
- Read this checkpoint, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and inspect `git status`; do not commit unless asked.

## 2026-10-21 (17:09 Asia/Kolkata / 11:39 UTC) — In-page rationale and reset-token flows

### Completed in this stage

- Replaced evidence-review rationale collection via native `window.prompt()` with an in-page dialog that identifies the status being recorded, requires a 10-character rationale, and keeps the dialog open after API failure.
- Replaced reviewer account suspension/reactivation and password-reset rationale prompts with validated dialogs. Reset-token output now appears in a dedicated one-time dialog with expiration, out-of-band delivery guidance, selectable token text, and user-initiated copy; it is never copied automatically.
- Updated the point-by-point engineering walkthrough. A source scan found no remaining native alert/confirm/prompt calls in the frontend source.

### Checks actually run

- `pnpm run build` (`tsc -b && vite build`) — passed; production bundle generated.
- Source scan for `window.prompt`, `window.confirm`, and `window.alert` — no matches.
- Browser interaction still cannot be exercised in this environment due to the previously recorded local socket restriction; no visual success is claimed.

### Files/components changed

- `frontend/src/App.tsx`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Visually exercise evidence review and reviewer account dialogs in a browser when app-local networking is available.
2. Continue backend privacy/security review, especially authorization scope, upload-size handling, and source provenance guarantees.
3. Complete container/hosted operational checks with Docker/host access and run evaluation only on authorized time-separated data.

### Resume commands

- From `frontend`, run `pnpm run build`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run the full unittest suite and `python -m compileall -q app tests evaluation`.
- Read this checkpoint, `BUILD_PLAN.md` and `ENGINEERING_WALKTHROUGH.md`; inspect `git status`; do not commit unless requested.

## 2026-10-21 (17:04 Asia/Kolkata / 11:34 UTC) — Compose database credential alignment

### Completed in this stage

- The default SQLAlchemy URL for both API and worker now derives from the same configurable `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` values used by the Postgres container. An explicit `DATABASE_URL` override remains available.
- README now tells operators when to set an explicit URL and notes percent-encoding for URL-reserved password characters.

### Checks actually run

- Rendered default Compose configuration with custom database name/user/password and asserted that Postgres, API and worker values all match — passed.
- `docker compose --profile production config --quiet` — passed.
- Full backend suite: **52 passed**; Python compilation passed after the worker-retention and privacy-minimal error handling changes.

### Files/components changed

- `docker-compose.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Continue the privacy/security review against persisted/API/logged data and upload boundaries.
2. Retry browser polling/report export with local socket access; verify containers/Neo4j/Postgres/TLS/backup restore with Docker and a controlled host.
3. Run ML/evidence/campaign evaluation only with authorized time-separated data.

### Resume commands

- From repository root: `docker compose config --quiet` and `docker compose --profile production config --quiet`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run the full unittest suite and Python compilation.
- Read the current top checkpoint, `BUILD_PLAN.md`, and `ENGINEERING_WALKTHROUGH.md`; inspect `git status`; do not commit unless requested.

## 2026-10-21 (17:04 Asia/Kolkata / 11:34 UTC) — Keep raw exception text out of job records

### Completed in this stage

- Worker processing-job diagnostics now persist only the exception class, not provider/parser exception text that could contain submitted values, local paths or query data.
- The regression test verifies that an injected synthetic private path/name/phone appears neither in the logger arguments nor the persisted job diagnostic. Safe UI recovery wording remains unchanged.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **52 tests passed** in 3.370 seconds.
- `python -m compileall -q app tests evaluation` — passed.

### Files/components changed

- `backend/app/worker.py`, `backend/app/graph_outbox.py`, `backend/app/main.py`, `backend/tests/test_api_flow.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Continue the privacy/security review and verify test coverage for case authorization, uploads, corrections, exports and log handling.
2. Reattempt browser auto-refresh/report export when localhost access is available.
3. Complete real PostgreSQL/Neo4j/container/hosted checks when Docker and a controlled host are available; obtain authorized evaluation data before reporting metrics.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Read `BUILD_PLAN.md`, this checkpoint and `ENGINEERING_WALKTHROUGH.md`; inspect `git status`; do not commit unless requested.

## 2026-10-21 (17:03 Asia/Kolkata / 11:33 UTC) — Privacy-minimal failure logs

### Completed in this stage

- Case-processing failures, graph projection failures and Neo4j graph-read fallback now log operation/case context and the exception class without serializing exception messages or tracebacks that could contain paths, source queries or submitted values.
- Added a regression test that injects a synthetic path/name/phone exception and verifies the logger receives only a case ID, attempt count and exception class.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **52 tests passed** in 3.459 seconds.
- The targeted database and frontend configuration checks from earlier checkpoints are unaffected. Python compilation is next for this logging-only change.

### Files/components changed

- `backend/app/worker.py`, `backend/app/graph_outbox.py`, `backend/app/main.py`, `backend/tests/test_api_flow.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Run Python compilation and inspect the final diff/status for the logging and retention changes.
2. Retry browser auto-refresh/report download when local browser-to-server access is available.
3. Run actual container, PostgreSQL/Neo4j, hosted TLS and backup/restore checks when Docker Engine/host access is available.
4. Continue open privacy/security items and run evaluation only with authorized time-separated data.

### Resume commands

- From `backend`, set `$env:PYTHONPATH='.pydeps'`; run `python -m compileall -q app tests evaluation` and `python -m unittest discover -s tests -v`.
- Read `BUILD_PLAN.md`, the latest section here, and `ENGINEERING_WALKTHROUGH.md` before continuing; inspect Git status. Do not commit unless asked.

## 2026-10-21 (17:00 Asia/Kolkata / 11:30 UTC) — Worker retention on a fresh upload path

### Completed in this stage

- The retention sweep now creates its configured private upload directory before cleaning expired/orphan files. This makes the first worker maintenance pass safe even when a local/private volume has not yet been initialized by an upload.
- Added a regression test that supplies a missing nested upload directory, runs retention against the isolated integration database, and verifies an empty directory is created.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **51 tests passed** in 4.206 seconds.
- `python -m compileall -q app tests evaluation` — passed.
- Previous stage's frontend build, migration check and Compose parse remain valid; this increment changes only the Python worker and API integration test.

### Files/components changed

- `backend/app/worker.py`, `backend/tests/test_api_flow.py`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Reattempt the post-change browser refresh and report-download check when local browser-to-server sockets are available; use a new isolated synthetic database.
2. Run Compose and production service integrations when Docker Engine is available.
3. Continue the remaining privacy/security, OCR, hosted TLS, backup/restore and authorized evaluation work listed in `ENGINEERING_WALKTHROUGH.md`.

### Resume commands

- Read `BUILD_PLAN.md`, this checkpoint and the engineering walkthrough; inspect `git status`.
- Backend: from `backend`, set `$env:PYTHONPATH='.pydeps'`, run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Keep changes uncommitted unless asked.

## 2026-10-21 (17:00 Asia/Kolkata / 11:30 UTC) — Live processing status and safer test isolation

### Completed in this stage

- Added an authenticated `GET /api/processing-status` endpoint returning a bounded list of job/case states and safe failure guidance. It does not expose worker exception text and avoids adding audit rows on every poll.
- Added client polling while cases are queued/processing. The case list updates during work; when a terminal state is observed, the client refreshes the case list and selected case once.
- Replaced browser `prompt()` for investigator/reviewer bootstrap codes with an optional masked sign-up field. Fixed validation error rendering to show field locations/messages without serializing user input.
- Changed the API integration test fixture from recursively deleting a fixed `backend/.test-runtime` directory to using a unique OS temporary directory. Added assertions for unauthenticated processing-status rejection and queued-to-completed transition.
- Expanded `ENGINEERING_WALKTHROUGH.md` with implementation steps by full-stack, applied-ML, security/product, and deployment roles, verification limits, a data-handling note, and ordered continuation steps.

### Checks actually run

- `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **50 tests passed** in 4.085 seconds, including status auth/transition checks.
- `python -m compileall -q app tests evaluation` — passed.
- `pnpm run build` (`tsc -b && vite build`) — passed; Vite generated the production bundle.
- `python -m alembic upgrade head` and `python -m alembic check` against a disposable SQLite migration database — passed; no new upgrade operations detected.
- `docker compose config --quiet` — passed.
- Local browser run before the polling patch verified synthetic signup, consented intake, background extraction, and persisted completion after reload. The new polling endpoint behavior is covered by API integration tests; a second browser visual check of auto-refresh is still pending.
- A fresh isolated visual run was attempted after the change, but the in-app browser timed out opening localhost and shell requests to localhost were denied by the environment's socket policy. The isolated API/worker/Vite processes were stopped. This run did not verify browser auto-refresh or report download.
- Local processes used for synthetic isolated verification were stopped. Docker Engine remains unavailable, so container startup and Postgres/Neo4j/Caddy health transitions remain unverified.

### Data-handling note

- One earlier attempted local browser run was inadvertently directed at a pre-existing `.test-runtime` database path. Worker startup reported zero expired cases removed, but it is not possible to determine whether orphan-upload cleanup touched any old file. The processes were stopped; the database was not inspected or reused afterward and was not deleted. Avoid this pre-existing runtime directory. Later browser work used a newly created isolated synthetic child. Integration tests now use unique OS temporary directories and no longer recursively operate on the shared runtime path.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `frontend/src/App.tsx`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. In an environment that permits local browser-to-server connections, use a fresh isolated database and synthetic data to visually verify automatic status refresh and report download. Do not use the pre-existing `.test-runtime` directory.
2. When Docker Engine is available, run default and production Compose services and verify database readiness, worker retries, graph outbox/rebuild/fallback, retention, and backup/restore.
3. Continue the open privacy/security review, OCR deployment verification, hosted TLS checks, and account recovery/audit hardening as detailed in `ENGINEERING_WALKTHROUGH.md`.
4. Obtain authorized time-separated data before reporting ML/evidence/campaign metrics; evaluation is pending and no performance results are claimed.

### Resume commands

- Read `BUILD_PLAN.md`, this checkpoint, and `ENGINEERING_WALKTHROUGH.md`; inspect `git status` before editing.
- Backend: from `backend`, set `$env:PYTHONPATH='.pydeps'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`. Tests now allocate isolated OS temp data.
- Frontend: from `frontend`, run `pnpm run build`.
- Compose config: from the repository root, run `docker compose config --quiet`; this parses configuration only and does not require live container proof.
- Keep changes uncommitted unless the user requests a commit.

## 2026-10-21 (16:45 Asia/Kolkata / 11:15 UTC) — Dependency-aware health checks

### Completed in this stage

- Split API liveness (`/health/live`) from PostgreSQL readiness (`/health/ready`); preserved `/health` as a readiness alias so Compose and existing operators cannot see a healthy API while its system-of-record database is unavailable.
- Readiness executes `SELECT 1`, returns HTTP 503 and a generic dependency status on SQLAlchemy failure, and does not return connection details.
- Updated Compose to probe API readiness and worker-to-PostgreSQL connectivity. Neo4j health now runs an authenticated Cypher query; corrected Compose `$` escaping so the credentials come from the container environment and added the required statement terminator.
- Documented how readiness relates to the PostgreSQL-authoritative design, where Neo4j outage is tolerated using the projection fallback.

### Checks actually run

- Full backend suite: **50 tests passed** in 3.519 seconds, including readiness success, liveness independence, database failure response, and error-detail non-disclosure.
- `python -m compileall -q app tests evaluation` — passed.
- Disposable SQLite Alembic upgrade through `a7b13c9e4d20` plus `alembic check` — passed; no schema drift.
- Default and production `docker compose config --quiet` — passed. A rendered config assertion verified the Neo4j health command retains `$NEO4J_USER`/`$NEO4J_PASSWORD`, the API probes `/health/ready`, and worker healthcheck exists.
- `git diff --check` and direct trailing-whitespace scan — passed.
- Docker Engine is unavailable; actual health transitions inside Postgres, Neo4j, API and worker containers were not observed.

### Files/components changed

- `backend/app/main.py`, `backend/tests/test_api_flow.py`, `docker-compose.yml`
- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. With Docker running, launch default and production profiles, verify every container reaches healthy, stop/restart PostgreSQL and Neo4j to observe readiness/fallback behavior, and restore services.
2. Verify live PostgreSQL row locking, worker job claims/retries, graph outbox recovery/rebuild, retention, and backup/restore.
3. Configure a real domain/secrets on a controlled host and verify Caddy certificate issuance, public TLS, response headers, and host-only API exposure.
4. Obtain authorized annotated time-separated Indian recruitment-scam data; run full matched comparisons and record actual metrics. Evaluation remains pending; no results are invented.
5. Re-read the latest checkpoint and continue with any deployment-independent gaps while Docker/data access is unavailable.

### Resume commands

- From `backend`: `$env:PYTHONPATH='.pydeps'`; set a disposable `$env:DATABASE_URL`; run `python -m unittest discover -s tests -v`, `python -m compileall -q app tests evaluation`, `python -m alembic upgrade head`, and `python -m alembic check`.
- From repository root: run `docker compose config --quiet` and `docker compose --profile production config --quiet`.
- Changes remain uncommitted.

## 2026-10-21 (16:41 Asia/Kolkata / 11:11 UTC) — Optional hosted TLS edge

### Completed in this stage

- Added an optional Docker Compose `production` profile with Caddy automatic HTTPS, persisted certificate/config storage, same-origin API/static routing, compression, and HSTS, CSP, frame, MIME-sniffing, and referrer response headers.
- Added loopback-only host binds for the API and frontend; PostgreSQL and Neo4j remain unpublished. All services share an application network. Caddy receives a stable configurable IPv4 address so operators can trust that exact proxy in Uvicorn rather than trusting arbitrary forwarding headers.
- Changed frontend API-base selection to preserve an explicitly empty `VITE_API_URL`, allowing production browser calls to use same-origin routes. The default remains `http://localhost:8000` for local Compose use.
- Documented DNS, firewall, domain, same-origin, proxy-trust, and launch instructions in README and the role-by-role engineering walkthrough.

### Checks actually run

- `docker compose config --quiet` and `docker compose --profile production config --quiet` — passed.
- Rendered production config with `VITE_API_URL=` and asserted the empty same-origin build argument, stable Caddy IP, loopback-only API bind, and worker membership in the application network — passed.
- Frontend production build (`pnpm run build`, TypeScript and Vite) — passed.
- `git diff --check` and direct trailing-whitespace scans of the edited files — passed. Build-generated TypeScript `.tsbuildinfo` is now ignored. Application files remain untracked in the workspace.
- Docker Engine is unavailable and no local Caddy binary is installed. No container startup, Caddyfile parser check, certificate issuance, DNS, inbound reachability, or TLS handshake was run. Do not claim hosted TLS works until tested on the target host.

### Files/components changed

- New `Caddyfile`; `docker-compose.yml`; `.env.example`; `frontend/src/App.tsx`
- `.gitignore`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. On the actual deployment host, choose a non-conflicting Docker subnet, configure the real domain and strong secrets, set `WEB_ORIGIN=https://<domain>`, set `VITE_API_URL=` (empty), and set `FORWARDED_ALLOW_IPS` to the exact `CADDY_PROXY_IP`. Confirm DNS and firewall access on TCP 80/443 and UDP 443.
2. Run `docker compose --profile production up --build -d`; verify service health, Caddy certificate logs, browser TLS, security headers, same-origin login/intake/report requests and host-only API exposure.
3. Continue the live PostgreSQL/Neo4j concurrency, outbox/rebuild, backup/restore and retention checks when Docker is available.
4. Obtain authorized, annotated time-separated Indian recruitment-scam data and run the registered metrics/baselines. Data and measured results are still absent.
5. Resume by reading this checkpoint, checking `git status`, and working the first verifiable deployment or evaluation acceptance item.

### Resume commands

- Validate local and production Compose syntax: `docker compose config --quiet` and `docker compose --profile production config --quiet`.
- Build frontend: from `frontend`, run `pnpm run build`.
- Production launch only after real host configuration: `docker compose --profile production up --build -d`.
- Changes remain uncommitted.

## 2026-10-21 (16:37 Asia/Kolkata / 11:07 UTC) — Opt-in RDAP registration metadata source

### Completed in this stage

- Implemented an optional IANA-bootstrap RDAP adapter for extracted public domain names. It caches the IANA bootstrap response, uses longest suffix selection, accepts HTTPS bases only, disables inherited proxies, blocks redirects, applies timeout/response limits, validates the returned domain, strips contact objects, and persists a minimized metadata excerpt and response hash with retrieval timestamp and outcome.
- Added `RDAP_ENABLED` (off by default), `RDAP_TIMEOUT_SECONDS`, and `RDAP_MAX_RESPONSE_BYTES` to settings and Compose. RDAP is independent of local evidence corpus checks.
- Added migration `a7b13c9e4d20` to persist a separate RDAP consent per case. Enabling RDAP changes intake consent to `consent-v3-rdap`; text and upload APIs reject missing or stale separate consent. Intake explains that only extracted domains are queried and registry/network operators may log queries. Historical cases without consent stay local-only.
- Added consent version/choice to case serialization, audit records and the redacted report metadata. Worker source checks are gated by both global configuration and the case's consent.
- Restricted findings so RDAP outcomes cannot produce “Confirmed by an authoritative source,” “Evidence supports concern,” or local-corpus “No adverse evidence found.” Registry result/no-result remains insufficient evidence.
- Expanded `ENGINEERING_WALKTHROUGH.md` with the engineering decisions and per-role step-by-step implementation record; updated README operating instructions.

### Checks actually run

- Full backend suite with local loopback permitted for FastAPI TestClient: **49 tests passed** in 3.426 seconds. Includes mocked/offline bootstrap routing, domain validation, neutral 404, no redirect following, minimized success response, consent version/persistence, worker opt-in gating, and verdict boundary tests. The live RDAP service was not queried.
- `python -m compileall -q app tests evaluation` — passed.
- Disposable SQLite migration upgrade through `a7b13c9e4d20` and `alembic check` — passed; no schema drift detected.
- Frontend production build (`pnpm run build`, TypeScript and Vite) — passed.
- `docker compose config --quiet`, `git diff --check`, and a direct trailing-whitespace scan of edited files — passed. All project files are currently untracked in this workspace, so Git's diff whitespace check alone does not inspect those untracked files.
- Live PostgreSQL, Neo4j, hosted TLS and live RDAP/provider behavior remain unverified. Docker Engine remains unavailable.

### Files/components changed

- `backend/app/source_adapters.py`, `config.py`, `models.py`, `schemas.py`, `main.py`, `worker.py`, `findings.py`
- `backend/migrations/versions/a7b13c9e4d20_external_source_consent.py`
- `backend/tests/test_rdap_adapter.py`, `test_findings.py`, `test_api_flow.py`
- `frontend/src/App.tsx`, `.env.example`, `docker-compose.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Review and run the RDAP adapter against a controlled public test domain only after an operator explicitly enables it; validate network egress policy, service rate limits and real registry behavior. Keep it off for default local use.
2. Verify account row locking, job claiming, graph outbox failure/recovery/rebuild, and backup/restore against live PostgreSQL and Neo4j when Docker is available.
3. Complete deployment TLS, ingress/proxy configuration, monitoring, secrets and restore drill.
4. Obtain properly authorized Indian recruitment-scam data, annotate a chronological campaign-separated split, run the full comparisons, and record measured results. These are pending; no model performance is claimed.
5. Re-read this checkpoint and `BUILD_PLAN.md`, check `git status`, and proceed with the first incomplete deployment/evaluation acceptance item.

### Resume commands

- Backend: from `backend`, set `$env:PYTHONPATH='.pydeps'` and a disposable `$env:DATABASE_URL`, then run `python -m unittest discover -s tests -v`, `python -m compileall -q app tests evaluation`, `python -m alembic upgrade head`, and `python -m alembic check`.
- Frontend: from `frontend`, run `pnpm run build`.
- Root: run `docker compose config --quiet`. To enable optional RDAP, set `RDAP_ENABLED=true` and restart API plus worker; the API will require new `consent-v3-rdap` submissions with separate opt-in. Never enable this without reviewing the outbound data disclosure and egress policy.
- Changes remain uncommitted.

## 2026-10-21 (16:27 Asia/Kolkata / 10:57 UTC) — One-time account recovery

### Completed in this stage

- Added migration `9a4c1e7d2b60` and a persisted password reset credential record with only a keyed HMAC-SHA-256 token digest, requesting reviewer, creation/expiry/consumption timestamps, and account relation.
- Reviewers can issue a short-lived token with a required rationale. Issuing a replacement invalidates earlier unused reset credentials. The API returns the raw token once with `Cache-Control: no-store, private`; the interface presents it once and instructs the reviewer to deliver through a separately verified secure channel.
- Added unauthenticated token redemption, password hashing via the existing Argon2 helper, single-use/expiry checks, neutral invalid-token response, reset-attempt throttling, audit events that omit token material, and revocation of all old sessions. Resetting a suspended account does not reactivate it.
- Added a reset form to the sign-in screen, reviewer issuance control, `PASSWORD_RESET_TOKEN_MINUTES` configuration, and retention cleanup for expired reset records.
- Updated README and the engineering walkthrough to state that email/SMS and verified-email recovery are not implemented, manual delivery is required, and public registration requires TLS and a controlled identity-check process.

### Checks actually run

- Focused password recovery API flow — **1 passed**, covering reviewer authorization, hash-only persistence, expiry, replacement invalidation, redemption, one-time use, password change, old-session invalidation, old/new sign-in, and audit redaction.
- Final full backend suite after consistent account/token lock ordering — **41 tests passed** in 3.380 seconds; `python -m compileall -q app tests evaluation` passed.
- Disposable SQLite Alembic upgrade through `9a4c1e7d2b60` and `alembic check` — passed; “No new upgrade operations detected.”
- Frontend production build (`pnpm run build`, `tsc -b && vite build`) — passed.
- `docker compose config --quiet` and `git diff --check` — passed.
- Live PostgreSQL row-locking, Neo4j and actual TLS/out-of-band delivery remain unverified; Docker Engine is unavailable.

### Files changed

- `backend/app/config.py`, `models.py`, `schemas.py`, `main.py`, `worker.py`
- `backend/migrations/versions/9a4c1e7d2b60_password_reset_tokens.py`
- `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`, `.env.example`, `docker-compose.yml`
- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Verify the PostgreSQL implementation of the account-management row locks and reset-token single-use concurrency; Docker must be running for this.
2. Continue the full operational review: live Neo4j projection/rebuild, backup/restore drill, TLS, monitoring and actual hosted reverse-proxy address configuration.
3. Complete authorized, time-separated evaluation with real annotated Indian recruitment-scam data; the procedures exist but measurements are not claimed.
4. Add optional external source adapters only after access rights and terms are established. I4C remains manual/local-only unless written automated-access authorization is obtained.

### Resume commands

- Read this checkpoint, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `SOURCE_ACCESS_REVIEW.md`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`, then run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- For migration verification, use a disposable SQLite `DATABASE_URL`, run `python -m alembic upgrade head` and `python -m alembic check`. Run `pnpm run build` from `frontend`; run `docker compose config --quiet` from the root.
- Changes remain uncommitted.

## 2026-10-21 (16:22 Asia/Kolkata / 10:52 UTC) — Explicit trusted-proxy configuration

### Completed in this stage

- Added `FORWARDED_ALLOW_IPS` to the API container configuration. Default trust remains loopback only; hosted operators can set exact proxy IPs/networks. README explains why `*` must not be used unless all possible upstreams are trusted and normalize forwarding headers.
- Verified Uvicorn's official proxy guidance: forwarded headers are spoofable unless the direct peer is trusted, and wildcard trust is only appropriate when every upstream is trusted. Linked the official documentation in README.
- Added middleware tests demonstrating that an untrusted peer's fake `X-Forwarded-For` does not change the client address, while a configured trusted proxy can supply it. This is the address used by the persisted login and registration throttle routes.

### Checks actually run

- Uvicorn proxy trust tests — **2 passed**.
- Full backend suite — **40 tests passed** in 2.874 seconds; `python -m compileall -q app tests evaluation` passed.
- Frontend production build — passed.
- `docker compose config --quiet` and `git diff --check` — passed.
- Live hosted proxy-chain behavior remains unverified and must be validated against the actual ingress topology. Docker Engine remains unavailable.

### Files changed

- `.env.example`, `docker-compose.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`
- `backend/tests/test_proxy_headers.py`

### Remaining work / exact next steps

1. Build an operator-controlled password recovery flow or explicitly close public account creation before deployment. Recovery must use one-time expiring credentials, hashed storage, audit, and session revocation; do not expose passwords in audit/logs.
2. Validate PostgreSQL reviewer row locking and throttle concurrency, plus Neo4j projection failure/rebuild, when Docker becomes available.
3. Continue authorized evaluation, lawful source-adapter work, backup/restore exercise, and hosted deployment checks. No live external provider or evaluation result is claimed.

### Resume commands

- Read this checkpoint, `BUILD_PLAN.md`, `ENGINEERING_WALKTHROUGH.md`, and `SOURCE_ACCESS_REVIEW.md`.
- From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Changes remain uncommitted.

## 2026-10-21 (16:20 Asia/Kolkata / 10:50 UTC) — I4C source-access review

### Completed in this stage

- Reviewed the official NCRP Suspect Search Repository, the portal's repository/reporting descriptions, and Ministry of Home Affairs material.
- The public repository is a CAPTCHA-protected citizen search and carries an explicit warning that entries are complaint-based, not authenticated by I4C, can be erroneous, and are incomplete. No public machine API, developer process, or authorization for automated querying was documented in the materials inspected.
- Added `SOURCE_ACCESS_REVIEW.md` with the dated source links, scope, limitations, decision, handling requirements for manually sourced records, and prerequisites for considering any future automated connector.
- Updated README and the engineering walkthrough. The application continues to use the local evidence corpus and makes no I4C network calls; no API integration is claimed.

### Checks / evidence

- Official public pages inspected via web search: I4C Suspect Search Repository, NCRP feature description, Report Suspect form, and MHA Annual Report 2023–24. The repository page displayed a last-updated date of 02/02/2024 when inspected.
- `docker compose config --quiet` and `git diff --check` passed before these documentation-only edits; no runtime code changed in this source-review stage.
- This review does not prove that no private or law-enforcement API exists, and is not legal advice or authorization. See the review document's explicit verification limit.

### Remaining work / exact next steps

1. Continue account recovery/security review. Password reset and verified email remain unimplemented; validate reviewer lifecycle locking on PostgreSQL when Docker is available.
2. Assess and implement any lawful optional sources behind the adapter contract only where access terms and operational safeguards can be established. Keep local evidence mode complete and preserve outcome/provenance semantics.
3. Continue authorized time-separated evaluation and full deployment verification. Live PostgreSQL, Neo4j, backup/restore, TLS and monitoring checks remain open.

### Resume commands

- Re-read this file, `BUILD_PLAN.md`, `SOURCE_ACCESS_REVIEW.md`, and current code before continuing.
- From `backend`, set `$env:PYTHONPATH='.pydeps'` and `$env:DATABASE_URL='sqlite:///./unit-check.db'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Changes remain uncommitted.

## 2026-10-21 (16:19 Asia/Kolkata / 10:49 UTC) — Reviewer account lifecycle controls

### Completed in this stage

- Added reviewer-only `GET /api/accounts` and `PATCH /api/accounts/{id}/status`. The list exposes account metadata only to reviewers; changing active state requires a rationale and creates an audit event without copying the email into event details.
- Suspending or reactivating an account increments its persisted token version, invalidating all current bearer sessions. Reactivation does not restore old tokens. Reviewers cannot suspend themselves, and the API guards the active-reviewer minimum under PostgreSQL row locks.
- Added the responsive **Workspace accounts** reviewer screen. It does not provide role editing or password reset.
- Expanded the engineering walkthrough and README with authorization, audit, session revocation, recovery limitations, and the requirement for a controlled operator recovery procedure before public registration.
- Added a regression test covering reviewer-only access, suspension, reactivation, stale-token rejection, self-suspension rejection, remaining active reviewer, and persisted audit records.

### Checks actually run

- Focused reviewer account-control API test — **1 passed**.
- Final full backend suite after adding the non-reviewer mutation denial assertion — **38 tests passed** in 2.911 seconds; `python -m compileall -q app tests evaluation` passed.
- Frontend production build (`pnpm run build`, `tsc -b && vite build`) — passed.
- `docker compose config --quiet` and `git diff --check` — passed. The subsequent Docker Engine availability check failed because the Docker Desktop Linux Engine named pipe is absent; live PostgreSQL row-lock behavior and Neo4j integration remain unverified.
- Existing non-failing Starlette/httpx test-client deprecation warning remains.

### Files changed

- `backend/app/main.py`, `backend/app/schemas.py`, `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`, `frontend/src/style.css`
- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Verify what official I4C materials document about automated access and record the result with source references. Keep the local corpus workflow complete and do not scrape or invent an API.
2. Continue account recovery and security review. Password reset/verified email are not implemented; reverse-proxy client IP behavior and Postgres lock concurrency require a real deployment test.
3. Continue toward the remaining release criteria: lawful source adapters, authorized time-separated evaluation and baselines, live PostgreSQL/Neo4j checks, backup/restore drill, TLS/monitoring and end-to-end deployment verification.

### Resume commands

- Read this checkpoint and `BUILD_PLAN.md`; from `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`, then run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Run `pnpm run build` from `frontend`; run `docker compose config --quiet` from the repository root. Start live integration only after Docker Desktop's Linux Engine is available.
- Changes remain uncommitted.

## 2026-10-21 (16:15 Asia/Kolkata / 10:45 UTC) — Registration-abuse throttling

### Completed in this stage

- Added persistent registration request throttling keyed by the direct connection peer, with a distinct hashed namespace from sign-in limits. Default policy: 20 registration requests in 15 minutes, then a 15-minute lockout. All attempts count, including successes and rejected registrations, which slows both account creation and probing of one-time role setup codes.
- Reused the existing database-backed throttle table and retention cleanup; throttle keys use HMAC-SHA-256, and raw IP addresses/account contents are not added to the key or audit events. A client-supplied `X-Forwarded-For` header does not choose the bucket.
- Added positive configuration validation and exposed the registration limits in Compose and `.env.example`.
- Expanded `README.md` and `ENGINEERING_WALKTHROUGH.md` with the security rationale, variables, proxy trust boundary, and deployment-specific verification requirement. The engineering document continues to separate implemented work from unverified operational behavior.
- Added an API regression test for the request ceiling and spoofed forwarding header.

### Checks actually run

- Focused TestClient registration throttle regression — **1 passed**.
- Final full backend suite after switching throttle fingerprints to HMAC-SHA-256 — **37 tests passed** in 2.693 seconds; `python -m compileall -q app tests evaluation` passed.
- Frontend production build (`pnpm run build`, `tsc -b && vite build`) — passed.
- `docker compose config --quiet` — passed.
- `git diff --check` — passed.
- Backend emits an existing Starlette/httpx deprecation warning. Docker live services were not started in this stage; PostgreSQL concurrency and reverse-proxy forwarded-address behavior remain unverified.

### Files changed

- `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_api_flow.py`
- `.env.example`, `docker-compose.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work / exact next steps

1. Check Docker Desktop availability. If available, run the full Compose stack and verify migrations, multi-worker PostgreSQL throttle behavior, and Neo4j outbox retry/rebuild flows against live services.
2. Continue account lifecycle and deployment security review. In particular, decide and implement an operator-supported account provisioning/suspension path; do not trust proxy headers unless the trusted proxy boundary is explicitly configured and validated.
3. Continue source-adapter lawful-access review and complete the authorized, time-separated evaluation run. No external service or evaluation result is claimed.

### Resume commands

- Read this checkpoint and `BUILD_PLAN.md`; from `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`, then run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Run `pnpm run build` from `frontend`; run `docker compose config --quiet` from the repository root. For service integration, first confirm Docker Desktop's Linux Engine is running, then `docker compose up --build`.
- Changes remain uncommitted.

## 2026-10-21 (16:07 Asia/Kolkata / 10:37 UTC) — Durable graph projection outbox

### Completed in this stage

- Added `graph_projection_outbox` migration `d84f8a1a5301` and model. Each case has a coalesced, generation-versioned outbox item; delete tombstones deliberately have no foreign key so they survive case deletion.
- Enqueued graph work in the same relational transaction as processing success/failure, entity review, corrections, campaign recomputation, link review, and retention deletion. Neo4j unavailability does not block PostgreSQL workflow commits.
- The worker claims due jobs using row locks/`SKIP LOCKED`, retries failures with bounded exponential delay, stores only the error class in the outbox, and recovers `running` jobs abandoned for more than ten minutes. A newer generation arriving during a projection remains queued and is applied after the older run.
- Graph case upserts now remove stale campaign edges before recreating current relationships. Retention produces delete tombstones; projection deletion also removes orphan identifier nodes.
- The graph endpoint now serves PostgreSQL-derived data whenever any outbox event is queued/running, as well as when Neo4j is unavailable; it will not intentionally show a known-stale Neo4j projection. A regression assertion exercises that fallback while a failed projection awaits retry.
- Updated README and engineering walkthrough with eventual projection consistency and rebuild behavior.

### Checks actually run

- Focused outbox failure/generation and retention-tombstone tests — **2 passed**.
- Full backend suite — **36 tests passed** in 2.473 seconds; `python -m compileall -q app tests evaluation` and targeted `py_compile` passed. The graph outbox regression also invokes the investigator entity-review route directly and verifies it persists a new projection generation.
- Disposable SQLite Alembic upgrade through `d84f8a1a5301` and `alembic check` — passed; “No new upgrade operations detected.”
- Frontend production build (`tsc -b && vite build`) — passed.
- `docker compose config --quiet` — passed. Docker Desktop's Linux engine is unavailable, so Neo4j Cypher execution and PostgreSQL concurrency behavior remain unverified.
- Non-failing Starlette/httpx and PyMuPDF/fitz deprecation warnings remain.

### Files changed

- `backend/app/models.py`, `graph_outbox.py`, `graph_store.py`, `main.py`, `worker.py`
- `backend/migrations/versions/d84f8a1a5301_graph_projection_outbox.py`
- `backend/tests/test_api_flow.py`
- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Remaining work

1. When Docker is available, verify PostgreSQL migration/upsert locking with multiple workers and exercise Neo4j update failure, retry, stale-edge replacement, tombstone deletion, and full rebuild against a real server.
2. Continue account lifecycle/security, source adapter legality/configuration, and authorized time-separated evaluation tasks recorded below. This outbox stage does not make the platform release-ready.

### Resume commands

- Read this checkpoint and `BUILD_PLAN.md`; from `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Run disposable migration check with `python -m alembic upgrade head` and `python -m alembic check`; run frontend build with `pnpm run build` from `frontend`.
- Changes remain uncommitted.

## 2026-10-21 (16:02 Asia/Kolkata / 10:32 UTC) — Redacted API field minimization

### Completed in this stage

- Expanded the API review from exception messages to arbitrary user-controlled text. Deterministic contact regexes cannot reliably detect unlabelled personal names, so analyst responses now omit free-text case titles, evidence source names/claims/excerpts, human review rationales and evidence details. They retain record IDs, types, outcomes, source categories, authority, review state and timestamps.
- Redacted report exports now also withhold free-text titles, source names/claims/excerpts and rationales. HTTP(S) source references retain the origin but replace path, query and fragment values; opaque system-generated local record references remain stable. The access-controlled investigator/reviewer case view retains the source content and exact references.
- Kept reviewer case access consistent with reviewer authority and the existing interface; analysts remain read-only and receive the minimized response.
- Updated the public policy description and case-view privacy message. Strengthened the API regression fixture with an unlabelled personal name in the title, source claim and excerpt, plus identifying path/query values in a source URL. Tests cover case detail, case list, campaign view and redacted report; a reviewer assertion confirms authorized source visibility.

### Checks actually run

- Expanded focused analyst/reviewer privacy API test — **1 passed**.
- Full backend suite — **35 tests passed** in 2.389 seconds; Python compilation passed.
- Frontend production build — passed (`tsc -b && vite build`).
- `docker compose config --quiet` and `git diff --check` — passed.
- `docker info --format '{{.ServerVersion}}'` — could not connect to the Docker Desktop Linux Engine named pipe; live integration remains unavailable in this environment.
- Deprecation warnings remain for Starlette/httpx and PyMuPDF/fitz. No live PostgreSQL or Neo4j deployment validation was possible.

### Files changed

- `backend/app/main.py`
- `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`
- `BUILD_STATUS.md`

### Remaining work

- Redaction is response minimization, not legal anonymization: an authorized investigator/reviewer can view submitted personal data, source hostnames can still be identifying, and logs/backups need separate access/retention controls. Continue route-by-route checks and verify all rendered surfaces.
- Durable, retryable projection work was added in the 16:07 checkpoint. Live PostgreSQL/Neo4j Docker integration, operational hardening and authorized evaluation remain.

### Resume command

- Read this file and `BUILD_PLAN.md`. From `backend`, set `$env:PYTHONPATH='.pydeps'`, `$env:DATABASE_URL='sqlite:///./unit-check.db'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`. From `frontend`, run `pnpm run build`.
- Changes remain uncommitted.

## 2026-10-21 (15:57 Asia/Kolkata / 10:27 UTC) — Safe processing-error API response

### Completed in this stage

- During the documented API privacy review, found that `GET /api/cases/{id}` returned the worker's raw `last_error` string. Exception text can contain internal filesystem paths or data derived from submitted material.
- Changed case detail to return an actionable but generic recovery message when processing failed. Raw diagnostics remain in protected service logs and are no longer serialized to authenticated users through this endpoint.
- Added a regression assertion that persists an internal error string containing a Windows path, a recruiter name and a phone number, then verifies the analyst response contains none of those values.

### Checks actually run

- Focused API privacy flow — **1 passed**.
- Full backend suite — **35 tests passed** in 2.739 seconds; `python -m compileall -q app tests evaluation` passed.
- The test run reports non-failing Starlette/httpx and PyMuPDF/fitz deprecation warnings.

### Files changed

- `backend/app/main.py`
- `backend/tests/test_api_flow.py`
- `BUILD_STATUS.md`
- The previous `ENGINEERING_WALKTHROUGH.md` already documents the broad privacy/security work; add this API response safeguard to its next consolidated engineering update.

### Remaining work

- Continue the API-by-API privacy review. Unlabelled personal names and arbitrary source material cannot be comprehensively masked by current deterministic text redaction; assess role-based access and field minimization, then add targeted tests.
- Then continue current checkpoint steps for Docker/PostgreSQL/Neo4j operations, graph reconciliation, deployment hardening, lawful external adapters, and authorized evaluation. The new response test does not prove those criteria.

### Resume command

- From `backend`, set `$env:PYTHONPATH='.pydeps'` and `$env:DATABASE_URL='sqlite:///./unit-check.db'`; run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Changes remain uncommitted.

## 2026-10-21 (15:54 Asia/Kolkata / 10:24 UTC) — Evaluation and operations checkpoint

### Completed in this stage

- Fixed the TF-IDF baseline's relative-import indentation and verified its CLI via unit tests.
- Added/verified chronological train/dev/test split validation in the scorer and TF-IDF input loader. The scorer also rejects campaign leakage across splits.
- Added a deterministic, dependency-free TF-IDF + logistic-regression baseline, a graph-ablation output transformer that requires measured timings from an actual ablated run, and a four-run comparator that enforces identical case IDs and gold provenance.
- Added the investigator evidence correction flow and confirmed that applied corrections flush before checking whether campaign links still share identifiers; stale links are correctly invalidated.
- Added persistent privacy-minimal login throttling, recruiter-label masking, analyst authorization assertions, and PowerShell backup/restore scripts with checksum and archive path checks in the prior stage. Updated the engineering walkthrough to describe them accurately.
- Updated the engineering walkthrough and evaluation guide to distinguish implemented tooling from experiments that still require authorized data and provider configuration.

### Checks actually run

- From `backend`, `PYTHONPATH=.pydeps`, `DATABASE_URL=sqlite:///./unit-check.db`, `python -m unittest discover -s tests -v` — **35 tests passed** in 2.948 seconds, including API flows, campaign rules, entity normalization/extraction, findings boundaries, evaluation, and TF-IDF runner.
- `python -m compileall -q app tests evaluation` — passed.
- Focused evaluation tests — **5 passed**; TF-IDF baseline tests — **3 passed**.
- From `frontend`, `pnpm run build` — passed (`tsc -b && vite build`).
- Disposable SQLite migration upgrade and `python -m alembic check` — passed; “No new upgrade operations detected.” The first invocation omitted `PYTHONPATH=.pydeps` and could not import Alembic; rerun with the proper path passed.
- `docker compose config --quiet` — passed.
- PowerShell parser checks for `scripts/backup.ps1` and `scripts/restore.ps1` — passed.
- Non-failing warnings: Starlette's current `httpx` test integration is deprecated; PyMuPDF's `fitz` import is deprecated. Docker Engine is unavailable, so live container, PostgreSQL, Neo4j and backup/restore behavior were not exercised.

### Files changed in this stage

- `backend/evaluation/baseline_tfidf_logreg.py` (fixed import indentation)
- `ENGINEERING_WALKTHROUGH.md` (evaluation process, commands, limitations and checkpoint record)
- `BUILD_STATUS.md`
- The prior work in this continuing session also changed API/model/security, tests, migrations, UI, Compose/env, evaluation utilities, README, and `scripts/backup.ps1` / `scripts/restore.ps1`; details are retained in the earlier checkpoints below.

### Remaining work, in order

1. Do an API-by-API privacy/authorization review, including unlabelled arbitrary personal names, source URLs, raw evidence excerpts, exports, audit access, and proxy-aware client address handling. Add regression tests for confirmed leaks/fixes.
2. Run the full stack against Docker/PostgreSQL/Neo4j when the engine is available: migration startup, intake/worker/OCR, graph projection and rebuild, correction propagation, retention, backup and restore. Current SQLite and unit tests do not prove these integrations.
3. Improve operational guarantees: durable graph projection reconciliation/outbox, account lifecycle and recovery, TLS/hosted secret management, monitoring, and backup encryption/restore drill.
4. Complete source adapter design only after lawful access and terms are verified. I4C integration is not implemented; continue with curated local evidence.
5. Complete authorized time-separated evaluation: build/publish annotation protocol, run the TF-IDF baseline and matched full/no-graph systems, and run an LLM/web-search comparator only with configured lawful providers and provenance. Do not invent metrics. The graph-ablation helper transforms true measured no-graph timings; it is not an ablated runtime.
6. Run end-to-end release verification and update this file after each stage. Do not call the current system fully working or release-ready until these gaps are closed.

### Resume commands

- Start by reading `BUILD_PLAN.md`, this checkpoint, `ENGINEERING_WALKTHROUGH.md`, applicable project instructions, and `git status`.
- Backend: from `backend`, set `$env:PYTHONPATH='.pydeps'` and `$env:DATABASE_URL='sqlite:///./unit-check.db'`, then run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests evaluation`.
- Frontend: from `frontend`, run `pnpm run build`.
- Migrations: from `backend`, set `PYTHONPATH` to `.pydeps` and a disposable SQLite `DATABASE_URL`; run `python -m alembic upgrade head` and `python -m alembic check`.
- Compose/parser checks: repository root `docker compose config --quiet`; parse both PowerShell scripts with `System.Management.Automation.Language.Parser`.
- Changes remain uncommitted. No real case data or evaluation metrics were added.

## 2026-10-21 (Asia/Kolkata; 2026-10-20 21:25 UTC) — Correction and sign-in security checkpoint

### Completed in this stage

- Extended the investigator correction form to target either one extracted entity or one evidence record and offer the relevant action set. The API rejects multiple targets in one action.
- Added test coverage for evidence contradiction corrections, exact phone normalization on corrected values, and withdrawal of a campaign link after the shared identifier is rejected. The link test found that `SessionLocal` disables autoflush; `apply_correction` now explicitly flushes changes before checking shared identifiers.
- Added configurable PostgreSQL-persisted sign-in throttling keyed by a hash of normalized email, direct client address and the JWT secret. Failed attempts are generic; unknown accounts perform a dummy Argon2 verification. Failure audit events omit account/address data. Expired throttle records are purged by retention maintenance.
- Added `login_throttles` migration `c96cc6d17573`, validated config at API startup, passed login settings into Compose for API and worker, and documented settings in `.env.example` and README.
- Expanded engineering documentation for sign-in security.

### Checks actually run

- Backend: `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — **30 tests passed**, including API correction token, entity reject/correction, evidence contradiction, campaign link staleness, generic login failures, persistent throttling and lockout.
- Backend syntax: `python -m compileall -q app tests evaluation` — passed.
- Frontend: `pnpm run build` (`tsc -b && vite build`) — passed after evidence-target correction UI changes.
- Migrations: disposable SQLite upgrade through `c96cc6d17573` and `python -m alembic check` — passed; no new operations detected.
- Compose configuration: `docker compose config --quiet` — passed.
- API tests required local loopback; the Windows sandbox denied it without escalation (WSAEACCES 10013). The test command was run with approved local network access. PostgreSQL concurrency and Neo4j runtime are still unverified.
- Test warnings: Starlette reports a deprecation for its `httpx` integration; PyMuPDF’s legacy `fitz` import reports a future deprecation. Neither failed the test run.

### Files/components changed

- `backend/app/config.py`, `models.py`, `main.py`, `security.py`, `worker.py`
- `backend/migrations/versions/c96cc6d17573_persist_login_throttles.py`
- `backend/tests/test_api_flow.py`
- `frontend/src/App.tsx`
- `.env.example`, `docker-compose.yml`, `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known gaps and next steps, in order

1. Review authorization and privacy across every API response/export, particularly arbitrary text/source URL redaction, login throttle behavior behind a trusted reverse proxy, and case-level event access; add focused tests for findings.
2. Add operations-grade PostgreSQL backup/restore instructions and executable commands; then validate them against a running database when Docker/PostgreSQL is available.
3. Implement reproducible baseline runners (TF-IDF + logistic regression, graph ablation, and a clearly configured LLM/web-search comparator interface) without inventing results or requiring hidden credentials.
4. Continue deployment hardening and verify production containers, Postgres migration/queue concurrency, Neo4j projection rebuild, OCR fixtures, retention deletion, and a full intake-to-report journey when runtime services are available.
5. Keep external source adapters unimplemented unless lawful access and terms are verified; no I4C API is assumed. Keep evaluation metrics pending until authorized time-separated data exists.

### Resume commands

- Re-read `BUILD_PLAN.md`, this file, `ENGINEERING_WALKTHROUGH.md`, and `git status`; continue from step 1 above.
- Backend (from `backend`): set `$env:PYTHONPATH='.pydeps'`; run `python -m unittest discover -s tests -v` (requires local loopback access for Starlette TestClient), then `python -m compileall -q app tests evaluation`.
- Frontend (from `frontend`): `pnpm run build`.
- SQLite migration check (from `backend`): set `$env:PYTHONPATH='.pydeps'` and `$env:DATABASE_URL='sqlite:///./migration-check.db'`; run `python -m alembic upgrade head` then `python -m alembic check`.
- Compose syntax (repository root): `docker compose config --quiet`.
- No commit was made; do not commit unless requested.

## 2026-10-21 (Asia/Kolkata; 2026-10-20 21:18 UTC) — Correction workflow checkpoint

### Completed in this stage

- Added one-time requester status credentials for correction requests. The API returns the token once, stores only a SHA-256 hash, and reveals status/resolution only when the request reference and token both match. Invalid references/tokens share a not-found response.
- Added investigator correction application for a case-specific entity or evidence record. Entity action can confirm, reject, or replace a value using the existing type normalizer; evidence can be marked relevant, irrelevant, needs review, or contradicts. Every applied action requires a rationale and persists before/after values in the audit event.
- Applied corrections recalculate persisted machine findings. Entity changes stale current links that no longer have a shared exact identifier and attempt to sync the Neo4j projection. Postgres stays authoritative.
- Added requester status lookup and investigator entity action controls to the frontend. Evidence-target correction is supported by the API but not yet exposed in the UI.
- Added migration `b6a6c0192de4_correction_status_tokens.py`.
- Expanded [ENGINEERING_WALKTHROUGH.md](ENGINEERING_WALKTHROUGH.md) with the engineering choices, user flow and correction workflow.

### Checks actually run

- Backend unit checks: 25 passed across campaign rules (4), extraction (8), file validation/graph projection (5), findings (5), and evaluation metrics (3).
- Backend syntax: `python -m compileall -q app tests evaluation` — passed.
- Frontend: `pnpm run build` (`tsc -b && vite build`) — passed.
- Migrations: disposable SQLite `python -m alembic upgrade head` through `b6a6c0192de4`, then `python -m alembic check` — passed; no new operations detected.
- Compose: `docker compose config --quiet` — passed.
- API flow tests were attempted, but `TestClient(app).__enter__()` hung before test execution while Python 3.14/Starlette created its Windows asyncio socket pair. A selector event-loop policy did not resolve it. Do not count API correction-flow tests as passed. Earlier API test results were from the pre-correction-token code and do not verify this stage.
- Docker runtime, PostgreSQL, Neo4j, and hosted deployment remain unverified; Docker Engine is unavailable here.

### Files/components changed

- `backend/app/models.py`, `schemas.py`, `main.py`
- `backend/migrations/versions/b6a6c0192de4_correction_status_tokens.py`
- `backend/tests/test_api_flow.py` (new status-token and applied-correction assertions; test execution currently blocked as described above)
- `frontend/src/App.tsx`
- `README.md`, `ENGINEERING_WALKTHROUGH.md`, `BUILD_STATUS.md`

### Known gaps and next steps, in order

1. Resolve or work around the Windows Python 3.14 Starlette TestClient startup hang; then run the entire API flow suite, including requester token authentication and correction application.
2. Expose evidence-target correction actions in the investigator interface and add validation/integration coverage for corrected identifier normalization, finding snapshots, campaign-link staleness and graph fallback.
3. Add target-specific correction communication. Current requester status lets the requester check progress only if they safely retain the one-time token; there is no email/SMS delivery or token recovery.
4. Continue privacy/security review (rate limits, login failure audit, correction queue/detail redaction, full report/source-URL redaction, account lifecycle and CSRF/session hardening).
5. Implement and verify the remaining deployment, external-source, evaluation-baseline and operational requirements listed in the prior checkpoint below. Do not call this release-ready.

### Resume commands

- Read `BUILD_PLAN.md`, this file and `git status`; continue from step 1 above.
- Backend unit checks from `backend`: set `$env:PYTHONPATH='.pydeps'` and `$env:DATABASE_URL='sqlite:///./unit-check.db'`, then run the five individual `unittest discover` commands recorded in this checkpoint; run API tests only after fixing the TestClient startup hang.
- Frontend: from `frontend`, run `pnpm run build`.
- Migrations: from `backend`, set `$env:DATABASE_URL='sqlite:///./migration-check.db'` and run `python -m alembic upgrade head` then `python -m alembic check`.
- Compose: from the repository root, run `docker compose config --quiet`.
- Changes remain uncommitted; do not commit unless requested.

## 2026-10-21 (Asia/Kolkata; 2026-10-20 20:47 UTC) — Active implementation checkpoint

### Repository and architecture

- Repository was empty apart from Git metadata when work began. Stack is React/TypeScript/Vite served by Nginx, FastAPI, PostgreSQL as system of record, Alembic migrations, a PostgreSQL-backed background queue, Neo4j as a rebuildable projection, and private local upload storage.
- The app has a local evidence corpus and does not depend on an LLM, paid services, or I4C access. No I4C API or automated access is claimed.
- `BUILD_PLAN.md` describes the stages and `README.md` provides local Compose setup.

### Implemented work

- Compose services for Postgres, Neo4j, API, worker, and production frontend bundle.
- Authentication with Argon2 password hashing, bearer sessions, role checks, and an investigator bootstrap code.
- Persisted cases, consent version/time, evidence, entities, audits, campaign links, durable processing jobs, corpus records, and correction requests.
- Text and private image/PDF intake, content signature and size checks, PDF parsing, Tesseract OCR with page/pixel/time limits, and queued/running/completed/failed states with retries.
- Deterministic extraction for email, Indian phone, URLs/domains, UPI-shaped values, and fee claims; local exact corpus lookup with retrieval outcome/provenance.
- Investigator review of extracted entities and evidence, deterministic case links with rejected-entity filtering, graph view/rebuild command, and PostgreSQL graph fallback.
- Analyst masking for contact identifiers and excerpts, redacted JSON report download, timeline, case detail, corpus management, campaign leads, and correction-request review queue.
- Public correction intake and investigator review with persistent request reference, resolution, and audit. It does not currently notify the requester or automatically propagate a correction to linked evidence/reports; this is incomplete.
- Persisted evidence relevance review (`relevant`, `irrelevant`, `needs_review`) with required rationale, reviewer/time, investigator UI controls, and case timeline audit event.
- Deterministic extraction stores the source text kind and exact character offsets for candidate matches; investigator UI displays the excerpt and span. Upload-derived spans refer to extracted text, not original page/image coordinates.
- PDF extraction maps identifiers to page numbers and page-relative character spans; image OCR output is separately labeled. Scanned fixtures still need verification in the deployment container.
- Every entity queried against the local evidence corpus now receives a persisted exact-match result or an explicit, timestamped neutral `no_result` record. Empty local corpus results state that they are not evidence of fraud or legitimacy.
- PostgreSQL and bundled corpus matching now run through a structured `LocalEvidenceCorpusAdapter` which returns a consistent source/outcome/retrieval/provenance record.
- Intake validates the active consent version server-side for both text and file submissions, requires explicit consent, and validates non-space upload titles. Stale clients must review the current notice before submitting.
- Redacted JSON reports include evidence outcome/review summaries, extraction source spans, system limitations, rule versions, and a redacted chronological case audit timeline; human actions remain distinct from system assessment.
- Stronger human dispositions require relevant result-bearing evidence and remain pending until a separate reviewer approves or rejects them with a rationale. A separate reviewer account uses a one-time setup code. Approval rechecks supporting evidence; self-review is prohibited. Case view, report, and reviewer queue preserve this as a human record, separate from system assessment.
- Startup rejects placeholder JWT, database, and Neo4j secrets, and requires separate investigator/reviewer bootstrap codes.
- URL normalization now lowercases scheme/host only, preserves case-sensitive paths/queries, handles IDNA hostnames, and avoids normalizing URLs containing embedded credentials into a mergeable identifier.
- Bearer sessions now carry a persisted user token version; logout increments it and invalidates existing tokens. Sign-in, case list/detail, graph, correction queue, and evidence corpus reads are audited. Retention also deletes expired global audit events.
- Retention policy endpoint and daily worker purge for cases, their audit/evidence records and private uploads, local corpus records, and correction requests.
- Evaluation schema/protocol and dependency-free scorer at `backend/evaluation/`. Metrics are pending authorized labeled data; no results are claimed.
- Versioned deterministic campaign signals now use documented per-type weights: phone/email/UPI 40, URL 25, domain 15; a URL and its derived domain count as one infrastructure signal. Thresholds are configurable from `CAMPAIGN_LINK_THRESHOLD` and included in the rule version. Pair explanations and scores are explicitly leads, not probability or guilt.
- A PostgreSQL-derived campaign-group endpoint and investigator view show connected cases, matching identifiers, rule version/score, and related evidence, with analyst masking. Group views omit rejected and stale links.
- Rejecting an extracted entity now stales all affected links, records an audit event, and syncs the graph projection; recomputation can reactivate a stale link under the current rule version. Stale links cannot be reviewed as active evidence.
- Deterministic extraction now also captures explicitly labeled company, role, recruiter, and location claims, plus literal dates and INR/₹/Rs amounts. These remain candidate claims, not verified facts. Each extraction persists character spans, parser confidence and an uncertainty explanation; the investigator case view surfaces that confidence is about extraction shape, not truth.
- Graph API responses now use stable hashed entity-node handles, mask recruiter-name labels, and redact contact values from link explanations; PostgreSQL fallback and Neo4j-backed responses use the same masked display behavior.

### Current verification

- Backend: `PYTHONPATH=.pydeps python -m unittest discover -s tests -v` — 24 tests passed. This includes all previously listed coverage plus explicitly labeled claim extraction, exact character spans, persisted uncertainty metadata, and graph node-id masking.
- Additional API assertions reject stale consent versions for text and multipart file submissions and check report redaction/review metadata.
- Backend syntax: `python -m compileall -q app tests evaluation` — passed with the test run.
- Migrations: `python -m alembic upgrade head` and `python -m alembic check` — passed on disposable SQLite through new revision `d1c77aa03521`; Alembic reported “No new upgrade operations detected.”
- Frontend: pnpm production build (`tsc -b && vite build`) — passed with campaign groups, stale-link behavior, and extraction uncertainty display.
- `docker compose config --quiet` and `git diff --check` — passed after current edits.
- The test dependencies are in ignored `backend/.pydeps`, and these tests use Python 3.14/SQLite rather than the pinned Python 3.12/Postgres deployment.
- Docker Engine is unavailable in this environment, so Postgres/Neo4j container startup, their real-server integrations, and full deployment startup have not been verified.

### Incomplete and known limitations

- Not release-ready; do not describe as fully working until remaining workflows and deployment checks are completed.
- No external source adapters are implemented. Local corpus starts empty and must be populated with sources the operator may lawfully retain. No web fetching or assumed I4C interface exists.
- Failed/unavailable external outcomes are not generated because there are no external source adapters; local exact lookup returns result or no-result outcomes.
- Entity extraction is deterministic regex/OCR; pasted-text and PDF page-relative spans are recorded, but image-region references, confidence/uncertainty, structured organization/job/title/date extraction, and richer source-location metadata remain incomplete.
- System assessment currently remains conservative and limited; full claim-level evidence weighting, conflicts/missing-check findings, and assessment rules are not implemented.
- Campaign matching is deterministic and versioned for exact phone/email/UPI/URL/domain links, with configurable thresholds, evidence/rule explanations, campaign groups, masking, and stale-link invalidation. Domain-context interpretation and deeper false-match analysis still need work; this is an investigative lead system, not guilt determination.
- Public correction status is accessible with a one-time token and investigators can apply a targeted entity/evidence change with finding/link recalculation. No email/SMS notification or token recovery exists; evidence correction controls are not yet exposed in the UI. Applied changes need API tests and live projection verification.
- Graph projection/rebuild and graph reads are implemented but unverified against a live Neo4j server. Projection sync is best-effort without a durable outbox.
- Report is redacted JSON, not a styled PDF. Redaction review across all excerpts and source URLs needs further work.
- Consent notice version enforcement is implemented, but the notice still needs a complete legal/privacy review by the deploying organization; software does not guarantee legal compliance.
- Access audit coverage is improved but still partial; failed login auditing, account lifecycle controls, rate limiting, additional authorization review, and security hardening remain incomplete.
- Deployment lacks TLS/hosted provider configuration, monitoring, backup/restore automation and Postgres/Neo4j operational validation. Compose example passwords/secrets must be replaced before use.
- Evaluation metric script and docs have not yet been executed/validated; authorized data, baseline runner implementations, and measured results are absent.
- Scanned image/PDF OCR, unsafe URL protection (URL fetching is not implemented), correction propagation, deletion behavior under Postgres, and full end-to-end journeys need additional verification.

### Next steps, in order

1. Resolve the Windows Starlette TestClient startup hang and run API-level coverage of current findings and correction paths.
2. Expose evidence-target corrections in the UI and verify correction propagation/recalculation across evidence, links, reports and graph.
3. Add requester communication or a safe status-token recovery path, then extend audit coverage and account lifecycle controls.
4. Add API-level graph access/redaction tests and review other routes for identifier leakage, including corpus and audit records.
5. Improve domain-context campaign rules and add sensitive false-match review cases; retain versioned history and lead-only language.
6. Add optional source adapters only after lawful access and terms are verified; do not assume an I4C API.
7. Add runnable baseline procedures and run evaluation only on a properly authorized time-separated dataset; keep results pending until then.
8. When Docker is available, run production build/start, real Postgres migrations, Neo4j projection/rebuild, OCR, backups/restores, and end-to-end checks.
9. Complete deployment operations documentation and redaction review, then run an end-to-end release checklist.

### Resume instructions

Re-read this file, `BUILD_PLAN.md`, repository instructions (if added), and `git status`. Continue from step 1 above. Backend checks: from `backend`, set `$env:PYTHONPATH='.pydeps'` and run `python -m unittest discover -s tests -v`. Frontend: from `frontend`, run `pnpm run build`. Docker integration checks require Docker Desktop Linux Engine, which was unavailable at this checkpoint. Configure distinct `INITIAL_INVESTIGATOR_CODE` and `INITIAL_REVIEWER_CODE` values in `.env`. Do not commit unless requested.























## 2026-11-03 20:24 (Asia/Kolkata) — Backend dependency security audit

### Completed work

- Audited backend pinned dependencies. The previous versions had known advisory findings affecting four direct dependencies.
- Updated FastAPI, Starlette, `python-multipart`, PyJWT and Pillow pins; added pinned `pip-audit` to backend CI.
- Rebuilt API and worker containers. Updated live API readiness reports FastAPI 0.142.3, Starlette 1.5.1, PyJWT 2.15.1, Pillow 13.0.0 and `python-multipart` 0.0.33.
- Documented the work in the engineering walkthrough and README; updated the acceptance traceability matrix.

### Checks actually run

- `pip-audit -r requirements.txt`: passed; no known vulnerabilities found in the pinned backend requirements.
- Backend harness in a disposable isolated container: 224 unit tests passed; 15 API-flow tests passed; 2 proxy tests passed. Two opt-in PostgreSQL tests were skipped in this harness; they passed separately against disposable migrated PostgreSQL test databases in an earlier stage.
- API readiness/version check: passed.
- `docker compose config -q`: passed. Verification Compose services (db, API, worker, web and Neo4j): all healthy.
- CI workflow YAML parsing and assertion that the pinned audit step exists: passed.

### Files/components changed

- `backend/requirements.txt`
- `.github/workflows/ci.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known gaps and next steps, in order

1. Run CI on a hosted runner after a repository remote is configured.
2. Complete the browser-based review of the Corrections page and graph filters only if the local-origin approval gate permits it; prior approval was declined, so do not bypass it.
3. Deploy to operator-owned hosting and verify TLS, storage controls, backup encryption and recovery.
4. Obtain authorized time-separated Indian recruitment-scam annotations and run the documented comparisons; report measured results only.
5. Continue reviewing hosted operational behavior, retention/deletion and restore procedures before calling the release complete.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 80`
- `docker compose -p rsaicdp-verification-20261103 ps`
- `docker compose config -q`
- `python -m pip install --disable-pip-version-check pip-audit==2.10.1; pip-audit -r backend/requirements.txt`
- `pnpm --dir frontend run build`

## 2026-11-12 17:12 (Asia/Calcutta) — Gate frontend dependency advisories in CI

### Completed work

- Audited all frontend dependencies and the production-only subset. Both `pnpm audit` and `pnpm audit --prod` reported no known vulnerabilities.
- Added `pnpm audit` to frontend CI between frozen-lockfile installation and the production build.
- Updated the README and requirements traceability matrix. The engineering walkthrough now records this work.

### Checks actually run

- `pnpm audit`: passed; no known vulnerabilities found.
- `pnpm run build`: passed with Vite 8.3.4.
- `pnpm run test:redaction`: 24 passed, 0 failed.
- Parsed `.github/workflows/ci.yml` using PyYAML in the running worker container and asserted that the frontend audit step runs `pnpm audit`: passed. An initial parser path was not mounted in the container and failed before parsing; the copied-file retry passed.

### Files or components changed

- `.github/workflows/ci.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Hosted CI has not run because no Git remote/runner is configured.
- Browser review of Corrections and graph filters remains unverified; prior browser-origin approval was declined.
- Hosted deployment, operator security/recovery verification, and evaluation with authorized time-separated data remain incomplete.

### Exact next steps, in order

1. Continue a local release-readiness audit; review container base images and add reproducible image scanning if practical.
2. Run hosted CI when a remote and runner are configured.
3. Complete permitted browser and accessibility review.
4. Deploy and verify operator-owned TLS, storage protections, egress and recovery.
5. Run the required evaluation using authorized, time-separated annotations and report measured results.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 80`
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`
- `git status --short`

## 2026-11-12 17:50 (Asia/Kolkata) — Remediate and locally verify runtime image findings

### Completed work

- Rechecked the worktree, build plan, Compose services and available disk space. Docker Engine 29.9.2 is running. The pre-existing protected `rsiacdp-postgres` container and `backend_postgres_data` volume were not modified.
- Added `database/Dockerfile`; Compose now builds `rsaicdp-postgres:16.15-alpine3.24` from the official PostgreSQL 16.15 Alpine image, applies current Alpine package fixes, installs `su-exec`, and maps the upstream entrypoint's `gosu` command path to `su-exec`. The image build runs a privilege-drop smoke check.
- Updated the CI PostgreSQL scan to target the Compose-built image. CI image scans explicitly use the vulnerability scanner; the Caddy config check now validates the same `caddy:2.11.9-alpine` tag that CI scans.
- Added `.trivyignore.yaml` with path-scoped exceptions expiring 2027-02-12: 26 Go stdlib findings detected in the now-hidden upstream `gosu` image layer, and one `golang.org/x/net/html` finding in `usr/bin/caddy` for Caddy 2.11.9. The Caddyfile enables only reverse proxy, headers and compression, not HTML templates. The exceptions are visible, narrowly scoped, and temporary; they do not mean the upstream binaries are patched.
- Updated README, requirements traceability and engineering walkthrough with the current image baseline, local scan outcomes, the temporary exceptions and outstanding scan/deployment limitations.

### Checks actually run

- Frontend `pnpm audit`: passed; no known vulnerabilities found.
- Frontend `pnpm run build`: passed with Vite 8.3.4.
- Frontend `pnpm run test:redaction`: 24 passed, 0 failed.
- Docker build of `rsaicdp-postgres:16.15-alpine3.24`: passed. Build output shows `zlib`, `krb5-libs`, and `libxslt` upgraded to the current Alpine fixed package releases; `gosu postgres true` passed.
- Final PostgreSQL image check: `/usr/local/bin/gosu` resolves to `/sbin/su-exec`, and `gosu postgres id` returned UID/GID 70. The updated database container became healthy; an API SQL query read the existing 3 synthetic cases and reported PostgreSQL 16.15. API and web returned HTTP 200.
- Trivy 0.76.2 vulnerability-only local image scans: API reported 0 High/Critical OS and Python-package findings; web reported 0 High/Critical findings after the Nginx/Alpine update (from the immediately preceding scan); PostgreSQL reported 0 Alpine package findings after the update, with only the explicitly ignored hidden `gosu` layer findings; Caddy reported 0 Alpine package findings, with only the explicitly ignored `usr/bin/caddy` advisory. Scans used `--ignore-unfixed --severity HIGH,CRITICAL --exit-code 1`; the PostgreSQL and Caddy scans loaded `.trivyignore.yaml`. The Neo4j image was not scanned locally because a prior large image export exhausted available disk space.
- Production `Caddyfile` validation using `caddy:2.11.9-alpine` with `--network none`: passed, `Valid configuration`.
- `docker compose ... config --quiet`: passed with the isolated test environment and the API's configured database URL.
- PyYAML parsed the final CI and Trivy policy YAML. Assertions confirmed five Trivy image targets, vulnerability-only scans, the PostgreSQL/Caddy exception inputs, 26 `gosu` path entries, one Caddy path entry, and the expiration date.
- `docker compose ps --all`: PostgreSQL, Neo4j, API, worker and web all healthy. Worker OCR verification passed for a real Tesseract image and scanned-PDF path.
- An attempted Prettier check did not run because Prettier is not installed. The YAML parser and Compose config checks passed instead. The first worker restart used a stale disposable test environment that supplied PostgreSQL credentials inconsistent with the API's database URL; after starting the worker with the API's existing database URL, it became healthy. This was a test-environment mismatch, not a code change.

### Files or components changed

- `.github/workflows/ci.yml`
- `.trivyignore.yaml`
- `database/Dockerfile`
- `docker-compose.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- The prior full Compose E2E and live backup/restore checks passed before this custom PostgreSQL image revision. They were not rerun after the image change; this stage verified image startup, PostgreSQL-backed API reads, service health and OCR. The database image preserves PostgreSQL major version 16 and the current synthetic data.
- Neo4j has not been locally scanned. The CI scan is configured, but hosted CI has not run because there is no Git remote or hosted runner configured.
- Local `.test-runtime/compose-e2e-20261103.env` is stale for the present project and omits the API's explicit `DATABASE_URL`; starting the worker from it alone can fail with mismatched PostgreSQL credentials. The current test stack is healthy because its worker was recreated with the API's configured URL. Do not use that stale file as a production configuration.
- Production deployment, operator-owned TLS/storage/egress/recovery verification, authorized time-separated evaluation data and measured baseline results remain incomplete. Browser review of Corrections and graph filters remains subject to the previously declined browser-origin approval; do not bypass it.
- The workspace has no Git remote and all project files remain untracked. No commit was created.

### Exact next steps, in order

1. Before further Compose operations, read `.env.example` and create a private local `.env` with unique secrets; do not reuse the stale ignored test env file. Validate with `docker compose config --quiet` and keep API/worker database URLs consistent with PostgreSQL credentials.
2. Run the Compose E2E and encrypted live backup/restore scripts against a fresh isolated project using the custom PostgreSQL image and synthetic data. Preserve the protected PostgreSQL container and its volume; never run `docker compose down -v` without proving the exact project name is disposable.
3. Scan Neo4j with the configured Trivy gate on a runner with adequate disk capacity; review and document any findings. Then run hosted CI after an authorized Git remote/runner is configured.
4. Continue the pending manual responsive/accessibility/browser review only if the browser-origin approval gate permits it.
5. Deploy only to operator-owned infrastructure and verify TLS, storage access/encryption, egress, monitoring and recovery there.
6. Obtain authorized, time-separated recruitment-scam labels; run all four documented comparisons and publish measured results only.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 100`
- `git status --short`
- `docker compose config --quiet` (after setting up `.env` from `.env.example` with unique local secrets)
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`
- `docker compose ps --all`

## 2026-11-12 18:06 (Asia/Kolkata) — Verify full workflows with the flattened PostgreSQL image

### Completed work

- Created a fresh isolated release-check project using newly generated test-only secrets, its own PostgreSQL/Neo4j/private-upload volumes, and a separate network. A temporary Compose override bound its web/API to ports 5178/8018 so the existing local project and protected PostgreSQL service were not disturbed.
- Built and started API, worker, web and flattened PostgreSQL images. PostgreSQL, Neo4j, API, worker and web all became healthy.
- Ran the full synthetic Compose intake/investigation test with investigator registration, consent, text and PDF cases, processing, extraction/source spans, local evidence, deterministic campaign linking, graph, report redaction, correction, recalculation, audit timeline and Neo4j outage/recovery. The script passed.
- Ran the encrypted live backup/restore test on the same flattened PostgreSQL image. It passed authenticated RSAICDPBK2 key-fingerprint verification, database and upload restoration, synthetic mutation rollback, private-upload retention (1 file), and API readiness. Neo4j rebuilt from PostgreSQL after restore.
- Ran the graph rebuild command after restore; Neo4j projection rebuilt for 3 cases and PostgreSQL reported migration revision `e7a91c0d4b62`.
- Added `/database` to weekly Dependabot Docker updates and parsed the final YAML, confirming backend, frontend, database and root Compose Docker update coverage.
- Updated the point-by-point engineering walkthrough with exact flow, commands, synthetic references, results and the remaining limits.

### Checks actually run

- `scripts/test-compose-e2e.ps1 -AllowSyntheticWrites -ExerciseNeo4jOutage` against `http://127.0.0.1:8018`: passed all reported intake, worker, PDF provenance, campaign, graph, report, correction, audit and outage/recovery assertions.
- `scripts/test-compose-backup-restore.ps1 -AllowSyntheticWrites -RequirePrivateUpload -ApiReadinessUrl http://127.0.0.1:8018/health/ready`: passed; the script reported restored encrypted database/uploads, rolled back the synthetic mutation, retained 1 private upload, and returned readiness 200.
- `docker compose exec worker python -m app.graph_rebuild`: passed; rebuilt 3 cases. Informational Neo4j CartesianProduct notices were emitted when saving link relationships; they did not prevent projection rebuild.
- `GET http://127.0.0.1:5178/`, same-origin `/api/policy`, and API `/health/ready`: all HTTP 200; CSP header present.
- Final post-restore Compose status: all five services healthy. The generated data and secrets are synthetic and local-only.
- Prior latest checks remain: backend harness 224 + 15 + 2 tests passed (2 opt-in PostgreSQL tests skipped); frontend audit/build/24 tests passed; API/web/PostgreSQL image scans clean for High/Critical vulnerabilities; Caddy scan has one path-scoped expiring exception; OCR passed.

### Files or components changed

- `BUILD_STATUS.md`
- `ENGINEERING_WALKTHROUGH.md`
- Ignored test-only files in `backend/.test-runtime/` for random configuration, Compose ports, and synthetic PDF. They are not tracked or intended as production configuration.

### Known bugs or unfinished work

- Neo4j image vulnerability scan remains pending because the local image export previously exhausted available disk. Neo4j runtime integration, graph projection, outage recovery and rebuild have passed.
- Hosted CI has not run; `git remote -v` is empty and project files are untracked. No commit was made.
- Caddy 2.11.9 has a single temporary path-scoped exception for CVE-2026-78661 in `usr/bin/caddy`, expiring 2027-02-12; update and rescan when an upstream fixed build is available.
- Hosted deployment and operator verification (TLS, storage ACL/encryption, egress, monitoring and recovery), manual visual/accessibility review under the existing browser-origin approval gate, and measured comparisons on authorized time-separated data are incomplete.
- The disposable older `rsaicdp-e2e-20261112` environment file has a stale database URL; use the fresh `rsaicdp-release-check-20261112` environment for local review, or create `.env` from `.env.example` with new deployment secrets. Do not use either ignored test env as production configuration.

### Exact next steps, in order

1. Run the Neo4j Trivy scan in hosted CI or a runner with sufficient disk; inspect the full scan report and address remaining findings.
2. Configure an authorized Git remote and hosted runner, then run all CI jobs and retain actual job output. Do not claim hosted CI is green until it runs.
3. Deploy to operator-owned infrastructure and verify TLS, secrets, storage access/encryption, egress, logging, backups, restore and deletion behavior.
4. Obtain authorized time-separated Indian recruitment-scam labels; run the documented comparisons and report actual metrics only.
5. Complete permitted browser and accessibility review; do not bypass the previously declined origin-approval gate.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 130`
- `git status --short`
- `docker compose --project-name rsaicdp-release-check-20261112 --env-file backend/.test-runtime/release-check-20261112.env -f docker-compose.yml -f backend/.test-runtime/release-check-20261112.override.yml ps --all`
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`

## 2026-11-12 18:00 (Asia/Kolkata) — Flatten PostgreSQL image and pass rebuilt backend harness

### Completed work

- Reworked `database/Dockerfile` to use a multi-stage build: patch the official PostgreSQL 16.15 Alpine filesystem and replace the `gosu` command path with `su-exec`, then copy the merged filesystem into a fresh `scratch` final stage. This removes the old upstream Go binary from image history instead of hiding its findings with a scanner exception.
- Restored the official PostgreSQL runtime configuration in the final image: required environment values, port, data volume, working directory, stop signal, entrypoint and command. The final image has one layer and preserves PostgreSQL 16.15.
- Removed all PostgreSQL CVE exceptions from `.trivyignore.yaml` and the PostgreSQL scan step. Only the time-limited, path-scoped Caddy exception remains.
- Rebuilt the disposable Compose PostgreSQL service against the existing isolated synthetic volume. API access still returned all 3 existing synthetic cases; the database reported 16.15. All five services are healthy.
- Reran the backend CI test harness from the rebuilt worker image against the current writable backend source tree, using CI-compatible test environment variables.

### Checks actually run

- Flattened PostgreSQL image inspection: 1 final image layer; expected official entrypoint/command/workdir metadata retained.
- PostgreSQL startup-helper check: `/usr/local/bin/gosu` resolved to `/sbin/su-exec`; `gosu postgres id` returned UID/GID 70.
- Trivy 0.76.2 PostgreSQL image scan without any ignore file: 0 High/Critical OS findings; the old upstream `gosu` binary is absent from the final image scan.
- Backend test harness passed: 224 unit tests, 15 isolated API-flow tests, 2 proxy-header tests; two opt-in PostgreSQL tests skipped in this harness. The first test attempt incorrectly set `UPLOAD_ENCRYPTION_KEY`, making plaintext test fixtures invalid and causing two assertion failures plus one OCR-region error. Re-running with the same test-variable shape as CI, which omits that key, passed all executed tests.
- Final CI and ignore YAML parsed with PyYAML. Assertions verified five vulnerability-only scans, no PostgreSQL exception input, and one Caddy exception at `usr/bin/caddy` expiring 2027-02-12.
- Dependabot YAML parsed; Docker update sources `/backend`, `/frontend`, `/database`, and `/` were all present.
- Caddy Trivy scan completed with only its declared scoped exception; offline Caddy configuration validation passed.
- Frontend audit/build/redaction checks remained green: no known dependency vulnerabilities, Vite build passed, 24 tests passed.
- API and web returned HTTP 200; the same-origin web `/api/policy` proxy returned 200 and the Content-Security-Policy header was present.
- Docker Compose configuration parsed successfully. Database/API persisted-data query reported 3 synthetic cases on PostgreSQL 16.15. PostgreSQL, Neo4j, API, worker and web were healthy; real Tesseract image/scanned-PDF OCR check passed.

### Files or components changed

- `database/Dockerfile`
- `.github/workflows/ci.yml`
- `.trivyignore.yaml`
- `docker-compose.yml`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`
- `.github/dependabot.yml`

### Known bugs or unfinished work

- Full Compose E2E and live encrypted backup/restore passed in an earlier image iteration, but they were not rerun after flattening the PostgreSQL image. This iteration verified database startup, preserved synthetic data, API SQL connectivity, worker health and OCR.
- Neo4j has not been locally scanned. The CI gate is present, but no hosted workflow has run because no Git remote/runner is configured.
- The ignored test env file still does not match the running API's database URL; re-creating the disposable worker from that file alone can fail authentication. The current worker is healthy with a database URL matching the API. Do not use this stale file as production configuration.
- `.trivyignore.yaml` retains one temporary Caddy exception for CVE-2026-78661 in `usr/bin/caddy`, expiring 2027-02-12. The production Caddyfile does not enable HTML templates, but the upstream binary itself remains an external dependency to update and re-scan.
- Hosted deployment, operator-owned TLS/storage/egress/recovery checks, visual browser review under the existing approval gate, and authorized time-separated evaluation remain incomplete. Do not claim full release readiness.

### Exact next steps, in order

1. Create a private `.env` from `.env.example` using distinct random secrets and validate it with `docker compose config --quiet`; do not reuse the stale `.test-runtime` environment file.
2. Run the complete Compose E2E and encrypted live backup/restore scripts in a fresh, disposable Compose project using the flattened PostgreSQL image; preserve unrelated volumes and verify the exact project before any cleanup.
3. Run the full image scan on a runner with enough disk for Neo4j, then run hosted CI after a Git remote/runner is configured. Review every scan result and any Caddy exception status.
4. Complete hosted deployment verification, permitted browser/accessibility review, and all data-backed evaluation comparisons with authorized time-separated annotations.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 110`
- `git status --short`
- `docker compose config --quiet` (after creating `.env` from `.env.example`)
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`
- `docker compose ps --all`

## 2026-11-12 17:15 (Asia/Calcutta) — Add first-party image scanning and base-image updates

### Completed work

- Added Trivy scans for API and frontend runtime images to the web-container job and PostgreSQL, Neo4j and Caddy images to the Compose E2E job. The gate fails on fixable High/Critical OS or library vulnerabilities.
- Pinned the Trivy action to the immutable v0.36.0 commit SHA, verified against GitHub release metadata.
- Updated the frontend runtime base from Nginx 1.27 to official `nginx:1.30.6-alpine3.24`.
- Added weekly Dependabot checks for backend/frontend Dockerfiles, Compose images, GitHub Actions, npm and pip.
- Updated README, traceability matrix and engineering walkthrough.

### Checks actually run

- Frontend `pnpm audit`: passed; no known vulnerabilities found.
- Frontend `pnpm run build`: passed (Vite 8.3.4).
- Frontend `pnpm run test:redaction`: 24 passed, 0 failed.
- Prettier YAML parser accepted `.github/workflows/ci.yml` and `.github/dependabot.yml`.
- Static workflow assertions found exactly five SHA-pinned Trivy scan steps targeting the API, web, PostgreSQL, Neo4j and Caddy images; the workflow YAML parser passed afterward.
- GitHub API lookup confirmed Trivy action tag v0.36.0 resolves to `ed142fd0673e97e23eac54620cfb913e5ce36c25`, the SHA pinned by CI.
- Docker CLI reported Docker Desktop Linux Engine pipe unavailable. No local image rebuild, Trivy scan, Nginx container smoke test, or Compose health check was run for this Nginx base update.

### Files or components changed

- `.github/workflows/ci.yml`
- `.github/dependabot.yml`
- `frontend/Dockerfile`
- `README.md`
- `REQUIREMENTS_TRACEABILITY.md`
- `ENGINEERING_WALKTHROUGH.md`
- `BUILD_STATUS.md`

### Known bugs or unfinished work

- Hosted CI must build and scan the new Nginx image and run the existing web-container smoke tests. Image scan results have not been produced.
- Container scan results are still not available until the hosted workflow runs.
- No Git remote is configured, so hosted CI cannot be started from this workspace.
- Deployment, operator-owned infrastructure/security verification and evaluation on authorized time-separated data remain incomplete.

### Exact next steps, in order

1. When Docker Engine is available, build and smoke-test the updated frontend container; scan API and web images with Trivy.
2. Configure a remote/hosted runner and execute all CI jobs, including PostgreSQL, Compose, Windows backup/restore, and image scanning.
3. Review image scan results; remediate findings or document justified exceptions with owners and expiry dates.
4. Complete deployed browser/accessibility, TLS, storage, egress, backup and recovery checks.
5. Run the four required comparisons on authorized, time-separated recruitment-scam data and publish only measured results.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 90`
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`
- `docker compose config -q` (after Docker Engine and local environment secrets are available)
- `git status --short`

## 2026-11-12 18:07 (Asia/Calcutta) — Current verified release-check checkpoint

### Completed since the prior checkpoint

- Rebuilt PostgreSQL as a one-layer patched image based on PostgreSQL 16.15; Alpine High/Critical scan findings are zero without an ignore file. The final runtime uses `su-exec` through the upstream `gosu` command path.
- Completed local Trivy scans: API, web and PostgreSQL reported zero High/Critical findings; Caddy has one declared, path-scoped CVE-2026-78661 exception expiring 2027-02-12. Neo4j image scan remains pending.
- Added the `/database` Dockerfile to weekly Dependabot Docker updates and parsed the final Dependabot YAML.
- Backend CI harness passed 224 unit tests, 15 API-flow tests and 2 proxy tests; 2 opt-in PostgreSQL tests were skipped. Frontend audit/build/redaction passed; 24 frontend tests passed.
- On a fresh isolated project at API port 8018/web port 5178, all five services became healthy. Full consented intake through extraction, local evidence, deterministic campaign link, graph, report, correction, audit, PDF provenance and Neo4j outage/recovery passed with synthetic data.
- Encrypted live backup/restore passed on that fresh project: manifest key identity, PostgreSQL restore, one private upload restore, synthetic mutation rollback, API readiness, and graph rebuild for 3 cases. Migration revision was `e7a91c0d4b62`.
- API readiness, web root, same-origin API policy, CSP header and all service health checks passed after restore. `ENGINEERING_WALKTHROUGH.md` records the point-by-point implementation and verification history.

### Current workspace and limitations

- Current isolated review app: `http://127.0.0.1:5178`; API: `http://127.0.0.1:8018`. Random test secrets and synthetic files are in ignored `backend/.test-runtime/` paths.
- Git has no remote configured; files are untracked and no commit was created. Hosted CI and hosted deployment have not been verified.
- Neo4j runtime flows pass, but its large image was not scanned locally due disk constraints. The configured CI scan remains pending.
- The Caddy exception is temporary and does not mean the upstream Caddy binary is patched. Production TLS/storage/egress/recovery, visual browser/accessibility review under the existing approval gate, and evaluation on authorized time-separated data remain incomplete.

### Exact next steps

1. Run CI on a runner with sufficient disk for Neo4j and resolve or document every image finding.
2. Configure an authorized Git remote/runner and retain actual hosted CI output.
3. Deploy to operator-owned infrastructure and verify TLS, storage ACL/encryption, egress, monitoring and restore.
4. Obtain authorized time-separated labels, run all four documented evaluation comparisons, and report measured metrics only.
5. Complete permitted browser/accessibility review without bypassing the prior origin-approval decision.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 100`
- `git status --short`
- `docker compose --project-name rsaicdp-release-check-20261112 --env-file backend/.test-runtime/release-check-20261112.env -f docker-compose.yml -f backend/.test-runtime/release-check-20261112.override.yml ps --all`
- `pnpm --dir frontend audit`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:redaction`

## 2026-11-12 18:11 — Release dependency recheck

- Re-read the build plan, latest checkpoint, requirements matrix and evaluation instructions; no Git remote is configured.
- Compose release-check inspection confirms all five services remain healthy.
- C: free space measured 746418176 bytes (about 712 MiB); no image export or destructive cleanup attempted.
- Corrected the stale traceability checklist entry to distinguish completed local API/worker checks from pending deployed and visual verification.
- Requested repository/hosting details and the path/authorization restrictions for evaluation data. No credentials requested.
- No application code changed and no tests rerun; this was a documentation and live service-status check.
- Next: configure the user-specified remote/runner and deployment target when provided, run the remaining Neo4j scan on adequate storage, complete permitted browser review, and evaluate with authorized labels. The project is not release-ready.


## 2026-11-12 18:15 — User-selected remote and synthetic evaluation rehearsal

- User supplied https://github.com/gaurvit06/RSIACDP and requested generated data. Git ls-remote succeeded with no advertised refs; configured origin. No commit or push performed.
- Added backend/evaluation/generate_synthetic.py and documented its commands/limitations in evaluation/README.md.
- Generated 108 fictional email-only cases (36 per simulated time split), generator provenance and SHA-256 manifest in ignored backend/.test-runtime/synthetic-evaluation-v1/.
- Actual TF-IDF/logistic-regression run produced 36 test predictions and SYNTHETIC-ONLY-tfidf-metrics.json. Validation passed unique text/IDs, chronological and campaign separation, reserved identifiers and manifest hash.
- Synthetic labels are generator-defined, not independent annotations. These results do not establish real-world accuracy or complete all four comparisons.
- Next: obtain explicit commit authorization before initial publication (user instruction forbids commits without request), choose hosting, execute hosted CI/remaining scan, run isolated full/no-graph synthetic rehearsals, configure the LLM/search experiment if desired, and complete permitted browser review. Real-world evaluation remains pending authorized data.


## 2026-11-12 18:17 — Initial GitHub publication authorized

- User explicitly authorized committing and pushing to origin https://github.com/gaurvit06/RSIACDP.git.
- Inspected all 147 publishable files for private-key/provider-token patterns, credential-bearing URIs, large binaries and runtime artifacts. URI matches were example-domain test fixtures; .env.example contains placeholders and the bundled corpus is empty.
- Runtime secrets, uploads, databases, dependencies and generated synthetic evaluation output remain ignored.
- Preparing initial commit on codex/initial-platform. Hosted CI results are pending; publication does not establish deployment readiness.
- User selected Vercel frontend, Render API/worker and Supabase PostgreSQL. Provider-specific deployment, shared private storage and Neo4j hosting remain to be implemented/configured and verified.

## 2026-11-12 18:18 — Hosted CI workflow validation fix

- Initial commit 11a0eea was pushed and verified against origin/codex/initial-platform.
- GitHub run 43221200266 failed before scheduling jobs: runner.temp was not recognized in the backend job-level environment block (lines 38–40).
- Moved TEMP/TMP/TMPDIR expressions to the backend test step environment, retaining runner-specific temporary directories where the context is available.
- This fixes workflow configuration, not an application test failure. Hosted execution must verify the revised workflow; no test pass is claimed.

## 2026-11-12 18:35 — Neo4j hosted scan diagnostics

- Corrected workflow run 43221328967: backend, frontend, operations-scripts, compose-config and web-container passed. Compose E2E stopped only at the Neo4j High/Critical Trivy gate; PostgreSQL scan passed. Subsequent OCR/intake/restore/rebuild steps were skipped.
- GitHub's public job log API denies log download to this account. Public check-run annotations expose only exit code 1, not the vulnerability list.
- Updated CI to write a JSON Trivy report, upload it as neo4j-trivy-report artifact, continue the rest of Compose integration checks, then enforce the scanner result after report upload.
- Exact artifact will reveal current findings without weakening the security gate. Next: inspect artifact from the new CI run; update Neo4j base/image or document a narrowly justified exception, then rerun full CI.

## 2026-11-12 19:12 — Vercel/Render/Supabase deployment and hosted-CI diagnostics

### Completed

- Implemented the optional Supabase private Storage adapter for the API and worker. Uploads use application AES-GCM encryption, opaque filenames, bounded downloads/listing, authenticated Storage API requests, no redirects, and Storage API deletion. Local private-disk storage remains the default for Compose.
- Added Vercel static hosting configuration and same-origin `/api/*` rewrite; frontend auth requests now send cookies through that rewrite.
- Added the Render Blueprint for the API, worker and private Neo4j service, including generated secrets, migration/health settings, and private persistent Neo4j data. Added a Render Neo4j image wrapper for the generated auth secret format.
- Reviewed Render's current Blueprint/private-network reference. Fixed the Neo4j host wiring to use Render `fromService` rather than a guessed DNS name; API and worker now construct `bolt://<generated-private-host>:7687`, while explicit local `NEO4J_URI` retains priority. Added regression coverage for both paths.
- Updated README and engineering walkthrough with provider setup, bucket policy, credentials, expected costs and provider limitations. No credentials were added to the repository.
- Hosted GitHub run `43224083243` on `b3ec799` failed in the Compose configuration job and at the Neo4j High/Critical vulnerability gate. Backend, frontend, operations-script and web-container jobs passed. Compose E2E reached backup/restore and graph rebuild, then failed final enforcement for Neo4j findings. The hosted artifact cannot be downloaded without GitHub authentication. The unpushed workflow now emits vulnerability and Compose-assertion diagnostics as check annotations; a fresh hosted run is pending publication.

### Checks run

- Backend CI harness after the dynamic Neo4j host change: **229 unit tests passed, 2 optional PostgreSQL-only tests skipped; 15 isolated API flow tests passed; 2 proxy-header tests passed**.
- Focused configuration suite: **12 tests passed**.
- Supabase Storage adapter tests: **3 passed** as part of the 229-test unit harness.
- `scripts/test-compose-config.ps1`: passed.
- Render Blueprint, GitHub Actions YAML, Vercel JSON and dynamic Neo4j service references: parsed and asserted successfully with PyYAML/JSON in the backend container.
- `git diff --check`: passed.
- Earlier in this stage, the fresh isolated five-service Compose application passed full intake-to-report, correction, graph, OCR/PDF and Neo4j outage/recovery workflows; encrypted backup/restore also passed with one private upload and graph rebuild. That E2E run was before the final dynamic-host refactor; local Compose still uses the same explicit URI path now covered by the unit test.
- Frontend build and 24 redaction tests passed earlier in this stage; the frontend code has not changed since those checks.

### Remaining and next steps

1. Commit and push this reviewed deployment/configuration change to `codex/initial-platform` (explicitly authorized by the user), then inspect the newly triggered GitHub Actions run and fix any surfaced Compose/Neo4j findings without weakening the scan gate.
2. Resolve the Neo4j High/Critical image findings from hosted annotations or a scan artifact obtainable through authorized GitHub access.
3. Configure operator-owned Supabase, Render and Vercel projects and secrets in their dashboards. No cloud account or provider credentials were supplied, so no hosted deployment or cloud upload has been run.
4. Verify live cookies/CSRF, consented upload, encrypted private object access, worker processing, retention, reports, correction, graph and a provider backup/restore.
5. Complete browser/accessibility review under the existing browser-origin approval gate and run evaluation on authorized, time-separated annotations. Synthetic generated data is not real-world validation.

### Resume commands

- `Get-Content BUILD_STATUS.md -Tail 90`
- `git status --short`
- `git diff --check`
- `./scripts/test-compose-config.ps1`
- Run the backend unit and API/proxy suites with `python run_ci_tests.py` in an isolated worker image, `APP_ENV=testing`, separate temporary SQLite/upload paths, no upload-encryption key, and empty Neo4j URI/host.
- After push, query `https://api.github.com/repos/gaurvit06/RSIACDP/actions/runs?per_page=3` and inspect the new run's jobs/annotations.

## 2026-11-12 19:26 — Hosted CI results and Neo4j security remediation

### Hosted run `43230213205` (`c091269`)

- Backend, frontend, operations-scripts, and web-container jobs passed.
- The Compose configuration job failed at `scripts/test-compose-config.ps1` line 51. The assertion incorrectly required Docker Compose to report `POSTGRES_PASSWORD` first when multiple required secrets were unset. This is an error-order assumption, not an application failure. Updated it to accept any required-secret diagnostic; separate checks still test every secret individually. The revised script passes locally.
- The Compose E2E job passed PostgreSQL, Neo4j and Caddy image scans at the step level, OCR/PDF processing, investigator intake, processing, campaign/graph linking, reports, corrections, encrypted backup/restore, and PostgreSQL-to-Neo4j rebuild. Final scan enforcement failed for six High findings in Neo4j 5.26.33: jackson-core/databind 2.22.2 and Debian zlib1g 1:1.3.dfsg+really1.3.1-1+b1. The new annotation diagnostic exposed exact packages and fixed versions.

### Remediation attempt pushed; security gate still failing

- Switched the Neo4j base to official Community image `2026.10.2-trixie`; Compose and Render now build/use the same custom `rsaicdp-neo4j:2026.10.2` image so CI scans the actual hosted image definition, including its password wrapper.
- Updated the custom entrypoint to preserve Compose's `NEO4J_AUTH` mode and to construct it from Render's generated `NEO4J_PASSWORD` when deployed. Added weekly Dependabot coverage for `/deployment/neo4j` and updated version/upgrade documentation.
- Added a Compose config assertion that Compose uses the same Neo4j Dockerfile as Render. Changed the missing-secret assertion to be order-independent.
- Commit `82fdc75` was pushed. Hosted run `43232234950` built and started the new image, passed all image scans at the step level plus OCR/PDF, complete investigator E2E, encrypted backup/restore and graph rebuild, but strict enforcement still found the same six High findings. The diagnostic annotations show Jackson `2.22.2` and Debian zlib1g `1:1.3.dfsg+really1.3.1-1+b1` remain in the new Neo4j image.

### Checks after the proposed remediation

- `scripts/test-compose-config.ps1`: passed, including the shared Neo4j image build assertion.
- Vercel JSON, Render Blueprint, GitHub Actions YAML, Dependabot YAML and dynamic private-host references: parsed/asserted successfully using PyYAML/JSON in the backend container.
- `bash -n deployment/neo4j/render-entrypoint.sh`: passed.
- Searched active deployment files for stale Neo4j 5.26.33 image references: none found.
- `git diff --check`: passed.
- The 229-unit/15-API-flow/2-proxy backend pass applies to commit `c091269`; backend implementation is unchanged in this pending remediation. Two optional PostgreSQL-only unit tests were skipped.

### Next steps

1. Patch Neo4j's Debian packages and vulnerable Jackson jars in the custom image, flatten the final root filesystem, then commit and push the change.
2. Inspect the new hosted build, runtime/E2E, and strict Trivy result. Do not add exceptions for the fixed findings.
3. Cloud provider setup, production provider-backed uploads, deployed recovery checks, browser/accessibility review, and authorized real-world evaluation remain incomplete.

## 2026-11-12 20:07 — Patched and flattened Neo4j image prepared

### First patched-image attempt pushed; hosted build failed before E2E

- The 2026.10.2 image still contained the exact fixed-vulnerability versions from run `43232234950`; the prior attempted upgrade did not pass the strict gate.
- Reworked `deployment/neo4j/Dockerfile` into a multi-stage build: apply Debian package security updates (including zlib1g), download jackson-core/databind 2.22.3 from Maven Central, verify the downloaded jars with pinned SHA-256 digests, replace every matching 2.22.2 jar under `NEO4J_HOME`, and copy the merged root filesystem into a fresh `scratch` image so parent-layer copies are absent.
- Preserved the official Neo4j 2026.10.2 runtime contract in the final image: environment, Java/Neo4j paths, ports, `/data` and `/logs`, working directory, default stop signal, entrypoint and command.
- Updated README and engineering walkthrough to explain the image remediation and state clearly that scan/runtime verification is pending.

### Checks

- `docker build --check --file deployment/neo4j/Dockerfile .`: passed; Docker parsed the custom build and resolved the official Neo4j 2026.10.2 Trixie base metadata. This was a build check, not a full image build.
- `scripts/test-compose-config.ps1`: passed.
- Vercel, Render, GitHub Actions and Dependabot manifests parsed successfully; Compose and Render both reference the shared custom Neo4j image.
- `bash -n deployment/neo4j/render-entrypoint.sh`: passed.
- `git diff --check`: passed before the latest status/documentation append; rerun before commit.
- No full local Neo4j image build or local Trivy scan was run. The next hosted workflow must prove the patched merged image builds, passes strict scanning, and runs E2E/recovery checks.
- Commit `0ba356d` was pushed. Hosted run `43234340852` failed in the stack-start step while building the image before it reached vulnerability scanning. Its public annotation only showed the step exit code; GitHub's public job-log download was unavailable. C: had about 515 MB free and the Docker cache/active data already occupied several GB, so a full local image build was not attempted.

### Exact next steps

1. Get actionable Docker build output from the next hosted run. The pending workflow change separates the Neo4j build, logs plain BuildKit progress and publishes the final redacted log lines as a check annotation if it fails.
2. Fix the precise build failure, then verify strict Trivy scanning and runtime/E2E/recovery checks on the patched image.
3. Cloud credentials/accounts, hosted deployment, cloud backup/restore, browser/accessibility review, and evaluation on authorized time-separated labels remain incomplete.

## 2026-11-12 — Hosted Neo4j build failure diagnostics

- Run `43234340852` (`0ba356d`) failed while building the patched Neo4j image; its public annotation contained only the failing step and exit code. Local C: space was about 515 MB with several GB of Docker images, volumes, and build cache. No cleanup or full local image build was attempted; existing local containers and data remain untouched.
- Added a dedicated hosted build step with plain BuildKit output and a sanitized failure annotation. Commit `2fc5754` pushed this diagnostic change. Hosted run [`43235150070`](https://github.com/gaurvit06/RSIACDP/actions/runs/43235150070) failed after 1m17s: the Jackson replacement guard found no exact `jackson-*-2.22.2.jar` match under `NEO4J_HOME`. The public annotation does not identify which artifact failed.
- The failure annotation's 24-line log excerpt confirmed the Dockerfile guard, but did not expose the individual artifact's shell trace. The next image change follows filesystem symlinks during jar discovery and prints available matching versions if the exact vulnerable file is absent.
- The flattened `scratch` stage also reset Docker image configuration, so the custom image now explicitly restores the documented `neo4j` runtime user.

## 2026-11-12 19:51 IST — Neo4j image discovery fix prepared

- Updated `deployment/neo4j/Dockerfile` to search with `find -L` under the configured Neo4j home (falling back to `/var/lib/neo4j`) and emit available Jackson jar paths before failing. The security update, pinned Maven SHA-256 checks, replacement, and strict Trivy gate remain intact.
- Restored `USER neo4j` in the final flattened image stage so it does not run as root after `FROM scratch`.
- Checks actually run: `docker build --check --file deployment/neo4j/Dockerfile .` passed (Dockerfile syntax/metadata only); `docker compose config --quiet` passed; `scripts/test-compose-config.ps1` passed; `git diff --check` passed.
- A full local image build and Trivy scan were not run because of the previously recorded low disk space. These checks do not prove that the amended layer builds or passes security scanning.

Next steps, in order:

1. Review the Dockerfile diff, commit and push this fix with the updated engineering walkthrough and status file.
2. Inspect the hosted build result. If jar discovery still fails, use the new diagnostic to locate the exact version/path; do not weaken the vulnerability gate.
3. Require the hosted Neo4j image to build, have zero fixed High/Critical Trivy findings, start under the `neo4j` user, and pass the complete intake, graph, report, encrypted backup/restore, and rebuild checks.
4. Continue with cloud account/provider setup, hosted deployment, deployed backup/restore, browser/accessibility review, and evaluation on an authorized time-separated dataset. These remain incomplete.

## 2026-11-12 19:59 IST — Improve hosted Neo4j build diagnostics

- Run [`43236626913`](https://github.com/gaurvit06/RSIACDP/actions/runs/43236626913) (`593d3c1`) reached the Compose job and failed at the same Jackson replacement guard after the symlink-aware search. The public annotation still does not show the concise shell trace needed to identify the artifact/path; the overall workflow was still finishing other jobs when checked.
- Updated `.github/workflows/ci.yml` to extract the relevant Docker/BuildKit shell trace, checksum, missing-file, Jackson path, and failure lines and publish each as a short sanitized annotation. This is diagnostic-only; it keeps build and vulnerability enforcement strict.
- Checks actually run: embedded Node script passed `node --check`; GitHub Actions YAML parsed successfully using PyYAML in the existing worker image; `docker compose config --quiet`, `scripts/test-compose-config.ps1`, and `git diff --check` passed.
- Next: commit/push this diagnostic improvement, inspect the next hosted result for the exact artifact and path, and patch based on that evidence. Do not widen the file search or ignore scanner findings without confirming the actual image contents.

## 2026-11-12 20:02 IST — Make the Jackson image patch idempotent

- Hosted run [`43237868337`](https://github.com/gaurvit06/RSIACDP/actions/runs/43237868337) (`e40d8a4`) confirmed the targeted annotations work. The build trace showed `/var/lib/neo4j/lib/jackson-core-2.22.3.jar` already existed, so the Dockerfile failed because it required a 2.22.2 file for every artifact. The Compose E2E job failed during the build; the rest of the workflow was still running at the time of review.
- Updated the Dockerfile to replace each vulnerable 2.22.2 JAR, accept an already-fixed 2.22.3 JAR, and fail with a version listing when neither expected version is found. It still verifies downloaded hashes and the strict Trivy scan remains unchanged.
- Next: run Dockerfile parse/config/Compose checks, update the walkthrough with this finding, commit and push, then check the hosted image build, both Jackson versions, Debian scan, runtime and full recovery workflow. Do not claim the security gate passes until the hosted Trivy report confirms it.

## 2026-11-12 20:09 IST — Search and patch Jackson copies across the image

- Hosted run [`43238338368`](https://github.com/gaurvit06/RSIACDP/actions/runs/43238338368) built the image and reached Trivy after the idempotent home-level patch. Trivy reported four High Jackson findings (core/databind 2.22.2); the previously reported zlib findings were absent, so the Debian package upgrade addressed those findings. The run annotation view does not provide full step logs, so record the E2E/recovery step-level outcome as unconfirmed here.
- Broadened replacement and final old-version assertions to scan the real image filesystem while pruning `/proc`, `/sys`, `/dev`, and `/run`. It now replaces all matching 2.22.2 jars regardless of directory, accepts 2.22.3 only when no vulnerable copy is found, and fails if the vulnerable version remains anywhere in the scanned filesystem.
- Checks actually run: `docker build --check --file deployment/neo4j/Dockerfile .` passed; `docker compose config --quiet`, `scripts/test-compose-config.ps1`, and `git diff --check` passed. No full local image build or Trivy scan was run because local disk remains constrained.
- Next: commit/push the global search and verify the hosted Trivy result has zero fixed High/Critical findings, the image starts as `neo4j`, and the full application/recovery suite passes. Cloud deployment, cloud backup/restore, browser/accessibility review, and evaluation on an authorized time-separated dataset remain incomplete.

## 2026-11-12 20:16 IST — Add file paths to Trivy annotations

- Hosted run [`43239638247`](https://github.com/gaurvit06/RSIACDP/actions/runs/43239638247) (`5e5b98b`) still reported the same four Jackson 2.22.2 High findings after the global filename patch. The six zlib findings remained absent. The CI report currently labels Java findings only as `Java`, masking the package's file/virtual path.
- Updated the vulnerability annotation builder to prefer Trivy's `PkgPath` when present and fall back to its result target. The next hosted scan will show whether this report includes a useful archive path for the remaining Jackson packages.
- Checks: embedded annotation JavaScript passed `node --check`; GitHub Actions YAML parsed successfully; Docker's Neo4j Dockerfile check passed; `scripts/test-compose-config.ps1` passed; and `git diff --check` passed. A separate bare `docker compose config --quiet` call initially failed because no local deployment secrets were set; the repository script then supplied synthetic validation values and passed its Compose configuration checks.
- Hosted run [`43241342196`](https://github.com/gaurvit06/RSIACDP/actions/runs/43241342196) (`eb4887d`) finished with frontend, backend, Compose config, web-container, operations scripts, synthetic intake/report/correction flow, encrypted restore, and PostgreSQL-to-Neo4j graph rebuild passing. Its only failure was strict Neo4j Trivy enforcement: four Jackson findings resolved to `var/lib/neo4j/lib/parquet-jackson-1.18.1.jar`.
- Reproduced the upstream diagnosis in Apache's own issue and official release notes: Parquet 1.18.1 shades Jackson 2.22.2, and Parquet 1.18.2 is the maintenance release with the Jackson update. Downloaded the official 1.18.2 JAR from Maven Central, matched Maven Central's SHA-1 sidecar, computed and pinned SHA-256 `dc20428b547c6376ae7dfa20c30a62c326b7e4ed4915ba5370ae7d7b0859408d`, and inspected its embedded metadata (Jackson core/databind 2.22.4).
- Checks for the Parquet replacement: `docker build --check --file deployment/neo4j/Dockerfile .` passed (syntax/metadata only); `scripts/test-compose-config.ps1` passed; and `git diff --check` passed. No full local image build or Trivy scan was run because Docker storage is constrained.
- Next: commit and push the targeted Parquet bundle replacement, then require Trivy to clear all findings and the same hosted full-flow/recovery checks to pass. No scanner exception is being added. Cloud deployment, cloud backups, browser/accessibility review, and authorized labeled evaluation remain incomplete.

## 2026-11-12 20:30 IST — Hosted Neo4j security gate and full E2E passed

- Hosted CI run [`43242930699`](https://github.com/gaurvit06/RSIACDP/actions/runs/43242930699), commit `fade4c0`, completed successfully. Frontend, backend, Compose configuration, web-container, operations scripts, and Compose E2E jobs all passed.
- The CI policy's fixed High/Critical image scans passed for API, web, PostgreSQL, Neo4j, and Caddy. The Compose run also passed Neo4j image build/startup, scanned-PDF OCR, synthetic case intake/processing/graph links/reports/corrections, encrypted backup and live restore, migrations, PostgreSQL-to-Neo4j rebuild, and cleanup. The existing path-scoped, expiring Caddy exception remains documented; the scan policy ignores unfixable findings.
- This verifies hosted CI on the pushed code, including the replacement of the scanned `parquet-jackson-1.18.1.jar` with the SHA-pinned Apache 1.18.2 release. It does not mean a Vercel, Render, or Supabase deployment has been provisioned or production configuration has been tested.
- Next: finish provider-specific setup using owner-created Vercel/Render/Supabase accounts and secrets; validate TLS, storage privacy, deployed health, egress and backup/restore; complete browser/accessibility review; and run evaluation on authorized labels. No cloud credentials have been shared with this workspace.

## 2026-11-12 20:43 IST — Reproduce and qualify the synthetic baseline metrics

- Inspected the existing ignored fixture artifact rather than overwriting it. SHA-256 of `synthetic-input.jsonl` matches `MANIFEST.json`: `f458554cfd53ef57041047ff83f37e16904bad0a0348564fd9d3c4168d7c00f5` (108 records; 36 train, 36 dev, 36 test).
- Independently reran `python evaluation/evaluate.py .test-runtime/synthetic-evaluation-v1/tfidf-predictions.jsonl` in the existing release-check worker image with the backend mounted read-only. It reproduced entity micro-F1 `0.00` (36 FN), campaign pairwise F1 `0.00` (36 FN), support precision undefined / recall `0.00` (18 FN), synthetic narrow concern FPR `0/18`, and classifier-only runtime mean `0.0157778 ms`, p95 `0.025 ms`. Bootstrap: 1,000 resamples, seed `20261103`; entity and campaign F1 intervals `[0,0]`; evidence precision interval undefined because there were no predicted claims.
- These are explicitly generator-defined synthetic rehearsal values. The TF-IDF comparator is text-only and intentionally predicts no entity, campaign, or evidence-support claims; the time boundary excludes app/worker, retrieval, OCR, graph operations, training and I/O. No real-world performance or production latency claim is supported.
- Updated `backend/evaluation/README.md` and the engineering walkthrough with the hash, metrics, limits, and interpretation. Full/no-graph application runs and LLM/web-search with lawful retrieval remain unmeasured; they cannot be honestly inferred from this baseline rehearsal. Evaluation on independent, authorized annotations remains pending.
- Checks actually run: the scorer completed successfully in the existing container using a read-only backend mount; the manifest hash matched; and `git diff --check` passed. Provider deployment and manual browser/accessibility review also remain incomplete.

## 2026-11-12 21:04 IST — Tighten fee-request extraction

- Reviewed the parser after the synthetic full-pipeline rehearsal exposed a false candidate: a mere phrase such as “A registration fee was mentioned” was extracted as `fee_request`.
- Replaced the broad substring rule with deterministic, sentence-scoped checks: explicit payment action before a fee/deposit/charge, or an explicit obligation after it. Added conservative no-fee/negation/waiver exclusions and exact source-span recording. Clause boundaries are precomputed once and binary-searched per candidate to avoid quadratic rescans. This remains a review candidate and does not change the finding/verdict rules.
- Added negative tests for generic fee mentions, mentions in separate clauses, no-fee and waived-fee text; added positive tests for explicit send/payment actions, mandatory fees, decimal amounts, and exact offsets.
- Checks: `python -m unittest tests.test_extract -v` passed (29 tests). The first full-suite attempt mounted the repository read-only; two pre-existing baseline tests correctly failed because they write under `.test-runtime`. Reran using a fresh temporary copy of tracked backend code and the dependency-complete worker image with network disabled: `backend/run_ci_tests.py` passed — 232 unit tests (2 opt-in PostgreSQL tests skipped), 15 isolated API-flow tests, and 2 proxy-header tests. The temporary copy is under OS Temp; no repository runtime files, shared database, or containers were modified. The local `.venv` lacks FastAPI, so tests ran in the existing worker image.
- Updated `ENGINEERING_WALKTHROUGH.md` section 9.95 with the applied-ML, product-safety, full-stack, and deployment rationale and steps.
- Not yet committed or pushed. Focused extraction tests and the complete backend runner passed on the final code, then `git diff --check` passed; the hosted run for this source change remains to be run.

Next steps, in order:

1. Run `git diff --check` and inspect the final parser/documentation diff.
2. Commit and push the extraction correction and documentation (push was authorized earlier); inspect its hosted CI result.
3. Continue the full-versus-no-graph synthetic integration rehearsal only if the fixture can avoid shared-domain campaign leakage; label any generator-derived outcomes as smoke/integration results, not accuracy results. Do not infer the outstanding LLM/web-search baseline without a configured lawful provider.
4. Resume deployment when the owner answers whether the Vercel, Render, and Supabase projects exist, selects the Supabase region/domain, and configures required secret values directly in the provider dashboards. Do not ask for secret values in chat.
5. Production TLS/storage/egress/backup checks, authorized browser/accessibility review, and independent time-separated evaluation remain incomplete; do not mark the project fully complete before these stages are actually done.

## 2026-11-12 21:20 IST — Complete the synthetic local pipeline smoke

- Follow-up to section 9.95: commit `72e4a9e` (“Make fee request extraction evidence-specific”) was pushed to `codex/initial-platform`. Hosted CI run [`43249522199`](https://github.com/gaurvit06/RSIACDP/actions/runs/43249522199) completed successfully for that revision. This CI result predates the v2 evaluation code recorded below.
- Kept the historical v1 fixture/output unchanged. Added `backend/evaluation/generate_synthetic_v2.py`: 108 generated cases, chronological split counts 36/36/36, explicit email plus derived-domain labels, distinct `.invalid` domain per campaign, generator provenance, and input SHA-256 manifest. This removes global placeholder-host leakage between synthetic campaigns.
- Added `backend/evaluation/run_synthetic_pipeline.py`, which uses actual application extraction, worker/local evidence/findings logic, campaign threshold 40, pipeline exporter, TF-IDF baseline and scorer. It creates isolated temporary SQLite databases, clones full/no-graph state, checks case/evidence and corpus snapshot HMAC equality, writes scorer-format outputs/metadata in a new protected output directory, and removes temporary database files. It forces local/test configuration and disables Supabase, Neo4j and RDAP. It does not connect to production or external services.
- Added `backend/tests/test_synthetic_v2.py`. Checks passed in the existing dependency-complete worker image with networking disabled: full backend runner — 235 unit tests (2 opt-in PostgreSQL tests skipped), 15 isolated API-flow tests and 2 proxy-header tests. The focused generator checks also passed locally: 3 tests covering labels/splits/manifest, source fingerprint and no-overwrite behavior.
- Ran the v2 pipeline smoke in that worker image with `--network none`. Input SHA-256: `67fdfbdabbc5a21f45b1af56d6bb37be825c124ee8e81219608f87a0f38ebe60`; 36 held-out synthetic test cases; matched full/no-graph evidence and corpus HMACs. Results are generator-defined, not model accuracy:
  - TF-IDF/logistic: entity F1 0.00; campaign pairwise F1 0.00; evidence support precision undefined/recall 0.00; concern FPR 0/18; classifier mean/p95 0.0155/0.0364 ms.
  - Evidence pipeline without graph linking: entity F1 1.00; campaign pairwise F1 0.00; evidence support precision/recall 1.00/1.00; concern FPR 0/18; worker mean/p95 43.711/75.605 ms.
  - Full evidence pipeline: entity F1 1.00; campaign pairwise F1 1.00; evidence support precision/recall 1.00/1.00; concern FPR 0/18; worker-plus-link mean/p95 51.654/82.462 ms.
- The full-pipeline perfect scores are tautological: the synthetic generator defines labels, generated local source records, and evidence relevance from the same rules. This confirms narrow workflow wiring only. The runner does not exercise Neo4j projection or independent investigator review; timings are not production latency. LLM/web-search with lawful retrieval remains unmeasured.
- Results and limitations documented in `backend/evaluation/README.md` and `ENGINEERING_WALKTHROUGH.md` section 9.96. The final output dataset/run remains outside Git under `C:\Users\gaurv\AppData\Local\Temp\rsaicdp-eval-v2-a7e4274ec9b7428cb5a8b2c56e70eca1\run-final2`; it contains only reserved synthetic records.
- Changes for the v2 generator, runner, tests and docs are not yet committed/pushed. Run `git diff --check`, inspect the final changes, commit/push under the earlier authorization, and inspect the new hosted CI result. Then continue provider deployment only after project existence, region/domain and dashboard setup inputs are resolved. Production service checks, independent labels, LLM baseline and authorized browser/accessibility review remain incomplete.

## 2026-11-12 21:30 IST — Tie the smoke run to the pushed evaluation revision

- Commit `626c000663cabe336365e1fd68dba3c3bef06e32` was pushed to `codex/initial-platform`. It adds the v2 fixture generator/runner, generator tests, updated evaluation procedure/results and the final fee-extraction grammar refinement. The backend runner passed immediately before the push: 235 unit tests (2 opt-in PostgreSQL tests skipped), 15 API-flow tests and 2 proxy-header tests. Focused extraction+fixture tests passed: 32 tests; `git diff --check` passed before commit.
- Hosted CI run [`43253517759`](https://github.com/gaurvit06/RSIACDP/actions/runs/43253517759) for this commit was still in progress when last checked. The prior extraction-only run [`43249522199`](https://github.com/gaurvit06/RSIACDP/actions/runs/43249522199) passed.
- Re-ran the synthetic v2 pipeline from the pushed commit, offline, in the existing worker image. Recorded Git revision `626c000663cabe336365e1fd68dba3c3bef06e32`, source snapshot SHA-256 `d5b460ca3381889b7d96f858c32188c43c9a1a94aba3363ec731ccd4a674bac0`, and input SHA-256 `67fdfbdabbc5a21f45b1af56d6bb37be825c124ee8e81219608f87a0f38ebe60`; full/no-graph evidence and corpus HMACs matched. Final synthetic test metrics (36 cases): TF-IDF entity/campaign F1 `0/0`, evidence precision undefined/recall `0`, FPR `0/18`, mean/p95 `0.0125/0.0177 ms`; no-graph F1 `1/0`, evidence P/R `1/1`, FPR `0/18`, time `39.580/56.708 ms`; full F1 `1/1`, evidence P/R `1/1`, FPR `0/18`, time `47.823/64.634 ms`. These remain generator-tautological integration results, not independent accuracy or production latency.
- The final output is outside the repository at `C:\Users\gaurv\AppData\Local\Temp\rsaicdp-eval-v2-a7e4274ec9b7428cb5a8b2c56e70eca1\run-commit-626c000`; the repository worktree is clean after the push and only synthetic reserved identifiers are present in that output.
- Next: inspect hosted CI run 44, update and push this follow-up record, then wait for the pending owner answers about provider project state/region/domain and approved LLM provider. Cloud deployment/TLS/storage/egress/backup verification, manual browser/accessibility review, and independent authorized evaluation remain open.

## 2026-11-12 21:36 IST — Remove wildcard proxy-header trust from Render

- Hosted CI run [`43253517759`](https://github.com/gaurvit06/RSIACDP/actions/runs/43253517759) completed successfully on commit `626c000663cabe336365e1fd68dba3c3bef06e32`; backend, frontend, operations scripts, web-container, Compose configuration and Compose E2E/recovery jobs all passed.
- Reviewed the Render deployment path after noticing `render.yaml` set `FORWARDED_ALLOW_IPS: "*"`, contradicting the project's explicit no-wildcard proxy rule. Changed the Blueprint to loopback-only `127.0.0.1` until a real hosted trust chain can be measured and verified. This fails closed against spoofed forwarded headers.
- Documented the effect: Render request-address throttles will see the platform proxy peer until a safe client-IP path is verified, so those limits are coarse/shared in hosted mode. The API's Render origin is public alongside the Vercel rewrite; before production, test both paths with spoofed `X-Forwarded-For`, inspect peer/forwarding behavior, and only configure a precise trusted-proxy list if direct-origin bypass cannot defeat it. Do not restore `*`.
- Added a check to `scripts/test-compose-config.ps1` requiring the Render Blueprint's forwarded-header trust to stay loopback-only. Verification passed: the script reported Compose security wiring/configuration passed, and PyYAML parsed `render.yaml` with the expected value. `git diff --check` remains to run after this documentation/config update.
- Changes are not yet committed/pushed. Next: run `git diff --check`, review the diff, commit/push, and inspect hosted CI. The Render/Vercel/Supabase project setup details are still pending; hosted proxy behavior cannot be verified before the services exist.

## 2026-11-12 21:44 IST — Verify the Render proxy trust change

- Commit `16d5fed0a4b92662896ae73981b5b5d1d0ca6462` was pushed to `codex/initial-platform` under the user's earlier authorization. It keeps Uvicorn forwarded-header trust loopback-only in `render.yaml`, adds a Compose configuration assertion, documents the shared/coarse request-address throttle limitation and the required Vercel/direct-Render spoofing check, and corrects the evaluation walkthrough's hosted-CI reference.
- Local checks passed: `scripts/test-compose-config.ps1`; `git diff --check`; and a PyYAML parse of `render.yaml` confirming `FORWARDED_ALLOW_IPS=127.0.0.1`.
- Hosted CI run [`43255358061`](https://github.com/gaurvit06/RSIACDP/actions/runs/43255358061) for the pushed revision completed successfully. Backend, frontend, operations scripts, web-container, Compose config, and Compose E2E/recovery jobs passed. E2E included image scans, app startup, OCR, synthetic intake/processing/graph/report/correction workflows, encrypted backup and live restore, migrations, and PostgreSQL-to-Neo4j rebuild. These checks run in CI's isolated environment; they do not verify any live Vercel, Render, or Supabase project.
- No cloud resources were provisioned. Waiting for the owner to create or identify the Vercel/Render/Supabase projects and provide nonsecret public endpoints/region. Never request passwords or secret keys in chat; configure those only in provider dashboards. Before production, verify TLS/cookies, direct-origin and Vercel proxy behavior, storage privacy, resource/retention behavior, provider backup and object restore, and operator accounts.
- Other outstanding work: independent authorized labels for evaluation, a lawful/configured LLM plus web-search baseline (optional to core local operation), and a manual browser/accessibility review. Synthetic v2 metrics remain generator-tautological integration checks, not product accuracy or production latency.
- Exact next steps: (1) obtain the Vercel production origin, Render API hostname, and Supabase region/project status; (2) confirm Render and Vercel deployment branches/settings and place Supabase/one-time bootstrap secrets in protected provider settings; (3) deploy and run the hosted verification checklist in `README.md`; (4) only then update the trusted proxy strategy based on observed provider behavior; (5) arrange authorized, time-separated annotations for external evaluation. No cloud deployment should be described as complete before those checks pass.

## 2026-11-13 00:10 IST — Prepare and verify free-tier hosted configuration

- Read the user-provided deployment task and confirmed its boundary: prepare and guide only; do not create provider resources or deploy until explicit approval. Existing Vercel project and Supabase resources are user-reported and were not inspected through provider credentials. No secret values were requested or accessed.
- Replaced the paid Render Blueprint with one Free Singapore Docker Web Service. It uses Supabase PostgreSQL and private Storage, disables optional Neo4j, uses PostgreSQL-backed graph views, and sets `RUN_INLINE_WORKER=true`; no Render database, worker service, persistent disk, pre-deploy command, or private service is defined.
- Implemented an optional API-owned background worker for the single-service host. Local Compose retains its separate worker with the default `RUN_INLINE_WORKER=false`. Worker polling is stoppable; the API lifespan starts/stops it; unexpected exits restart with capped exponential backoff; iteration failures back off without exposing exception text.
- Added worker runtime and API lifespan tests, registered the API test in the isolated backend runner, documented the environment variable in `.env.example`, updated README hosting notes, created `FREE_DEPLOYMENT.md`, and recorded engineering decisions in `ENGINEERING_WALKTHROUGH.md` section 9.97. Extended the Compose/Render config checker; fixed its single-service PowerShell array assertion after an initial local check exposed scalar-string indexing.
- Checks actually run on the final code: backend runner passed with 238 unit tests (2 opt-in PostgreSQL tests skipped), 15 API-flow tests, 1 inline-worker API lifespan test, and 2 proxy-header tests; frontend frozen-lockfile install passed; Vite/TypeScript production build passed; 24 redaction/UI-state tests passed; `scripts/test-compose-config.ps1` passed with synthetic values; PyYAML parse and Render Free service/inline worker/proxy-trust assertions passed; `git diff --check` passed after the script fix.
- Limits: Docker Engine was not running, so no image build, container startup, live PostgreSQL/Neo4j integration, or Compose E2E ran locally. Provider dashboards and secret/config values, Supabase migration state and bucket ACL, public Vercel/Render origin behavior, billing/quotas, TLS, deployed retention, and backup/restore remain unverified. No deployment was performed. Do not push the branch until the deployment boundary and auto-deploy behavior are resolved.
- Exact next steps, in order: (1) inspect the complete final diff and check local Git status; (2) keep local changes saved and prepare a local commit if required; (3) confirm whether the owner explicitly approves deployment and that the Vercel project's auto-deploy behavior will not violate that approval boundary; (4) privately confirm the Vercel public origin, Render service hostname/branch/region/Free plan and Supabase region, database pooler connection and private bucket without sharing secrets in chat; (5) only after explicit approval, push/apply the Blueprint and run the synthetic hosted checklist in `FREE_DEPLOYMENT.md`; (6) separately complete authorized independent evaluation and manual browser/accessibility review. Resume with `git status --short`, read this entry, then run `git diff --check` before proceeding.

## 2026-11-13 00:17 IST — Verify local web serving and resume state

- Re-read the project plan and latest status. `git status --short --branch` confirms the worktree is clean on `codex/initial-platform`, with local commit `df75ea4` one commit ahead of `origin/codex/initial-platform`.
- Started the Vite development server for a local-only HTTP smoke, confirmed `/`, `/src/main.tsx`, and `/src/App.tsx` each returned HTTP 200, checked the HTML title and React module entry, and then stopped the server. This verifies local asset serving; it is not a visual, accessibility, authenticated API, or deployed-endpoint review.
- The host has no discoverable `psql`, `postgres`, or `neo4j` command/service, and Docker Engine is unavailable. No live PostgreSQL, Neo4j, Docker image, or Compose E2E check was possible locally. Existing backend API integration tests used isolated SQLite and passed in the previous entry; do not describe that as PostgreSQL verification.
- Manual browser/accessibility review remains incomplete. Windows Computer Use previously stopped before navigation because it could not determine the current browser URL confidently; no application interaction was performed. A follow-up `node_repl` call also showed no `cua` binding in that runtime, so no UI automation was attempted this turn.
- No deployment approval response has arrived. The local commit remains unpushed because the connected Vercel project may deploy automatically on push and the user-provided deployment task explicitly requires approval first. No provider settings, cloud resources, secrets, or case data were touched.
- Next steps: (1) wait for the already presented explicit push/deployment approval; (2) if approved, verify the actual Vercel auto-deploy behavior and non-secret provider project/region/origin settings before any push or resource creation; (3) configure only free services and secrets privately in the dashboards; (4) run hosted checks with synthetic cases; (5) perform manual visual/accessibility review via an available approved browser path; (6) obtain independent authorized evaluation labels or keep model accuracy pending. Do not ask for secrets in chat.

## 2026-11-13 00:22 IST — Cross-check deployment guide against source migrations

- Corrected `FREE_DEPLOYMENT.md` to match the owner's stated provider state (Vercel and Supabase projects are user-reported; the Render Web Service has not yet been created). The guide now explicitly tells the operator to remove stale `NEO4J_*` variables from any previously configured Render service or environment group so the documented PostgreSQL graph fallback is actually selected.
- Used the pinned backend environment and Alembic's `ScriptDirectory` to verify one migration head and compare all 18 ordered revisions against the guide. The documented order matches the source revision graph exactly.
- Ran `alembic heads`, `alembic history`, and `alembic upgrade head --sql` against the PostgreSQL dialect without connecting to a database. Alembic generated 441 lines of offline DDL and advanced `alembic_version` through `e7a91c0d4b62` with a final `COMMIT`. This verifies migration-chain rendering only; it does not verify execution against Supabase or PostgreSQL server compatibility at runtime.
- No deployment, push, provider access, or database mutation occurred. GitHub is still two commits behind local `codex/initial-platform`; explicit deployment approval remains unanswered.
- Next: proceed with the previously recorded non-secret provider checks and deployment only if explicit approval arrives. Until then, keep the code local and do not report Supabase migrations, storage, billing, TLS, or backups as verified.

## 2026-11-13 00:26 IST — Receive deployment approval and refresh readiness audit

- The owner explicitly approved pushing the prepared branch and proceeding with hosted deployment on the free Vercel/Render/Supabase stack. This supersedes the earlier wait-for-approval status; payment-card and paid-resource restrictions remain in effect.
- Re-read current Git status and project instructions. The branch is clean before this documentation update and contains the approved free Render Blueprint/inline-worker commits locally. Current hosted CI still does not include these local changes.
- Audited `REQUIREMENTS_TRACEABILITY.md` against current `BUILD_STATUS.md`, CI history, and the current environment. Corrected stale statements claiming there was no Git remote/hosted runner, no hosted CI, an available local Docker Engine, and outdated test counts. It now distinguishes earlier hosted CI run `43255358061` for commit `16d5fed` from the untested local deployment commits, records current local test counts, and marks provider/browser/evaluation proof as pending.
- Updated `FREE_DEPLOYMENT.md` to record the approval and reflect that the deployment may now proceed under the no-charge constraints. The 18-revision migration chain was independently checked against Alembic source and PostgreSQL offline DDL; no live Supabase migration occurred.
- Next steps, in order: (1) run final whitespace/secret/diff checks and commit this traceability refresh; (2) push the approved branch; (3) inspect current GitHub CI and Vercel deployment results; (4) confirm actual Render free plan, project URL/region, Vercel origin, Supabase project region, private bucket and database migration state through provider interfaces; (5) configure secrets only in Render's protected settings, create the one Free Web Service, and run the synthetic hosted workflow; (6) stop if any provider asks for billing/paid resources; (7) report anything blocked by missing account access without claiming deployment complete.

## 2026-11-13 00:40 IST — Verify provider state and start approved deployment

- Re-read `BUILD_PLAN.md`, `BUILD_STATUS.md`, `FREE_DEPLOYMENT.md`, `render.yaml`, `frontend/vercel.json`, repository instructions, and Git status. Worktree was clean on `codex/initial-platform` at `8f1ee94e6bc6195d0a16cdd70bc7bc227c6f277c`, tracking the same remote commit.
- GitHub Actions run [`43285357799`](https://github.com/gaurvit06/RSIACDP/actions/runs/43285357799) completed successfully for that commit: frontend, backend, operations scripts, web-container, Compose config, and Compose E2E jobs all passed.
- Inspected provider dashboards without reading/copying any provider secret. Render's signed-in workspace reports no services and no environment groups. Supabase has one healthy Free project in Tokyo (`ap-northeast-1`), current overview reports no migrations and no backups, and Storage has the `private-evidence` bucket with the Public bucket switch off. The bucket shows the default 50 MB limit and Any MIME type; application-level validation remains the 10 MiB plaintext limit. Render is configured for Singapore, so Supabase database calls will cross regions.
- The signed-in Vercel Hobby workspace had no RSIACDP project. Started the approved frontend import from `gaurvit06/RSIACDP`, branch `codex/initial-platform`, root directory `frontend`, Vite preset, project name `rsiacdp-frontend`. Vercel required step-up email verification before deployment; the code was sent and the browser is waiting for the account owner to enter it. The project has not yet been created and no production URL exists.
- No database migrations were run, no Render service was created, and no secrets were accessed or entered. No payment-card, billing, paid-tier, or trial flow was started.
- Updated `FREE_DEPLOYMENT.md` with the observed provider state, verification boundary, existing region mismatch, and accurate Vercel workspace status.
- Checks in this stage: GitHub Actions above passed; provider state was visually inspected in authenticated dashboards; final documentation diff passed `git diff --check`. Documentation commit and hosted CI remain to be completed.
- Exact next steps: (1) owner enters Vercel's one-time code directly into the open browser and replies `done` (never send the code in chat); (2) verify the Vercel frontend deployment and capture its generated production origin; (3) create the one Free Render service from root `render.yaml`, stopping if billing/card/payment or a paid tier is required; (4) owner enters `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and the exact `WEB_ORIGIN` in Render's protected configuration only; (5) verify generated secrets and start the service; (6) inspect the existing Supabase schema first, confirm it is fresh, then let the API's Alembic startup apply migrations; (7) run hosted synthetic end-to-end, privacy, proxy, TLS, health, retention and correction checks; (8) record what is actually verified, commit/push this status and deployment documentation, and inspect CI. Do not claim hosted workflows complete before those checks pass.

## 2026-11-13 00:56 IST — Record the live deployment blocker after approval

- The owner explicitly approved pushing the prepared commit and proceeding with hosted deployment. The branch is already pushed and clean at `cb09da0` (`origin/codex/initial-platform` matches). The deployment approval does not override the no-card/no-charge constraint recorded in the deployment task.
- Verified public endpoints directly: `https://rsiacdp-frontend.vercel.app/` returns HTTP 200; `https://rsiacdp-frontend.vercel.app/api/health/live`, `https://rsiacdp-api.onrender.com/health/live`, and `/health/ready` on the planned Render hostname return HTTP 404. This is a live static frontend only, not a working end-to-end deployment.
- GitHub Actions run [43287764588](https://github.com/gaurvit06/RSIACDP/actions/runs/43287764588) passed all six jobs for `cb09da0`: backend, frontend, operations scripts, web container, Compose configuration, and Compose E2E. CI does not provision or verify provider services.
- In the prior authenticated provider session, Render had no service or environment group. Starting the Blueprint flow displayed an identity-verification requirement for a payment card and temporary USD 1 authorization. The flow was canceled; no card was entered, no charge/authorization was initiated, and no Render resource was created. No bypass was attempted.
- Supabase dashboard had shown the Free project healthy in Tokyo and `private-evidence` private. Its overview showed no migrations or backups, but no SQL/schema query was run; migration state is therefore **unverified**. No migration ran, no provider secrets were read or copied, and no database/storage mutation occurred in this stage.
- Updated `FREE_DEPLOYMENT.md` to replace stale Vercel/Render onboarding status with current public endpoint and dashboard observations, and to state plainly that hosted deployment is not end to end. No application code changed.
- Checks: direct HTTP status probes above; GitHub CI run above; `git diff --check` passed; reviewed the complete documentation diff. No tests were run because this change only updates deployment/status documentation.
- Exact next steps, in order: (1) resolve the backend-hosting conflict: either the owner changes the no-card constraint and completes Render's card verification personally, or selects/approves a different backend deployment design that does not require a card; do not enter payment details or switch hosts silently; (2) only after the chosen host is approved, configure secrets directly in its protected dashboard and deploy; (3) query Supabase schema/migration state before any startup migration; (4) run hosted synthetic end-to-end, access-control, storage, health, retention, correction, proxy, TLS, and backup/restore checks; (5) review the browser UI and accessibility; (6) obtain independent authorized evaluation labels or leave evaluation pending; (7) update this status and inspect CI for every subsequent push.
- Resume commands: `git status --short --branch`; read `BUILD_STATUS.md` and `FREE_DEPLOYMENT.md`; query `https://api.github.com/repos/gaurvit06/RSIACDP/actions/runs?branch=codex%2Finitial-platform&per_page=5` for hosted CI. Do not claim the project is complete while the backend deployment and listed verification stages remain unfinished.

## 2026-11-13 01:17 IST — Make missing-backend behavior actionable

- Added `frontend/src/api-client.ts` with shared network failure handling and safe response parsing. Wired it into the common authenticated request wrapper, session restoration, sign-in/account creation, password reset, and public correction submission/status workflows. Structured API validation details remain visible; non-JSON 404/5xx and empty gateway responses now produce actionable service messages rather than a JSON parser exception.
- Added `frontend/tests/api-client.test.ts` for a missing non-JSON route, non-JSON server error, empty 502 gateway response, structured 422 detail, successful JSON response, and network failure. Existing tests still cover session state, evidence mode, graph filters, review rules, and redaction.
- Verified the active Vite server's actual `/api/auth/me` proxy response: HTTP 502, `text/plain`, empty body. Running that response through the new helper yielded: “The investigation service is temporarily unavailable. Check the backend deployment or retry shortly.”
- Recovered the local Chrome target from a fresh window list after an earlier computer-use stop. The sign-in screen visibly displayed the new temporary-service alert with no JSON parser exception. This confirms frontend failure-state presentation only; no authenticated API/backend workflow was available.
- Checks: `pnpm run test:redaction` passed 30 tests; `pnpm run build` passed (`tsc -b` and Vite production bundle); `git diff --check` passed. No backend or database checks were rerun because only frontend error handling and documentation changed.
- Updated `ENGINEERING_WALKTHROUGH.md` section 9.98 and added a documented Vercel-host assessment to `FREE_DEPLOYMENT.md`. Vercel can host FastAPI, but the current 10 MiB upload limit, Docker-installed Tesseract, and lifespan-managed worker require an actual architecture migration; the app has not been migrated and Render remains the selected backend.
- Known limitations: Render still has no service because its onboarding requires card verification under the owner's no-card constraint. The Vercel page remains static-only; `/api/*` has no working backend. Supabase schema/migration state was not queried. Independent evaluation labels, hosted E2E/security/recovery checks, and complete accessibility review remain pending.
- Next steps, in order: (1) keep the backend host decision pending; do not change from Render without owner authorization; (2) commit and push the frontend error-handling/docs stage under the existing authorization, then inspect Vercel and CI deployment results; (3) if the owner selects a no-card backend, implement the required durable job processing, private upload, OCR, and migration changes before hosting it; (4) otherwise continue local backend/UI verification and retain the clear hosted-unavailable state; (5) resume hosted integration only once a backend path and protected secrets are available; (6) keep the overall project active until every completion criterion is verified.

## 2026-11-13 01:25 IST — Verify the pushed frontend error handling and CI

- Commit `99283398944c003bfa26c49a8af305c72b057a68` (`9928339`, “Handle unavailable investigation API responses”) was pushed to `codex/initial-platform`; `origin/codex/initial-platform` matches and the worktree is clean.
- Vercel published the frontend revision: `https://rsiacdp-frontend.vercel.app/` returned HTTP 200, and the deployed JavaScript asset contains the new actionable investigation-service error text and no longer contains the prior raw JSON parser error. This verifies the static frontend deployment only.
- The six jobs in GitHub Actions run [43294015797](https://github.com/gaurvit06/RSIACDP/actions/runs/43294015797) all completed: backend (14 successful steps), frontend (12), Compose config (6), Compose E2E (20 successful and 4 conditionally skipped), web container (12), and operations scripts (5). No executed step had a failure conclusion. This CI run uses isolated CI services; it does not establish that cloud services are deployed.
- Live API checks remain unavailable: the Vercel `/api/health/live` route and planned Render `/health/live` and `/health/ready` endpoints returned HTTP 404. Render still has no service because provider onboarding requested card verification under the no-card/no-charge constraint. No card or payment information was entered; no provider service was created. Supabase remains unqueried for schema/migration state.
- No application code changed in this verification step. The prior `pnpm run test:redaction` (30 passing tests), `pnpm run build`, and `git diff --check` are recorded in the preceding section. The new CI run additionally exercised the backend, frontend, Compose configuration, full Compose E2E/recovery, web-container, and operations-script jobs as listed above.
- Remaining deployment decision: keep the selected Vercel/Render/Supabase design unless the owner authorizes a different backend host or resolves Render card verification. Do not silently migrate the backend. Once the host path is decided, configure provider secrets only in the relevant protected dashboard, inspect Supabase schema/migration state before starting migrations, deploy the backend, and run the hosted verification checklist.
- Exact next steps: (1) obtain the owner's explicit backend-host decision compatible with the no-card constraint; (2) after that, deploy/configure the selected backend and verify the database state before migrations; (3) run hosted synthetic end-to-end, privacy, storage, TLS, proxy, retention, correction, and backup/restore checks; (4) complete authorized browser/accessibility review and independent labeled evaluation when data is available; (5) update this file with actual results. The application is not fully deployed or complete while these criteria remain open.

## 2026-11-13 01:54 IST — Prepare the owner-authorized no-card backend path

- The owner chose to authorize a no-card host change and asked me to choose the host after Render's verified setup flow stopped at card verification. I assessed current official provider docs and selected Hostless for a **synthetic-data review deployment only**. Hostless account/service creation, app origin, region, and provider-side security/privacy review are still pending. No Hostless or Supabase secrets were read, shared, or entered.
- Added root `hostless.yaml` for the existing backend Docker image and one queue worker. Each process is fixed to one 0.1-vCPU/256-MiB replica; no database or persistent volume is provisioned there. PostgreSQL and encrypted private evidence objects remain in Supabase. Neo4j remains optional; the graph screen uses the PostgreSQL-derived fallback if no graph service is configured.
- Replaced the fixed Render rewrite with `frontend/vercel.mjs`, using the Vercel project variable `$API_ORIGIN` for the same-origin `/api/*` route. The URL is not guessed or committed; it must be set after Hostless assigns a verified origin. The existing security headers remain.
- Updated `FREE_DEPLOYMENT.md`, `README.md`, `BUILD_PLAN.md`, and this walkthrough with the architecture, resource limits, environment inventory, migration preflight, data-protection boundary, exact activation sequence, and outstanding checks. `render.yaml` remains a legacy fallback; Hostless is the authorized target.
- Dependency audit caught two high advisories in the initially selected `@vercel/config` SDK. Removed that package, used Vercel's supported JavaScript config and the equivalent documented `$API_ORIGIN` routing placeholder, then reran the full frontend audit successfully with no known vulnerabilities.
- Checks on this unpushed workspace: `pnpm install --frozen-lockfile` passed; `pnpm audit` reported no known vulnerabilities; `pnpm run test:redaction` passed all 35 tests, including Hostless YAML/resource bounds, absence of committed secrets/volumes, Vercel API routing, review rules and redaction; `pnpm run build` passed TypeScript and Vite; `git diff --check` passed. Latest pushed CI run [43295235569](https://github.com/gaurvit06/RSIACDP/actions/runs/43295235569) had six successful jobs before these changes; the new manifest is not yet in hosted CI.
- Deployment status remains incomplete: Vercel's live page is static-only and its current API route is unavailable; no Hostless service or `API_ORIGIN` exists; Supabase schema/migration state is unverified; no hosted workflow has been run. Hostless's reviewed public material did not establish a region, DPA, or independent security assurance for this project. Keep real personal evidence out of this target until owner verification and hosted security/backup checks. The 256-MiB limit may also be insufficient for some OCR inputs and needs live measurement.
- Exact next steps: (1) review the deployment/docs diff and push this prepared stage under the existing authorization; (2) verify the new GitHub CI run and Vercel deployment result, without claiming API availability; (3) owner runs the Supabase schema preflight in `FREE_DEPLOYMENT.md`; (4) owner creates the Hostless app only if its dashboard confirms no-card, no-paid capacity, and $0, then sets required secrets directly there; (5) set Vercel `API_ORIGIN` to the verified Hostless URL; (6) run synthetic hosted intake/OCR/worker/report/correction, privacy, migration, TLS, proxy, retention, and backup checks. Do not call the project complete until the hosted flows and all other completion criteria are verified.

## 2026-11-13 02:03 IST — Push and verify the no-card deployment preparation

- Committed the Hostless and Vercel deployment configuration as `d1797ff25e7bf1206cf15692de3b1588a333341a` (`Prepare no-card Hostless backend deployment`) and pushed it to `origin/codex/initial-platform` under the owner's existing push authorization. The branch is clean and synchronized.
- GitHub Actions run [43300545988](https://github.com/gaurvit06/RSIACDP/actions/runs/43300545988) completed with `success` for all six jobs: backend (14 successful steps), frontend (12), Compose config (6), Compose E2E/recovery (20 successful and 4 conditionally skipped), web container (12), and operations scripts (5). No job had a failed step. Compose E2E covered synthetic intake/processing, reports/corrections, encrypted backup/restore, migration and graph rebuild in isolated CI services; it is not a hosted-provider test.
- The public Vercel home page returned HTTP 200. Its `/api/health/live` route returned HTTP 404, confirming the API rewrite has no working backend target yet. Hostless has not been provisioned, `API_ORIGIN` has not been set in Vercel, no provider environment values were entered, and no Supabase schema query or migration was run. The Vercel result therefore verifies static hosting only.
- Final local checks immediately before the push: `pnpm install --frozen-lockfile` passed; `pnpm audit` reported no known vulnerabilities; `pnpm run test:redaction` passed 35/35; `pnpm run build` completed TypeScript and Vite; `git diff --check` passed. GitHub CI for the pushed commit also passed as detailed above.
- Exact next steps: (1) owner runs the Supabase SQL preflight in `FREE_DEPLOYMENT.md` and reports only whether the schema is fresh or which migration head is present (no connection string/keys); (2) owner signs in to Hostless and creates the app only if the dashboard confirms no card, no paid resource, and a $0 estimate; (3) enter the required environment values directly in Hostless's protected settings, deploy and verify API/worker health; (4) set Vercel `API_ORIGIN` to the assigned verified Hostless origin and redeploy; (5) run synthetic hosted end-to-end, privacy, security, deletion, backup, and restore checks; (6) review provider region/terms/security before any real personal evidence. Stop if the provider asks for billing or if database state is ambiguous. The core hosted workflows remain incomplete.

## 2026-11-13 07:03 IST — Verify the live Supabase schema preflight

- Re-read the current deployment state at pushed commit `49f8422`; the branch had been clean and synchronized before these documentation updates. The code-bearing deployment commit `d1797ff` and documentation follow-up `49f8422` both have successful six-job CI runs (`43300545988` and `43301638048`).
- In the authenticated Supabase dashboard, confirmed project `rsiacdp` is healthy in Tokyo (`ap-northeast-1`), on the Free/Nano compute tier. The dashboard displayed “No migrations” and “No backups.”
- Ran only read-only SQL in the project SQL Editor: `select to_regclass('public.alembic_version')::text as alembic_version_table;` returned `NULL`; `select tablename from pg_catalog.pg_tables where schemaname = 'public' order by tablename;` returned zero rows. This confirms no app tables in the `public` schema at check time. No migration, table change, credential read, or storage change occurred. Recheck before the first API startup.
- The local Docker CLI is installed (`29.9.2`) but the Docker Desktop Linux Engine pipe is unavailable, so no local Compose run was possible. Current hosted CI already passed the isolated Compose E2E/recovery job; this is not proof of a hosted Supabase migration or Hostless service.
- Updated `FREE_DEPLOYMENT.md`, `REQUIREMENTS_TRACEABILITY.md`, and `ENGINEERING_WALKTHROUGH.md` to replace stale “preflight unverified” and “current changes unpushed” statements with this evidence. Hostless still has no signed-in account session in Chrome, no service, and no `API_ORIGIN`; Vercel `/api/health/live` remains HTTP 404.
- Exact next steps: (1) owner signs in directly to Hostless, verifies account capacity is no-card and $0, and leaves the dashboard open; (2) owner explicitly authorizes me to place `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and generated upload/JWT/bootstrap secrets into the protected Hostless environment, or enters them directly; (3) create/deploy the Hostless API and worker after confirming runtime/migration settings, then verify `/health/ready` and worker operation; (4) set Vercel `API_ORIGIN` to the verified service origin and verify the same-origin API route; (5) run the synthetic hosted workflow and privacy/security/backup checks; (6) review provider region, terms, data processing and backups before any real case evidence. No secret values should be sent in chat.

## 2026-11-13 07:25 IST — Complete isolated local investigator UI review

- Re-read `BUILD_PLAN.md`, this status file, and the current Git state. The pushed code is still at `300260c`; the owner authorized changing the backend to a no-card host but has not named the provider. Updated deployment guidance to mark Hostless as a candidate only; do not provision it until the owner names the host.
- The pre-existing ignored `backend/.pydeps` bundle lacked `cryptography`, so the first local API start failed before application initialization. Created a disposable Python 3.12 virtualenv under `%TEMP%` and installed the exact pinned `backend/requirements.txt`; tracked project files were not changed for dependency setup.
- Started the API on `127.0.0.1:8000` with a unique temporary SQLite database, local private upload directory, synthetic-only bootstrap/JWT values, `APP_ENV=testing`, RDAP disabled, no Supabase credentials, and no Neo4j. Alembic applied through `e7a91c0d4b62`; `/health/ready` returned `ready`. Existing Vite on `localhost:5173` returned HTTP 200 and rendered the application title. Stopped the API after browser review.
- Created one fabricated investigator and two consented, fabricated message cases. The local worker completed both, persisted entity source spans and local-corpus `no_result` evidence with retrieval timestamps, and kept both system assessments at `Insufficient evidence`. The UI explicitly said missing evidence was not proof of fraud or legitimacy.
- Recomputed the shared synthetic identifier group: 55/100 `proposed` under `campaign-signals-v3-threshold-40`. The graph displayed masked contact identifiers. Selecting type `email` plus review status `proposed` reduced the graph to two case nodes and one relationship; resetting filters restored the broader view. Date and evidence-source filters were not manually checked.
- Submitted a synthetic public correction request, verified its status using the one-time token, and applied an investigator correction to the synthetic email. The request became resolved, findings recalculated, and the remaining domain-only link became 15/100 `low_signal`. Downloaded the Markdown report; it included limitations and contained neither the corrected raw email nor the one-time token. Browser console errors: 0.
- Checks this stage: temporary API migration/startup and health check passed; local web root returned HTTP 200; intake, inline processing, local evidence result storage, campaign linking, graph filtering, correction/status, correction application, and report download were reviewed in the browser. No full automated suite was rerun in this documentation/UI stage. This SQLite run does not prove hosted PostgreSQL/Supabase or provider behavior.
- CI follow-up: pushed documentation commit `03c230a` completed GitHub Actions run [43349274823](https://github.com/gaurvit06/RSIACDP/actions/runs/43349274823) successfully across all six jobs. The unchanged application code at `300260c` also passed run [43346448189](https://github.com/gaurvit06/RSIACDP/actions/runs/43346448189).
- Temporary resources: the API is stopped. A cleanup command for three exact review directories under `%TEMP%` and deletion of the generated report in Downloads were rejected by the execution policy, so artifacts may remain. Temporary folder names are `rsiacdp-local-review-9a32156eb99943908fbeba837d7aeb7e`, `rsiacdp-review-env-3dabd22d6d4f47ebbb7a63a966c68047`, and `rsiacdp-local-review-83b59b2ffb954ac98bd46eb0bf246824`; the downloaded synthetic report is `C:\Users\gaurv\Downloads\RC-883E88DB-report.md`. The venv and SQLite folder contain synthetic test material only.
- Files changed this stage: `BUILD_PLAN.md`, `BUILD_STATUS.md`, `ENGINEERING_WALKTHROUGH.md`, `FREE_DEPLOYMENT.md`, `README.md`, and `REQUIREMENTS_TRACEABILITY.md`. No application source, database, account, cloud resource, or secret was changed.
- Exact next steps, in order: (1) owner names the no-card backend host; until then, keep `hostless.yaml` as a candidate and do not create services or set `API_ORIGIN`; (2) inspect that provider's current no-card/$0 offer, region, terms, and capabilities; (3) owner signs in directly and enters any required secrets into its protected settings, never chat; (4) re-run Supabase's read-only schema preflight before the first migration; (5) configure the chosen host and Vercel origin, then run the hosted synthetic acceptance checklist in `FREE_DEPLOYMENT.md`; (6) complete provider security, backup/restore, retention, correction/deletion, and data-processing review; (7) run authorized time-separated evaluation data and comparisons, or keep performance evaluation pending. Resume by reading this entry and checking `git status --short --branch`.
