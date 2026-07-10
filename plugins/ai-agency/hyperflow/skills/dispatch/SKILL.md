---
name: dispatch
description: |
  Use when a task file exists in .hyperflow/tasks/ and workers need dispatching. Fans out parallel workers under per-batch Reviewers, runs a final integration review, and commits per sub-task. Endpoint of the auto-chain — no auto-deploy.
  Trigger with /hyperflow:dispatch, "run the plan", "execute the task", "build it", "run the batches".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*), Bash(grep:*), Bash(rm:*), Bash(bash:*), Bash(python3:*), Agent, Skill, AskUserQuestion
argument-hint: "[task-file | handoff-slug] [session=one|two] [--phases=all|next] [--from-batch N] [--final-only] [--thorough]"
version: 3.2.0
license: MIT
compatibility: Designed for Claude Code
tags: [execution, parallel, review, multi-agent, orchestration]
---

# Dispatch

Workhorse phase. Picks up a task file from `/hyperflow:plan` and runs it through the orchestrator pattern with parallel worker dispatch and multi-level reviews.

This skill exercises **Layer 3 (Orchestrator)**, **Layer 5 (Quality Gates)**, **Layer 6 (Project Memory)**, **Layer 8 (Git Workflow)**, and **Layer 9 (Security)** from the doctrine. Multi-level review (L1–L5) is applied per the triage's flow profile.

## Per-Step Agent Map (DOCTRINE rule 12 — §12.1 inline-allowed for trivial steps · §12.2 sub-phase decomposition)

Every substantive step dispatches at least one Agent. Trivial steps (≤ 2 tool calls, no content generation, no decision-making, mechanically verifiable) MAY be performed inline by the orchestrator per §12.1. Non-trivial steps decompose into ≥ 2 named sub-phases per §12.2.

| Step | Sub-phase | Workers | Reviewer | Notes |
|---|---|---|---|---|
| 0 — Mode confirm | — (exempt) | — | — | `AskUserQuestion` only |
| 0.5 — Operational choices | — (exempt) | — | — | `AskUserQuestion` only |
| 1 — Load task | — (atomic · §12.2.8) | — | — | Read + schema check = single mechanical decision; no parallel angles |
| 2a — Pre-dispatch | Composer × N parallel — one per sub-task; stitches persona + injects learnings | **Reviewer** — reviews prompt set for completeness | Parallel worker prompts built before any fan-out fires |
| 2b — Worker fan-out | Implementer / Searcher / Writer × N parallel | **Domain specialist Reviewer** — the `Specialist:`-matched agent, batched over full batch (P2) or per-sub-task fallback | One Reviewer call per batch; security/correctness specialists run with `--thorough` |
| 2c — Gate run | Worker — runs lint/typecheck/tests on affected files | **Reviewer** — judges gate output | Small focused diff |
| 2d — Learnings + commit | Writer — synthesizes per-batch learnings | — (mechanical commit · §12.1) | Per-sub-task PASS commits land here; learnings appended to context |
| 3 — Final integration review | — (atomic · §12.2.8) | **Reviewer** — broadest matching specialist(s), L1–L<n> over full diff | Single Reviewer dispatch; skipped under D7 incl. single-specialist coverage (rule 17) |
| 4 — Wrap up | Writer — optional; only if memory prose is non-trivial | — | §12.1 trivial-inline; no Reviewer (D5) |
| 5 — End of chain | — (exempt) | — | ONE `AskUserQuestion` with audit + deploy questions |

Iron rule — `review agents ≥ batches + 1` (one batched Reviewer per batch + final integration when not skipped). The batched Reviewer counts as 1 per batch regardless of how many sub-tasks are in the batch. If less, a per-step reviewer was skipped.

## Review Levels (scale by flow profile)

Every batch reviewer and the final integration reviewer uses the level set below. Profile comes from `/hyperflow:plan` triage and is propagated via the chain args (`triage=`).

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
| Session context | Step 0, resolved (not asked) | inherited `session=` / handoff `HANDOFF.md` / default `one` |
| Phase-dispatch scope | Step 1.5, feature mode with ≥ 2 incomplete phases | `AskUserQuestion` — all phases / phase by phase |
| Inter-batch (manual mode only) | After each batch's gates pass | `AskUserQuestion` — continue / stop. **Auto mode fires NO inter-batch question** — see DOCTRINE rule 8 (invented gates banned). |
| Hard halt | Any `SECURITY_VIOLATION` from a reviewer | Stop the chain, surface the finding |
| **Audit prompt** | Step 5, after wrap-up | `AskUserQuestion` — run `/hyperflow:audit`? (yes/no, recommended toggles with flow profile) |
| **Deploy prompt** | Step 5, after audit gate | `AskUserQuestion` — run `/hyperflow:deploy`? (yes/no, recommended toggles with gate state) |

## Inputs

