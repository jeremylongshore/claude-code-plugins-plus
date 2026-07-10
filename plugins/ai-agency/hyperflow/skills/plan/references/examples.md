# Examples

Worked transcripts for `/hyperflow:plan`. Illustrative — not load-bearing for behaviour. They show how the folded amplify → design → decompose flow plays out across the skip paths.

### Full design path (amplify + design + decompose)

```
/hyperflow:plan add a token-bucket rate-limit middleware for this app

[Step 0 — silent: max thinking engaged, flags parsed, NO startup questions]

**Classifier** — triaging request            [concurrent with context Searchers · P3]
Searcher — surface mapping · Searcher — semantic + convention scan
[all complete]  Triage — types: [feature, middleware] · flow: standard · ambiguity: 0.6

Writer — amplified prompt → **Reviewer** — rubric score  (prompt sharpened: persona = api/security)

**Analyst** — 6-dimension analysis

?  Where should the bucket state live?
   In-memory per-instance (Recommended) — fits this single-node deploy; no Redis dep
   Redis-backed                          — survives restarts; needed if you horizontally scale
?  What's the right limit for /login specifically?
   5 req/min (Recommended) · 10 req/min · 30 req/min

Writer — synthesis  [∥ Writer — approaches · P3]  →  **Reviewer** — batched
[user confirms synthesis · picks "Token bucket with Redis fallback"]

Writer — §1 Architecture · §2 Data flow · §3 Key decisions · §4 Edge cases · §5 File structure  [all parallel · P1]
**Reviewer** — batched: all 5 sections
[user approves all 5 in the combined gate]

Writer — finalize spec → .hyperflow/specs/rate-limit-middleware.md  ·  **Reviewer** — final sanity check

**Planner** — batch graph → **Reviewer**  ·  Searcher — sizing ∥ Writer — criteria
Writer — task file  [∥ Writer — memory append · P3]  →  **Reviewer** — assembled task file vs design

Plan ready — .hyperflow/tasks/rate-limit-middleware.md (3 batches, 7 sub-tasks)
?  Where should this be built?
   This session (Recommended) · Another session · Stop
[user picks This session]
Building here — handing to /hyperflow:dispatch…   (dispatch asks commit/branch/push at its Step 0.5)
```

### Concise request — amplify skipped, only 2 questions fire

```
/hyperflow:plan rename "Cart" to "Bag" across the codebase

[triage ambiguity 0.2 → amplify skipped (prompt already specific) → light depth → exactly 2 questions]

? Rename only user-visible text (UI strings, docs), or also internal symbols (types, variables, file names)?
? Do any integrations (analytics events, API contracts) depend on the "Cart" name?

[user answers; design walk-through proceeds, then decomposes the rename into batches]
```

### Bounce — clear request skips the design phase entirely

```
/hyperflow:plan add a /health endpoint that returns {status: "ok"}

[triage ambiguity 0.25 · complexity: low → bounce threshold met at Step 5]

That's clear enough to skip the design phase — decomposing directly.

**Planner** — batch graph → **Reviewer**  ·  Writer — task file
Plan ready — .hyperflow/tasks/health-endpoint.md (1 batch, 2 sub-tasks)
?  Where should this be built?  This session (Recommended) · Another session · Stop
```

### Thorough mode — P1/P2/P4 disabled, P3/P5 stay on

```
/hyperflow:plan --thorough redesign the authentication system

[P1, P2, P4 disabled — sequential drafts, per-section reviewers, every step runs, standalone final-integration pass added]
[P3 stays on — Classifier + context Searchers still concurrent]
[P5 stays on — lean worker prompts still used]
```
