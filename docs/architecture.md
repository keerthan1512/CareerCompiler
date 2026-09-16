# Architecture Document

> Status: Phase 1 stub — full document in progress

## System Architecture

See [README.md](../README.md) for the current architecture overview and [context.md](../context.md) for the living technical context.

## Layers

| Layer | Package | Status |
|---|---|---|
| Presentation | `apps/web` | Phase 7 |
| API Gateway | `apps/api` | ✅ Phase 1 |
| Resume Intelligence | `services/resume-parser` | ✅ Phase 1 |
| Job Intelligence | `services/job-intelligence` | Phase 2 |
| Matching Engine | `services/matching-engine` | Phase 3 |
| Tailoring Orchestrator | `services/tailoring-orchestrator` | Phase 3 |
| Document Engineering | `services/document-engineering` | Phase 4 |
| ATS Evaluation | `services/ats-evaluation` | Phase 5 |

## Message Flow

All long-running operations are dispatched via Celery + Redis and return `202 Accepted + job_id`.
Clients poll `GET /api/v1/jobs/{job_id}` or subscribe via WebSocket (Phase 7).
