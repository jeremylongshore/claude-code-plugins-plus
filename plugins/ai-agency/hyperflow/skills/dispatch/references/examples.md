## Examples

### Single-batch task — D7 skip + §12.1 inline + D2 combined gate

```
/hyperflow:dispatch add-version-command

[chain-mode auto, propagated from scope]

Batch 1 — add /version command + smoke test (2 parallel sub-tasks, both L1-L2)
Implementer — creating /version command
Writer — adding smoke test
[both workers complete]
**Reviewer** — batched review Batch 1 (L1-L2, 2 sub-tasks)
── Batched Review ──────────────────────
/version command:  PASS
smoke test:        PASS
────────────────────────────────────────
GLOBAL VERDICT: APPROVED
[2 per-sub-task commits]

Layer 5 gates: lint pass · typecheck pass · tests pass

Final integration review skipped — all batches PASSed first try
[D7 skip conditions met: 1/1 batches first-try PASS · no escalations · no security flags]

[Wrap-up inline — §12.1: delete task file · append memory · chore(memory): commit]

── Hyperflow Usage ──────────────────────
Thinking (Opus 4.8)     1 agent    14.2k tokens  (1 batch reviewer)
Worker   (Sonnet 4.6)   2 agents   38.0k tokens  (1 implementer + 1 writer)
Total                   3 agents   52.2k tokens
─────────────────────────────────────────

? End-of-chain gates

  [1] Run /hyperflow:audit on the cumulative diff?
      Yes — outside-eye L3 review
      No  — per-batch L1-L2 reviewers already covered it (standard profile)

  [2] Run /hyperflow:deploy now?
      Yes — all gates green, ready to ship
      No  — keep local; push manually later
```

### Multi-batch with learning injection (P2 batched review)

```
/hyperflow:dispatch implement-auth

Batch 1 — schema + types (2 parallel, both L1-L3)
Implementer — creating TokenClaims schema
Implementer — creating auth type exports
[both workers complete]
**Reviewer** — batched review Batch 1 (L1-L3, 2 sub-tasks)
── Batched Review ──────────────────────
schema:  PASS
types:   PASS
────────────────────────────────────────
GLOBAL VERDICT: APPROVED
[2 per-sub-task commits]
[Synthesize: "TokenClaims uses discriminated union; downstream batches should import from src/auth/types.ts"]

Batch 2 — middleware + login route (3 parallel, all L1-L3, learning injected)
Implementer — creating auth middleware
Implementer — creating login route
Writer — creating route index
[all workers complete]
**Reviewer** — batched review Batch 2 (L1-L3, 3 sub-tasks)
── Batched Review ──────────────────────
auth middleware:  PASS
login route:      NEEDS_FIX — missing TokenClaims import from src/auth/types.ts (cross-section note from B1)
route index:      PASS
────────────────────────────────────────
GLOBAL VERDICT: NEEDS_FIX
[Commit middleware + route index immediately (2 commits). Re-dispatch login route worker only.]
Implementer — fixing login route (TokenClaims import)
**Reviewer** — reviewing login route fix (L1-L3)
[PASS — 1 additional commit]

Batch 3 — tests (4 parallel, all L1-L2)
...
**Reviewer** — batched review Batch 3 (L1-L2, 4 sub-tasks)
[all PASS — 4 per-sub-task commits]

Layer 5 gates
**Reviewer** — final integration review (L1-L3)
[D7 skip conditions NOT met: Batch 2 had a NEEDS_FIX retry — integration review runs]

[Wrap-up inline — §12.1: delete task file · synthesize multi-batch learnings via Writer · chore(memory): commit]

── Hyperflow Usage ──────────────────────
Thinking (Opus 4.8)     4 agents   58.8k tokens  (3 batch reviewers + 1 final)
Worker   (Sonnet 4.6)  11 agents  210.0k tokens  (includes re-dispatch + wrap-up Writer)
Total                  15 agents  268.8k tokens
─────────────────────────────────────────
```

### Mid-batch SECURITY_VIOLATION (batched review)

```
Batch 2 — payment processor (3 parallel, all L1-L3)
Implementer — wiring stripe webhook
Implementer — creating payment record writer
Implementer — adding payment route
[all workers complete]
**Reviewer** — batched review Batch 2 (L1-L3, 3 sub-tasks)
── Batched Review ──────────────────────
stripe webhook:        SECURITY_VIOLATION — webhook signature verified with == instead of crypto.timingSafeEqual (src/payments/webhook.ts:18)
payment record writer: PASS
payment route:         PASS
────────────────────────────────────────
GLOBAL VERDICT: SECURITY_VIOLATION

Halted chain. No commits from Batch 2. Per-sub-task commits from Batch 1 remain on branch. Do not push.
Resume with /hyperflow:dispatch --from-batch 2 after the timing-safe fix.
```

### Mixed level caps — per-sub-task fallback

```
Batch 2 — auth + analytics (mixed profile)
[auth sub-task: L1-L5 (complex, new feature) — analytics sub-task: L1-L2 (simple, config change)]
[Mixed level caps detected — falling back to per-sub-task reviewers]
Implementer — creating auth flow
Implementer — updating analytics config
**Reviewer** — reviewing auth flow (L1-L5)
**Reviewer** — reviewing analytics config (L1-L2)
[both PASS — 2 per-sub-task commits]
```

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #8 structural gates, #12 per-step agents).
- [worker-prompt.md](references/worker-prompt.md) — Sonnet implementer/searcher/writer template.
- [reviewer-prompt.md](references/reviewer-prompt.md) — Opus reviewer template (per-sub-task fallback).
- [reviewer-prompt-batched.md](../../hyperflow/reviewer-prompt-batched.md) — Opus batched reviewer template (P2).
- [latency-patterns.md](../spec/references/latency-patterns.md) — P1–P5 latency patterns; P2 dispatch win ~75% reviewer-phase latency.
- [review-levels.md](references/review-levels.md) — L1-L5 checklist.
