# Build plan

## Current decision architecture · 22 November 2026

The owner requested a trained model for the primary posting decision. The worker now persists a versioned logistic-regression text prediction for each processed case. A separate TF-IDF verifier automatically corroborates published vacancies on configured employer boards. Other source findings, deterministic identifier matching, campaign links and human dispositions retain their own evidence and review requirements. A model score alone cannot promote a claim to an authoritative confirmation.

The repository was empty at the start of implementation. The application will be built as a deployable web service with PostgreSQL as its system of record and Neo4j as a rebuildable graph projection.

## Stages

1. **Runnable foundation:** Docker Compose, FastAPI service, database models, authentication, case intake, upload validation, local extraction, and React investigator screens.
2. **Traceable investigations:** durable processing queue, OCR/text extraction, evidence source adapters, retrieval outcomes, evidence timeline, entity review, and auditable investigator actions.
3. **Campaign intelligence:** deterministic identifier resolution, versioned campaign rules, Neo4j projection/rebuild, campaign review UI.
4. **Operational readiness:** report export, correction/appeal and retention flows, deployment/security hardening, evaluation scripts and documentation.

Every stage must retain a runnable local workflow without requiring an LLM or paid external service. Work is complete only when the completion criteria in the user-provided specification are implemented and verified; unfinished items must remain explicit. Do not call the project release-ready until PostgreSQL/Neo4j integration, security and privacy workflows, deployment checks, and end-to-end verification are complete.

## Current deployment decision

As of 22 November 2026, the owner has replaced the hosting objective with reliable localhost operation. Hosted deployment is out of scope. Preserve existing local accounts and cases, keep local secrets outside Git and temporary folders, provide repeatable startup/shutdown, and verify the full investigation workflows against isolated synthetic data. Historical cloud notes below are no longer blocking requirements for this goal.

The owner selected Vercel for the static frontend and Supabase for PostgreSQL/private evidence storage, authorized replacing Render with a no-card backend, and selected Hostless on 13 November 2026. No Hostless account configuration, backend service, or API origin is set up yet. Verify the account-specific no-card entitlement and $0 estimate before creating resources; stop if a payment method or paid capacity is required. Neo4j remains an optional rebuildable projection; the graph API can derive its view from PostgreSQL when it is not hosted. See `FREE_DEPLOYMENT.md` for limits, privacy boundary, migration preflight, and hosted checks.
