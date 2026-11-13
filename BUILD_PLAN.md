# Build plan

The repository was empty at the start of implementation. The application will be built as a deployable web service with PostgreSQL as its system of record and Neo4j as a rebuildable graph projection.

## Stages

1. **Runnable foundation:** Docker Compose, FastAPI service, database models, authentication, case intake, upload validation, local extraction, and React investigator screens.
2. **Traceable investigations:** durable processing queue, OCR/text extraction, evidence source adapters, retrieval outcomes, evidence timeline, entity review, and auditable investigator actions.
3. **Campaign intelligence:** deterministic identifier resolution, versioned campaign rules, Neo4j projection/rebuild, campaign review UI.
4. **Operational readiness:** report export, correction/appeal and retention flows, deployment/security hardening, evaluation scripts and documentation.

Every stage must retain a runnable local workflow without requiring an LLM or paid external service. Work is complete only when the completion criteria in the user-provided specification are implemented and verified; unfinished items must remain explicit. Do not call the project release-ready until PostgreSQL/Neo4j integration, security and privacy workflows, deployment checks, and end-to-end verification are complete.

## Current deployment decision

The owner selected Vercel for the static frontend and Supabase for PostgreSQL/private evidence storage, and authorized changing the backend from Render to a no-card host after Render required card verification. The owner has not yet named that backend host. `hostless.yaml` and the Hostless-specific setup guide are a prepared candidate only; do not provision Hostless or set Vercel `API_ORIGIN` to it until the owner selects it. No backend service or API origin is configured. Neo4j remains an optional rebuildable projection; the graph API can derive its view from PostgreSQL when it is not hosted. See `FREE_DEPLOYMENT.md` for the candidate's limits, privacy boundary, migration preflight, and hosted checks.