- **Task artefact** — positional arg (slug or path): either a flat `.hyperflow/tasks/<slug>.md` **or** a feature folder `.hyperflow/features/<slug>/` (see [`../hyperflow/feature-phases.md`](../hyperflow/feature-phases.md)). Default — the most-recently-modified of either.
- **Handoff package** — a positional slug/path resolving to `.hyperflow-handoff/<slug>/` (see [`../hyperflow/session-handoff.md`](../hyperflow/session-handoff.md)). When present, dispatch is a **second-session build**: it rehydrates `artefact/` into `.hyperflow/` (Step 1.0) and reads `session`/`handoff`/chain args from `HANDOFF.md`. `on_complete` (review|deploy) governs Step 5.
- **`session=<one|two>`** — passed in by `/hyperflow:plan` (or read from a handoff package's `HANDOFF.md`). If absent, assume `one`. In a two-session build, `handoff=<review|deploy>` governs the end-of-build behavior at Step 5.
- **`--from-batch <n>`** — resume from a specific batch (skip prior batches).
- **`--final-only`** — skip batch dispatch, run only the final integration review.
- **`--thorough`** — disable P2 batched reviews; fall back to per-sub-task reviewers for every sub-task in every batch, and always run the final integration review (D7 skip is disabled). Use when belt-and-suspenders depth is required on a high-risk run. P3 (concurrent pre-conditions) and P5 (lean worker prompts) remain on. When `--thorough` is passed, BOTH D5 (wrap-up Reviewer drop) and D7 (integration review skip) are disabled — the full pre-round-2 ceremony runs. D2 combined gate stays (no quality tradeoff), D6 default L1-L2 stays (cap can still be elevated by triage flags).

## Flow

### Step 0 — Resolve session context (only if invoked directly)

Dispatch is the **build endpoint** — it is on the far side of the planning→build split, so it does **not** ask the one/two-session question (that decision is made upstream at spec/scope, or carried inside a handoff package). It resolves the session context instead:

- A `session=<one|two>` arg was propagated (from scope) → use it.
- Invoked directly on a **handoff package** (slug resolving to `.hyperflow-handoff/<slug>/`) → read `session`/`handoff`/chain args from its `HANDOFF.md`; this is a second-session build (see [`../hyperflow/session-handoff.md`](../hyperflow/session-handoff.md)).
- Invoked directly on a plain task file with no `session=` arg → default `session=one` (build here, then offer the audit/deploy gates at Step 5). No session question fires — there is nothing left to split.

### Step 0.5 — Operational Choices (STRUCTURAL GATE · fires immediately after Step 0)

When operational args (`commit=`, `branch=`, `push=`) were NOT already propagated from a prior chain-starter or a handoff package, fire ONE `AskUserQuestion` call with 3 questions covering every operational decision dispatch needs. After this batch, dispatch runs silently until the end-of-chain audit + deploy gates.

Skip when operational args are already propagated (re-asking is an invented-gate violation).

Dispatch owns this gate (plan no longer asks operational choices at startup — it stops at a build-location gate and lets dispatch decide commit/branch/push when a build actually starts). The 3 questions are **commit cadence · branch behaviour · push at end**, with the canonical option text, recommended-default logic, the `Per-task (deferred)` queue behaviour, and the `commit=/branch=/push=` propagation contract in [`../hyperflow/git-workflow.md`](../hyperflow/git-workflow.md). Recommended defaults: commit `Per-task` (unless `complexity=low ∧ sub-tasks≤2` → `Single`); branch `Create` on main/master else `Stay`; push `Ask at deploy gate` always. Skip only when the args are already propagated (re-asking is an invented-gate violation).

### Step 1.0 — Handoff rehydration (handoff pickup only)

When invoked on a handoff package (`.hyperflow-handoff/<slug>/`), before loading the task:
1. Read `HANDOFF.md` → artefact type, chain args (`commit=/branch=/push=/triage=/mode=`, plus `gh_issue=/pr=/comment=` when the plan was GitHub-native), `on_complete`.
2. If the `.hyperflow/` cache is absent → run `/hyperflow:scaffold` first (so workers get Layer-0 context). If scaffold cannot run here, fall back to the package's `context/` copies.
3. Copy `artefact/tasks/<slug>.md` → `.hyperflow/tasks/<slug>.md` (flat), or `artefact/features/<slug>/` → `.hyperflow/features/<slug>/` (feature), if not already present locally.
4. Leave `STATUS=planned` until the build completes (Step 5 flips it).

Then continue Step 1 normally. (Non-handoff runs skip Step 1.0.)

### Step 1 — Load the task (atomic · §12.2.8)

Detect the artefact mode:
- **Flat** — `.hyperflow/tasks/<slug>.md` (the terse roster). Read it; extract batches, sub-tasks, flow-profile, and operational args. For each roster line carrying a `Brief: <slug>/T<id>.md` pointer, note the brief path — Step 2a loads it verbatim (do not inline its body here).
- **Feature (multi-phase)** — `.hyperflow/features/<slug>/`. Read `feature.md` for the **ordered phase roster** +
  dependency graph + `Specialists`. Each `phase-<n>-<name>/` is executed **as if it were a task file**: its
  `phase.md` carries the batch/task roster and its `tasks/T*.md` are the sub-tasks. Also read each phase's `spec.md`
  / `research.md` (when present) and inject them as the phase's design context into Step 2a Composers.

Confirm structural completeness: batches/tasks non-empty, each task has `id`, `title`, `files`, `complexity`,
`Specialist`. If absent or malformed, stop and suggest `/hyperflow:plan` first.

> Atomic-exempt per §12.2.8 — file/folder existence + schema validation is a single mechanical decision with no parallel angles. No Worker or Reviewer dispatched.

### Step 1.5 — Phase loop (feature mode only)

**Phase-dispatch scope gate (STRUCTURAL GATE · feature mode, ≥ 2 incomplete phases).** Before the loop, fire ONE `AskUserQuestion` — a named-workflow choice, so the recommended option goes first with `(Recommended)`:

```
This feature has <N> phases. How should I build them?

  All phases (Recommended)  — build every phase in order, straight through to the end.

  Phase by phase            — build only the NEXT phase, then stop so you can review it
                              before the next one starts. Re-run /hyperflow:dispatch
                              <slug> to continue with the following phase.
```

Skip the gate (default `all`) when: only one phase is incomplete; `--phases=all|next` was passed; or this is an `on_complete=deploy` two-session build (fully autonomous — `all`). Portable surface without popup (Codex / OpenCode / Grok) → `Hyperflow Question` chat-block fallback; no channel at all → default `All phases`. Propagate the choice as `--phases=<all|next>`.

In **feature mode**, Step 2 runs **once per phase, in roster order**. A phase does not start until its `Depends on`
phase is `completed`. For each phase:
1. Run Step 2 over that phase's batches (parallel inside the phase, exactly as flat mode).
2. On all-tasks-PASS + exit criteria met → set `phase.md` status `completed`, advance `feature.md`'s Phases bar,
   and append the phase's `decisions.md` learnings to `.hyperflow/memory/` (Step 2d learnings synthesis writes here).
3. Run Step 3 (final integration review) **per phase** over that phase's cumulative diff (D7 + single-specialist
   skip apply per phase). After the **last** phase, also run one feature-level integration pass over the full diff
   when ≥ 2 phases touched disjoint surfaces.
