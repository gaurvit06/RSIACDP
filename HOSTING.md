# Running the hosted demonstration

Open [Casework](https://rsiacdp-frontend.vercel.app/) to try the public fictional offer. Choose **Create account** to get a personal case workspace, or **Sign in** to return to an existing one. Personal accounts can submit offers and read and export their own results. The project owner supplies an investigator login separately. Once signed in, the [vacancy walkthrough](https://rsiacdp-frontend.vercel.app/#vacancy-demo) takes you from a fictional job offer to its source and graph. The original presentation computer has its own database and case history.

## Deployment configuration

| Service | Configuration |
| --- | --- |
| Vercel | GitHub repository `gaurvit06/RSIACDP`, branch `codex/initial-platform`, project root `frontend`, Vite preset, output `dist`. Leave `VITE_API_URL` unset. The checked-in [routing configuration](frontend/vercel.json) sends `/api/*` to Hostless so login and private requests use the same browser origin. |
| Hostless | App `casework-api`, same repository and branch, Dockerfile build from `/backend`. Run the image's default command. One instance with 0.5 vCPU and 1 GB RAM runs FastAPI and its inline worker. The HTTP readiness path is `/health/ready`. |
| Supabase | The dedicated project holds PostgreSQL and the private Storage bucket `private-evidence`. The runtime login uses the session pooler with TLS and creates application tables in `casework_app`. Its database search path points at that schema. Alembic applies migrations at API startup. |
| Graph | The hosted API builds the masked graph from PostgreSQL. The [local installation](LOCALHOST.md) also runs Neo4j. |

In Hostless's private environment set `APP_ENV=production`, `WEB_ORIGIN=https://rsiacdp-frontend.vercel.app`, `RUN_INLINE_WORKER=true`, `ALLOW_ANALYST_SELF_REGISTRATION=false`, `UPLOAD_STORAGE_BACKEND=supabase`, `SUPABASE_URL`, `SUPABASE_STORAGE_BUCKET=private-evidence` and `DATA_RETENTION_DAYS=30`. Use the session-pooler URL for `DATABASE_URL` with the SQLAlchemy `postgresql+psycopg` driver and `sslmode=require`. Set `SUPABASE_SERVICE_ROLE_KEY` to a dedicated backend key. Keep it out of Vercel and browser code. Configure `JWT_SECRET`, `UPLOAD_ENCRYPTION_KEY`, `INITIAL_INVESTIGATOR_CODE` and `INITIAL_REVIEWER_CODE` with independent private values. The key format and validation rules are in [backend configuration](backend/app/config.py). Preserve the upload encryption key to read existing files after recovery.

## Check a deployment

1. Check the [backend readiness endpoint](https://casework-api.hostless.app/health/ready). Then open the [public intake policy through Vercel](https://rsiacdp-frontend.vercel.app/api/policy). Both should return JSON. A working landing page alone checks only the static frontend.
2. Sign in. Open a synthetic case, check its evidence timeline and download the masked report. Submit one of the [fictional inputs](demo/) with consent to exercise the worker. A scanned PDF also checks protected storage and OCR.
3. For an update, select the intended Git revision in Hostless. Wait for the readiness check to pass and repeat step 1 through **both** hosts. Route changes also need a Vercel production deployment.
4. If the workspace is unavailable, check the Hostless deployment and runtime logs and the Supabase project status. Resume a paused database project from its dashboard. During the first release, the backend URL may return 404 until Hostless starts the instance and its database migrations finish. Recheck readiness and private storage access before retrying writes.

The hosted instance is sized for a classroom demonstration. Its worker enforces the configured retention period when running. To keep a demonstration repeatable after cases expire, use the committed fictional inputs. A hosted recovery requires both the private database schema and encrypted bucket objects from the same backup, along with the original upload encryption key. Validate recovery in a separate environment before relying on it.
