---
name: dispatch
description: |
  Use when a task file exists in .hyperflow/tasks/ and workers need dispatching. Fans out parallel Sonnet workers under per-batch Opus reviewers, runs a final integration review, and commits per sub-task. Endpoint of the auto-chain — no auto-deploy.
  Trigger with /hyperflow:dispatch, "run the plan", "execute the task", "build it", "run the batches".
allowed-tools: Read, Write, Edit, Bash(git:*), Agent, AskUserQuestion
argument-hint: "[task-file] [chain-mode=auto|manual] [--from-batch N] [--final-only] [--thorough]"
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [execution, parallel, review, multi-agent, orchestration]
---

# Dispatch

Workhorse phase. Picks up a task file from `/hyperflow:scope` and runs it through the orchestrator pattern with parallel worker dispatch and thinking-tier reviews.

This skill exercises **Layer 3 (Orchestrator)**, **Layer 5 (Quality Gates)**, **Layer 6 (Project Memory)**, **Layer 8 (Git Workflow)**, and **Layer 9 (Security)** from the doctrine. Multi-level review (L1–L5) is applied per the triage's flow profile.

## Per-Step Agent Map (DOCTRINE rule 12 — §12.1 inline-allowed for trivial steps · §12.2 sub-phase decomposition)

Every substantive step dispatches at least one Agent. Trivial steps (≤ 2 tool calls, no content generation, no decision-making, mechanically verifiable) MAY be performed inline by the orchestrator per §12.1. Non-trivial steps decompose into ≥ 2 named sub-phases per §12.2.

| Step | Sub-phase | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 0 — Mode confirm | — (exempt) | — | — | `AskUserQuestion` only |
| 0.5 — Operational choices | — (exempt) | — | — | `AskUserQuestion` only |
| 1 — Load task | — (atomic · §12.2.8) | — | — | Read + schema check = single mechanical decision; no parallel angles |
| 2a — Pre-dispatch | Composer × N parallel (Sonnet) — one per sub-task; stitches persona + injects learnings | **Reviewer** (Sonnet) — reviews prompt set for completeness | Parallel worker prompts built before any fan-out fires |
| 2b — Worker fan-out | Implementer / Searcher / Writer × N parallel (Sonnet) | **Reviewer** (Sonnet · worker tier) — batched over full batch (P2) or per-sub-task fallback (mixed caps / `--thorough`) | One Reviewer call per batch · escalates to Opus under `--thorough` |
| 2c — Gate run | Worker (Sonnet) — runs lint/typecheck/tests on affected files | **Reviewer** (Sonnet) — judges gate output | Small focused diff; Sonnet sufficient |
| 2d — Learnings + commit | Writer (Sonnet) — synthesizes per-batch learnings | — (mechanical commit · §12.1) | Per-sub-task PASS commits land here; learnings appended to context |
| 3 — Final integration review | — (atomic · §12.2.8) | **Reviewer** (Opus · thinking tier) — L1–L<n> over full diff | Single Reviewer dispatch, no parallel angles; atomic-exempt |
| 4 — Wrap up | Writer (Sonnet) — optional; only if memory prose is non-trivial | — | §12.1 trivial-inline; no Reviewer (D5) |
| 5 — End of chain | — (exempt) | — | ONE `AskUserQuestion` with audit + deploy questions |

Iron rule — `thinking agents ≥ batches + 1` (one batched Reviewer per batch + final integration when not skipped). The batched Reviewer counts as 1 per batch regardless of how many sub-tasks are in the batch. If less, a per-step reviewer was skipped.

## Review Levels (scale by flow profile)

Every batch reviewer and the final integration reviewer uses the level set below. Profile comes from `/hyperflow:spec` triage and is propagated via the `chain-mode` args.

| Profile | Levels | Workers | Reviewers |
|---|---|---|---|
| `fast` | L1 | 1 | inline self-review only |
| `standard` | **L1–L2 default** | 1–2 | 1 per-batch reviewer |
| `deep` | L1–L5 | 3+ | per-batch + final integration |
| `research` | L1–L2 + synthesis | 3+ searchers | inline synthesis |
| `creative` | L1–L3 + UX | 1–2 | 1 reviewer |
| `scientific` | L1–L5 + TDD | 2–3 | per-batch + final |

L1 syntax/format · L2 spec/naming/edges · L3 integration/security · L4 perf/scale · L5 a11y/UX. See [review-levels.md](references/review-levels.md) for the full checklist.

**Default cap is L1-L2.** Triage may flag `security: true` or `integration_risk: true` in its output; when either is set, the cap elevates to L1-L3 for both per-batch and final integration reviewers. Workers do NOT request elevation — only the upstream triage classification can elevate. See `reviewer-prompt-batched.md` — workers must honor the cap passed to them (cap enforcement lives on the reviewer-prompt side).

## Approval Gates