4. **If `--phases=next`** — STOP after this phase completes. Print: `Phase <name> done (<k>/<N>). Review it, then run /hyperflow:dispatch <slug> to build the next phase.` Do NOT advance to the next phase. **If `--phases=all`** — continue to the next phase immediately.

In **flat mode**, skip Step 1.5 — Step 2 runs once over the single task file's batches as before.

### Step 2 — For each batch

Print the batch header: `Batch <n> — <one-line description>`.

**Mode resolution (one-time per chain, before Step 2a fires for the first batch):** run `python3 $PLUGIN_ROOT/scripts/resolve-mode.py $PROJECT_ROOT --from-args "$CHAIN_ARGS"` and cache the resulting word (`default` / `lean` / `thorough`). Subsequent batches use the cached value.

Sub-phases 2a–2d run in order for every batch (P1 sequential — each depends on the prior sub-phase's output). Within each sub-phase, Workers are parallel.

#### Step 2a — Pre-dispatch (P1 · sequential after mode resolution)

For each sub-task in the batch, dispatch a Composer Worker in parallel (one Composer per sub-task — N total). Each Composer:
- **Loads the pre-authored brief verbatim when one exists.** If the roster line carries a `Brief: <slug>/T<id>.md` pointer (plan's `briefs=auto` default), read that file and use its body — Task / Why / Scope / Files / Acceptance criteria / Test cases (incl. the E2E case) / Gotchas — as the worker-prompt body **unchanged**. Do NOT re-derive those sections; plan already authored them on the strong model. The Composer's only job is then to *append* context (below). **Fallback (no brief):** trivial sub-task or a legacy terse task file → author the brief inline per [worker-prompt.md](references/worker-prompt.md), the pre-existing behavior. This loader path is what lets dispatch run faithfully on a cheaper model or a second session.
- Selects the worker persona (Implementer / Searcher / Writer) from the sub-task brief.
- Stitches the persona header + Project Context per resolved mode:
  - **mode = default / thorough** → inline excerpts from `.hyperflow/profile.md`, `architecture.md`, `conventions.md` matching the worker's role.
  - **mode = lean** → render the lean Project Context block: a `Project Context (load on demand):` heading + paths to `.hyperflow/memory/session-context.md`, `.hyperflow/profile.md`, `.hyperflow/architecture.md`, `.hyperflow/conventions.md`, `.hyperflow/testing.md`, `.hyperflow/memory/index.md` with one-line descriptions each. Workers read on demand. Saves ~2k tokens × N; same content, lazy access.
- Injects accumulated `Learnings from prior batches` (in all modes).
- Outputs a complete worker prompt ready for fan-out.

Use the [worker-prompt.md](references/worker-prompt.md) template for each Composer output. Persona stitching (top-3), memory injection (all tag matches), and all clarification gates remain unchanged regardless of mode.

Each Composer also reads the sub-task's `Specialist:` field from the task file and stitches that specialist's
**output-contract expectations** ([`../../agents/README.md`](../../agents/README.md)) into the worker prompt, so
workers produce review-ready output for the specialist that will judge it (e.g. an `api-reviewer` sub-task tells the
worker to document status codes + validation up front). It also fills the worker-prompt `{{CONSULT_PEER_HINT}}` slot
from that specialist's `Composes with:` line (the recommended peers); if the line is absent it renders "any
specialist as needed". The hint only ranks peers — the worker may consult any agent in `agents/` ([consultation.md](../hyperflow/consultation.md)).

After all Composers return, dispatch one **Reviewer** over the full prompt set: confirms persona selection is correct, context block is well-formed, learnings are injected. Verdict: `PASS` / `NEEDS_REVISION`. NEEDS_REVISION re-dispatches only the affected Composer(s).

#### Step 2b — Worker fan-out (P1 · sequential after 2a · internal parallelism P1)

Dispatch all N sub-task Workers in a **single message** with parallel `Agent` calls using the composed prompts from Step 2a. Workers are Implementer / Searcher / Writer and run fully in parallel.

When all workers have returned, dispatch **one** batched per-batch **Reviewer** covering the entire batch (P2 — batched single-pass review):
- **Dispatch as the matching domain specialist.** Read the batch's sub-task `Specialist:` fields (Brain-decided, from the task file). Dispatch the per-batch Reviewer **as that specialist agent** ([`../../agents/README.md`](../../agents/README.md)) — its charter + strict checklist + output contract injected on top of `reviewer-prompt-batched.md`. When the batch spans several surfaces, inject the **union** of the matching charters. On a gated flow the specialist runs its web-research-first pass ([web-research.md](../hyperflow/web-research.md)) before the verdict.
- **Check level-cap homogeneity first.** If every sub-task shares the same review-level cap → batched review. If any sub-task carries a different cap (rare mixed profile) → fall back to per-sub-task reviewers.
- **Also fall back to per-sub-task reviewers** when `--thorough` was passed.
- **Batched reviewer dispatch:** use [reviewer-prompt-batched.md](../hyperflow/reviewer-prompt-batched.md). Print `**Reviewer** — batched review Batch <n> (L1–L<n>, <k> sub-tasks)`. Returns one verdict per sub-task.
- **Per-sub-task fallback (mixed caps or `--thorough`):** dispatch a separate reviewer per sub-task per [reviewer-prompt.md](references/reviewer-prompt.md). Print `**Reviewer** — reviewing <subtask> (L1–L<n>)`.
- **Per-batch vs final-integration split:** per-batch reviewers are anchored to one batch's diff and catch L1–L<n> issues there. The final integration Reviewer at Step 3 sees the cumulative diff across all batches and catches cross-batch contradictions no single batch-anchored reviewer could see. Running both passes covers more ground than running either alone.

_(Path note: `reviewer-prompt-batched.md` lives in `skills/hyperflow/` because it is a cross-skill template shared across the chain; `reviewer-prompt.md` stays in `dispatch/references/` from prior convention. The asymmetric paths are intentional.)_

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). When a Worker errors out (tool crash, OOM, 5xx, timeout) or returns malformed output: retry → escalate (add a deeper review pass) → abort. After 3 cumulative aborts in the chain, the chain itself aborts and prints the full failure trail.

Parse the per-sub-task verdicts:
- `SECURITY_VIOLATION` — **halt the chain** immediately. Surface the finding; do not commit anything in the batch.
- Worker returned `OVERSIZE: <reason>` with `SUGGESTED-SPLIT:` — do NOT proceed. Dispatch a Planner consultation: `**Planner — mid-flight split** — split <sub-task-id> per Worker's OVERSIZE signal`. Pass the Worker's reason, suggested split, the original brief, and batch context. The Planner returns a final split plan (N new sub-tasks, each `complexity = low | medium`). Remove the original; dispatch the N new sub-tasks as a new sub-batch. The per-batch Reviewer fires after the new sub-batch completes. No user question — splitting an oversized brief is a mechanical reshape.
- Worker (or batched Reviewer) returned `CONSULT: <peer> — <question>` — do NOT mark the sub-task done. Broker per [consultation.md](../hyperflow/consultation.md): resolve `<peer>` to `agents/<name>.md` (any registered agent), dispatch it with the consultation brief (`CONSULT-CONTEXT` + "answer in ≤8 lines, you are consulted not taking over"), then re-dispatch only that Worker/Reviewer with `Consultation answer from <peer>:` injected. Cap 2 consults/worker; a consulted peer may not itself consult (depth-1). If `<peer>` doesn't resolve or errors, fall back to failure-recovery (ESCALATE) — never block. No user question — a consult is a mechanical handoff.
- `NEEDS_FIX` — re-dispatch only that sub-task's Worker with the fix list. After the fix, dispatch a single focused reviewer for just that sub-task (not a full re-batch). Repeat until `PASS` (max 3 retries before re-scoping the sub-task).
- `PASS` — sub-task handed to Step 2d for commit.

#### Step 2c — Gate run (P1 · sequential after 2b verdicts resolve)

After all sub-tasks in the batch have passed review, run **Layer 5 quality gates** (lint / typecheck / tests on affected files) per [quality-gates.md](references/quality-gates.md).

Dispatch one Worker to run the gate commands. Dispatch one **Reviewer** to judge the gate output. Verdict: `PASS` / `NEEDS_FIX`. On NEEDS_FIX the Worker applies fixes (never amending per-sub-task commits — fixes land as small additional commits) and the gate re-runs. Max 3 gate cycles before escalating.

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). When the per-batch Reviewer returns NEEDS_REVISION, retry the Worker once with a `## Learnings from review` injection. A second NEEDS_REVISION surfaces the sub-task as partial; the chain continues with the latest output marked partial — no third Worker dispatch.

