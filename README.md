# CareerCompiler

**AI-Powered, Evidence-Grounded Resume Engineering and ATS Evaluation Platform**

> One immutable master LaTeX resume is the single source of truth for every job-specific variant.

CareerCompiler lets professionals maintain one authoritative `.tex` resume and generate factually grounded, job-specific variants — preserving original design, preventing hallucinations, and evaluating ATS compatibility through transparent, measurable analysis.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [Development Phases](#development-phases)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)

---

## Architecture Overview

```
Presentation Layer (Next.js)
         │
    API Gateway (FastAPI)
         │
  ┌──────┴──────────────────────────────────────┐
  │ Resume     Job        Matching  Tailoring    │
  │ Intelligence Intelligence Engine Orchestrator│
  └──────────────────────┬──────────────────────┘
                         │
                 ATS Evaluation Engine
                         │
              Version & Storage Layer
              (Postgres + Local FS)
```

Cross-cutting: Celery + Redis (async jobs) · LangChain + LangGraph (agents) · Groq API (LLM) · sentence-transformers (embeddings)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 + TypeScript |
| Backend API | Python 3.12 + FastAPI |
| Agent Framework | LangChain + LangGraph |
| LLM Provider | Groq API (Llama 3.3 70B) |
| LaTeX Parser | TexSoup + pylatexenc |
| LaTeX Compiler | tectonic |
| Database | PostgreSQL 16 + pgvector |
| ORM / Migrations | SQLAlchemy 2 async + Alembic |
| Async Queue | Celery + Redis |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Auth | Firebase Auth (Phase 7; dev-stub in Phase 1) |
| File Storage | Local filesystem → S3 (later) |

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ and pnpm 9+
- Docker Desktop (for Postgres + Redis)
- `tectonic` LaTeX compiler ([install](https://tectonic-typesetting.github.io/))

### 1. Clone and install

```bash
git clone https://github.com/your-org/CareerCompiler.git
cd CareerCompiler

# Install JS dependencies
pnpm install

# Set up Python environments
cd apps/api && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd ../..

cd services/resume-parser && pip install -e ".[dev]"
cd ../..

cd packages/llm-client && pip install -e .
cd ../..
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY
```

### 3. Start infrastructure

```bash
# Start Postgres + Redis
./scripts/run_local_stack.sh

# Run Alembic migrations
cd apps/api
source .venv/bin/activate
alembic upgrade head
```

### 4. Start the API

```bash
cd apps/api
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API is live at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### 5. Start Celery worker (separate terminal)

```bash
cd apps/api
source .venv/bin/activate
celery -A src.celery_app worker --loglevel=info
```

### 6. Start the frontend

```bash
cd apps/web
pnpm dev
# → http://localhost:3000
```

### 7. Seed dev data

```bash
./scripts/seed_dev_data.sh
```

---

## Repository Structure

```
CareerCompiler/
├── apps/
│   ├── api/               # FastAPI backend
│   └── web/               # Next.js frontend
├── services/
│   └── resume-parser/     # LaTeX parsing & canonical profile builder
├── packages/
│   ├── llm-client/        # Groq/LangChain abstraction layer
│   └── schemas/           # Shared JSON schemas
├── infra/
│   └── init-db.sql        # Postgres init (pgvector extension)
├── docs/                  # Architecture, agent design, ATS methodology
├── benchmarks/            # Labeled datasets + eval scripts
├── scripts/               # Local dev helpers
├── docker-compose.yml     # Postgres + Redis local stack
├── .env.example           # All environment variables documented
└── context.md             # Living technical context document
```

---

## Development Phases

| Phase | Status | Focus |
|---|---|---|
| **Phase 1 — Resume Foundation** | 🟢 Active | Monorepo scaffold, LaTeX parser, canonical profile, FastAPI |
| **Phase 2 — Job Intelligence** | ⬜ Planned | JD ingestion, extraction, skill normalization |
| **Phase 3 — Evidence Matching** | ⬜ Planned | Matching engine, evidence graph, tailoring plan, approvals |
| **Phase 4 — Document Engineering** | ⬜ Planned | Templated rendering, compilation, validation |
| **Phase 5 — ATS Engine** | ⬜ Planned | Extraction simulation, deterministic scoring |
| **Phase 6 — Benchmarking** | ⬜ Planned | Benchmark datasets, regression suite |
| **Phase 7 — Production UX** | ⬜ Planned | Full Next.js UI (all 10 modules), Firebase Auth, hardening |

---

## API Reference

Full OpenAPI spec: `http://localhost:8000/docs`

### Phase 1 Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/master-resumes` | Upload `.tex` + assets |
| `GET` | `/api/v1/master-resumes/{id}` | Get resume + canonical profile |
| `POST` | `/api/v1/master-resumes/{id}/reparse` | Re-run parser |
| `GET` | `/api/v1/jobs/{job_id}` | Poll async job status |
| `GET` | `/api/v1/health` | Health check |

**Dev auth**: All Phase 1 endpoints use a bypass header:
```
X-Dev-User-Id: dev-user-00000000-0000-0000-0000-000000000001
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list with documentation.

**Minimum required for Phase 1:**
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string  
- `GROQ_API_KEY` — Groq API key (for LLM connectivity test)
- `UPLOAD_DIR` — local path for uploaded files (default: `./uploads`)

---

## Contributing

See [`context.md`](context.md) for the living technical context, architecture decisions, and current state of the codebase.

---

## License

MIT