| Gate | When | Format |
|---|---|---|
| Chain mode | Step 0, only if invoked directly | `AskUserQuestion` — auto / manual |
| Inter-batch (manual mode only) | After each batch's gates pass | `AskUserQuestion` — continue / stop. **Auto mode fires NO inter-batch question** — see DOCTRINE rule 8 (invented gates banned). |
| Hard halt | Any `SECURITY_VIOLATION` from a reviewer | Stop the chain, surface the finding |
| **Audit prompt** | Step 5, after wrap-up | `AskUserQuestion` — run `/hyperflow:audit`? (yes/no, recommended toggles with flow profile) |
| **Deploy prompt** | Step 5, after audit gate | `AskUserQuestion` — run `/hyperflow:deploy`? (yes/no, recommended toggles with gate state) |

## Inputs

- **Task file** — positional arg (slug or path). Default — most-recently-modified file in `.hyperflow/tasks/`.
- **`chain-mode=<auto|manual>`** — passed in by `/hyperflow:scope`. Controls whether to pause for confirmation after the final integration review. If absent, assume `auto`.
- **`--from-batch <n>`** — resume from a specific batch (skip prior batches).
- **`--final-only`** — skip batch dispatch, run only the final integration review.
- **`--thorough`** — disable P2 batched reviews; fall back to per-sub-task reviewers for every sub-task in every batch. Use when belt-and-suspenders depth is required on a high-risk run. P3 (concurrent pre-conditions) and P5 (lean worker prompts) remain on. When `--thorough` is passed, BOTH D5 (wrap-up Reviewer drop) and D7 (integration review skip) are disabled — the full pre-round-2 ceremony runs. D2 combined gate stays (no quality tradeoff), D6 default L1-L2 stays (cap can still be elevated by triage flags).

## Flow

### Step 0 — Choose mode (only if invoked directly · STRUCTURAL GATE)

This is a **structural gate** per DOCTRINE rule 8. When dispatch is invoked directly (no `chain-mode` arg from `scope`), it MUST fire. "No clarifying questions" / "auto-pilot" / any autonomy directive does NOT skip it. Defaulting silently is a doctrine violation.

If a `chain-mode` arg was passed, skip this step — the chain-starter already asked.

Otherwise, ask via `AskUserQuestion`. Per DOCTRINE rule 8, the recommended option goes first with `(Recommended)`:

```
How should I handle progress through the batches?

  Auto (Recommended)  — run all batches + final review and stop. Print next-step suggestions.
  Manual              — pause between batches and ask before continuing.
```

Wait for the user's answer. Do not proceed without it. If `AskUserQuestion` cannot be presented as a popup, use the Codex fallback: print the same gate as a `Hyperflow Question` chat block with numbered options, then stop and wait for the user's answer. If no interactive channel is available at all, print an error and stop — never silently default.

### Step 0.5 — Operational Choices (auto-mode only · STRUCTURAL GATE · fires immediately after Step 0)

When the user picks `Auto` at Step 0 AND operational args (`commit=`, `branch=`, `push=`) were NOT already propagated from a prior chain-starter, fire ONE `AskUserQuestion` call with 3 questions covering every operational decision dispatch needs. After this batch, dispatch runs silently until the end-of-chain audit + deploy gates.

Skip when `chain-mode=manual` (per-batch pauses cover ops decisions) OR when operational args are already propagated (re-asking is an invented-gate violation).

