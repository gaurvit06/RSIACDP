# Casework · Recruitment Scam Investigation and Campaign Intelligence Platform

Casework helps an investigator answer three questions about a job offer. **What does the message say? What can a source verify? Where has the same identifier appeared before?** A student can follow one fictional offer from submission to a source-backed finding, a graph connection and a downloadable report.

**[Open Casework on the web](https://rsiacdp-frontend.vercel.app/).** Choose **Explore a sample case** for the public example. Choose **Create account** to submit and track your own offers. For the shared classroom cases and investigator tools, use the investigator login supplied by the project owner. The [hosting guide](HOSTING.md) describes the deployment and how to check its health.

## Run it locally

Install Git, Docker Desktop with Linux containers (Compose 2.24.4 or later), and PowerShell 7.1 or later. Start Docker Desktop. The first build needs internet access to download images and dependencies. No cloud account, LLM key or training dataset is required.

**Evaluation materials:** [editable presentation](evaluation-materials/Casework.pptx) · [two-minute script, ten-minute route and viva questions](evaluation-materials/VIVA.md). The reproducible application revision is [fcb6b6c](https://github.com/gaurvit06/RSIACDP/commit/fcb6b6c1e467a960cf5ff18dadbcfaf3e8d736fa). The branch also contains the subsequent documentation and slides.

On a **new computer**, open PowerShell and run:

```powershell
git clone --branch codex/initial-platform https://github.com/gaurvit06/RSIACDP.git
cd RSIACDP
pwsh -File scripts/local.ps1 -Action Init
pwsh -File scripts/local.ps1 -Action Rebuild
pwsh -File scripts/local.ps1 -Action CreateInvestigator
```

Choose your own email and password when prompted. Open [Casework on localhost](http://localhost:5175/) and choose **Sign in**. On the **existing demonstration computer**, start Docker Desktop, run `pwsh -File scripts/local.ps1 -Action Start`, and sign in with the existing account. The saved cases are in that installation’s PostgreSQL volume. A fresh clone includes the fictional demo materials and starts with an empty private workspace.

### Environment and dependencies

The verified Windows toolchain used PowerShell 7.6.9, Git 2.53.0.windows.1, Docker Engine 29.9.2 and Docker Compose 5.6.1. The containers supply the application runtimes. Reserve loopback ports 5175 for the website and 8001 for the API. To rebuild precisely the application revision above, run `git checkout --detach fcb6b6c1e467a960cf5ff18dadbcfaf3e8d736fa` before Init.

| Component | Versions and source of truth |
| --- | --- |
| Browser application | Node 22.23.5 and pnpm 11.25.0 in the tested build. React and React DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.8, React plugin 6.3.0 and lucide-react 0.468.0. [Manifest](frontend/package.json) and [frozen dependency lock](frontend/pnpm-lock.yaml). |
| API and worker | Python 3.12.16, FastAPI 0.142.3, SQLAlchemy 2.0.39, Alembic 1.15.2 and psycopg 3.2.6. All [direct requirements](backend/requirements.txt) and [resolved Python packages](backend/runtime-constraints.txt) are pinned. |
| Parsing and OCR | PyMuPDF 1.25.4, pytesseract 0.3.13, Pillow 13.0.0 and the Tesseract 5.5.0 system binary in the tested image. The bundled posting model runs without a training job. |
| Storage and serving | Local PostgreSQL 16.15, Neo4j Community 2026.10.2, Python Neo4j driver 5.28.1 and Nginx 1.30.7. The Dockerfiles apply OS security updates during the build. Future builds can therefore differ at the OS or runtime-patch level. |

### Configuration, database and demo data

`Init` generates credentials in the ignored `.local/compose.env` and records the installation identity in `.local/state.json`. Use the same checkout for subsequent runs. At startup Alembic migrates PostgreSQL, Docker attaches the persistent database, graph and upload volumes, and the worker starts processing queued cases. The first investigator and optional reviewer are provisioned through the launcher. Public **Create account** creates a personal account with access to its own cases.

| Settings | Purpose |
| --- | --- |
| `POSTGRES_PASSWORD`, `NEO4J_PASSWORD` | Generated locally. Compose supplies the database names, users and URLs. Hosted PostgreSQL uses `DATABASE_URL`. |
| `JWT_SECRET`, `UPLOAD_ENCRYPTION_KEY`, `BACKUP_ENCRYPTION_KEY` | Generated secrets for sessions, stored uploads and backups. Preserve the encryption keys for recovery. |
| `INITIAL_INVESTIGATOR_CODE`, `INITIAL_REVIEWER_CODE` | Separate generated staff setup codes consumed by the provisioning workflow. |
| `WEB_ORIGIN`, `VITE_API_URL`, `WEB_PROXY_IP`, `FORWARDED_ALLOW_IPS`, `APP_NETWORK_SUBNET` | Browser origin, API routing and trusted proxy configuration. The local launcher supplies same-origin defaults. |
| `DATA_RETENTION_DAYS`, `MAX_UPLOAD_BYTES`, `CAMPAIGN_LINK_THRESHOLD` | Local defaults are 180 days, 10 MiB and 40 out of 100 respectively. |
| `OFFICIAL_JOB_BOARDS`, `RDAP_ENABLED` | Local defaults allow the configured Canonical and Figma boards and disable RDAP. Set `OFFICIAL_JOB_BOARDS=` for an offline demonstration after building. |

See the [configuration example](.env.example), [runtime settings](backend/app/config.py) and [hosted configuration](HOSTING.md) for other options. To populate a new installation, use the vacancy walkthrough below for the first case and corpus record. To demonstrate OCR, upload [the fictional scanned offer](demo/offer-scanned.pdf) as a separate case. A CSV import is unnecessary.

### Run and verify

Run these from the repository root in PowerShell. `Stop` stops services while preserving the case volumes.

```powershell
pwsh -File scripts/local.ps1 -Action Status
Invoke-RestMethod http://127.0.0.1:8001/health/ready
Invoke-RestMethod http://127.0.0.1:5175/api/policy
pwsh -File scripts/test-compose-config.ps1
docker run --rm --mount "type=bind,src=$((Resolve-Path frontend).Path),dst=/src,readonly" -w /src node:22-alpine sh -c 'node --experimental-strip-types --test tests/*.test.ts'
pwsh -File scripts/local.ps1 -Action Stop
pwsh -File scripts/local.ps1 -Action Start
```

For the **end-to-end acceptance test**, use a separate disposable installation with an empty database. On a fresh computer run Init and Rebuild, then run the following **before** CreateInvestigator. The test provisions its own first investigator, submits cases, checks the worker and graph, downloads a masked report and applies a correction.

```powershell
pwsh -File scripts/test-compose-e2e.ps1 -BaseUrl http://127.0.0.1:8001 -EnvironmentFile .local/compose.env -AllowSyntheticWrites
```

For the full backend suite, the [CI backend job](.github/workflows/ci.yml) gives the disposable PostgreSQL service, environment variables and setup commands. From `backend/` its commands are `python -m pip install -r requirements.txt`, `python -m alembic upgrade head` against the disposable PostgreSQL database, then `python run_ci_tests.py` with the test environment. The same workflow exercises PDF upload, Neo4j recovery and encrypted backup/restore. For time-separated fixtures and scoring commands, see the [evaluation guide](backend/evaluation/README.md).

## A five-minute demonstration

| Step | What to do | What to look for |
| --- | --- | --- |
| 1. Read the offer | After signing in, open the [vacancy walkthrough](http://localhost:5175/#vacancy-demo). Compare the JL-204 email with the linked fictional employer register. | Both name the same vacancy contact. The example works offline once the application is built. |
| 2. Follow the evidence | Consent and select **Create training case**. Once processing finishes, choose **Confirm email and mark source relevant**, then **Show case connections**. | The corpus supplies a source, excerpt and retrieval time. The graph shows which evidence checked which identifier in this case. |
| 3. Find a possible campaign | Open **Cases → New case** twice. Paste the [sample message](demo/offer-message.txt) as a message and the [sample email](demo/offer-email.eml) as an email. Use separate titles, give consent and wait for completion. Confirm the shared email in both cases, choose **Recompute links** in a case and open **Campaigns**. | Two different submissions reuse the same mailbox. Inspect the link reason and the rule that produced it. |
| 4. Take the result away | Open one case, inspect the fee wording and its source location, then download the Markdown report. | The report brings together the finding, supporting records and review trail with personal identifiers masked by default. |

![Two fictional cases connected by an identifier in the Campaigns view](demo/walkthrough/linked-cases.jpg)

For the existing demonstration cases, OCR with a screenshot or scanned PDF, and the full feature checklist, see the [presenter’s walkthrough](FEATURE_WALKTHROUGH.md).

## How to read the results

| Output | Question it answers | How to interpret it |
| --- | --- | --- |
| **Model decision** | Does the posting resemble higher-risk examples? | The bundled Hiring Market logistic regression uses 5,000 TF-IDF features and ten numeric inputs. Scores from 0.35 receive **Higher fraud risk**. Fewer than three distinct recognized words produce **More posting text needed**. |
| **Evidence finding** | What supports this specific claim? | A payment request can be traced to the submitted words. A vacancy publication can be corroborated against a configured employer board. **Insufficient evidence** means the available checks could not establish the claim. |
| **Campaign link** | Do separate cases share identifiers? | An exact mailbox match can create a lead. Open the edge to inspect the reason. Identifying a sender or establishing wrongdoing requires separate evidence. |
| **Human disposition** | What did the investigator conclude? | The application keeps the investigator’s rationale, supporting evidence and review history separately. |

A copied advert can match a real vacancy. Confirmation of its publication leaves the identity of the sender and the terms of an individual offer unresolved. Independent accuracy on Indian recruitment offers remains unmeasured. The posting model is adapted from the [Hiring Market Analysis project](https://github.com/Sumersingpatil2694/Fake-Job-Detection-And-Hiring-Market-Analysis). Casework adds mixed-format intake, claim-level provenance, deterministic case linking and investigator review.

## Where to look in the repository

| Start here | Contents |
| --- | --- |
| [Frontend](frontend/src/) | React and TypeScript investigator workspace, public sample and vacancy walkthrough |
| [Backend](backend/app/) and [migrations](backend/migrations/) | FastAPI, the processing worker, posting model, evidence rules, PostgreSQL records and rebuildable Neo4j graph |
| [Engineering walkthrough](ENGINEERING_WALKTHROUGH.md) | Step-by-step implementation, design decisions and pointers to the owning code |
| [Local operations](LOCALHOST.md) | Startup, accounts, ports, troubleshooting and encrypted backup and recovery |
| [Demo files](demo/) | Fictional messages, screenshot, searchable and scanned PDFs, and the vacancy register |
| [Evaluation](backend/evaluation/README.md) | Synthetic fixtures, time-separated evaluation, baselines, scoring and limitations |
| [Verification](BUILD_STATUS.md) and [CI](.github/workflows/ci.yml) | Submission checks and automated tests for the application and recovery workflows |
| [Source access](SOURCE_ACCESS_REVIEW.md) | Data-source provenance and access limits, including I4C |
