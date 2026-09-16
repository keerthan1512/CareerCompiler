# CareerCompiler
## Business Requirements Document (BRD) — Production Grade
**AI-Powered, Evidence-Grounded Resume Engineering and ATS Evaluation Platform**

| | |
|---|---|
| **Version** | 2.0 (Expanded / Production) |
| **Status** | Draft for Engineering Sign-off |
| **Core Principle** | One immutable master LaTeX resume is the single source of truth for every job-specific variant. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [Problem Statement](#3-problem-statement)
4. [Proposed Solution](#4-proposed-solution)
5. [Objectives & Success Metrics](#5-objectives--success-metrics)
6. [Scope](#6-scope)
7. [Target Users & Personas](#7-target-users--personas)
8. [Product Principles](#8-product-principles)
9. [High-Level Architecture](#9-high-level-architecture)
10. [Functional Requirements](#10-functional-requirements)
11. [ATS Evaluation Requirements](#11-ats-evaluation-requirements)
12. [AI Agent Architecture](#12-ai-agent-architecture)
13. [Data Model](#13-data-model)
14. [API Specification (Contract-Level)](#14-api-specification-contract-level)
15. [Business Rules](#15-business-rules)
16. [Non-Functional Requirements](#16-non-functional-requirements)
17. [User Experience Modules](#17-user-experience-modules)
18. [Core Workflow](#18-core-workflow)
19. [Quality & Benchmarking](#19-quality--benchmarking)
20. [Security & Privacy](#20-security--privacy)
21. [Technology Stack (Recommended)](#21-technology-stack-recommended)
22. [Repository Structure](#22-repository-structure)
23. [Infrastructure & DevOps](#23-infrastructure--devops)
24. [Risks & Mitigations](#24-risks--mitigations)
25. [Development Phases & Roadmap](#25-development-phases--roadmap)
26. [Future Enhancements](#26-future-enhancements)
27. [Final Product Definition](#27-final-product-definition)
28. [Recommended Next Documents](#28-recommended-next-documents)

---

## 1. Executive Summary

CareerCompiler is a production-grade AI resume intelligence and optimization platform. It lets users maintain one authoritative master resume in LaTeX and generate factually grounded, job-specific variants. The platform analyzes a job description, maps requirements to verified evidence, proposes tailored content, preserves the original design, compiles a reliable PDF, and evaluates ATS parsing compatibility and job relevance.

The ATS feature is a **transparent simulation** of common recruiting-software behaviors — it does not claim to reproduce any proprietary ATS exactly.

## 2. Product Vision

Transform a professional's existing experience into high-quality, job-specific application documents without compromising factual accuracy, document ownership, visual identity, or explainability.

## 3. Problem Statement

- Generic resumes fail to emphasize role-specific requirements.
- AI tools may invent skills, responsibilities, metrics, dates, or achievements.
- Existing tools often damage the original formatting.
- ATS scores are frequently opaque or misleading.
- Users lack traceable version history.
- LaTeX users need editable source and reliable PDF output.

## 4. Proposed Solution

- Upload and preserve the master LaTeX resume.
- Parse it into a canonical structured professional profile.
- Ingest and analyze a target job description.
- Normalize requirements and technical skills.
- Match requirements against verified resume evidence.
- Create an explainable tailoring plan.
- Generate grounded content proposals.
- Allow approval, rejection, and editing.
- Render approved changes into the original LaTeX template.
- Compile in a secure sandbox and validate the document.
- Run ATS compatibility and job-match evaluation.
- Save a versioned variant and export PDF/LaTeX.

## 5. Objectives & Success Metrics

| Objective | Success Metric | Target |
|---|---|---|
| Preserve original template/design | Visual diff score between master and variant (non-content elements) | ≥ 98% structural similarity |
| Prevent hallucinations | Hallucination rate (unsupported claims / total claims) | < 1% |
| Improve JD relevance | Job Match Score uplift vs. master resume | ≥ 20% average uplift |
| Explainability | % of AI edits with a rationale + evidence link | 100% |
| Compilable output | Compilation success rate | ≥ 99% (with auto-repair loop) |
| ATS parsing risk detection | Precision/recall of known parsing-risk patterns | ≥ 90% F1 on benchmark set |
| Traceability | % of variants with full audit trail | 100% |
| Continuous improvement | Benchmark regression suite run per release | Every release, no regression > 2% |

## 6. Scope

### In Scope
- Master resume management
- LaTeX parsing and semantic representation
- JD ingestion and analysis
- Skill normalization
- Evidence-based matching
- Tailoring and human review
- Template-preserving rendering
- Secure compilation and QA
- ATS analysis
- Job-match scoring
- Versioning and export

### Out of Scope (v1)
- Guaranteed interviews or offers
- Exact replication of proprietary ATS algorithms
- Fabricated qualifications
- Automatic job submission
- Uncontrolled rewriting of LaTeX source

## 7. Target Users & Personas

| Persona | Description | Key Need |
|---|---|---|
| **Student / New Graduate** | Limited work history, needs projects/coursework framed against JDs | Guided evidence extraction from academic work |
| **Early-Career Professional** | 1–5 YOE, applying broadly | Fast tailoring across many JDs |
| **Experienced Professional** | 5+ YOE, senior/lead roles | Nuanced seniority and scope framing |
| **Technical / LaTeX Candidate** | Wants full control of source, precise formatting | LaTeX diff editor, compilation transparency |
| **Career Coach / Placement Cell** | Manages resumes for multiple candidates | Multi-user workspace, batch reporting |

## 8. Product Principles

- **Master-first**: original resume is immutable.
- **Evidence before generation.**
- **No invented** skills, dates, employers, metrics, or achievements.
- **User approval and ownership** of every change.
- **Explainable** changes and scores.
- **Deterministic, reproducible** evaluation.
- **No final artifact** without compilation and validation.
- **Parsing compatibility and job relevance are separate dimensions.**

## 9. High-Level Architecture

```
                         ┌─────────────────────────────┐
                         │      Presentation Layer      │
                         │  (Dashboard / Editor / PDF)  │
                         └──────────────┬───────────────┘
                                        │ REST/GraphQL + WebSocket (job status)
                         ┌──────────────▼───────────────┐
                         │        API Gateway / BFF      │
                         └──────────────┬───────────────┘
        ┌───────────────┬───────────────┼───────────────┬────────────────┐
        ▼               ▼               ▼               ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌────────────────┐
│Resume          │ │Job             │ │Matching        │ │Tailoring       │ │Document         │
│Intelligence    │ │Intelligence    │ │Engine          │ │Orchestrator    │ │Engineering       │
│Layer           │ │Layer           │ │                │ │                │ │(Render/Compile)  │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └────────┬─────────┘
        │                  │                  │                  │                    │
        └──────────────────┴──────────┬───────┴──────────────────┴────────────────────┘
                                       ▼
                         ┌──────────────────────────────┐
                         │     ATS Evaluation Engine     │
                         └──────────────┬───────────────┘
                                        ▼
                         ┌──────────────────────────────┐
                         │   Version & Storage Layer     │
                         │ (Object Store + Metadata DB)  │
                         └──────────────────────────────┘

Cross-cutting: Message Queue (async jobs) · Sandboxed Compilation Workers ·
Observability (logs/metrics/traces) · Auth & Access Control · Audit Log
```

### Layers

- **Resume Intelligence Layer**: parser, canonical profile, evidence graph.
- **Job Intelligence Layer**: JD parser, requirement extractor, skill ontology.
- **Matching Engine**: requirement-to-evidence mapping.
- **Tailoring Orchestrator**: planning, optimization, approvals.
- **Document Engineering**: renderer, compiler, layout validator.
- **ATS Evaluation Engine**: extraction and compatibility analysis.
- **Version and Storage Layer**.
- **Presentation Layer**: dashboard, editor, preview, reports.

---

## 10. Functional Requirements

Requirements are grouped by module, with acceptance criteria and priority (**M**ust / **S**hould / **C**ould, MoSCoW).

### 10.1 Auth & Workspace

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-001 | Authentication and workspace management | Email/password + OAuth (Google); workspace supports single-user and team (coach) modes with role-based access | M |
| FR-001a | Multi-tenant isolation for coach/placement-cell workspaces | Candidates' data invisible across workspaces without explicit share | M |

### 10.2 Master Resume Management

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-002 | Master LaTeX upload | Accepts `.tex` + assets (images, `.cls`, `.sty`, `.bib`); validates compilability on upload | M |
| FR-003 | Immutable original source | Master is stored read-only after ingestion; all edits create a new variant, never mutate master | M |
| FR-004 | LaTeX metadata, section, bullet, link, and style parsing | Parser extracts sections, sub-sections, bullet lists, hyperlinks, and macro-based styling with ≥95% structural accuracy on benchmark templates | M |
| FR-005 | Canonical JSON professional profile with source references | Every profile field links back to `(file, line-range)` in the master `.tex` | M |
| FR-005a | Multiple master templates per user (future-ready) | Data model supports >1 master per user even if UI limits to 1 in v1 | S |

### 10.3 Job Intelligence

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-006 | Job-description ingestion | Accepts pasted text or URL; strips boilerplate/ads via HTML cleaning | M |
| FR-007 | JD extraction: title, company, skills, responsibilities, seniority, domain | Structured JSON output with confidence per field | M |
| FR-008 | Skill and alias normalization | Canonical skill dictionary + alias map (see §11) applied consistently | M |

### 10.4 Matching & Evidence

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-009 | Requirement-to-evidence matching with confidence | Each JD requirement mapped to 0..n evidence items with a confidence score (0–1) and category (Direct / Transferable / Gap) | M |
| FR-010 | Evidence graph and provenance | Graph nodes = evidence; edges = requirement matches; every node traceable to master source location | M |

### 10.5 Tailoring

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-011 | Explainable tailoring plan | Plan lists proposed changes, each with rationale + linked evidence + linked requirement | M |
| FR-012 | Grounded content optimization | Rewording/reordering of bullets only draws on existing evidence; no new facts introduced | M |
| FR-013 | Human approval/rejection/editing | Per-change accept/reject/edit UI; rejected changes never applied; edited text re-validated against evidence | M |
| FR-022 | Bounded iterative optimization | Optimization loop capped at N iterations (config, default 3) to avoid runaway rewriting | M |

### 10.6 Document Engineering

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-014 | Original-template LaTeX rendering | Approved changes injected via templated diff (not full regeneration); non-content LaTeX (preamble, styling macros) untouched | M |
| FR-015 | Sandboxed compilation | Compilation runs in isolated container, no network, resource-limited (CPU/mem/time) | M |
| FR-016 | Document validation and page checks | Validates page count vs. target, checks for overfull/underfull boxes, broken references | M |

### 10.7 ATS & Scoring

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-017 | ATS parsing simulation | Simulates plain-text extraction as common ATS parsers would (column collapse, table flattening, font/icon loss) | M |
| FR-018 | ATS compatibility score | Deterministic scoring formula (see §11), 0–100 | M |
| FR-019 | ATS failure-risk detection | Flags: tables, columns, text boxes, icons-as-text, non-standard fonts, headers/footers with critical info | M |
| FR-020 | Separate job-match score | Computed independently of ATS parsing score | M |
| FR-021 | Strengths, gaps, and recommendations | Human-readable report generated from MatchResult + EvaluationResult | M |

### 10.8 Versioning & Export

| ID | Requirement | Acceptance Criteria | Priority |
|---|---|---|---|
| FR-023 | Variant versioning | Each save creates immutable version record (master_id, job_id, version_n) | M |
| FR-024 | Master/variant comparison | Side-by-side and unified diff views (LaTeX + rendered PDF) | M |
| FR-025 | PDF and LaTeX export | Download individually or as a zip with assets | M |

---

## 11. ATS Evaluation Requirements

The platform **shall** label its output as an *estimated CareerCompiler evaluation*, not an official vendor score.

### 11.1 Evaluated Dimensions
- Text readability and extraction
- Section and heading recognition
- Contact, date, company, title, and bullet association
- Skill/entity extraction
- Requirement and keyword matching
- Evidence strength and relevance
- Formatting and layout compatibility

### 11.2 Score Composition

| Score | Definition | Computation Style |
|---|---|---|
| **Parsing Compatibility Score** | How reliably the document's text/structure survives naive extraction | Deterministic rule engine (regex/structure checks) |
| **Job Match Score** | Degree of alignment between resume evidence and JD requirements | Deterministic weighted matching (embedding similarity + keyword overlap), LLM used only for explanation text |
| **Evidence/Grounding Score** | % of resume claims with traceable evidence | Deterministic ratio (grounded claims / total claims) |
| **Overall Resume Readiness** | Transparent weighted blend of the above | Documented, user-visible weighting formula, e.g. `0.35*Parsing + 0.40*JobMatch + 0.25*Grounding` |

> **Rule**: The score must be primarily deterministic. LLMs may assist with semantic interpretation and explanations but must **never** arbitrarily choose the final number. Every score ships with a methodology note and a confidence indicator.

### 11.3 Skill Normalization Rules

- Normalize: `React.js → React`, `Amazon Web Services → AWS`, `Postgres → PostgreSQL`, `JS → JavaScript`.
- **Preserve distinctions**: `Docker` ≠ `Kubernetes`; `SQL` ≠ `PostgreSQL`; `AWS` ≠ `EC2`.
- Normalization map is versioned and auditable (changes require review, since they affect scoring reproducibility).

---

## 12. AI Agent Architecture

| Agent | Responsibility | Input | Output | Deterministic? |
|---|---|---|---|---|
| **Resume Parser Agent** | Parse LaTeX into structured sections/bullets | Master `.tex` + assets | Structured AST + line references | Mostly deterministic (grammar-based) with LLM fallback for ambiguous macros |
| **Job Description Analyzer Agent** | Extract JD structure | Raw JD text | Title, company, skills, responsibilities, seniority, domain (JSON) | LLM-assisted |
| **Requirement Matching Agent** | Map requirements to evidence | Canonical profile + normalized JD | MatchResult[] with confidence | Hybrid (embedding similarity + LLM judgment, capped) |
| **Evidence Graph Builder** | Build/maintain provenance graph | Canonical profile, MatchResults | Graph nodes/edges | Deterministic |
| **Tailoring Planner Agent** | Produce ordered change plan | MatchResults, gaps | TailoringPlan (proposed edits + rationale) | LLM-assisted, evidence-constrained |
| **Content Optimizer Agent** | Rewrite/reorder bullet text | Approved plan items, evidence | Proposed text | LLM-assisted, constrained decoding against evidence |
| **Fact Verification Agent** | Verify no unsupported claims introduced | Proposed text vs. evidence | Pass/fail + flagged spans | LLM + rule-based entailment check |
| **LaTeX Rendering Agent** | Inject approved content into template | Approved diffs, original `.tex` | Updated `.tex` (non-approved regions untouched) | Deterministic templated diff |
| **Compilation and Repair Agent** | Compile, detect/fix common LaTeX errors | `.tex` | `.pdf` or repair suggestions | Deterministic compiler + rule-based repair, LLM as last resort |
| **ATS Analyzer Agent** | Simulate ATS extraction, score compatibility | Compiled PDF | ATS report | Deterministic |
| **Evaluation and Orchestration Agent** | Coordinate pipeline, aggregate scores, manage retries | All above | Final EvaluationResult, orchestration logs | Deterministic (state machine) |

### 12.1 Guardrails Applied Across All LLM-Assisted Agents
- Every LLM call is grounded with retrieved evidence text in the prompt context (RAG-style, not free generation).
- Outputs are schema-validated (JSON schema) before use downstream.
- The **Fact Verification Agent** acts as a hard gate — no proposed content reaches the user without passing entailment checks.
- All agent inputs/outputs are logged for auditability (see FR/NFR on audit logs).

---

## 13. Data Model

### 13.1 Core Entities

```
User
 ├─ id, email, name, role (individual | coach), created_at

Workspace
 ├─ id, owner_id, type (personal | team), members[]

MasterResume
 ├─ id, user_id, original_tex (immutable blob ref), assets[], checksum,
 │  template_metadata { class, packages, macros }, profile_json_ref, created_at

CanonicalProfile
 ├─ id, master_resume_id, sections[], bullets[], skills[], dates[],
 │  each field: { value, source_ref: {file, line_start, line_end} }

JobDescription
 ├─ id, user_id, raw_text, source_url, normalized_requirements[],
 │  extracted { title, company, seniority, domain, skills[] }

Evidence
 ├─ id, master_resume_id, source_section, source_text, claim,
 │  confidence, provenance_ref

MatchResult
 ├─ id, job_id, requirement_id, evidence_id, category (Direct|Transferable|Gap),
 │  confidence, explanation

TailoringPlan
 ├─ id, job_id, master_resume_id, items[] { requirement_id, evidence_id,
 │   proposed_text, rationale, status (pending|approved|rejected|edited) }

ResumeVariant
 ├─ id, parent_master_id, job_id, tex_blob_ref, pdf_blob_ref,
 │  status (draft|compiled|failed|final), version_n, created_at

EvaluationResult
 ├─ id, variant_id, parsing_score, job_match_score, grounding_score,
 │  overall_score, issues[], recommendations[], methodology_version

AuditLog
 ├─ id, actor (user|agent), action, entity_type, entity_id, diff, timestamp
```

### 13.2 Relationships
- One `User` → many `MasterResume` (v1 UI restricts to 1 active).
- One `MasterResume` → many `ResumeVariant` (one per JD, versioned).
- One `ResumeVariant` → one `EvaluationResult` per evaluation run (re-runs create new records, not overwrites — for reproducibility).
- `Evidence` is derived from exactly one `MasterResume` and referenced by many `MatchResult`s.

---

## 14. API Specification (Contract-Level)

> Full OpenAPI spec is a separate deliverable (see §28). This section defines the contract surface.

| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/login`, `/auth/oauth/google` | POST | Authentication |
| `/workspaces` | GET/POST | Workspace management |
| `/master-resumes` | POST | Upload master LaTeX + assets |
| `/master-resumes/{id}` | GET | Fetch parsed profile + metadata |
| `/master-resumes/{id}/reparse` | POST | Re-run parser (e.g., after asset fix) |
| `/job-descriptions` | POST | Ingest JD (text or URL) |
| `/job-descriptions/{id}` | GET | Fetch normalized JD |
| `/matches` | POST | Trigger requirement-to-evidence matching for `(master_id, job_id)` |
| `/tailoring-plans/{id}` | GET | Fetch proposed plan |
| `/tailoring-plans/{id}/items/{item_id}` | PATCH | Approve/reject/edit a single change |
| `/variants` | POST | Render + compile approved plan into a variant |
| `/variants/{id}` | GET | Fetch variant status, PDF/LaTeX links |
| `/variants/{id}/evaluate` | POST | Run ATS + job-match evaluation |
| `/variants/{id}/compare?against=master` | GET | Diff view |
| `/variants/{id}/export` | GET | Download PDF/LaTeX/zip |
| `/audit-logs` | GET | Query audit trail (admin/coach) |

**Async pattern**: Long-running operations (`reparse`, `matches`, `variants` compile, `evaluate`) return `202 Accepted` + `job_id`; clients poll `/jobs/{job_id}` or subscribe via WebSocket for status.

---

## 15. Business Rules

- Never overwrite the master resume.
- Every variant references exactly one master.
- Every claim must be evidence-grounded.
- Never add unsupported skills or achievements.
- Preserve user edits and distinguish them from AI edits (tagged `source: user | ai`).
- A failed compilation cannot be marked `final`.
- Page overflow triggers warnings or controlled reduction (never silent truncation).
- Every score ships with methodology and confidence metadata.
- All transformations are auditable (immutable `AuditLog` entries).

---

## 16. Non-Functional Requirements

### 16.1 Performance
| ID | Requirement | Target |
|---|---|---|
| NFR-P1 | Master resume parse time | < 5s for a typical 1–2 page resume |
| NFR-P2 | JD analysis time | < 8s |
| NFR-P3 | End-to-end tailoring pipeline (match → plan) | < 30s (async, non-blocking UI) |
| NFR-P4 | LaTeX compilation | < 15s per attempt, ≤ 3 auto-repair attempts |
| NFR-P5 | ATS evaluation | < 10s |

### 16.2 Reliability & Availability
| ID | Requirement | Target |
|---|---|---|
| NFR-R1 | Service uptime | ≥ 99.5% monthly |
| NFR-R2 | Compilation job retries | Automatic retry with backoff, max 3 attempts, then surfaced to user with repair suggestions |
| NFR-R3 | Idempotent job processing | Duplicate job submissions do not create duplicate variants |
| NFR-R4 | Graceful degradation | If LLM provider is down, deterministic scoring/matching still functions in reduced mode |

### 16.3 Scalability
- Queue-based architecture (e.g., SQS/RabbitMQ/Redis Streams) for all long-running agent tasks.
- Horizontally scalable compilation workers (stateless containers, autoscaled on queue depth).
- Stateless API layer behind a load balancer.

### 16.4 Security
- Encryption at rest (AES-256) and in transit (TLS 1.2+).
- Workspace-level RBAC (owner, editor, viewer, coach-view).
- Sandboxed compilation: isolated containers, **no network access**, CPU/memory/time-limited, ephemeral filesystem.
- Secrets managed via vault (e.g., AWS Secrets Manager / HashiCorp Vault) — never in code or env files committed to repo.
- No sensitive data sent to external LLM providers without explicit user authorization and data-minimization (strip PII where feasible before external calls, or use a provider under a zero-data-retention agreement).

### 16.5 Observability
- Structured logging (JSON) for every agent invocation, including prompt/response hashes (not raw PII in logs where avoidable).
- Metrics: pipeline latency per stage, compilation success rate, hallucination-flag rate, queue depth.
- Distributed tracing across the async pipeline (trace_id propagated from initial request through all agents).
- Alerting on: compilation failure rate spikes, LLM provider errors, queue backlog thresholds.

### 16.6 Maintainability & Extensibility
- Modular model/provider architecture: LLM calls go through an abstraction layer supporting swap between providers (Anthropic, OpenAI, local models) via config.
- Clear separation between deterministic scoring logic and LLM-assisted components (independently testable).
- Versioned normalization dictionaries and scoring methodologies (changing them requires a version bump and regression test run).

### 16.7 Compliance & Data Governance
- User-initiated data deletion (right to erasure) removes master, variants, evidence, and derived artifacts within a defined SLA (e.g., 30 days, immediate on request where feasible).
- Configurable data retention policy per workspace.
- Full audit log retained independent of user data deletion (anonymized) for compliance purposes.

### 16.8 Accessibility & Internationalization (should-have for v1, must for later phases)
- Dashboard/editor meets WCAG 2.1 AA where practical.
- LaTeX/resume content assumed English-first in v1; architecture should not hardcode English-only assumptions in the parser (Unicode-safe throughout).

---

## 17. User Experience Modules

- Dashboard
- Master Resume Workspace
- Job Description Workspace
- Requirement Matching View
- Tailoring Review Workspace
- LaTeX Diff Editor
- PDF Preview
- ATS Evaluation Dashboard
- Version History
- Export Center

---

## 18. Core Workflow

1. User uploads a master resume **once**.
2. For each target role, the user supplies a JD.
3. System analyzes the role and maps requirements to evidence.
4. System proposes grounded changes with rationale.
5. User reviews a diff and approves/rejects/edits each change.
6. System renders approved changes into the **original template**.
7. System compiles and validates the document (auto-repair loop if needed).
8. System runs ATS and job-match evaluation.
9. System saves the result as a versioned, derivative variant, exportable as PDF/LaTeX.

---

## 19. Quality & Benchmarking

| Metric | Definition |
|---|---|
| Requirement matching precision/recall/F1 | Against a hand-labeled benchmark set of (resume, JD) pairs |
| Grounding rate | % of AI-proposed claims backed by evidence |
| Hallucination rate | % of AI-proposed claims **not** backed by evidence (target: < 1%) |
| Section/contact/date/entity extraction accuracy | Against labeled LaTeX templates covering common formats (moderncv, awesome-cv, custom) |
| Compilation success rate | % of variants that compile without manual intervention |
| Page-count compliance | % of variants matching user's target page count |
| Text extraction loss rate | % of visible resume content lost under naive ATS-style extraction |
| User acceptance of suggested edits | % of proposed plan items accepted as-is or with minor edits |

A **regression benchmark suite** runs on every release; any metric regressing beyond a defined threshold blocks release.

---

## 20. Security & Privacy

- Encrypt stored resume sources and artifacts (at rest and in transit).
- Workspace-level access control (RBAC).
- Compile in isolated containers with network access disabled.
- Limit CPU, memory, execution time, and filesystem access per compilation job.
- Provide deletion and retention controls to users.
- Maintain immutable audit logs.
- Do not send sensitive data to external providers without authorization; support provider-level data-processing agreements (zero-retention where possible).

---

## 21. Technology Stack (Recommended)

| Layer | Recommendation | Notes |
|---|---|---|
| Frontend | React + TypeScript, Vite | Component-driven; diff/editor views need a rich-text/monaco-style component |
| LaTeX Diff Editor | Monaco Editor with LaTeX syntax highlighting | Supports inline diff rendering |
| Backend API | Node.js (NestJS) or Python (FastAPI) | FastAPI favored if most agent code is Python (LLM/NLP ecosystem) |
| Async/Queue | Redis Streams or RabbitMQ (SQS if AWS-native) | Backs the agent pipeline |
| Orchestration | A workflow engine (e.g., Temporal) or custom state machine | Manages multi-step pipeline with retries |
| LLM Provider Abstraction | Internal SDK wrapper supporting Anthropic Claude API (primary), pluggable alternates | Function-calling / structured output for schema-validated agent responses |
| Compilation Sandbox | Firecracker/gVisor microVMs or Docker with `--network none`, seccomp profiles | Runs `latexmk`/`tectonic` |
| LaTeX Toolchain | `tectonic` (self-contained, deterministic) or `texlive` in a pinned container image | `tectonic` preferred for reproducibility |
| Database (relational) | PostgreSQL | Users, workspaces, metadata, MatchResults, EvaluationResults |
| Graph storage (Evidence Graph) | PostgreSQL with a graph extension (e.g., AGE) or a dedicated graph DB (Neo4j) if scale warrants | Start relational; migrate if needed |
| Object Storage | S3-compatible (AWS S3 / MinIO) | Master `.tex`, assets, compiled PDFs |
| Search/Embeddings | pgvector or a dedicated vector DB (e.g., Qdrant) | For requirement-to-evidence semantic matching |
| Observability | OpenTelemetry + Grafana/Loki/Tempo (or Datadog) | Tracing across async pipeline |
| Auth | Auth0 / self-hosted (e.g., Ory Kratos) + OAuth (Google) | |
| CI/CD | GitHub Actions | Lint, test, build, deploy, benchmark suite gate |
| Infra as Code | Terraform | |
| Container Orchestration | Kubernetes (or ECS for simpler ops) | Autoscale compilation workers |

---

## 22. Repository Structure

Recommended **monorepo** layout (adjust package manager tooling — e.g., pnpm workspaces / Nx / Turborepo — as needed):

```
career-compiler/
├── README.md
├── BRD.md                          # this document
├── docs/
│   ├── srs.md                      # Software Requirements Specification
│   ├── architecture.md
│   ├── api-spec.yaml               # OpenAPI 3.1
│   ├── data-model.md
│   ├── ats-methodology.md
│   ├── agent-design.md
│   └── benchmark-design.md
│
├── apps/
│   ├── web/                        # Frontend (React + TS)
│   │   ├── src/
│   │   │   ├── modules/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── master-resume/
│   │   │   │   ├── job-description/
│   │   │   │   ├── matching/
│   │   │   │   ├── tailoring-review/
│   │   │   │   ├── latex-diff-editor/
│   │   │   │   ├── pdf-preview/
│   │   │   │   ├── ats-dashboard/
│   │   │   │   ├── version-history/
│   │   │   │   └── export-center/
│   │   │   ├── shared/ (components, hooks, api-client)
│   │   │   └── main.tsx
│   │   ├── public/
│   │   └── package.json
│   │
│   └── api/                        # Backend API (FastAPI or NestJS)
│       ├── src/
│       │   ├── auth/
│       │   ├── workspaces/
│       │   ├── master_resumes/
│       │   ├── job_descriptions/
│       │   ├── matches/
│       │   ├── tailoring_plans/
│       │   ├── variants/
│       │   ├── evaluations/
│       │   ├── audit_logs/
│       │   ├── jobs/                # async job status endpoints
│       │   └── main.py / main.ts
│       ├── tests/
│       └── requirements.txt / package.json
│
├── services/
│   ├── resume-parser/               # Resume Intelligence Layer
│   │   ├── src/
│   │   │   ├── latex_ast_parser/
│   │   │   ├── canonical_profile_builder/
│   │   │   └── evidence_extractor/
│   │   └── tests/
│   │
│   ├── job-intelligence/            # JD parsing, skill normalization
│   │   ├── src/
│   │   │   ├── jd_extractor_agent/
│   │   │   ├── skill_normalizer/
│   │   │   │   └── normalization_map.json   # versioned
│   │   │   └── requirement_extractor/
│   │   └── tests/
│   │
│   ├── matching-engine/
│   │   ├── src/
│   │   │   ├── embedding_matcher/
│   │   │   ├── evidence_graph_builder/
│   │   │   └── confidence_scorer/
│   │   └── tests/
│   │
│   ├── tailoring-orchestrator/
│   │   ├── src/
│   │   │   ├── planner_agent/
│   │   │   ├── content_optimizer_agent/
│   │   │   ├── fact_verification_agent/
│   │   │   └── approval_manager/
│   │   └── tests/
│   │
│   ├── document-engineering/
│   │   ├── src/
│   │   │   ├── latex_rendering_agent/
│   │   │   ├── compilation_agent/          # invokes sandbox
│   │   │   ├── repair_agent/
│   │   │   └── layout_validator/
│   │   ├── sandbox/
│   │   │   ├── Dockerfile.compiler         # tectonic/texlive, network disabled
│   │   │   └── seccomp-profile.json
│   │   └── tests/
│   │
│   ├── ats-evaluation/
│   │   ├── src/
│   │   │   ├── extraction_simulator/
│   │   │   ├── scoring_engine/             # deterministic scoring
│   │   │   ├── risk_detector/
│   │   │   └── report_generator/
│   │   └── tests/
│   │
│   └── orchestration/                      # Evaluation & Orchestration Agent
│       ├── src/
│       │   ├── pipeline_state_machine/
│       │   ├── retry_policies/
│       │   └── job_dispatcher/
│       └── tests/
│
├── packages/                        # shared libraries
│   ├── llm-client/                  # provider abstraction (Anthropic, etc.)
│   │   └── src/
│   ├── schemas/                     # shared JSON Schema / Pydantic / Zod models
│   │   ├── canonical_profile.schema.json
│   │   ├── job_description.schema.json
│   │   ├── match_result.schema.json
│   │   ├── tailoring_plan.schema.json
│   │   └── evaluation_result.schema.json
│   ├── audit-logger/
│   └── ui-components/               # shared design system for web app
│
├── infra/
│   ├── terraform/
│   │   ├── modules/ (network, eks/ecs, rds, s3, redis, secrets)
│   │   └── envs/ (dev, staging, prod)
│   ├── k8s/
│   │   ├── base/
│   │   └── overlays/ (dev, staging, prod)
│   └── docker-compose.yml           # local dev stack
│
├── benchmarks/
│   ├── datasets/
│   │   ├── resumes/ (labeled LaTeX templates)
│   │   └── job_descriptions/
│   ├── eval_scripts/
│   │   ├── matching_precision_recall.py
│   │   ├── hallucination_rate.py
│   │   ├── extraction_accuracy.py
│   │   └── compilation_success_rate.py
│   └── reports/
│
├── .github/
│   └── workflows/
│       ├── ci.yml                   # lint/test/build on PR
│       ├── benchmark-gate.yml       # blocks release on regression
│       └── deploy.yml
│
└── scripts/
    ├── seed_dev_data.sh
    ├── run_local_stack.sh
    └── generate_openapi.sh
```

---

## 23. Infrastructure & DevOps

- **Environments**: `dev`, `staging`, `prod`, isolated via Terraform workspaces / separate accounts.
- **CI Pipeline**: lint → unit tests → integration tests → build images → benchmark-gate (blocks merge/release on regression) → deploy.
- **Compilation Sandbox Isolation**: dedicated node pool / worker group with strict network policies (deny-all egress except to internal artifact store).
- **Secrets**: injected at runtime via vault/secrets manager; never baked into images.
- **Blue/Green or Canary Deploys** for the API layer to avoid downtime during schema migrations.
- **Database Migrations**: versioned, reversible (e.g., Alembic/Prisma Migrate), run as a pre-deploy step.
- **Backup & DR**: automated PostgreSQL backups + object storage versioning; documented RPO/RTO targets (e.g., RPO 1h, RTO 4h for v1).

---

## 24. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Unsupported AI claims | Evidence graph, verifier agent, provenance tracking, mandatory user approval |
| Compilation failure | Sandbox, validation, automated repair loop with capped retries |
| Misleading ATS score | Transparent, separated dimensions and explicit no-vendor-equivalence disclaimer |
| Formatting damage | Semantic, templated rendering into the original document (never full regeneration) |
| Page overflow | Prioritization logic, controlled shortening, explicit warnings (never silent truncation) |
| Provider dependency | Model/provider abstraction layer; deterministic fallback for scoring |
| PII exposure to third-party LLMs | Data minimization before external calls, zero-retention provider agreements, user authorization gate |
| Runaway/looping AI optimization | Bounded iteration count (FR-022), circuit breakers in orchestration state machine |
| Scoring irreproducibility | Versioned normalization maps and scoring methodology; regression benchmark suite per release |

---

## 25. Development Phases & Roadmap

| Phase | Focus | Key Deliverables |
|---|---|---|
| **Phase 1 — Resume Foundation** | Master upload, LaTeX parsing, canonical profile | FR-001–005 |
| **Phase 2 — Job Intelligence** | JD ingestion, extraction, normalization | FR-006–008 |
| **Phase 3 — Evidence Matching & Tailoring** | Matching engine, evidence graph, tailoring plan, approvals | FR-009–013, FR-022 |
| **Phase 4 — Document Engineering** | Templated rendering, sandboxed compilation, validation | FR-014–016 |
| **Phase 5 — ATS Engine** | Extraction simulation, scoring, risk detection | FR-017–021 |
| **Phase 6 — Evaluation & Benchmarking** | Benchmark datasets, regression suite, quality dashboards | §19 |
| **Phase 7 — Production Security, Scaling & UX** | Hardening, autoscaling, full UX modules, audit/compliance | §16, §17, §20 |

---

## 26. Future Enhancements

- PDF/DOCX ingestion
- Multiple templates
- Grounded cover letters
- LinkedIn optimization
- Skill-gap analysis
- Application tracking
- Career analytics
- University placement dashboards
- Recruiter-facing reports

---

## 27. Final Product Definition

CareerCompiler enables users to maintain one authoritative LaTeX resume and intelligently generate factually grounded, job-specific resume variants — while preserving original design, validating document quality, and evaluating ATS compatibility through transparent, measurable analysis.

---

## 28. Recommended Next Documents

- Software Requirements Specification (`docs/srs.md`)
- System Architecture Document (`docs/architecture.md`)
- Database Schema (DDL + ERD)
- AI Agent Design (`docs/agent-design.md`)
- LaTeX Parsing and Rendering Design
- ATS Evaluation Methodology (`docs/ats-methodology.md`)
- API Specification (`docs/api-spec.yaml`, OpenAPI 3.1)
- UI/UX Specification (wireframes/Figma link)
- Development Roadmap (Gantt/sprint plan derived from §25)
- Evaluation Benchmark Design (`docs/benchmark-design.md`)
