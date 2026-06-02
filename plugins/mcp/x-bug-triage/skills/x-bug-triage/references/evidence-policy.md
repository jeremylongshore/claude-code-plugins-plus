# Evidence Policy — X Bug Triage Plugin

## 4-Tier Hierarchy

| Tier | Name | Examples | Use |
|------|------|----------|-----|
| 1 | Exact | Error string match, known issue match, explicit repro, screenshot reuse, same thread | Justifies clustering alone |
| 2 | Strong contextual | Same conversation tree, same surface + repro, suspicious commit, matching deploy window | Strengthens, never substitutes Tier 1 |
| 3 | Moderate | Semantic symptom similarity, similar language, same platform/release window | Supports grouping, not routing |
| 4 | Weak | Generalized complaint, high-level feature mention, heuristic proximity | Never presented as hard evidence |

## Rules
- Tier 1 alone justifies clustering
- Tier 2 strengthens but never silently substitutes for Tier 1
- Tier 3 supports grouping but not routing
- Tier 4 must never be presented as hard evidence
- Repo scan evidence is triage-quality — NOT root cause proof
