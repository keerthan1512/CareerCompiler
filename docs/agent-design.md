# AI Agent Design

> Status: Phase 3 stub

## Agent Pipeline (BRD §12)

| Agent | Package | Phase | LLM? |
|---|---|---|---|
| Resume Parser Agent | `services/resume-parser` | ✅ 1 | No (TexSoup + regex) |
| Job Description Analyzer | `services/job-intelligence` | 2 | Yes (Groq) |
| Requirement Matching Agent | `services/matching-engine` | 3 | Hybrid |
| Evidence Graph Builder | `services/matching-engine` | 3 | No |
| Tailoring Planner Agent | `services/tailoring-orchestrator` | 3 | Yes (Groq) |
| Content Optimizer Agent | `services/tailoring-orchestrator` | 3 | Yes (Groq) |
| Fact Verification Agent | `services/tailoring-orchestrator` | 3 | Yes + rules |
| LaTeX Rendering Agent | `services/document-engineering` | 4 | No |
| Compilation & Repair Agent | `services/document-engineering` | 4 | No (repair: rule-based) |
| ATS Analyzer Agent | `services/ats-evaluation` | 5 | No |
| Orchestration Agent | `services/orchestration` | 3+ | No (state machine) |

## Framework

LangChain + LangGraph for stateful multi-agent pipelines.
All LLM calls go through `packages/llm-client` (Groq API primary).

## Guardrails

- Every LLM call grounded with retrieved evidence (RAG-style)
- All outputs schema-validated (JSON schema) before use
- Fact Verification Agent is a hard gate — no content reaches user without passing
- All agent inputs/outputs logged (AuditLog)
