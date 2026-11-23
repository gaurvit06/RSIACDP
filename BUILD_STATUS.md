# Submission verification

## 23 November 2026 · 21:14 IST · Web image update

The first hosted CI run flagged six fixed advisories against the Nginx 1.30.6 package. The frontend Dockerfile now uses the published 1.30.7 Alpine image. The security gate still fails on fixable high or critical findings. For the check results on the submitted revision, open the [CI history](https://github.com/gaurvit06/RSIACDP/actions/workflows/ci.yml).

## 23 November 2026 · 21:09 IST

**Scope.** The submitted version runs on localhost. The public sample, private investigation workspace, bundled prediction model, fictional demonstration inputs, evaluation scripts, historical benchmark and automated tests are included. Earlier cloud manifests and the superseded classifier and comparison launcher were removed.

**Handoff changes.** The README now takes a reviewer from a fresh checkout to the first case. LOCALHOST.md covers account provisioning and recovery. FEATURE_WALKTHROUGH.md has separate instructions for the original presentation computer and a new installation. ENGINEERING_WALKTHROUGH.md maps each processing stage to its source code. The local launcher generates private configuration for a fresh install and provisions the two privileged roles through the registration API.

| Check | Result |
| --- | --- |
| Clean Windows checkout and local configuration | Initialized a fresh installation, repeated Init to check reuse, and built all five services. A Windows checkout initially broke the Linux entrypoints. Pinning shell scripts to LF fixed the failure. All five services became healthy in the isolated stack. |
| Local Compose contracts | `pwsh -File scripts/test-compose-config.ps1` passed, including required secrets, private build contexts, database settings, proxy trust and upload limits. |
| Frontend | Production container build passed with the committed lockfile. `node --experimental-strip-types --test frontend/tests/*.test.ts` passed all 40 tests. |
| Backend | `python run_ci_tests.py` inside the application image passed all 268 tests (248 unit/handler, 17 API, 1 inline-worker and 2 proxy tests). Both concurrency checks ran against a dedicated migrated PostgreSQL test database. |
| Intake through report | Ran `scripts/test-compose-e2e.ps1` with synthetic writes and a PDF on a disposable stack. Registration, processing, source spans, campaign linking, masked Neo4j data, report redaction, corrections and recalculation passed. |
| Presenter’s walkthrough | Used a browser to sign in with a newly provisioned reviewer, create the fictional JL-204 case, confirm the email, mark the register relevant, trace the mailbox in the graph and reopen the persisted case after reload. |
| Original presentation workspace | Compared the count and a digest of the sorted case references before and after cleanup. All 13 case references matched. The website and API remained healthy. The tracked demo files, training source, synthetic generators and benchmark predictions were preserved. |

## Running the next session

1. On the original computer, run `pwsh -File scripts/local.ps1 -Action Start`. On a new machine, follow [first installation](LOCALHOST.md#first-installation).
2. Sign in and use the [presenter’s walkthrough](FEATURE_WALKTHROUGH.md). Local case references differ between installations.
3. For further research, collect appropriately authorized, independently labelled cases before estimating real-world accuracy. The synthetic exercises and historical posting CSV use different inputs and labels. The optional LLM/web-search baseline needs a configured provider. See [evaluation](backend/evaluation/README.md).

The encrypted backup/restore exercise and vulnerability scans have their own [CI checks](.github/workflows/ci.yml). They were outside this local submission verification run. The [earlier dated build log](https://github.com/gaurvit06/RSIACDP/blob/35df9a1258d9990f8877f8ef7892ad8e3d12ce3b/BUILD_STATUS.md) preserves the previous implementation and verification history.