The 3-question batch is identical to scope Step 0.5 — see [scope/SKILL.md § Step 0.5](../scope/SKILL.md#step-05--operational-choices-auto-mode-only--structural-gate--fires-immediately-after-step-0) for the full question + option text + recommended-default logic + chain-arg propagation contract. Spec, scope, dispatch share one canonical definition; whoever fires first owns the batch, the others see the args propagated and skip.

### Step 1 — Load the task (atomic · §12.2.8)

Read `.hyperflow/tasks/<slug>.md`. Extract batches, sub-tasks, flow-profile, and operational args. Confirm the task file is structurally complete: batches array non-empty, each sub-task has `id`, `title`, `files`, `complexity`. If absent or malformed, stop and suggest `/hyperflow:scope` first.

> Atomic-exempt per §12.2.8 — file existence check + schema validation is a single mechanical decision with no parallel angles. No Worker or Reviewer dispatched.

### Step 2 — For each batch

Print the batch header: `Batch <n> — <one-line description>`.

**Mode resolution (one-time per chain, before Step 2a fires for the first batch):** run `python3 $PLUGIN_ROOT/scripts/resolve-mode.py $PROJECT_ROOT --from-args "$CHAIN_ARGS"` and cache the resulting word (`default` / `lean` / `thorough`). Subsequent batches use the cached value.

Sub-phases 2a–2d run in order for every batch (P1 sequential — each depends on the prior sub-phase's output). Within each sub-phase, Workers are parallel.

#### Step 2a — Pre-dispatch (P1 · sequential after mode resolution)

For each sub-task in the batch, dispatch a Composer Worker in parallel (one Composer per sub-task — N total). Each Composer:
- Selects the worker persona (Implementer / Searcher / Writer) from the sub-task brief.
- Stitches the persona header + Project Context per resolved mode:
  - **mode = default / thorough** → inline excerpts from `.hyperflow/profile.md`, `architecture.md`, `conventions.md` matching the worker's role.
  - **mode = lean** → render the lean Project Context block: a `Project Context (load on demand):` heading + paths to `.hyperflow/memory/session-context.md`, `.hyperflow/profile.md`, `.hyperflow/architecture.md`, `.hyperflow/conventions.md`, `.hyperflow/testing.md`, `.hyperflow/memory/index.md` with one-line descriptions each. Workers read on demand. Saves ~2k tokens × N; same content, lazy access.
- Injects accumulated `Learnings from prior batches` (in all modes).
- Outputs a complete worker prompt ready for fan-out.

Use the [worker-prompt.md](references/worker-prompt.md) template for each Composer output. Persona stitching (top-3), memory injection (all tag matches), and all clarification gates remain unchanged regardless of mode.

After all Composers return, dispatch one **Reviewer** (Sonnet) over the full prompt set: confirms persona selection is correct, context block is well-formed, learnings are injected. Verdict: `PASS` / `NEEDS_REVISION`. NEEDS_REVISION re-dispatches only the affected Composer(s).

#### Step 2b — Worker fan-out (P1 · sequential after 2a · internal parallelism P1)

Dispatch all N sub-task Workers in a **single message** with parallel `Agent` calls using the composed prompts from Step 2a. Workers are Implementer / Searcher / Writer (Sonnet) and run fully in parallel.

When all workers have returned, dispatch **one** batched per-batch **Reviewer** (Sonnet by default — `model: "<resolved-worker>"`) covering the entire batch (P2 — batched single-pass review):
- **Check level-cap homogeneity first.** If every sub-task shares the same review-level cap → batched review. If any sub-task carries a different cap (rare mixed profile) → fall back to per-sub-task reviewers.
- **Also fall back to per-sub-task reviewers** when `--thorough` was passed (reviewers escalate to Opus under `--thorough`).
- **Batched reviewer dispatch:** use [reviewer-prompt-batched.md](../hyperflow/reviewer-prompt-batched.md) with `model: "<resolved-worker>"` (or `"<resolved-thinking>"` under `--thorough`). Print `**Reviewer** (Sonnet) — batched review Batch <n> (L1–L<n>, <k> sub-tasks)`. Returns one verdict per sub-task.
- **Per-sub-task fallback (mixed caps or `--thorough`):** dispatch a separate reviewer per sub-task per [reviewer-prompt.md](references/reviewer-prompt.md). Print `**Reviewer** (Sonnet) — reviewing <subtask> (L1–L<n>)`.
- **Why Sonnet by default:** per-batch reviewers see one batch's diff (typically 2–8 files). L1 (syntax/format) and L2 (spec/naming/edges) are pattern-matching work Sonnet handles at near-Opus quality. The cross-cutting concerns Sonnet might miss (L3+ integration, architectural drift) are exactly what the Opus final integration Reviewer at Step 3 catches over the cumulative diff. Two-tier review covers more ground than two-Opus review at a fraction of the cost.

_(Path note: `reviewer-prompt-batched.md` lives in `skills/hyperflow/` because it is a cross-skill template shared across the chain; `reviewer-prompt.md` stays in `dispatch/references/` from prior convention. The asymmetric paths are intentional.)_

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). When a Worker errors out (tool crash, OOM, 5xx, timeout) or returns malformed output: retry → escalate tier → abort. After 3 cumulative aborts in the chain, the chain itself aborts and prints the full failure trail.

Parse the per-sub-task verdicts:
- `SECURITY_VIOLATION` — **halt the chain** immediately. Surface the finding; do not commit anything in the batch.
- Worker returned `OVERSIZE: <reason>` with `SUGGESTED-SPLIT:` — do NOT proceed. Dispatch a Thinking Lead consultation: `**Thinking Lead — Planner (mid-flight split)** — split <sub-task-id> per Worker's OVERSIZE signal`. Pass the Worker's reason, suggested split, the original brief, and batch context. The Thinking Lead returns a final split plan (N new sub-tasks, each `complexity = low | medium`). Remove the original; dispatch the N new sub-tasks as a new sub-batch. The per-batch Reviewer fires after the new sub-batch completes. No user question — splitting an oversized brief is a mechanical reshape.
- `NEEDS_FIX` — re-dispatch only that sub-task's Worker with the fix list. After the fix, dispatch a single focused reviewer for just that sub-task (not a full re-batch). Repeat until `PASS` (max 3 retries before escalating to a thinking-tier worker).
- `PASS` — sub-task handed to Step 2d for commit.

#### Step 2c — Gate run (P1 · sequential after 2b verdicts resolve)

After all sub-tasks in the batch have passed review, run **Layer 5 quality gates** (lint / typecheck / tests on affected files) per [quality-gates.md](references/quality-gates.md).

Dispatch one Worker (Sonnet) to run the gate commands. Dispatch one **Reviewer** (Sonnet) to judge the gate output. Verdict: `PASS` / `NEEDS_FIX`. On NEEDS_FIX the Worker applies fixes (never amending per-sub-task commits — fixes land as small additional commits) and the gate re-runs. Max 3 gate cycles before escalating.

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). When the per-batch Reviewer returns NEEDS_REVISION, retry the Worker once with a `## Learnings from review` injection. A second NEEDS_REVISION surfaces the sub-task as partial; the chain continues with the latest output marked partial — no third Worker dispatch.

