---
name: trace
description: |
  Use when encountering bugs, test failures, runtime errors, broken builds, or "this doesn't work" reports. Systematic root-cause analysis before any patch — never blind-patches symptoms. Standalone, ends with thinking-tier review of the fix.
  Trigger with /hyperflow:trace, "debug this", "find the root cause", "why is this failing", "this test is broken".
allowed-tools: Read, Bash(git:*), Bash(npm:*), Bash(pnpm:*), Glob, Grep, Agent
argument-hint: "<bug description or failing test name>"
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [debugging, root-cause, systematic, multi-agent]
---

# Trace

Root cause, not symptom. Never patch over a bug without understanding why it happened.

Dispatcher and reviewer — Opus 4.8 (thinking-tier). Implementer/Searcher/Writer — Sonnet 4.6.

## Per-Step Agent Map (DOCTRINE rule 12)

Every substantive step dispatches at least one Agent. Atomic steps (per DOCTRINE 12.2.8) are a single Worker → Reviewer pair with no independent angles to fan out.

| Step | Status | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 1 — Reproduce | Atomic (12.2.8) | Searcher (Sonnet) | **Reviewer** (Opus) | Runs if repro missing; single Worker→Reviewer pair |
| 2 — Gather evidence | Atomic (12.2.8) | Searcher × 3 (Sonnet) | **Reviewer** (Opus) | 3 parallel Searchers → single Reviewer; one Worker-group→Reviewer pair |
| 3 — Hypothesize | Atomic (12.2.8) | **Debugger** (Opus) | **Reviewer** (Opus) | Single Debugger (5 Whys + ranked hypotheses in one pass) → Reviewer |
| 4 — Verify | 2 sub-phases | Implementer × N (Sonnet) | **Debugger** (Opus) · **Reviewer** (Sonnet) | 4a: parallel Implementers → Sonnet Reviewer; 4b: Debugger re-evaluation → Reviewer |
| 5 — Fix at root | Atomic (12.2.8) | Implementer × N (Sonnet) | **Reviewer** (Opus) | N Implementers (one per file) → Opus Reviewer; single Worker-group→Reviewer pair |
| 6 — Regression test | Atomic (12.2.8) | Writer (Sonnet) | **Reviewer** (Opus) | Single Writer → single Reviewer; no parallel angle |
| 7 — Memory + final | Atomic (12.2.8) | Writer (Sonnet) | **Reviewer** (Opus) | Single Writer → integration Reviewer; no parallel angle |

## Step 1 — Reproduce

Atomic — single Searcher → Reviewer pair (DOCTRINE 12.2.8). No parallel angles: artifact retrieval is a single-scope search when the symptom is unknown.

If the user supplied a stack trace, test name, or log snippet — skip the Worker dispatch entirely (Step 1 is then trivially fulfilled by existing input; proceed to Step 2).

Otherwise dispatch `Searcher — locating bug reproduction in recent changes/tests` (Sonnet).

Collect: failing test name or command, error message, stack trace, log lines, recent commits touching the affected surface.

Then dispatch `**Reviewer** — confirming reproduction is valid` (Opus) with the collected artifacts.

Reviewer confirms:
- The failure is consistent and deterministic (or flags intermittent).
- The error matches the stated symptom.
- The repro is not a test-environment artifact (missing seed data, wrong env vars, clock skew).

If environmental (CI-only, intermittent, time-dependent) — flag explicitly before proceeding to Step 2.

## Step 2 — Gather Evidence

Atomic — one Worker-group (3 parallel Searchers) → single Reviewer pair (DOCTRINE 12.2.8). The three Searchers are parallel angles inside one sub-phase, not independent sub-phases.

Dispatch simultaneously in a single message:
- `Searcher — reading error stack traces and logs` (Sonnet)
- `Searcher — mapping the code paths involved` (Sonnet)
- `Searcher — finding related tests (passing and failing)` (Sonnet)

Each Searcher writes its findings as a structured list: file paths, line numbers, key values, timestamps.

Then dispatch `**Reviewer** — verifying evidence coverage` (Opus) over all three Searcher outputs.

