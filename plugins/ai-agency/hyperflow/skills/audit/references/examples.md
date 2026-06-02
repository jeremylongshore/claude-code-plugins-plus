## Examples

### Default — review uncommitted changes at L2

```
/hyperflow:audit

── Review Result ──────────────────────
Scope: git diff HEAD + git diff --staged (3 files)
Level: L2
Verdict: NEEDS_FIX

[Critical]
- src/auth/middleware.ts:42 — token compared with == instead of timingSafeEqual; switch to crypto.timingSafeEqual.

[Important]
- src/auth/middleware.ts:18 — missing rate-limit on /login. Wire token-bucket from src/lib/limiter.ts.

[Suggestions]
- src/auth/types.ts:5 — TokenClaims interface could be a discriminated union for refresh vs access tokens.
───────────────────────────────────────
Agents: 1 searcher (sonnet) · 1 reviewer (opus)

?  Audit found 3 issues — apply fixes?
   Fix all (Recommended)   — Critical + Important + Suggestions
   Critical + Important    — skip Suggestions
   Critical only           — fix the must-haves
   No, leave as-is         — stop; handle manually
```

### Explicit target + deep review

```
/hyperflow:audit src/payments --level 4

── Review Result ──────────────────────
Scope: src/payments/** (12 files)
Level: L4
Verdict: PASS
[Praise]
- src/payments/processor.ts:120 — idempotency key handling is correct under retries.
───────────────────────────────────────
Audit clean — no fixes needed.
```

### PR review

```
/hyperflow:audit --pr 145 --level 3

(reviews the diff between the PR's base and head; same output format)
```

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #8 structural gates, #12 per-step agents).
- [review-levels.md](references/review-levels.md) — full checklist for L1-L5.
- [reviewer-prompt.md](references/reviewer-prompt.md) — Opus reviewer template.
- [security.md](references/security.md) — security scan policy (mandatory at L3+).
- [memory-system.md](references/memory-system.md) — how patterns are persisted.