#### Step 2d — Learnings + commit (P1 · sequential after 2c PASS)

For each sub-task whose verdict is `PASS`:
- **Commit immediately** per [git-workflow.md](references/git-workflow.md) rule 2 (per-sub-task commit cadence). Stage only the files that sub-task touched. Write a conventional commit (`feat(<scope>): <title>` derived from the task file). One sub-task = one commit. A batch of 3 parallel sub-tasks produces 3 commits, even though they were reviewed in a single batched Reviewer call.
- **Update the task file's `## Status` block** after each commit lands: tick `[ ]` → `[x]`, increment `Sub-tasks: <done>/<total>`, add tokens to `Tokens used:` running totals, refresh `Wall-clock:` and `Last update:`, recompute `ETA:` once ≥3 sub-tasks are done. This is what `/hyperflow:status` reads for live progress.

Dispatch one Writer (Sonnet) in parallel to synthesize per-batch learnings from all Worker outputs and the Reviewer's notes. The learnings are appended to the in-memory `Learnings from prior batches` context (injected at Step 2a of subsequent batches). Writer also checks off the batch in the task file.

The two activities (commits + learnings synthesis) run concurrently — the Writer synthesizes while commits land sequentially per the commit cadence arg.

After Step 2d, print a one-line status update — *"Batch 1 done · 9/36 sub-tasks · next: B2 deps"* — then proceed to the next batch immediately in `auto` mode. Per DOCTRINE rule 8, "transparency checkpoints" / "midway sanity checks" / "scope re-confirmations" / "cost heads-ups" are banned. The only inter-batch gates are: (a) `chain-mode=manual` → pause and ask before the next batch fires; (b) `SECURITY_VIOLATION` → hard halt; (c) `ESCALATE: <reason>` crossing the irreversibility boundary → fire the escalation gate per [escalation.md](../hyperflow/escalation.md). If none apply, the next batch fires immediately.

### Step 3 — Final Integration Review

**Skip condition (D7):** if ALL of the following hold, skip the final integration review and print `Final integration review skipped — all batches PASSed first try`:
- Every per-batch Reviewer returned PASS on first try (no NEEDS_FIX retries)
- No escalations fired (no `ESCALATE:` markers during Step 2)
- No security flags raised (no triage `security: true` AND no Reviewer security warnings)
- No per-batch Reviewer surfaced `[Important]` out-of-cap notes (via the `reviewer-prompt-batched.md` "Honor the Level Cap" escape hatch — these notes signal a concern the Reviewer wanted to flag but couldn't escalate within the cap; D7 must NOT swallow them)

If ANY of these conditions fails, the final integration review runs.

> **Risk note:** the skip is the riskiest D-decision in round 2 — multi-batch cross-interaction bugs could slip. The guard conditions are deliberately strict (first-try PASS + no escalations + no security flags) to keep risk low. Pass `--thorough` to disable the skip and always run the integration review.

> Atomic-exempt per §12.2.8 — this is a single Reviewer dispatch (Opus over the cumulative diff) with no parallel angles. No sub-phase decomposition warranted.

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). If the Opus integration Reviewer errors, retry once with the prior error injected. On a second failure, re-dispatch with the prior error in context (no higher tier exists — escalation here means re-dispatching Opus with the error visible). Third failure → abort the integration review; chain completes with a partial integration verdict surfaced to the user.

Dispatch a thinking-tier **Reviewer** (`model: "<resolved-thinking>"` — always Opus, regardless of `--thorough`) over the full changed-file set across every batch (all sub-task commits from Step 2d). Use the same level cap as the batch reviewers (per flow profile).

Print: `**Reviewer** (Opus) — final integration review (L1–L<n>)`

The Opus Reviewer returns a single structured verdict with per-sub-task findings where applicable. This is the one pass that catches cross-batch contradictions — Sonnet per-batch reviewers are anchored to one batch's diff and cannot see cross-batch integration issues. Opus tier is mandatory here.

Parse the verdict:
- `PASS` → proceed to Step 4.
- `NEEDS_FIX` → re-dispatch only the affected sub-tasks' Workers with the fix list. After fixes land, re-run Step 3 for the updated diff.
- `SECURITY_VIOLATION` → **halt the chain immediately.** Print finding; do not auto-continue.

### Step 4 — Wrap Up

Trivial-eligible per §12.1 (D5 + D9). Wrap-up is mechanical work: delete task file + memory append + chore commit. The per-batch reviewers and final integration review (when not skipped per D7) already validated the substantive changes.

