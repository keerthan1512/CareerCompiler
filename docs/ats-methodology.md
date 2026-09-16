# ATS Evaluation Methodology

> Status: Phase 5 stub

## Score Composition

| Score | Formula | Notes |
|---|---|---|
| Parsing Compatibility | Deterministic rule engine | regex/structure checks |
| Job Match | Weighted keyword + embedding similarity | LLM for explanation only |
| Grounding | grounded_claims / total_claims | deterministic ratio |
| Overall | `0.35*Parsing + 0.40*JobMatch + 0.25*Grounding` | documented, user-visible |

## Disclaimer

All scores are labeled as *estimated CareerCompiler evaluations*. They do not represent any proprietary ATS vendor score.

## Evaluated Dimensions (Phase 5)

- Text readability and extraction
- Section and heading recognition
- Contact, date, company, title, bullet association
- Skill/entity extraction
- Requirement and keyword matching
- Evidence strength and relevance
- Formatting and layout compatibility