#### Step 2d — Learnings + commit (P1 · sequential after 2c PASS)

For each sub-task whose verdict is `PASS`:
- **Commit immediately** per [git-workflow.md](references/git-workflow.md) rule 2 (per-sub-task commit cadence). Stage only the files that sub-task touched. Write a conventional commit (`feat(<scope>): <title>` derived from the task file). One sub-task = one commit. A batch of 3 parallel sub-tasks produces 3 commits, even though they were reviewed in a single batched Reviewer call.
- **Update the task file's `## Status` block** after each commit lands: tick `[ ]` → `[x]`, increment `Sub-tasks: <done>/<total>`, add tokens to `Tokens used:` running totals, refresh `Wall-clock:` and `Last update:`, recompute `ETA:` once ≥3 sub-tasks are done. This is what `/hyperflow:status` reads for live progress.

Dispatch one Writer in parallel to synthesize per-batch learnings from all Worker outputs and the Reviewer's notes. The learnings are appended to the in-memory `Learnings from prior batches` context (injected at Step 2a of subsequent batches). Writer also checks off the batch — in **flat mode** in the task file; in **feature mode** in the current phase's `phase.md` task roster (and writes durable learnings to that phase's `decisions.md`).

The two activities (commits + learnings synthesis) run concurrently — the Writer synthesizes while commits land sequentially per the commit cadence arg.

After Step 2d, print a one-line status update — *"Batch 1 done · 9/36 sub-tasks · next: B2 deps"* — then proceed to the next batch immediately. Per DOCTRINE rule 8, "transparency checkpoints" / "midway sanity checks" / "scope re-confirmations" / "cost heads-ups" are banned. The only inter-batch gates are: (a) `SECURITY_VIOLATION` → hard halt; (b) `ESCALATE: <reason>` crossing the irreversibility boundary → fire the escalation gate per [escalation.md](../hyperflow/escalation.md). If none apply, the next batch fires immediately.

### Step 3 — Final Integration Review

**Skip condition (D7):** if ALL of the following hold, skip the final integration review and print `Final integration review skipped — all batches PASSed first try`:
- Every per-batch Reviewer returned PASS on first try (no NEEDS_FIX retries)
- No escalations fired (no `ESCALATE:` markers during Step 2)
- No security flags raised (no triage `security: true` AND no Reviewer security warnings)
- No per-batch Reviewer surfaced `[Important]` out-of-cap notes (via the `reviewer-prompt-batched.md` "Honor the Level Cap" escape hatch — these notes signal a concern the Reviewer wanted to flag but couldn't escalate within the cap; D7 must NOT swallow them)
- **Single-specialist coverage (DOCTRINE rule 17 extension):** one specialist covered the whole changed surface (all batches map to the same responsible specialist). When several specialists touched **disjoint** surfaces, this condition fails — keep the final pass to catch cross-surface contradictions no single anchored specialist could see.

If ANY of these conditions fails, the final integration review runs.

> **Risk note:** the skip is the riskiest D-decision in round 2 — multi-batch cross-interaction bugs could slip. The guard conditions are deliberately strict (first-try PASS + no escalations + no security flags) to keep risk low. Pass `--thorough` to disable the skip and always run the integration review.

> Atomic-exempt per §12.2.8 — this is a single Reviewer dispatch over the cumulative diff with no parallel angles. No sub-phase decomposition warranted.

**Failure recovery:** DOCTRINE rule 14 — [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). If the integration Reviewer errors, retry once with the prior error injected. On a second failure, re-dispatch with the prior error in context. Third failure → abort the integration review; chain completes with a partial integration verdict surfaced to the user.

Dispatch a **Reviewer** over the full changed-file set across every batch (all sub-task commits from Step 2d). Dispatch it **as the broadest matching specialist(s)** from the task file's `Specialists` roster (Brain-decided) — when the diff spans several surfaces, inject the union of their charters so the integration pass carries the right domain lenses. Use the same level cap as the batch reviewers (per flow profile). On a gated flow the specialist runs web-research-first before the verdict.

Print: `**Reviewer** — final integration review (L1–L<n>)`

The integration Reviewer returns a single structured verdict with per-sub-task findings where applicable. This is the one pass that catches cross-batch contradictions — per-batch reviewers are anchored to one batch's diff and cannot see cross-batch integration issues.

Parse the verdict:
- `PASS` → proceed to Step 4.
- `NEEDS_FIX` → re-dispatch only the affected sub-tasks' Workers with the fix list. After fixes land, re-run Step 3 for the updated diff.
- `SECURITY_VIOLATION` → **halt the chain immediately.** Print finding; do not auto-continue.

### Step 4 — Wrap Up

Trivial-eligible per §12.1 (D5 + D9). Wrap-up is mechanical work: delete task file + memory append + chore commit. The per-batch reviewers and final integration review (when not skipped per D7) already validated the substantive changes.

**Nominal path (inline orchestrator):** perform the following directly without an Agent dispatch wrapper:
1. **Flat mode** — delete the completed task file from `.hyperflow/tasks/`. **Feature mode** — set `feature.md`
   status `completed` (do not delete mid-feature); when every phase is `completed`, the feature folder becomes
   eligible for archival to `.hyperflow/archive/features/YYYY-MM/<slug>/` (the session-start archiver moves it).
2. Before appending: `grep -F` the proposed entry's first-line title against `.hyperflow/memory/*.md` files (inline dedup-check — replaces the dropped Reviewer dedup pass). If a match exists, edit the existing entry rather than append a duplicate.
3. Append durable patterns/decisions to `.hyperflow/memory/` per [memory-system.md](references/memory-system.md).
4. Commit the memory + task-file-deletion as a `chore(memory):` commit (separate from the per-sub-task commits from Step 2 — keeping memory writes out of feature commits keeps the diff clean).
5. Print the usage summary per [output-style.md](references/output-style.md).
6. Mark dispatch-end compact readiness by writing `.hyperflow/.dispatch-auto-compact-ready` with the current UTC timestamp. This short-lived marker is consumed by the `PreCompact` hook and is the only signal that allows automatic compaction; do not write it before every sub-task, batch, gate, or partial stop has completed.

**When the Writer dispatch IS required:** if memory append requires non-trivial prose generation (e.g., synthesizing learnings from a multi-batch run with cross-cutting patterns), dispatch `Writer — finalizing dispatch artifacts` for the memory write. At that point the step is no longer §12.1-trivial and the Writer Agent handles it. The chore commit still follows immediately; no Reviewer is dispatched for wrap-up.

> **No wrap-up Reviewer (D5):** the Reviewer that previously sanity-checked the chore commit and memory entries is dropped. Wrap-up is mechanically verifiable — `git status` clean, task file absent, memory file present. The orchestrator's direct observation is sufficient.

### Step 5 — End of build

**Handoff build (second session) — completion marker first.** When this run came from a handoff pickup, before the normal gate: write the completion marker, then branch on `on_complete`:
1. Write `.hyperflow-handoff/<slug>/COMPLETION.md` (built-by provider, base = originating commit from `HANDOFF.md`, head = current `HEAD`, `Diff range = <base>..<head>`, commit count, branch, `Result: built | partial (<done>/<total>)`).
2. Set `STATUS=built`.
3. `git add .hyperflow-handoff/<slug>/` + commit `chore(handoff): build complete <slug>`; if `handoff.autoPush` and `push != never` → push (surface the push command on failure).
4. Branch:
   - **`on_complete=deploy`** → invoke `Skill` with `skill: deploy` (its own push gate applies). Do NOT also fire the audit/deploy `AskUserQuestion` below — `on_complete` already encoded the disposition.
   - **`on_complete=review`** → STOP. Print: `Build complete — committed + pushed (range <base>..<head>). Return to session 1 and run /hyperflow:audit <base>..<head> (or /hyperflow:handoff review <slug>).`

**Normal (single-session) end-of-chain — Audit + Deploy gates.** Dispatch is the endpoint of the auto-chain. Fire ONE `AskUserQuestion` with **both** questions in the `questions[]` array (D2 — combined gate). DOCTRINE rule 8 — structural gates always fire, never silently default. The `AskUserQuestion` tool accepts up to 4 questions per call; this combined gate uses 2 (audit + deploy) — or 3 when the chain is **GitHub-native** (`gh_issue=` chain arg present and `pr=ask`): question [3] is the PR exit below. Do not cram further unrelated questions here; the gate's scope is end-of-chain disposition only. On portable surfaces (Codex / OpenCode / Grok), if the popup UI is unavailable, render the questions in one `Hyperflow Question` chat block and wait for the user's answers.

> **DOCTRINE rule 8 preserved:** every gate question still fires; they just batch into one round-trip instead of two or three. Combined gate cuts human-in-the-loop latency at end-of-chain.

```
?  End-of-chain gates

   [1] Run /hyperflow:audit on the cumulative diff?
       Yes — outside-eye L3 review, independent of per-batch reviewers
       No  — skip; per-batch L1–L<n> reviews were enough

   [2] Run /hyperflow:deploy now? (lint + typecheck + build + tests + security sweep, then asks before push)
       Yes — gates pass · ready to ship
       No  — keep commits local · push manually later

   [3] Open a pull request for this chain?           (GitHub-native chains only — gh_issue= present, pr=ask)
       Yes — push feature branch · gh pr create · Closes #<n>
       No  — keep the branch local · print the gh pr create command
```

Per DOCTRINE rule 8, the gate questions are binary action gates — no `(Recommended)` marker on any option. Two-outcome framing is symmetric; the orchestrator's analysis is reflected in the surrounding status output (gate results, retry counts, security verdict), not in pre-marking the choice.

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
| `/hyperflow:audit` was run and applied fixes through `/hyperflow:plan → :dispatch` | This is the audit fix-gate working as designed. The code is now *better* than before audit. Strong positive signal. |
| Quality gates passed on first try (or after one auto-fix retry) | First-pass green is the happy path. |
| Single-batch dispatch with no escalations | Simpler runs trend cleaner, not more suspect. |
| Many sub-tasks (e.g. 27 commits) without any of the concrete-signal failures above | Volume is not a risk signal on its own. |

The orchestrator is not the user's risk advisor. The user already saw every reviewer verdict, every gate result, and the audit findings in scrollback. Inventing risk narratives in the recommendation label ("eyeballing the diff before push is prudent") is paternalism, not guidance.

On deploy `Yes` → invoke `Skill` with `skill: deploy`. Deploy has its own push-confirmation gate at its Step 6.

**PR exit (GitHub-native chains only — `gh_issue=<n>` present).** Fires after the deploy answer is processed:

- `pr=ask` (default) → question [3] in the combined gate: `Open a pull request for this chain? Yes / No` (binary, no marker). `pr=auto` → open without asking once the chain's gates passed. `pr=never` → skip; print the ready-to-run `gh pr create` command in the wrap-up instead.
- On PR yes/auto: `git push -u origin <branch>` (never force, never to `main`/`master` directly — the feature branch is the only outbound surface), then `gh pr create` with a conventional title from the dominant commit type and a body of what / why / validation summary + `Closes #<n>`. No AI attribution anywhere in the PR.
- After the PR opens: when `comment=ask`, offer one courtesy comment on issue `#<n>` linking the PR; `comment=never` skips silently. One batched comment — never incremental updates.
- `gh` unauthenticated or push rejected → print the exact recovery commands (`gh auth login`, `git push -u origin <branch>`, `gh pr create …`) and stop cleanly. Never half-post.

On `No` to both gates → stop cleanly. Print one line:

```
Dispatch complete — <n> batches, <m> agents, <p> per-sub-task commits on branch <branch>.
Next: invoke /hyperflow:audit or /hyperflow:deploy manually when ready.
```

The orchestrator does **NOT** auto-invoke audit or deploy. Both gates wait for an explicit user choice. Defaulting silently is a doctrine violation.

## Agent Label Style

No icons, no brackets. Em-dash separator. Bold for Reviewer and Debugger roles:

```
Implementer — creating auth middleware
Searcher — finding related test files
Writer — generating API documentation
**Reviewer** — reviewing auth middleware output
**Debugger** — investigating test failure in auth.test.ts
```

## Operational Args (from Scope Step 0.5 pre-elections)

Scope batches three operational pre-elections at its Step 0.5 (`commit`/`branch`/`push`) and propagates them as chain args (or, in two-session mode, embeds them in the handoff package's `HANDOFF.md`); the GitHub-native args (`pr`/`comment`) arrive from `/hyperflow:issue` the same way. Dispatch reads them at Step 1 and honors them without re-asking. Missing args fall back to the indicated defaults.

| Arg | Values | Default | Honored at |
|---|---|---|---|
| `commit` | `per-task` / `per-batch` / `per-task-deferred` / `single` / `none` | `per-task` | Step 2 (commit cadence after each PASS) |
| `branch` | `new` / `current` | `new` if currently on `main` or `master`, else `current` | Step 2 (before first commit) |
| `push` | `ask` / `auto` / `never` | `ask` | Forwarded to Deploy Step 6 via chain args |
| `pr` | `ask` / `auto` / `never` | `ask` | Step 5 PR exit — only meaningful when `gh_issue=<n>` is present (set by `/hyperflow:issue`) |
| `comment` | `ask` / `never` | `ask` | Step 5 PR exit — courtesy comment on the originating issue |

**`commit=per-task`** (default) — commit after every sub-task PASS as the existing flow. Commits land directly on the user's working branch as they happen.
**`commit=per-batch`** — accumulate sub-task changes; commit once per batch after all sub-tasks PASS, with a message rolling up the batch (`feat(<scope>): batch <n> — <one-line summary>`). One per-batch commit per batch.
**`commit=per-task-deferred`** — produce N per-task commits like `per-task`, but **queue them on a private `hyperflow/staging-<chain-id>` branch during the chain** and flush all onto the user's working branch at Step 4 wrap-up. Useful when the user wants no user-visible commits landing mid-chain (atomic cumulative reveal at the end) or wants the crash-safe manifest recovery path. After each sub-task PASS, call `bash $PLUGIN_ROOT/scripts/queue-commit.sh $PROJECT_ROOT $CHAIN_ID "<msg>" <file>...` instead of `git add` + `git commit`. The script auto-creates the staging branch + manifest at first call, runs `git commit` **with hooks enabled** (no `--no-verify` — ever, per DOCTRINE Layer 8), and appends to `.hyperflow/commits-queue/manifest.json`. If a hook rejects a sub-task's commit, the orchestrator surfaces the error and stops; the user fixes and resumes from the affected sub-task. At Step 4 wrap-up, dispatch runs `bash $PLUGIN_ROOT/scripts/flush-commits.sh $PROJECT_ROOT` which fast-forward-merges the staging branch onto the user's branch (every queued commit lands in order, original SHAs preserved, original messages preserved). If the user's branch diverged (manual commits mid-chain on same branch), flush surfaces the error + recovery suggestions (`git rebase` / `git cherry-pick`); staging branch + manifest preserved for manual handling. Crash recovery: `/hyperflow:flush` re-runs the same script against the persisted manifest.

**Trade-off honesty:** hooks fire per sub-task (same load as `per-task` immediate). The deferred mode does NOT skip pre-commit hooks — it never has, and any earlier draft suggesting otherwise was a doctrine violation since corrected. Use this mode for the UX benefit (no user-visible commits until end) and crash-safety (manifest survives session loss); not for hook avoidance.
**`commit=single`** — accumulate all changes; commit once at Step 4 wrap-up with a message rolling up the whole chain (`feat(<scope>): <feature name> · <n> sub-tasks`). One commit total.
**`commit=none`** — never commit during dispatch; leave working tree dirty. Skip the per-sub-task commit step entirely. Print at Step 4: `Working tree intentionally left dirty (commit=none); review and commit manually before deploy.`

**`branch=new`** — at Step 2 before the first commit, if currently on `main` / `master` / `develop`, create `feat/<task-slug>` and switch to it. If already on a feature branch, treat as `branch=current`.
**`branch=current`** — never auto-create. All commits land on whatever branch the orchestrator was invoked on.

**`push=…`** — dispatch does NOT push commits to the user's branch. It only propagates the chosen value to Deploy Step 6 in the chain args; Deploy honors it there. **One carve-out:** the GitHub-native PR exit (Step 5, `gh_issue=` present) pushes the *feature branch* itself before `gh pr create` — that push is the PR's outbound surface, gated by `pr=` (not `push=`), and never targets `main`/`master`.

## Iron Rules

- **Failure recovery (rule 14).** Worker errors, malformed output, NEEDS_REVISION, and gate failures follow the canonical policy in [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Retry → escalate → abort. Chain budget: 3 cumulative aborts.
- Workers never review, never coordinate, never ask the user questions.
- Every batch produces **one** per-batch Reviewer dispatch — batched over all sub-tasks in the batch (P2), or per-sub-task when mixed level caps or `--thorough`. Either way: one Reviewer call per batch in the nominal case.
- Plus **one** final integration Reviewer at the end (Step 3) **when not skipped per D7** — this is the Reviewer that sees the cumulative diff across batches.
- **No wrap-up Reviewer at Step 4 (D5).** Wrap-up is §12.1 trivial — delete task file + memory append + chore commit is mechanical and the orchestrator performs it inline. The previous Reviewer at Step 4 is dropped.
- Therefore — `review agents in usage summary >= batches + 1`. Floor lowered from +2 to +1 per round 2 D5: the wrap-up Reviewer is dropped because wrap-up is §12.1 trivial. If your dispatch run includes a final integration review (conditions for D7 skip not met), the floor adapts: `>= batches + 1` still holds because the integration review is the "+1". If the integration review skips AND all batches pass, `review agents = batches` exactly — which satisfies the floor since the +1 was the integration review that ran implicitly. The batched Reviewer counts as **1** per batch regardless of sub-task count. If less, a per-step reviewer was skipped. The task was done wrong.
- Any `SECURITY_VIOLATION` verdict from the batched Reviewer (or a per-sub-task reviewer) halts the chain immediately — no commits, no auto-continue. Same behavior regardless of whether review is batched or per-sub-task.
- **Usage summary fires ONLY at the very end of the chain — after Step 4 wrap-up. NEVER mid-batch. NEVER after partial sub-task completion.** Printing `── Hyperflow Usage ──` with "B1W1 only" or "<n>/<m> sub-tasks completed" while sub-tasks remain pending is a doctrine violation, not a status update. In `auto` mode, a usage summary is a terminal signal — it means the chain is finished. If you printed one with sub-tasks still pending, the chain is in a broken state.
- **Automatic compact readiness is end-of-dispatch only.** `.hyperflow/.dispatch-auto-compact-ready` is written exactly once after Step 4 wrap-up and the final usage summary. The `PreCompact` hook blocks automatic compaction until this marker exists and is fresh; manual `/compact` still works at any time.
- **Auto mode must complete every sub-task in every batch before producing any summary, transition, or end-of-chain artefact.** "To resume" instructions, partial usage tables, or "stopping here for now" prose are all forbidden in `auto` mode. The only legal terminations mid-chain are: (a) `SECURITY_VIOLATION`, (b) `ESCALATE: <reason>` crossing the irreversibility boundary, (c) a per-sub-task Reviewer returning `NEEDS_FIX` after 3 worker retries with no resolution. If none of those fired and the chain stopped, surface as `ESCALATE: dispatch halted with N/M sub-tasks remaining — root cause unknown` and ask the user — do NOT print a partial usage summary as if the chain ended cleanly.
- **If batch dispatch is interrupted (token exhaustion, runtime crash, manual abort) — leave the task file's Status block intact with the partial `[x]` checkmarks, do NOT print a usage summary, do NOT print "To resume" hand-off instructions.** The user can re-invoke `/hyperflow:dispatch --from-batch <n> <slug>` on their own; the task file already reflects which sub-tasks completed. Hand-off instructions printed by a half-finished chain are themselves the bug — they make the user think the chain self-paused cleanly when it actually broke.

## Doctrine

Full rules in [DOCTRINE.md](../hyperflow/DOCTRINE.md). This skill is the execute phase invoked at the end of `/hyperflow:plan`.

## Overview

`/hyperflow:dispatch` is the workhorse phase — it reads a task file from `/hyperflow:plan` and executes it through the orchestrator pattern.

Parallel workers dispatched in a single message, per-batch Reviewers that send work back with `NEEDS_FIX`, a conditional final integration review (skipped when all batches pass first-try with no escalations), inline wrap-up, and (at the end of the auto-chain) ONE combined `AskUserQuestion` gate with both audit and deploy questions.

Doctrine floor: review agents ≥ batches + 1 (per-batch reviewer + final integration when not skipped per D7; wrap-up Reviewer dropped per D5 / §12.1).

## Prerequisites

- A task file exists at `.hyperflow/tasks/<slug>.md` (produced by `/hyperflow:plan`).
- `.hyperflow/profile.md`, `architecture.md`, `conventions.md` populated (Layer 0 context injected into worker prompts).
- Git repository for per-sub-task commits.
- For Step 5: `AskUserQuestion` popup available, or Codex chat fallback available — required for audit + deploy gates. Headless mode with no interactive channel skips gates with explicit warning.

## Instructions

The numbered steps live in [Step 0 — Choose mode](#step-0--choose-mode-only-if-invoked-directly--structural-gate) through [Step 5 — End of Auto-Chain](#step-5--end-of-auto-chain--audit--deploy-gates) above. Summary:

1. Resolve session context (inherited `session=` / handoff `HANDOFF.md` / default `one`) — dispatch is the build endpoint, no session question.
2. Load task file from `.hyperflow/tasks/` — Read + schema check inline (atomic · §12.2.8).
3. Per batch, run four sub-phases in sequence:
   - **Step 2a** — Composer Workers in parallel build worker prompts; Reviewer confirms prompt set.
   - **Step 2b** — Worker fan-out (N parallel Workers); batched Reviewer over the batch; parse verdicts (PASS / NEEDS_FIX / SECURITY_VIOLATION / OVERSIZE).
   - **Step 2c** — Layer 5 quality gates via a Worker + Reviewer.
   - **Step 2d** — Per-sub-task commits + learnings synthesis via Writer.
4. Final integration review — conditional (D7): skip if all batches PASSed first try + no escalations + no security flags. Otherwise: Reviewer dispatched over cumulative diff; verdict routes to Step 4 (PASS), re-dispatch (NEEDS_FIX), or halt (SECURITY_VIOLATION). Atomic per §12.2.8.
5. Wrap-up (§12.1 inline) — orchestrator deletes task file + appends memory + makes `chore(memory):` commit, then writes `.hyperflow/.dispatch-auto-compact-ready` after the usage summary. No Reviewer (D5). Writer Agent required only if memory prose generation is non-trivial.
6. ONE combined `AskUserQuestion` gate with both audit and deploy questions — process answers in order.

## Output

Per-batch and per-sub-task agent labels print as they fire (`Implementer — creating auth middleware`, `**Reviewer** — reviewing auth middleware output (L1-L3)`). After the full chain, the usage summary prints:

```
── Hyperflow Usage ──────────────────────
11 agents  206.4k tokens  (5 implementers + 1 writer + 1 searcher + 3 batch reviewers + 1 final)
─────────────────────────────────────────
```

(Wrap-up Reviewer no longer appears per D5. If the integration review skipped per D7, the review agent count equals the batch count exactly.)

Plus the End-of-Chain block listing batches, agents, and per-sub-task commits.

## Error Handling

| Failure | Behavior |
|---|---|
| No task file at `.hyperflow/tasks/` | Stop and suggest `/hyperflow:plan` first. |
| Worker times out or returns nothing | Re-scope the sub-task into smaller pieces; redispatch. Max 2 re-scope attempts before surfacing the failure. |
| Reviewer returns `NEEDS_FIX` | Re-dispatch worker with the fix list. Max 3 retries before surfacing the failure to the user. |
| Reviewer returns `SECURITY_VIOLATION` | **Halt the chain immediately.** Print finding; do not commit, do not auto-continue. User decides remediation. |
| Layer 5 gate failure (lint/typecheck/test) | Worker fix + re-run. Max 3 gate cycles before escalating. |
| Per-sub-task commit fails (hook rejects, conflict) | Stop; surface the hook error. Do NOT use `--no-verify`. Do NOT amend per-sub-task commits. |
| Wrap-up memory append has duplicate entries (detected post-commit) | `git revert HEAD` reverts the chore(memory) commit; orchestrator rewrites and recommits. No Reviewer to catch this inline — `git log` and `git revert` are the recovery path. |
| `AskUserQuestion` popup unavailable (Codex / OpenCode / Grok) | Print audit/deploy as a `Hyperflow Question` chat block and wait for the user's answers. |
| No interactive channel for audit/deploy gates | Print end-of-chain block with `Audit/Deploy gates skipped — interactive mode required`. Do NOT silently auto-invoke either. |
| Thinking-agent count < batches + 1 at end (when integration review ran) | Print explicit doctrine violation warning in usage summary. Suggests a per-step reviewer was skipped. |

## Examples

Worked transcripts moved to [examples.md](references/examples.md) so the SKILL body stays lean. The examples are illustrative — not load-bearing for behaviour. Read the companion file when you want to see end-to-end transcripts.

## Resources

- [DOCTRINE.md](../hyperflow/DOCTRINE.md) — orchestration rules (especially #8 structural gates, #12 per-step agents).
- [worker-prompt.md](references/worker-prompt.md) — implementer/searcher/writer template.
- [reviewer-prompt.md](references/reviewer-prompt.md) — reviewer template (per-sub-task fallback).
- [reviewer-prompt-batched.md](../hyperflow/reviewer-prompt-batched.md) — batched reviewer template (P2).
- [latency-patterns.md](../hyperflow/latency-patterns.md) — P1–P5 latency patterns; P2 dispatch win ~75% reviewer-phase latency.
- [review-levels.md](references/review-levels.md) — L1-L5 checklist.
- [memory-system.md](references/memory-system.md) — wrap-up memory append format.
- [quality-gates.md](references/quality-gates.md) — Layer 5 lint/typecheck/test policy.
- [git-workflow.md](references/git-workflow.md) — per-sub-task commit cadence, no AI attribution.
- [output-style.md](references/output-style.md) — agent label + usage summary format.