Reviewer confirms the three Searchers actually triangulate the failure surface. If gaps remain (e.g., no log found, code path incomplete), the Reviewer names specific missing angles — re-run the Searcher(s) for those gaps only, then re-run the Reviewer. Repeat until coverage is confirmed.

**Failure recovery:** Searcher tool errors and NEEDS_REVISION verdicts follow DOCTRINE rule 14 (`skills/hyperflow/failure-recovery.md`). For trace specifically, a Searcher that aborts mid-evidence-gathering leaves the debugger with incomplete coverage — flag the gap explicitly in the Step 3 Reviewer output and carry it forward as a known uncertainty in the root-cause synthesis. Do not silently proceed as if evidence is complete.

## Step 3 — Hypothesize

Atomic — single Debugger → Reviewer pair (DOCTRINE 12.2.8). 5 Whys and hypothesis ranking are a single sequential reasoning task; one Debugger call produces both in one pass.

Dispatch `**Debugger** — 5 Whys + hypothesis ranking: <bug-summary>` (Opus).

Single call produces:

**Part A — 5 Whys causal chain** (depth-first):
- Why does this fail? → because X → why X? → because Y → continue to root.
- Goal: reach a structural cause (data contract violation, state mutation, missing guard, timing assumption), not a surface symptom.
- Output: one causal chain ending at the deepest reachable root.

