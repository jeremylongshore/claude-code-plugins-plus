## Examples

### Standard exploration (P3+P1+P2 active)

```
/hyperflow:spec add a token-bucket rate-limit middleware for this app

?  How should I advance through the chain after each phase?
   Auto (Recommended) — chain forward through spec → scope → dispatch with no gates
   Manual              — pause between phases and ask before advancing

[user picks Auto]

**Classifier** — triaging request  [concurrent with Searcher]
Searcher — mapping context relevant to rate-limit middleware
[both complete]
Triage — types: [feature, middleware] · flow: standard · ambiguity: 0.6

**Analyst** — 6-dimension exploration

?  Where should the bucket state live?
   In-memory per-instance (Recommended) — fits this single-node deploy; no Redis dep
   Redis-backed                          — survives restarts; needed if you horizontally scale

?  What's the right limit for /login specifically?
   5 req/min (Recommended) — common anti-bruteforce threshold
   10 req/min              — more lenient; rely on captcha for hard cases
   30 req/min              — very lenient; depends on captcha + lockout

Writer — drafting requirement synthesis  [concurrent with Approaches Writer]
Writer — drafting 2-3 approaches         [concurrent with Synthesis Writer]
[both complete]
**Reviewer** — batched review: synthesis + approaches

[user confirms synthesis and picks "Token bucket with Redis fallback"]

Writer — drafting section: Architecture  [all 5 parallel]
Writer — drafting section: Data flow
Writer — drafting section: Key decisions
Writer — drafting section: Edge cases
Writer — drafting section: File structure
[all 5 complete]
**Reviewer** — batched review: all 5 design sections

[user approves all 5 in combined gate]

Writer — writing spec to .hyperflow/specs/rate-limit-middleware.md
**Reviewer** — final spec sanity check

Spec complete — design approved
Auto-chaining to /hyperflow:scope...
```

### Concise request — only 2 questions fire

```
/hyperflow:spec rename "Cart" to "Bag" across the codebase

[triage ambiguity 0.2 → light depth → exactly 2 questions]

? Should I rename only user-visible text (UI strings, docs) or also internal symbols (types, variables, file names)?
? Are there integrations (analytics events, API contracts) that depend on the "Cart" name?

[user answers; spec proceeds with parallel 5-section walk-through, scope handles the actual rename]
```

### Bounces to scope when clear (P4 hard enforcement)

```
/hyperflow:spec add a /health endpoint that returns {status: "ok"}

[triage ambiguity 0.25 · complexity: low → P4 bounce threshold met]

That's clear enough to skip the design phase. Auto-chaining to /hyperflow:scope...
```

### Thorough mode — all latency patterns disabled except P3 and P5

```
/hyperflow:spec --thorough redesign the authentication system

[P1, P2, P4 disabled — sequential drafts, per-section reviewers, all steps run]
[P3 stays on — Classifier + Searcher still concurrent]
[P5 stays on — lean worker prompts still used]
```

