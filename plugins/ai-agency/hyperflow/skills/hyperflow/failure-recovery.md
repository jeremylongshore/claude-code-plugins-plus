# Failure Recovery

Canonical retry / escalate / abort policy for Worker errors and Quality Gate failures. Referenced from [DOCTRINE rule 14](DOCTRINE.md).

## Why this exists

Before this doc, each skill improvised its failure path. Lint failure in deploy might silently retry; Worker OOM in dispatch might hang waiting for output; a malformed Writer response in spec might cascade into a confused Reviewer. Same skill, three different recovery shapes. This file is the single source of truth so every skill behaves the same when things break.

## The taxonomy

Four failure classes, four recovery shapes.

### 1. Worker tool error

The Agent dispatch itself failed: tool crash, OOM, network 5xx, timeout, no output stream.

| Step | Action |
|---|---|
| Attempt 1 fails | Retry once with identical prompt (caches may be cold; transient errors clear) |
| Attempt 2 fails | Escalate tier: dispatch the same role at thinking-tier with `## Prior attempt` block injected — the error message + any partial output |
| Attempt 3 fails | Abort the batch. Print `WORKER_ABORT: <role> · <error-chain>` to the user. Do not advance to the next batch. The chain is in a failed state |

The `## Prior attempt` injection lets the thinking-tier Worker see exactly what went wrong on the worker tier and avoid the same failure mode.

### 2. Worker malformed output

The Agent returned, but the output doesn't match the expected schema: a Writer that returned code instead of prose, a Reviewer that returned a bare verdict without findings, an Implementer that returned a diff for files outside its assigned scope.

| Step | Action |
|---|---|
| Attempt 1 violates | Retry once with `## Violation` block: `Prior attempt produced X; expected Y. Conform to the schema in <prompt section>.` |
| Attempt 2 violates | Escalate tier with same `## Violation` block |
| Attempt 3 violates | Abort. `WORKER_ABORT: <role> · schema violation · <last-violation>` |

### 3. Worker NEEDS_REVISION verdict

Different from an error: the Worker produced valid output, the Reviewer judged it insufficient (incomplete implementation / missed edge case / failing test scaffold).

| Step | Action |
|---|---|
| Reviewer returns NEEDS_REVISION | Retry the Worker once with `## Learnings from review` injection containing the specific findings |
| Second NEEDS_REVISION | Print one-line status: `NEEDS_REVISION × 2 on <sub-task> — surfacing for review`. The chain continues with the latest output marked as `partial`. Do NOT re-dispatch a third time. Do NOT fire AskUserQuestion mid-flight. The end-of-chain concerns report includes the partial sub-task |

NEEDS_REVISION twice usually means the Reviewer's criteria and the Worker's interpretation disagree on something the brief didn't disambiguate. A third Worker dispatch typically loops with the same misunderstanding. Surfacing it is the correct exit.

### 4. Quality Gate failure (Layer 5)

Lint, typecheck, build, tests, security sweep — any gate the deploy skill or the per-batch verification fires.

| Step | Action |
|---|---|
| Gate fails (attempt 1) | Retry the gate once. Caches may be stale (node_modules, .next, tsbuildinfo) |
| Gate still fails | Surface the exact failing command + full stderr to the user. Do NOT proceed to push. Do NOT `--no-verify`, EVER. Do NOT silently call an Implementer to "fix it" without explicit user direction — the user must dispatch the fix as a new task |

The "do not auto-fix" rule is a security rule: a lint failure in a security-related linter (e.g., `eslint-plugin-security` flagging a regex DoS) is exactly the case where a worker silently "fixing" it could mask a real vulnerability. Human-in-the-loop on quality gate failures is non-negotiable.

### 5. Reviewer error

The Reviewer itself errored (tool crash, malformed output, timeout). Treated the same as Worker tool error (class 1): retry once → escalate tier → abort.

If the Reviewer errors after the Worker succeeded, the Worker's output is preserved (do not discard it). The retry / escalated Reviewer reviews the same Worker output. If all Reviewer attempts fail and the abort fires, the chain still has the Worker's output but no verdict — print `REVIEWER_ABORT: <role> · output preserved · no verdict` and surface to the user as a partial result.

## Cross-cutting rules

- **Retry budget per chain.** Each chain has a budget of **3 cumulative aborts** across all batches and sub-phases. After the third abort, the chain itself aborts and prints the full failure trail.
- **Never `--no-verify`.** Quality gates exist for a reason. Bypassing them is a doctrine violation.
- **Never force-push to main/master.** A failure is not a license to overwrite history.
- **Background agent failures.** Background agents follow the same policy but failures are surfaced via `/hyperflow:background show <id>` rather than blocking the foreground chain. Foreground continues; user reviews background state asynchronously.
- **Wall-clock accounting.** Retries count against the chain's wall-clock budget. A chain that retries every Worker once is taking 2× the wall-clock — that should appear in the end-of-chain usage summary so the user can see if there's a systemic issue (network, model degradation, prompt quality).

## What this is NOT

- **NOT a tool for auto-fixing failures.** The orchestrator surfaces failures; the user decides whether to dispatch a fix.
- **NOT a license to swallow errors.** Every aborted dispatch produces a user-visible `WORKER_ABORT` / `REVIEWER_ABORT` line.
- **NOT a replacement for the SECURITY_VIOLATION halt** (DOCTRINE rule 9). Security violations bypass this entire policy and halt the chain immediately with no retries.
- **NOT specific to any skill.** Every skill that dispatches Workers or runs Quality Gates follows this policy.

## Observability

Every retry, escalation, and abort emits exactly one status line in this format — no exceptions. The failure-recovery budget burn is visible in real time, not only at chain end.

**Status-line formats:**

```
[retry 1/3 · <role> · <error-class>]
[escalate → thinking-tier · <role> · <error-class>]
[abort · <role> · <error-class> · chain budget N/3]
```

Where:
- `<role>` — the agent role: Implementer, Searcher, Writer, Reviewer, Classifier, etc.
- `<error-class>` — short error category: `tool-error`, `malformed-output`, `needs-revision`, `gate-failure`, `timeout`, `oom`, `5xx`
- The retry counter (`1/3`, `2/3`) shows position against the per-attempt limit for that failure class
- The abort line's `chain budget N/3` shows how many of the 3 cumulative chain aborts have been consumed

**Examples:**

```
[retry 1/3 · Implementer · tool-error]
[retry 2/3 · Writer · malformed-output]
[escalate → thinking-tier · Searcher · timeout]
[abort · Reviewer · 5xx · chain budget 2/3]
```

The status line fires at the moment of the transition — before the retry or escalation is dispatched, and at the moment of abort. One line per event; no batching of events into a single line.

## Summary table

| Failure class | Attempt 1 | Attempt 2 | Attempt 3 |
|---|---|---|---|
| Worker tool error | Retry | Escalate tier | Abort batch |
| Worker malformed output | Retry with violation note | Escalate tier with violation note | Abort batch |
| Worker NEEDS_REVISION | Retry with learnings | Surface as partial; continue chain | — (no third dispatch) |
| Quality gate failure | Retry (clear caches) | Surface stderr to user; halt push | — |
| Reviewer error | Retry | Escalate tier | Surface partial output, no verdict |
| Security violation | Halt immediately | — | — |

Chain-level: 3 cumulative aborts → chain aborts.