**Nominal path (inline orchestrator):** perform the following directly without an Agent dispatch wrapper:
1. Delete the completed task file from `.hyperflow/tasks/`.
2. Before appending: `grep -F` the proposed entry's first-line title against `.hyperflow/memory/*.md` files (inline dedup-check — replaces the dropped Reviewer dedup pass). If a match exists, edit the existing entry rather than append a duplicate.
3. Append durable patterns/decisions to `.hyperflow/memory/` per [memory-system.md](references/memory-system.md).
4. Commit the memory + task-file-deletion as a `chore(memory):` commit (separate from the per-sub-task commits from Step 2 — keeping memory writes out of feature commits keeps the diff clean).
5. Print the usage summary per [output-style.md](references/output-style.md).
6. Mark dispatch-end compact readiness by writing `.hyperflow/.dispatch-auto-compact-ready` with the current UTC timestamp. This short-lived marker is consumed by the `PreCompact` hook and is the only signal that allows automatic compaction; do not write it before every sub-task, batch, gate, or partial stop has completed.

**When the Writer dispatch IS required:** if memory append requires non-trivial prose generation (e.g., synthesizing learnings from a multi-batch run with cross-cutting patterns), dispatch `Writer — finalizing dispatch artifacts` for the memory write. At that point the step is no longer §12.1-trivial and the Writer Agent handles it. The chore commit still follows immediately; no Reviewer is dispatched for wrap-up.

> **No wrap-up Reviewer (D5):** the Reviewer that previously sanity-checked the chore commit and memory entries is dropped. Wrap-up is mechanically verifiable — `git status` clean, task file absent, memory file present. The orchestrator's direct observation is sufficient.

### Step 5 — End of Auto-Chain · Audit + Deploy gates

Dispatch is the endpoint of the auto-chain. Fire ONE `AskUserQuestion` with **both** questions in the `questions[]` array (D2 — combined gate). DOCTRINE rule 8 — structural gates always fire, never silently default. The `AskUserQuestion` tool accepts up to 4 questions per call; this combined gate uses 2 (audit + deploy). Do not cram further unrelated questions here; the gate's scope is end-of-chain disposition only. In Codex, if the popup UI is unavailable, render both questions in one `Hyperflow Question` chat block and wait for the user's answers.

> **DOCTRINE rule 8 preserved:** both questions still fire; they just batch into one round-trip instead of two. Combined gate cuts human-in-the-loop latency by ~half at end-of-chain.

```
?  End-of-chain gates

   [1] Run /hyperflow:audit on the cumulative diff?
       Yes — outside-eye L3 review, independent of per-batch reviewers
       No  — skip; per-batch L1–L<n> reviews were enough

   [2] Run /hyperflow:deploy now? (lint + typecheck + build + tests + security sweep, then asks before push)
       Yes — gates pass · ready to ship
       No  — keep commits local · push manually later
```

Per DOCTRINE rule 8, both questions are binary action gates — no `(Recommended)` marker on either option. Two-outcome framing is symmetric; the orchestrator's analysis is reflected in the surrounding status output (gate results, retry counts, security verdict), not in pre-marking the choice.

**Process answers in order:**

On audit `Yes` → invoke `Skill` with `skill: audit` and `args: "level=3"` (or `level=5` for scientific). Wait for it to finish. Then process the deploy answer.

Then, process the deploy answer. Option labels MUST be one short clause each (≤ 12 words) — never paragraphs of reasoning.

**Internal recommendation signal (used for status framing, NOT for marker):**

The orchestrator still computes whether the chain is in a "green" or "marginal" state — this drives the status line the user reads above the gate, not a `(Recommended)` marker on the options. A chain is **marginal** (and the status line should say so) when one of these *concrete* signals is present:

- A `SECURITY_VIOLATION` was raised (and resolved) during dispatch
- A worker `ESCALATE:` crossed the irreversibility boundary
- ≥ 2 Hyperflow batch-reviewer retries (`NEEDS_FIX` → re-dispatch) for the *same* sub-task — true repeated failure of the Layer 5 quality gates
- A flaky test failure that wasn't conclusively root-caused
- Any reviewer left a `[Critical]` finding unresolved

The following are **NOT** "marginal" signals and MUST NOT flip the recommendation to `No`:

| Signal | Why it's fine |
|---|---|
| Pre-commit hook auto-fixed style (commitlint subject-case, prettier, eslint --fix) | These are commit-time linters at the editor layer, not Hyperflow quality gates. Hooks fixing themselves is normal. |
| `/hyperflow:audit` was run and applied fixes through `/hyperflow:scope → :dispatch` | This is the audit fix-gate working as designed. The code is now *better* than before audit. Strong positive signal. |
| Quality gates passed on first try (or after one auto-fix retry) | First-pass green is the happy path. |
| Single-batch dispatch with no escalations | Simpler runs trend cleaner, not more suspect. |
| Many sub-tasks (e.g. 27 commits) without any of the concrete-signal failures above | Volume is not a risk signal on its own. |

The orchestrator is not the user's risk advisor. The user already saw every reviewer verdict, every gate result, and the audit findings in scrollback. Inventing risk narratives in the recommendation label ("eyeballing the diff before push is prudent") is paternalism, not guidance.

