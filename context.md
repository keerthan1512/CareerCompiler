# CareerCompiler — Living Technical Context

> This document is the single source of truth for anyone (human or AI) picking up this codebase.
> It is updated at the end of every build phase to reflect the current state of the project.

---

## Project Overview

CareerCompiler is an AI-powered resume engineering platform. Users upload one master LaTeX resume; the platform generates factually grounded, job-specific variants by analyzing job descriptions, matching requirements to evidence, proposing changes, and compiling validated PDFs.

**Core principle**: The original `.tex` file is immutable. Every change is evidence-grounded, user-approved, and auditable.

---

## Current Phase: Phase 1 — Resume Foundation

**Completed:** 2026-09-15  
**Status:** 🟢 Active

### What is built in Phase 1

| Component | Status | Notes |
|---|---|---|
| Monorepo structure | ✅ Done | pnpm workspaces, apps/api, apps/web, services/resume-parser, packages/* |
| Docker Compose (Postgres + Redis) | ✅ Done | pgvector/pgvector:pg16 + redis:7-alpine |
| FastAPI backend scaffolded | ✅ Done | Async SQLAlchemy 2, Alembic migrations, Celery + Redis |
| Postgres schema (Phase 1 tables) | ✅ Done | users, master_resumes, canonical_profiles, audit_logs, parse_jobs |
| LaTeX parser service | ✅ Done | TexSoup + pylatexenc, extracts sections/bullets/skills/contact with line refs |
| Canonical profile builder | ✅ Done | Converts raw AST → structured JSON with source references |
| Evidence extractor | ✅ Done | Extracts skills, experience bullets, claims |
| File storage abstraction | ✅ Done | Local filesystem (./uploads/), S3-ready interface |
| API endpoints (Phase 1) | ✅ Done | POST /master-resumes, GET /master-resumes/{id}, POST /reparse, GET /jobs/{id} |
| Dev auth bypass | ✅ Done | X-Dev-User-Id header; Firebase Auth wired in Phase 7 |
| LLM client (Groq) | ✅ Done | langchain-groq wrapper, connectivity-tested, not called in parser yet |
| Shared JSON schemas | ✅ Done | canonical_profile, job_description, match_result, tailoring_plan, evaluation_result |
| Next.js placeholder | ✅ Done | Landing page only; full UI in Phase 7 |
| README + context.md | ✅ Done | Setup instructions, architecture, environment variables |

### What is NOT built yet (future phases)

- Job description ingestion and analysis (Phase 2)
- Requirement-to-evidence matching (Phase 3)
- Tailoring plan + content optimizer agents (Phase 3)
- Fact verification agent (Phase 3)
- LaTeX rendering + sandboxed compilation (Phase 4)
- ATS evaluation engine (Phase 5)
- Benchmark datasets and regression suite (Phase 6)
- Full Next.js UI — all 10 modules (Phase 7)
- Firebase Auth (Phase 7)
- S3 file storage (Phase 7+)

---

## Architecture Decisions (ADRs)

### ADR-001: Solo MVP → pragmatic simplifications
- Auth is a dev bypass header (`X-Dev-User-Id`) in Phase 1. Firebase Auth added in Phase 7.
- LaTeX compilation is local `tectonic` (no Docker sandbox). Sandbox added post-MVP.
- File storage is local filesystem. S3 swap is a config change only (abstracted).
- Celery/Redis are scaffolded but parsing runs synchronously in Phase 1. Async dispatch in Phase 3+.

### ADR-002: Python monorepo with pip editable installs
- `services/resume-parser` and `packages/llm-client` are installed as editable packages into `apps/api/.venv`.
- This avoids subprocess IPC overhead and keeps imports clean.

### ADR-003: Async SQLAlchemy everywhere
- All DB access uses `async with session` pattern.
- Alembic runs synchronously (standard pattern) but the engine is configured to run async migrations.

### ADR-004: LLM never touches Phase 1 parsing
- The LaTeX parser uses only TexSoup + pylatexenc + regex in Phase 1.
- LangChain + Groq are imported and tested for connectivity but not called in the parse pipeline.
- LLM fallback for ambiguous macros starts in Phase 3.

### ADR-005: Embeddings model is local sentence-transformers
- `all-MiniLM-L6-v2` runs locally via HuggingFace sentence-transformers.
- Vectors stored in Postgres as JSONB in Phase 1 (pgvector columns added Phase 3).
- Groq does not provide an embeddings API.

### ADR-006: Two-mode tailoring UX
- **Quick Mode**: AI delivers complete tailored resume, user edits directly in Monaco Editor.
- **Review Mode**: Per-change approval panel with rationale + evidence link (BRD FR-013).
- Both modes preserved in Phase 7 UX.

---

## Data Flow (Phase 1)

```
User → POST /api/v1/master-resumes (multipart: .tex + assets)
  → FileStorage.save() → uploads/{user_id}/{resume_id}/main.tex
  → MasterResume record created (DB)
  → parse_resume() called synchronously (Phase 1) or Celery task (Phase 3+)
    → LaTeXParser.parse(tex_content, filename)
      → TexSoup structural parse
      → SectionDetector.detect(nodes)
      → CanonicalProfileBuilder.build(sections, raw_lines)
      → EvidenceExtractor.extract(canonical_profile)
    → CanonicalProfile record saved (DB, status=complete)
  → ParseJob record updated (status=complete)
  → Response: { resume_id, profile_id, status }

User → GET /api/v1/master-resumes/{id}
  → Returns MasterResume + CanonicalProfile JSON
```

---

## Key File Locations

| File | Purpose |
|---|---|
| `apps/api/src/main.py` | FastAPI app entry point, router registration |
| `apps/api/src/config.py` | All settings (pydantic-settings, reads .env) |
| `apps/api/src/database.py` | Async SQLAlchemy engine + session factory |
| `apps/api/src/models/` | SQLAlchemy ORM models |
| `apps/api/src/routers/master_resumes.py` | Core Phase 1 endpoints |
| `apps/api/alembic/versions/` | Database migration scripts |
| `services/resume-parser/src/latex_ast_parser/parser.py` | Core LaTeX → AST parser |
| `services/resume-parser/src/canonical_profile_builder/builder.py` | AST → canonical JSON |
| `services/resume-parser/src/evidence_extractor/extractor.py` | Skill/claim extraction |
| `packages/llm-client/src/groq_client.py` | LangChain + Groq wrapper |
| `packages/schemas/canonical_profile.schema.json` | JSON schema for the profile |
| `docker-compose.yml` | Local Postgres + Redis |
| `.env.example` | All environment variables documented |

---

## Canonical Profile JSON Structure

```json
{
  "resume_id": "uuid",
  "parser_version": "1.0.0",
  "contact": {
    "name": { "value": "Jane Doe", "source_ref": { "file": "main.tex", "line_start": 5, "line_end": 5 } },
    "email": { "value": "jane@example.com", "source_ref": { ... } },
    "phone": { "value": "+1-555-0123", "source_ref": { ... } },
    "linkedin": { "value": "linkedin.com/in/jane", "source_ref": { ... } },
    "github": { "value": "github.com/jane", "source_ref": { ... } }
  },
  "sections": [
    {
      "id": "uuid",
      "name": "Experience",
      "normalized_name": "experience",
      "source_ref": { "file": "main.tex", "line_start": 42, "line_end": 42 },
      "entries": [
        {
          "id": "uuid",
          "title": "Software Engineer",
          "organization": "Acme Corp",
          "location": "SF, CA",
          "dates": { "start": "Jan 2022", "end": "Present", "raw": "Jan 2022 – Present" },
          "source_ref": { "file": "main.tex", "line_start": 44, "line_end": 50 },
          "bullets": [
            {
              "id": "uuid",
              "text": "Built distributed system using Python and Kafka",
              "source_ref": { "file": "main.tex", "line_start": 45, "line_end": 45 }
            }
          ]
        }
      ]
    }
  ],
  "skills": [
    {
      "id": "uuid",
      "category": "Programming Languages",
      "items": [
        { "name": "Python", "normalized": "Python", "source_ref": { ... } }
      ],
      "source_ref": { "file": "main.tex", "line_start": 90, "line_end": 92 }
    }
  ],
  "template": {
    "document_class": "moderncv",
    "packages": ["hyperref", "geometry"],
    "detected_format": "moderncv"
  },
  "metadata": {
    "parsed_at": "2026-09-15T18:00:00Z",
    "total_bullets": 15,
    "total_sections": 5,
    "total_skills": 20,
    "source_file": "main.tex"
  }
}
```

---

## Environment Quick Reference

| Variable | Phase 1 Required | Default |
|---|---|---|
| `DATABASE_URL` | ✅ | postgresql+asyncpg://ccuser:ccpassword@localhost:5432/careercompiler |
| `REDIS_URL` | ✅ | redis://localhost:6379/0 |
| `GROQ_API_KEY` | ✅ (connectivity test) | — |
| `UPLOAD_DIR` | ✅ | ./uploads |
| `DEV_AUTH_BYPASS` | ✅ | true |
| `FIREBASE_*` | ❌ (Phase 7) | — |

---

## Phase Roadmap

| Phase | Description | Key FRs |
|---|---|---|
| 1 ✅ | Resume Foundation — parser, canonical profile, FastAPI | FR-001–005 |
| 2 | Job Intelligence — JD ingestion, extraction, skill normalization | FR-006–008 |
| 3 | Matching + Tailoring — evidence graph, tailoring plan, approvals | FR-009–013, FR-022 |
| 4 | Document Engineering — rendering, sandboxed compilation | FR-014–016 |
| 5 | ATS Engine — simulation, deterministic scoring, risk detection | FR-017–021 |
| 6 | Benchmarking — datasets, regression suite | §19 |
| 7 | Production UX — all 10 modules, Firebase Auth, hardening | §16, §17, §20 |

---

*Last updated: Phase 1 build — 2026-09-15*