**Part B — Hypothesis fan-out** (using Part A's causal chain):
- Emit 1–3 ranked hypotheses. Each must include:
  - **What** — suspected root cause
  - **Evidence** — what from Step 2 supports it
  - **Counter-evidence** — what would falsify it
  - **Test** — minimal change to verify (used by Step 4)

Then dispatch `**Reviewer** — validating causal chain and hypothesis set` (Sonnet) over the Debugger's output.

Reviewer confirms the causal chain reaches a structural root (not a symptom) and that each hypothesis is independently testable.

## Step 4 — Verify

Two sub-phases (genuine sequential dependency: 4b depends on 4a results; 4b Debugger does substantive re-evaluation work, not a pure review pass).

### Step 4a — Minimal change verification

Workers: `Implementer` × N (Sonnet) parallel, where N = number of hypotheses to test. One Implementer per hypothesis dispatched simultaneously.

- `Implementer — verifying hypothesis 1: <hypothesis-1-test>` — make the minimal change to confirm/falsify
- `Implementer — verifying hypothesis 2: <hypothesis-2-test>` (if applicable)

Each Implementer makes only the change described in the hypothesis's **Test** field from Step 3. No additional cleanup, no reformatting. Run the failing test/command after each change and capture the result.

If only one hypothesis exists — single Implementer is justified (no parallel angle; single-Worker sub-phase per DOCTRINE 12.2.3 single-Worker exception).

Reviewer: `Reviewer — checking verification results are deterministic` (Sonnet) over the Implementer outputs. Confirms each test run is deterministic and the result cleanly maps to a confirm/falsify verdict.

**Failure recovery (4a):** Implementer tool errors and NEEDS_REVISION verdicts follow DOCTRINE rule 14 (`skills/hyperflow/failure-recovery.md`). An Implementer that aborts or cannot confirm/falsify its hypothesis marks that hypothesis `INCONCLUSIVE` — the chain does not abort. Other hypotheses proceed normally; the 4b Debugger receives the full set including any INCONCLUSIVE entries.

### Step 4b — Re-evaluation + loop gate

Worker: `**Debugger** — re-evaluating hypotheses against verification results` (Opus). Substantive reasoning — the Debugger compares hypothesis predictions against actual test outcomes and decides the next branch. Not a pass/fail check: the Debugger may emit `CONFIRMED`, `FALSIFIED ALL`, or `PARTIALLY CONFIRMED` with new directions.

Reviewer: `Reviewer — confirming re-evaluation verdict is sound` (Sonnet) over the Debugger's verdict.

**Failure recovery (4b):** Debugger tool errors and NEEDS_REVISION verdicts follow DOCTRINE rule 14 (`skills/hyperflow/failure-recovery.md`). A failed 4b Debugger dispatch does not abort the chain; retry once, then escalate to thinking-tier. If all attempts fail, mark the entire verify step as `INCONCLUSIVE` and surface to the user — do not advance to Step 5 without a root-cause verdict.

Debugger verdicts:
- `CONFIRMED <hypothesis-N>` → proceed to Step 5 with that hypothesis as the confirmed root cause.
- `FALSIFIED ALL` → loop back to Step 2 with a broader evidence scope.
- `PARTIALLY CONFIRMED` → redispatch Step 4a for the leading candidate with a tighter test.

Revert all minimal changes from 4a before entering Step 5 (the real fix goes in Step 5, not here).

## Step 5 — Fix at Root

Atomic — one Worker-group (N parallel Implementers) → single Opus Reviewer pair (DOCTRINE 12.2.8). N Implementers are parallel angles inside one Worker-group; the Opus Reviewer gates the group output.

Dispatch one Implementer per affected file simultaneously (or one Implementer total if single-file):
- `Implementer — fixing root cause in <file-1>: <change-description>` (Sonnet)
- `Implementer — fixing root cause in <file-2>: <change-description>` (Sonnet, if applicable)

Each Implementer receives: the bug, the verified root cause from Step 4b, the minimal change. No extra refactoring, no opportunistic cleanup — root cause only.

Constraints (non-negotiable):
- No error swallowing
- No defensive try/catch around the symptom
- No flags or feature gates to hide the bug

Then dispatch `**Reviewer** — checking fix is at root` (Opus) over all Implementer outputs.

Reviewer verifies:
- The fix addresses the confirmed root cause from Step 4b, not the symptom.
- No constraint violations (error-swallow, try/catch workaround, feature gate).
- Files changed are internally consistent (no partial fix across N files).

On rejection — loop Step 5 with the Reviewer's specific objection attached. Do NOT commit until Step 5 passes.

## Step 6 — Regression Test

Atomic — single Writer → single Reviewer pair (DOCTRINE 12.2.8). Test authorship has no parallel angle: two Writers would produce duplicate or conflicting tests.

Dispatch `Writer — adding regression test for <bug>` (Sonnet).

The test must:
- Exercise the exact code path that was broken.
- Assert the behavior that was missing (not just assert the fix is present).
- Be named to describe the bug scenario, not the implementation.

Then dispatch `**Reviewer** — confirming regression test fails-without and passes-with the fix` (Opus).

Reviewer process:
1. Mentally (or via Bash) revert the Step 5 fix.
2. Confirm the new test fails in the broken state.
3. Re-apply the fix.
4. Confirm the test passes in the fixed state.

If the test passes both with and without the fix — reject; Writer rewrites. The test must demonstrably distinguish the buggy and fixed states.

If existing suite had coverage gaps that allowed this bug → note for Step 7.

## Step 7 — Memory + Final Review

Atomic — single Writer → single Opus integration Reviewer pair (DOCTRINE 12.2.8). Single-artifact write with no parallel angle; Reviewer covers the full cumulative diff.

Dispatch `Writer — appending pitfall to .hyperflow/memory/pitfalls.md` (Sonnet) per [memory-system.md](references/memory-system.md).

Entry must include:
- The bug pattern (generalized, not project-specific)
- Why existing tests missed it
- Prevention strategy
- Tags: `pitfall` plus domain tags (e.g., `auth`, `async`, `state`)

Then dispatch `**Reviewer** — final validation of fix + test + memory entry` (Opus).

This is the integration review for the entire trace flow. Reviewer assesses the cumulative diff:
- Fix lands at root (not symptom).
- Regression test distinguishes broken vs fixed.
- Memory entry generalizes the pattern correctly.
- No constraint violations introduced anywhere in the chain.

This is the sole Opus integration reviewer for the trace chain. Pass required before hand-off to deploy.

## Anti-Patterns (refuse these)

| Symptom patch | Why it's wrong |
|---|---|
| "Just catch the exception" | Find why it threw |
| "Add a null check" | Find why it was null |
| "Increase the timeout" | Find why it's slow |
| "Retry on failure" | Understand the failure mode first |

## Output Format

```
── Debug Result ─────────────────────
Bug: <one-line>
Reproducible: yes / no / intermittent
Root cause: <one-line>
Fix: <one-line summary>
Files changed: <list>
Regression test: <path>
─────────────────────────────────────
```

End with usage summary (model names, agent count, token totals) per [output-style.md](references/output-style.md).

## Hand-off

Debug is **off the auto-chain** — it's standalone. After Step 7 reviewer passes, stop and suggest `/hyperflow:deploy` to run pre-push gates and commit the fix + regression test together. Do **not** auto-invoke ship — push requires explicit user opt-in.

## Doctrine

Full rules in [DOCTRINE.md](references/DOCTRINE.md). See also [worker-prompt.md](references/worker-prompt.md) and [reviewer-prompt.md](references/reviewer-prompt.md).

**Failure recovery (rule 14).** Worker errors and NEEDS_REVISION verdicts follow the canonical policy in `skills/hyperflow/failure-recovery.md`. For trace, a failed hypothesis test (Step 4) marks the hypothesis `INCONCLUSIVE` rather than aborting the chain — other hypotheses can still resolve the bug. A Searcher abort in Step 2 leaves incomplete evidence; flag the gap in the root-cause synthesis rather than proceeding as if coverage is full.

## Overview

`/hyperflow:trace` is the systematic-debugging skill. It refuses to symptom-patch — every fix starts with reproduction, evidence gathering, hypothesis ranking via Opus Debugger, and verification before any code changes. Three parallel Sonnet searchers triangulate the failure surface; an Opus Debugger applies 5-Whys + hypothesis ranking in one pass; an Opus Reviewer confirms the fix lands at the root and a regression test fails-without / passes-with. Off the auto-chain — standalone.

## Prerequisites

- A reproducible bug (or enough symptom info to reproduce). If unclear, Step 1 dispatches a Searcher to locate the failure.
- Git repository — for diffing recent changes and committing the fix + regression test together.
- Test runner detected in `.hyperflow/testing.md` (vitest/jest/playwright/pytest/etc.) — required for Step 6 regression test.
- `.hyperflow/memory/pitfalls.md` writable — Step 7 appends the learned pattern.

## Instructions

The 7 numbered steps live in [Step 1 — Reproduce](#step-1--reproduce) through [Step 7 — Memory + Final Review](#step-7--memory--final-review) above. Steps 1, 2, 3, 5, 6, 7 are atomic (DOCTRINE 12.2.8). Step 4 has 2 sub-phases (genuine sequential dependency). Summary:

1. **Reproduce** — Atomic. Searcher locates repro artifacts (if needed); Opus Reviewer validates reproducibility. Flag intermittent before proceeding.
2. **Gather evidence** — Atomic. 3 parallel Searchers (logs, code paths, related tests); Opus Reviewer verifies coverage; re-runs specific Searchers if gaps remain.
3. **Hypothesize** — Atomic. Opus Debugger runs 5-Whys causal chain AND fans out 1–3 ranked hypotheses in one call; Sonnet Reviewer validates the causal chain and hypothesis set.
4. **Verify** — 2 sub-phases. 4a: parallel Implementers make minimal change per hypothesis → Sonnet Reviewer confirms determinism. 4b: Opus Debugger re-evaluates against results and emits verdict → Sonnet Reviewer confirms verdict is sound. Loops 4a or proceeds.
5. **Fix at root** — Atomic. Parallel Implementers fix per affected file; Opus Reviewer confirms fix is not a symptom-patch; loops if rejected.
6. **Regression test** — Atomic. Writer adds a test that must fail on broken code; Opus Reviewer confirms fail-without / pass-with; rejects if test is trivially passing.
7. **Memory + final review** — Atomic. Writer appends pitfall pattern to `.hyperflow/memory/pitfalls.md`; Opus Reviewer integration review over the full cumulative diff.

## Output

See [Output Format](#output-format) above for the structured block (Bug, Reproducible, Root cause, Fix, Files changed, Regression test). Ends with usage summary showing the thinking/worker tier split (typically 4-6 Opus + 3-5 Sonnet for a normal trace).

## Error Handling

| Failure | Behavior |
|---|---|
| Cannot reproduce | Step 1 prints `Cannot reproduce — needs more info`; ask user via `AskUserQuestion` for additional repro context. Do NOT proceed to Step 2 with unreliable repro. |
| Intermittent / flaky | Flag explicitly in Step 1 output; ask whether user wants to proceed treating as flake vs investigate root cause. |
| All hypotheses falsified | Loop back to Step 2 with broader evidence collection scope. After 2 full cycles, surface to user: `Cannot localize root cause — need additional traces`. |
| Reviewer says fix is a symptom-patch | Reject and loop back to Step 5 with the Reviewer's feedback. Do NOT commit a symptom-patch. |
| Regression test passes both with and without fix | Reject; Writer rewrites the test. The test must demonstrably distinguish the buggy and fixed states. |
| Test runner missing | Skip Step 6 with explicit warning: `No test runner detected — fix committed without regression test`. Suggest user add one. |

## Examples

### Standard trace — failing test

```
/hyperflow:trace one of my auth tests is failing — find the root cause and fix it

Searcher — locating bug reproduction in recent changes/tests
**Reviewer** — confirming reproduction is valid
Searcher — reading error stack traces and logs
Searcher — mapping the code paths involved
Searcher — finding related tests (passing and failing)
**Reviewer** — verifying evidence coverage
**Debugger** — 5 Whys + hypothesis ranking: auth.test.ts:42 "refresh token rejected"

Hypothesis 1 (likely): refresh token TTL changed in PR #189 but test fixture wasn't updated
Hypothesis 2 (possible): clock skew between test env and JWT issuer

Implementer — verifying hypothesis 1: refresh token TTL
Implementer — verifying hypothesis 2: clock skew check
Reviewer — checking verification results are deterministic
**Debugger** — re-evaluating hypotheses against verification results
Reviewer — confirming re-evaluation verdict is sound
[hypothesis 1 confirmed]

Implementer — fixing root cause: align test fixture TTL with new TOKEN_REFRESH_TTL constant
**Reviewer** — checking fix is at root
Writer — adding regression test for TTL drift
**Reviewer** — confirming regression test fails-without and passes-with the fix
Writer — appending pitfall to .hyperflow/memory/pitfalls.md
**Reviewer** — final validation of fix + test + memory entry

── Debug Result ─────────────────────
Bug: auth.test.ts:42 "refresh token rejected"
Reproducible: yes
Root cause: test fixture TTL hardcoded to old value; not synced with TOKEN_REFRESH_TTL constant
Fix: import TOKEN_REFRESH_TTL into test fixture; remove magic number
Files changed: src/auth/test-fixtures.ts, test/auth/refresh.test.ts
Regression test: test/auth/refresh.test.ts::"TTL constant drift catches stale fixtures"
─────────────────────────────────────
Agents: 4 searcher + 1 implementer + 1 writer (sonnet) · 5 reviewer + 1 debugger (opus)
```

### Refuses symptom-patch request

```
/hyperflow:trace just catch the exception in src/payments/processor.ts

Refusing — trace never patches symptoms. The exception is a signal. Let me find why it throws.

Searcher — reading error stack traces and logs
... (proceeds with full root-cause flow)
```

### Intermittent bug

```
/hyperflow:trace tests pass locally but fail in CI ~30% of the time

Flagged — intermittent. Possible causes: ordering dependency, race condition,
environmental difference, flaky external. Proceeding with extra evidence gathering.

Searcher — reading CI logs vs local logs
Searcher — looking for shared state between test files
...
```

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #12 per-step agents).
- [worker-prompt.md](references/worker-prompt.md) — Sonnet implementer prompt template.
- [reviewer-prompt.md](references/reviewer-prompt.md) — Opus reviewer prompt template.
- [memory-system.md](references/memory-system.md) — pitfall entry format.
- [output-style.md](references/output-style.md) — agent label format + usage summary spec.