On deploy `Yes` → invoke `Skill` with `skill: deploy`. Deploy has its own push-confirmation gate at its Step 6.

On `No` to both gates → stop cleanly. Print one line:

```
Dispatch complete — <n> batches, <m> agents, <p> per-sub-task commits on branch <branch>.
Next: invoke /hyperflow:audit or /hyperflow:deploy manually when ready.
```

The orchestrator does **NOT** auto-invoke audit or deploy. Both gates wait for an explicit user choice. Defaulting silently is a doctrine violation.

## Agent Label Style

No icons, no brackets. Em-dash separator. Bold for thinking-tier roles:

```
Implementer — creating auth middleware
Searcher — finding related test files
Writer — generating API documentation
**Reviewer** — reviewing auth middleware output
**Debugger** — investigating test failure in auth.test.ts
```

## Operational Args (from Scope Step 2.6 · auto-mode pre-elections)

When `chain-mode=auto`, scope batches three operational pre-elections at its Step 2.6 and propagates them as chain args. Dispatch reads them at Step 1 and honors them without re-asking. Missing args fall back to the indicated defaults.

| Arg | Values | Default | Honored at |
|---|---|---|---|
| `commit` | `per-task` / `per-batch` / `per-task-deferred` / `single` / `none` | `per-task` | Step 2 (commit cadence after each PASS) |
| `branch` | `new` / `current` | `new` if currently on `main` or `master`, else `current` | Step 2 (before first commit) |
| `push` | `ask` / `auto` / `never` | `ask` | Forwarded to Deploy Step 6 via chain args |

**`commit=per-task`** (default) — commit after every sub-task PASS as the existing flow. Commits land directly on the user's working branch as they happen.
**`commit=per-batch`** — accumulate sub-task changes; commit once per batch after all sub-tasks PASS, with a message rolling up the batch (`feat(<scope>): batch <n> — <one-line summary>`). One per-batch commit per batch.
**`commit=per-task-deferred`** — produce N per-task commits like `per-task`, but **queue them on a private `hyperflow/staging-<chain-id>` branch during the chain** and flush all onto the user's working branch at Step 4 wrap-up. Useful when the user wants no user-visible commits landing mid-chain (atomic cumulative reveal at the end) or wants the crash-safe manifest recovery path. After each sub-task PASS, call `bash $PLUGIN_ROOT/scripts/queue-commit.sh $PROJECT_ROOT $CHAIN_ID "<msg>" <file>...` instead of `git add` + `git commit`. The script auto-creates the staging branch + manifest at first call, runs `git commit` **with hooks enabled** (no `--no-verify` — ever, per DOCTRINE Layer 8), and appends to `.hyperflow/commits-queue/manifest.json`. If a hook rejects a sub-task's commit, the orchestrator surfaces the error and stops; the user fixes and resumes from the affected sub-task. At Step 4 wrap-up, dispatch runs `bash $PLUGIN_ROOT/scripts/flush-commits.sh $PROJECT_ROOT` which fast-forward-merges the staging branch onto the user's branch (every queued commit lands in order, original SHAs preserved, original messages preserved). If the user's branch diverged (manual commits mid-chain on same branch), flush surfaces the error + recovery suggestions (`git rebase` / `git cherry-pick`); staging branch + manifest preserved for manual handling. Crash recovery: `/hyperflow:flush` re-runs the same script against the persisted manifest.

**Trade-off honesty:** hooks fire per sub-task (same load as `per-task` immediate). The deferred mode does NOT skip pre-commit hooks — it never has, and any earlier draft suggesting otherwise was a doctrine violation since corrected. Use this mode for the UX benefit (no user-visible commits until end) and crash-safety (manifest survives session loss); not for hook avoidance.
**`commit=single`** — accumulate all changes; commit once at Step 4 wrap-up with a message rolling up the whole chain (`feat(<scope>): <feature name> · <n> sub-tasks`). One commit total.
**`commit=none`** — never commit during dispatch; leave working tree dirty. Skip the per-sub-task commit step entirely. Print at Step 4: `Working tree intentionally left dirty (commit=none); review and commit manually before deploy.`

**`branch=new`** — at Step 2 before the first commit, if currently on `main` / `master` / `develop`, create `feat/<task-slug>` and switch to it. If already on a feature branch, treat as `branch=current`.
**`branch=current`** — never auto-create. All commits land on whatever branch the orchestrator was invoked on.

**`push=…`** — dispatch does NOT push. It only propagates the chosen value to Deploy Step 6 in the chain args. Deploy honors it there.

## Iron Rules

- **Failure recovery (rule 14).** Worker errors, malformed output, NEEDS_REVISION, and gate failures follow the canonical policy in [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Retry → escalate → abort. Chain budget: 3 cumulative aborts.
- Workers never review, never coordinate, never ask the user questions.
- Every batch produces **one** per-batch Reviewer dispatch (Sonnet · worker tier) — batched over all sub-tasks in the batch (P2), or per-sub-task when mixed level caps or `--thorough`. Either way: one Reviewer call per batch in the nominal case. Escalates to Opus under `--thorough`.
- Plus **one** final integration Reviewer at the end (Step 3 · Opus · thinking tier) **when not skipped per D7**. Always Opus regardless of flags — this is the one Reviewer that sees the cumulative diff across batches.
- **No wrap-up Reviewer at Step 4 (D5).** Wrap-up is §12.1 trivial — delete task file + memory append + chore commit is mechanical and the orchestrator performs it inline. The previous Reviewer at Step 4 is dropped.
- Therefore — `thinking agents in usage summary >= batches + 1`. Floor lowered from +2 to +1 per round 2 D5: the wrap-up Reviewer is dropped because wrap-up is §12.1 trivial. If your dispatch run includes a final integration review (conditions for D7 skip not met), the floor adapts: `>= batches + 1` still holds because the integration review is the "+1". If the integration review skips AND all batches pass, `thinking agents = batches` exactly — which satisfies the floor since the +1 was the integration review that ran implicitly. The batched Reviewer counts as **1** per batch regardless of sub-task count. If less, a per-step reviewer was skipped. The task was done wrong.
- Any `SECURITY_VIOLATION` verdict from the batched Reviewer (or a per-sub-task reviewer) halts the chain immediately — no commits, no auto-continue. Same behavior regardless of whether review is batched or per-sub-task.
- **Usage summary fires ONLY at the very end of the chain — after Step 4 wrap-up. NEVER mid-batch. NEVER after partial sub-task completion.** Printing `── Hyperflow Usage ──` with "B1W1 only" or "<n>/<m> sub-tasks completed" while sub-tasks remain pending is a doctrine violation, not a status update. In `auto` mode, a usage summary is a terminal signal — it means the chain is finished. If you printed one with sub-tasks still pending, the chain is in a broken state.
- **Automatic compact readiness is end-of-dispatch only.** `.hyperflow/.dispatch-auto-compact-ready` is written exactly once after Step 4 wrap-up and the final usage summary. The `PreCompact` hook blocks automatic compaction until this marker exists and is fresh; manual `/compact` still works at any time.
- **Auto mode must complete every sub-task in every batch before producing any summary, transition, or end-of-chain artefact.** "To resume" instructions, partial usage tables, or "stopping here for now" prose are all forbidden in `auto` mode. The only legal terminations mid-chain are: (a) `SECURITY_VIOLATION`, (b) `ESCALATE: <reason>` crossing the irreversibility boundary, (c) a per-sub-task Reviewer returning `NEEDS_FIX` after 3 worker retries (escalates to thinking-tier worker; if that also fails, surfaces ESCALATE). If none of those fired and the chain stopped, surface as `ESCALATE: dispatch halted with N/M sub-tasks remaining — root cause unknown` and ask the user — do NOT print a partial usage summary as if the chain ended cleanly.
- **If batch dispatch is interrupted (token exhaustion, runtime crash, manual abort) — leave the task file's Status block intact with the partial `[x]` checkmarks, do NOT print a usage summary, do NOT print "To resume" hand-off instructions.** The user can re-invoke `/hyperflow:dispatch --from-batch <n> <slug>` on their own; the task file already reflects which sub-tasks completed. Hand-off instructions printed by a half-finished chain are themselves the bug — they make the user think the chain self-paused cleanly when it actually broke.

## Doctrine

Full rules in [DOCTRINE.md](references/DOCTRINE.md). This skill is the execute phase invoked at the end of `/hyperflow:scope`.

## Overview

`/hyperflow:dispatch` is the workhorse phase — it reads a task file from `/hyperflow:scope` and executes it through the orchestrator pattern.

Parallel Sonnet workers dispatched in a single message, per-batch Opus reviewers that send work back with `NEEDS_FIX`, a conditional final integration review (skipped when all batches pass first-try with no escalations), inline wrap-up, and (at the end of the auto-chain) ONE combined `AskUserQuestion` gate with both audit and deploy questions.

Doctrine floor: thinking agents ≥ batches + 1 (per-batch reviewer + final integration when not skipped per D7; wrap-up Reviewer dropped per D5 / §12.1).

## Prerequisites

- A task file exists at `.hyperflow/tasks/<slug>.md` (produced by `/hyperflow:scope`).
- `.hyperflow/profile.md`, `architecture.md`, `conventions.md` populated (Layer 0 context injected into worker prompts).
- Model routing config supports both thinking (Opus) and worker (Sonnet) tiers.
- Git repository for per-sub-task commits.
- For Step 5: `AskUserQuestion` popup available, or Codex chat fallback available — required for audit + deploy gates. Headless mode with no interactive channel skips gates with explicit warning.

## Instructions

The numbered steps live in [Step 0 — Choose mode](#step-0--choose-mode-only-if-invoked-directly--structural-gate) through [Step 5 — End of Auto-Chain](#step-5--end-of-auto-chain--audit--deploy-gates) above. Summary:

1. Ask `chain-mode` (auto / manual) if invoked directly — structural gate.
2. Load task file from `.hyperflow/tasks/` — Read + schema check inline (atomic · §12.2.8).
3. Per batch, run four sub-phases in sequence:
   - **Step 2a** — Composer Workers in parallel build worker prompts; Sonnet Reviewer confirms prompt set.
   - **Step 2b** — Worker fan-out (N parallel Workers); batched Sonnet Reviewer over the batch; parse verdicts (PASS / NEEDS_FIX / SECURITY_VIOLATION / OVERSIZE).
   - **Step 2c** — Layer 5 quality gates via a Worker + Sonnet Reviewer.
   - **Step 2d** — Per-sub-task commits + learnings synthesis via Writer.
4. Final integration review — conditional (D7): skip if all batches PASSed first try + no escalations + no security flags. Otherwise: Opus Reviewer dispatched over cumulative diff; verdict routes to Step 4 (PASS), re-dispatch (NEEDS_FIX), or halt (SECURITY_VIOLATION). Atomic per §12.2.8.
5. Wrap-up (§12.1 inline) — orchestrator deletes task file + appends memory + makes `chore(memory):` commit, then writes `.hyperflow/.dispatch-auto-compact-ready` after the usage summary. No Reviewer (D5). Writer Agent required only if memory prose generation is non-trivial.
6. ONE combined `AskUserQuestion` gate with both audit and deploy questions — process answers in order.

## Output

Per-batch and per-sub-task agent labels print as they fire (`Implementer — creating auth middleware`, `**Reviewer** — reviewing auth middleware output (L1-L3)`). After the full chain, the usage summary prints:

```
── Hyperflow Usage ──────────────────────
Thinking (Opus 4.8)     4 agents   52.3k tokens  (3 batch reviewers + 1 final)
Worker   (Sonnet 4.6)   7 agents  154.1k tokens  (5 implementers + 1 writer + 1 searcher)
Total                  11 agents  206.4k tokens
─────────────────────────────────────────
```

(Wrap-up Reviewer no longer appears in the Thinking row per D5. If the integration review skipped per D7, the Thinking count equals the batch count exactly.)

Plus the End-of-Chain block listing batches, agents, and per-sub-task commits.

## Error Handling

| Failure | Behavior |
|---|---|
| No task file at `.hyperflow/tasks/` | Stop and suggest `/hyperflow:scope` first. |
| Worker times out or returns nothing | Re-scope the sub-task into smaller pieces; redispatch. Max 2 re-scope attempts before escalating to a thinking-tier worker. |
| Reviewer returns `NEEDS_FIX` | Re-dispatch worker with the fix list. Max 3 retries before escalating reviewer + worker pair to Opus + Opus. |
| Reviewer returns `SECURITY_VIOLATION` | **Halt the chain immediately.** Print finding; do not commit, do not auto-continue. User decides remediation. |
| Layer 5 gate failure (lint/typecheck/test) | Worker fix + re-run. Max 3 gate cycles before escalating. |
| Per-sub-task commit fails (hook rejects, conflict) | Stop; surface the hook error. Do NOT use `--no-verify`. Do NOT amend per-sub-task commits. |
| Wrap-up memory append has duplicate entries (detected post-commit) | `git revert HEAD` reverts the chore(memory) commit; orchestrator rewrites and recommits. No Reviewer to catch this inline — `git log` and `git revert` are the recovery path. |
| `AskUserQuestion` popup unavailable in Codex | Print audit/deploy as a `Hyperflow Question` chat block and wait for the user's answers. |
| No interactive channel for audit/deploy gates | Print end-of-chain block with `Audit/Deploy gates skipped — interactive mode required`. Do NOT silently auto-invoke either. |
| Thinking-agent count < batches + 1 at end (when integration review ran) | Print explicit doctrine violation warning in usage summary. Suggests a per-step reviewer was skipped. |

## Examples

Worked transcripts moved to [examples.md](references/examples.md) so the SKILL body stays lean. The examples are illustrative — not load-bearing for behaviour. Read the companion file when you want to see end-to-end transcripts.

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #8 structural gates, #12 per-step agents).
- [worker-prompt.md](references/worker-prompt.md) — Sonnet implementer/searcher/writer template.
- [reviewer-prompt.md](references/reviewer-prompt.md) — Opus reviewer template (per-sub-task fallback).
- [reviewer-prompt-batched.md](../hyperflow/reviewer-prompt-batched.md) — Opus batched reviewer template (P2).
- [latency-patterns.md](../spec/references/latency-patterns.md) — P1–P5 latency patterns; P2 dispatch win ~75% reviewer-phase latency.
- [review-levels.md](references/review-levels.md) — L1-L5 checklist.
- [memory-system.md](references/memory-system.md) — wrap-up memory append format.
- [quality-gates.md](references/quality-gates.md) — Layer 5 lint/typecheck/test policy.
- [git-workflow.md](references/git-workflow.md) — per-sub-task commit cadence, no AI attribution.
- [output-style.md](references/output-style.md) — agent label + usage summary format.
