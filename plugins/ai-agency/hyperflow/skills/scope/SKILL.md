---
name: scope
description: |
  Use when the user has a clear-enough task and wants it decomposed into batched worker sub-tasks before any code is written. Writes a task file under .hyperflow/tasks/ and auto-chains into /hyperflow:dispatch.
  Trigger with /hyperflow:scope, "plan this", "decompose this task", "break this down", "write the task file".
allowed-tools: Read, Write, Edit, Bash(git:*), Glob, Grep, AskUserQuestion
argument-hint: "<task description> [chain-mode=auto|manual]"
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [planning, decomposition, task-graph, multi-agent]
---

# Scope

Decompose, don't build. Read-only with respect to source code. The only writes are to `.hyperflow/tasks/`, `.hyperflow/memory/`, and `.hyperflow/specs/`. When the task file is ready, hand off to `dispatch` (auto or with a gate, depending on chain mode).

This skill exercises **Layer 0 (Project Analysis)** for context, **Layer 6 (Project Memory)** for past-learning surfacing, and **Layer 7 (Task Templates)** for decomposition patterns. It also inherits the triage classification from `/hyperflow:spec` to size each batch correctly.

## Iron Rules

- **Failure recovery (rule 14).** Worker errors, malformed output, NEEDS_REVISION, and Reviewer errors follow the canonical policy in [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Retry → escalate → abort. Chain budget: 3 cumulative aborts.

## Per-Step Agent Map (DOCTRINE rule 12 + 12.2)

Every substantive step dispatches at least one Agent per DOCTRINE rule 12. Trivial steps per §12.1 may be performed inline by the orchestrator. Non-trivial Steps decompose into ≥ 2 named sub-phases per DOCTRINE rule 12.2.

| Step | Sub-phase | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 0 — Chain mode | — (atomic) | — | — | `AskUserQuestion` only; 12.2.8-exempt |
| 0.4 — Triage (Classifier + Reviewer) | — (atomic) | Classifier (Sonnet) [if not inherited] | **Triage Reviewer** (Sonnet) [if not inherited + P4 conditions not met] | Skipped entirely when chained from spec (spec's validated triage is canonical); on direct invocation, dispatches its own Classifier then Triage Reviewer; skips Triage Reviewer on P4 conditions; 12.2.8-exempt |
| 0.5 — Ops choices | — (atomic) | — | — | Single `AskUserQuestion` batch; 12.2.8-exempt |
| 1 — Route | — (atomic) | — | — | Single mechanical routing decision; 12.2.8-exempt |
| 2 — Research | 2a + 2b + 2c (P1 parallel) | | | Sub-phase aggregate handed to Step 3 |
| | 2a — Surface mapping | Searcher × 2 (glob discovery + import-graph traversal) | **Reviewer** (Sonnet) | P1; no inter-dependency with 2b/2c |
| | 2b — Semantic indexing | Searcher × 2 (type-system probe + symbol-graph probe) | **Reviewer** (Sonnet) | P1; no inter-dependency with 2a/2c |
| | 2c — Convention scan | Searcher × 1 (test patterns + lint config; single-angle justified: no independent probe angle for config) | **Reviewer** (Sonnet) | P1; single Worker per 12.2.3 exception |
| 2.5 — Clarify | — (atomic) | — | — | At most one `AskUserQuestion`; 12.2.8-exempt |
| 2.6 — Vestigial | — | — | — | Does nothing; number reserved for back-compat |
| 3 — Decompose | 3a + 3b + 3c | | | 3a fires first; 3b/3c parallel after 3a |
| | 3a — Batch graph | — | **Planner** × 1 (Opus; dependency analysis + parallel/sequential mapping; single-angle: canonical aggregation, no independent angle) + **Reviewer** (Sonnet · per-sub-phase: completeness + sane batch boundaries; verdict ∈ {PASS, NEEDS_REVISION, ESCALATE}) | Sequential synthesis; Planner justified single-Worker per 12.2.3; Reviewer required per 12.2.4 |
| | 3b — Complexity sizing | Searcher × 2 (sub-task LOC estimation + subsystem cross-cut check) | **Reviewer** (Sonnet) | Parallel; depends on 3a output |
| | 3c — Acceptance criteria | Writer × 2 (per-sub-task criteria + verification hooks) | **Reviewer** (Sonnet) | Parallel; depends on 3a output; 3b and 3c concurrent |
| 4 — Write task file | 4a + 4b + 4c (P3 concurrent with Step 6) | | | 4a fires first; 4b/4c parallel after 4a |
| | 4a — Status + Goal + Why | Writer × 2 (status block draft + goal/why narrative) | **Reviewer** (Sonnet) | Sequential first sub-phase; anchors 4b/4c |
| | 4b — Scope + Affected files | Writer × 2 (scope-at-a-glance table + affected-file listing) | **Reviewer** (Sonnet) | Parallel; depends on 4a output; runs concurrently with 4c |
| | 4c — Execution plan + Batches + Verification | Writer × 2 (execution plan ASCII + batch checklist) | **Reviewer** (Sonnet) | Parallel; depends on 4a output; runs concurrently with 4b |
| | 4d — Final task-file verification | — | **Reviewer** (Sonnet · per-step) verifies whole task file vs design | Fires after all sub-phases complete; ensures every design requirement maps to ≥1 sub-task and no orphan sub-tasks exist |
| 4+6 — parallel | — | Writer (Step 4) ∥ Writer (Step 6) fire after Step 3 (P3) | — | Concurrent dispatch; both wait on Step 3 aggregate |
| 5 — Output | — (atomic) | — | — | Print only; §12.1-exempt |
| 6 — Memory | — (atomic; single-angle) | Writer (Sonnet) appends to memory files | **Reviewer** (Sonnet) checks duplicates/contradictions | Single Worker → Reviewer with no independent angles; 12.2.8-exempt |
| 7 — Hand off | — (atomic) | — | — | `Skill` tool invocation; §12.1-exempt |

**Latency flags:** `--thorough` disables P1 **in Step 4 only** (sequential Writer-internal section drafts instead of parallel). Step 2 sub-phases (also P1) are NOT affected — they stay parallel under all flag configurations because they are independent reads with no quality tradeoff. P3 (Steps 4 + 6 concurrent) is always on. See [`../spec/references/latency-patterns.md`](../spec/references/latency-patterns.md) for pattern definitions.

## Approval Gates

| Gate | When | Format |
|---|---|---|
| Chain mode | Step 0, only if invoked directly | `AskUserQuestion` — auto / manual |
| Decomposition sanity | Step 4, after writing the task file | Print the batch summary; user reads it |
| Phase advance (if `manual` mode) | Step 7, before invoking `dispatch` | `AskUserQuestion` — continue / stop |

## Flow

### Step 0 — Choose chain mode (FIRST tool call · STRUCTURAL GATE)

This is a **structural gate** per DOCTRINE rule 8. It MUST fire every time the skill is invoked directly. "No clarifying questions" / "auto-pilot" / "always-on" / any other autonomy directive does NOT skip it. Defaulting to `auto` without asking is a doctrine violation.

**Latency arg:** `--thorough` (or `depth=max`) disables P1 **in Step 4 only** (sequential Writer-internal section drafts instead of parallel). The Step 2 parallel Searchers are NOT affected — they stay parallel under all flag configurations because they are independent reads with no quality tradeoff. P3 (Step 4 + Step 6 concurrent dispatch) stays on always. If the user passes `--thorough`, note it and apply to Step 4 dispatch only.

If invoked with a `chain-mode=<auto|manual>` arg (from `/hyperflow:spec` or a prior skill), skip this step — the previous chain-starter already asked.

Otherwise, **before research**, ask via `AskUserQuestion`. Per DOCTRINE rule 8, the recommended option goes first with `(Recommended)`:

```
How should I advance through the chain after this phase?

  Auto (Recommended)  — chain forward through scope → dispatch with no gate.
                        Fewer interruptions, faster end-to-end.

  Manual              — pause between phases and ask before advancing.
                        More control, more confirmations.
```

Wait for the user's answer. Do not proceed without it. Save the chosen mode and propagate via `args: "chain-mode=<mode>"` when invoking dispatch.

If the agent cannot present `AskUserQuestion` as a popup, use the Codex fallback: print the same gate as a `Hyperflow Question` chat block with numbered options, then stop and wait for the user's answer. If no interactive channel is available at all, print an error and stop — never silently default.

### Step 0.4 — Triage (Classifier + Reviewer) (DOCTRINE rule 15 · atomic-exempt)

Atomic-exempt: no parallel probe dimension exists. Two distinct paths depending on whether scope is chained from spec or invoked directly.

**Path A — chained from `/hyperflow:spec`:** spec already ran its own Classifier and Triage Reviewer and passed the validated triage JSON via chain args. Scope skips this step entirely — re-classifying a triage that spec already vetted is redundant and wasteful. Print:

```
Triage Reviewer skipped — spec's validated triage inherited via chain args.
```

Then proceed to Step 0.5.

**Path B — invoked directly (no inherited triage in chain args):** scope dispatches its own Classifier first, then (unless P4 conditions apply) validates it with the Triage Reviewer.

1. Dispatch `Classifier — triaging request` (Sonnet). The Classifier produces `{ types[], complexity, risk, scope, ambiguity, flow, personas[] }` JSON mirroring spec Step 1's Classifier output. Persist and propagate forward via chain args as `triage=<base64-json>`.

2. **P4 skip (DOCTRINE §13.P4):** if ALL of the following hold — `triage.complexity == low`, `triage.ambiguity < 0.2`, `triage.scope ∈ {0-file, 1-file}`, `triage.risk != high` — skip the Triage Reviewer entirely and consume the Classifier output as-is. Print:

   ```
   Triage Reviewer skipped (P4: low complexity + low ambiguity + single-file scope). Direct triage consumed.
   ```

   Then proceed to Step 0.5. The mis-classification cost at this confidence tier is bounded by the small-task token budget and falls below the ~2k token Reviewer cost.

3. If any P4 condition fails, dispatch the Triage Reviewer. The Reviewer validates the triage classification (inherited via chain args on Path A, or produced by the Classifier in step 1 on Path B) against:

   1. The user's original request — does the classification reflect what they actually asked for?
   2. `.hyperflow/profile.md` — does the classification match the codebase's tech stack, risk level, and known complexity patterns?

   ```
   **Triage Reviewer** — validating classification against request and project profile
   ```

   Verdict ∈ {`PASS`, `RECLASSIFY`, `ESCALATE`}:

   - **PASS** — consume triage as-is; proceed to Step 0.5.
   - **RECLASSIFY** — Reviewer returns a corrected classification with reasoning. Orchestrator uses the corrected version and prints one line: `Triage reclassified: complexity high → medium · personas added: [security]`. Then proceeds to Step 0.5 with the corrected triage.
   - **ESCALATE** — Reviewer cannot determine the correct classification; the ambiguity surfaces as a clarification question at Step 2.5 (post-research, per DOCTRINE rule 8 post-analysis clarification clause). Proceed to Step 0.5 with the original triage as a provisional fallback — mark it `provisional=true` so Step 3 Planner knows to treat complexity sizing conservatively.

Cost (Path B, non-P4): ~2k tokens for Classifier + ~2k for Triage Reviewer. Catches mis-classifications that would otherwise cascade into the wrong flow profile, wrong personas, and a botched batch graph — silently.

### Step 0.5 — Operational Choices (auto-mode only · STRUCTURAL GATE · fires immediately after Step 0)

When the user picks `Auto` at Step 0 AND operational args (`commit=`, `branch=`, `push=`) were NOT already propagated from a prior chain-starter, fire ONE `AskUserQuestion` call with 3 questions covering every operational decision the chain needs. After this batch, the chain runs silently until the end-of-chain audit + deploy gates — the user is interrupted exactly twice at startup (chain-mode in Step 0, ops in Step 0.5) and then not again until done.

Skip this step when:
- `chain-mode=manual` — manual users review every phase, so operational choices defer to per-phase gates
- Operational args already propagated (`commit=…`, `branch=…`, `push=…` in chain args) — re-asking is an invented-gate violation per DOCTRINE rule 8

The 3-question batch:

```
Commit cadence?
  Per-task (Recommended)   — one commit per sub-task; cleanest bisectable history
  Per-batch                — one commit per batch; tidier branch graph, less granular
  Per-task (deferred)      — queue per-task commits on hyperflow/staging-<id> during chain;
                             flush all onto user's branch at end (atomic cumulative reveal;
                             crash-safe via manifest at .hyperflow/commits-queue/)
  Single                   — one commit at end of chain; smallest log footprint
  None                     — leave dirty working tree; you'll commit manually

Branch behaviour?
  Create feat/<slug> (Recommended on main/master) — new feature branch
  Stay on <current>                                — direct commits on the current branch

Push at end?
  Ask at deploy gate (Recommended) — standard push confirmation after release.sh
  Auto-push                        — push branch + tag without asking at end
  Never                            — always hold local; user pushes manually
```

Recommended defaults adapt:
- Commit: `Per-task` unless triage shows `complexity=low AND sub-tasks<=2` (then `Single` is recommended)
- Branch: `Create` if currently on `main` or `master`; `Stay` otherwise (already on a feature branch)
- Push: `Ask at deploy gate` always — bumping to auto-push without explicit user consent violates DOCTRINE rule 8

Save chosen values and propagate via chain args: `commit=<per-task|per-batch|per-task-deferred|single|none> branch=<new|current> push=<ask|auto|never>`. Dispatch (Step 2) reads commit + branch; deploy (Step 6) reads push.

**On Per-task (deferred):** dispatch routes through `scripts/queue-commit.sh` after each sub-task PASS instead of `git commit` directly. Commits land on a private `hyperflow/staging-<chain-id>` branch with hooks enabled (no `--no-verify`, ever — per DOCTRINE rule 9) and original per-task file scope + messages preserved. At Step 4 wrap-up, `scripts/flush-commits.sh` fast-forward-merges staging onto the user's working branch — every queued commit lands in order with original SHAs preserved. Same N commits as Per-task immediate, just atomic at the end. Crash recovery: `/hyperflow:flush` re-runs the same flush against the persisted `.hyperflow/commits-queue/manifest.json`.

### Step 1 — Route

Pure routing decision — no clarification questions here. Clarification fires at Step 2.5, AFTER research has analyzed the requirement against the codebase.

- Pure design question (the user is asking *should we?* not *how do we?*) → suggest `/hyperflow:spec` instead and stop
- Anything else → proceed to Step 2 (research first, then ask only about what research couldn't resolve)

### Step 2 — Research (3 parallel sub-phases · P1)

All three sub-phases (2a, 2b, 2c) dispatch in a **single message** — they share the same upstream task description and have no inter-dependency. Sub-phase Reviewers are Sonnet. Read `.hyperflow/profile.md`, `architecture.md`, `conventions.md`, and `.hyperflow/memory/index.md` before dispatching to surface relevant past learnings. Step 2 output = union of sub-phase worker outputs + 3 sub-phase Reviewer verdicts, handed to Step 3.

**Step 2a — Surface mapping**

Dispatch in parallel (no dependency):
- `Searcher — glob discovery: enumerate all files touched by the task description`
- `Searcher — import-graph traversal: trace dependency edges from entry points`

Then dispatch `**Reviewer** — verifying surface-mapping coverage` over both Searcher outputs. If gaps remain, redispatch a Searcher targeting the gap.

**Step 2b — Semantic indexing**

Dispatch in parallel (no dependency on 2a):
- `Searcher — type-system probe: enumerate interfaces, types, and schemas relevant to the change`
- `Searcher — symbol-graph probe: locate call sites, re-exports, and aliased references`

Then dispatch `**Reviewer** — verifying semantic coverage` over both Searcher outputs.

**Step 2c — Convention scan**

Single-angle justified: lint config and test pattern files have no independent probe dimension — both are read from fixed config paths. Single Worker per DOCTRINE 12.2.3 exception.

- `Searcher — test patterns and lint config: read test file naming, runner config, lint rules`

Then dispatch `**Reviewer** — verifying convention capture` over the Searcher output.

**P1 rationale:** sub-phases 2a, 2b, 2c are independent siblings — no output feeds another. Firing all three in one message cuts wall-clock to the slowest sub-phase. See [`../spec/references/latency-patterns.md`](../spec/references/latency-patterns.md) §P1.

Note: `--thorough` does NOT affect Step 2. Sub-phases 2a/2b/2c stay parallel under all flag configurations because they are independent reads with no quality tradeoff. `--thorough` only disables P1 internal parallelism in Step 4.

### Step 2.5 — Clarify (post-analysis · max 3)

Only the ambiguities that Step 2 research did NOT resolve become questions. Per DOCTRINE rule 8 (post-analysis clarification clause), clarification stages fire AFTER the orchestrator has read the relevant code and analyzed the requirement — never before.

- If research fully grounded every assumption → skip this step entirely. No question for question's sake.
- If ≥1 ambiguity remains (target file unclear, two equally plausible interfaces, a config the codebase doesn't reveal a precedent for) → fire `AskUserQuestion`, max 3 questions, each tied to a specific finding the Searchers surfaced.
- Frame every question by citing what research found: *"Searcher mapped both `src/auth/middleware.ts` and `src/api/auth/route.ts` — which is the intended target for the new guard?"* — never *"where should the new guard go?"* in the abstract.

The 2-question floor from `/hyperflow:spec` does NOT apply to scope. Scope asks zero questions when research is conclusive; it asks 1-3 when genuine post-analysis ambiguity remains.

### Step 2.6 — Operational Choices (MOVED to Step 0.5)

This step has been moved to Step 0.5 (immediately after Step 0 chain-mode) so operational decisions are batched with the only other startup question — the user is interrupted once at chain start, then the chain runs silently. Step 2.6 is preserved as a NUMBER for backward-reference only; it intentionally does nothing.

If propagation from a prior chain-starter failed and operational args are missing at this point in scope, fall through to Step 3 with default values (`commit=per-task branch=new push=ask`) rather than firing an invented mid-chain gate. The orchestrator MUST NOT fire `AskUserQuestion` here — Step 0.5 is the only correct location for this question batch.

### Step 3 — Decompose (3 sub-phases · 3a sequential then 3b/3c parallel)

Sub-phase 3a fires first — 3b and 3c depend on its output and then run concurrently. Step 3 output = union of sub-phase outputs + 3 sub-phase Reviewer verdicts, handed to Steps 4 and 6.

**Step 3a — Batch graph (sequential first; single-angle justified)**

Single-angle justified: the batch graph is a canonical synthesis from research outputs — no independent angle exists to fan out across. Single Worker per DOCTRINE 12.2.3 exception.

Dispatch `**Planner** — producing batch graph` with the Step 2 aggregate (surface mapping + semantic index + conventions), triage classification, and applicable templates from [task-templates.md](references/task-templates.md) (CRUD Feature, API Endpoint, UI Component, Database Migration, Refactor, Bug Fix — else bespoke).

After the Planner emits the batch graph, dispatch `**Reviewer** — validating decomposition completeness and batch boundaries` over the Planner's output. Reviewer checks: every research finding maps to at least one sub-task; no sub-task spans > 1 subsystem boundary without a split; batch ordering is topologically sound. Verdict ∈ {PASS, NEEDS_REVISION, ESCALATE}. On `NEEDS_REVISION`, redispatch the Planner with Reviewer feedback targeting the specific gaps (not the whole batch graph).

The Planner produces, for each sub-task:
- Worker role — Implementer / Searcher / Writer
- Files to read / modify / create
- Dependencies — parallel vs sequential
- Complexity estimate (drives review level cap downstream)

**Oversize-split mandate (DOCTRINE Layer 3 · Thinking Lead — Planner).** Before finalising the batch graph, the Planner runs a split checklist on every candidate sub-task. Any sub-task that triggers ANY of these signals MUST be split into 2+ smaller sub-tasks (each at `complexity = low | medium`):

| Signal | Threshold |
|---|---|
| File breadth | > 5 files touched |
| Change volume | > 500 LOC of expected changes |
| Subsystem cross-cut | touches 2+ distinct subsystems (auth + UI + DB, frontend + API + migration, …) |
| Complexity tag | `complexity = high` from triage |
| Mixed concerns | one sub-task spans data-model + business-logic + UI + tests |
| Reviewability | a human reviewing the resulting commit would need > 10 minutes to grasp it |

Split target: each resulting sub-task is (a) reviewable in under 10 minutes of human time, (b) fits comfortably in a single Worker prompt + reasonable response, (c) has a single coherent purpose nameable in one conventional-commit subject line. The Planner never keeps `complexity = high` after the checklist — high-complexity work is decomposed until every piece is low/medium.

Splitting is a **cost optimisation**, not just a quality one: three small sub-tasks dispatched to three Sonnet Workers in parallel cost less wall-clock AND less total tokens than one Worker chewing through an oversized brief (parallelism + focused prompts + fewer retries).

**Step 3b — Complexity sizing (parallel with 3c · depends on 3a)**

Dispatch in parallel:
- `Searcher — LOC estimation: estimate change volume per sub-task against the batch graph`
- `Searcher — subsystem cross-cut check: verify each sub-task does not span > 1 subsystem boundary`

Then dispatch `**Reviewer** — validating complexity sizing` over both Searcher outputs. If any sub-task exceeds oversize thresholds and was not already split in 3a, Reviewer returns `NEEDS_REVISION` and 3b re-dispatches targeting the gap (not the whole Step 3).

**Step 3c — Acceptance criteria (parallel with 3b · depends on 3a)**

Dispatch in parallel:
- `Writer — per-sub-task acceptance criteria: one concrete verifiable condition per sub-task`
- `Writer — verification hooks: map each criterion to a test file path or smoke step`

Then dispatch `**Reviewer** — verifying acceptance criteria completeness` over both Writer outputs. `NEEDS_REVISION` re-dispatches 3c only.

### Step 4 — Write Task File (3 sub-phases · P3 concurrent with Step 6)

**P3 — concurrent dispatch:** Step 4 (task file) and Step 6 (memory) are independent after Step 3 completes. Dispatch both in the same message immediately after Step 3 returns. Wait for both before advancing to Step 5.

**Mode resolution (one-time per chain).** Before dispatching, run `python3 $PLUGIN_ROOT/scripts/resolve-mode.py $PROJECT_ROOT --from-args "$CHAIN_ARGS"` and propagate the result via chain args (`mode=<default|lean|thorough>`) to downstream skills. When `mode=lean`, Writers render the **artefact-format minimum template** for small tasks (`triage.complexity == low` AND projected sub-tasks ≤ 5) — status table + Goal + per-task lines + cost table only. The full rich template auto-restores when the task graduates past 5 sub-tasks or any sub-task has `complexity != low`. Persona stitching, memory injection, reviewer model + template, clarification gates, and security blocklist remain unchanged regardless of mode.

Sub-phase 4a fires first to anchor section numbering and the status block. Sub-phases 4b and 4c are independent of each other and run concurrently after 4a. A final per-Step Reviewer verifies the assembled task file vs the full design after all sub-phases complete.

**Step 4a — Status + Goal + Why (sequential first)**

Dispatch in parallel:
- `Writer — status block: emit Status table, branch, commit cadence`
- `Writer — goal and why: draft the Goal one-liner and Why paragraph`

Then dispatch `**Reviewer** — verifying status/goal/why section` over both Writers. These anchoring sections must land before 4b/4c can reference them.

**Step 4b — Scope + Affected files (parallel with 4c · depends on 4a)**

Dispatch in parallel:
- `Writer — scope-at-a-glance table: surface, file counts, risk ratings`
- `Writer — affected-file listing: Created / Modified / Skipped with one-line purpose per path`

Then dispatch `**Reviewer** — verifying scope coverage against Step 2 surface map` over both Writers. `NEEDS_REVISION` re-dispatches 4b only.

**Step 4c — Execution plan + Batches + Verification (parallel with 4b · depends on 4a)**

Disable with `--thorough` (Writers draft sections in sequential passes instead of parallel).

Dispatch in parallel:
- `Writer — execution plan and batches: ASCII batch graph + per-batch task checklist with role, files, complexity`
- `Writer — open questions and verification plan: any unresolved items + concrete smoke/test steps`

Then dispatch `**Reviewer** — verifying execution plan matches Step 3 batch graph` over both Writers. `NEEDS_REVISION` re-dispatches 4c only.

**Step 4 final verify.** After all sub-phases complete, dispatch `**Reviewer** — verifying assembled task file vs design` to confirm every design requirement maps to at least one sub-task and no orphan sub-tasks exist. Writers write to `.hyperflow/tasks/<task-slug>.md` using the template below.

Task-file template — follows [`artefact-format.md`](../hyperflow/artefact-format.md). The Writer applies the full template by default; reduces to the `fast` variant only when triage classifies `complexity=low AND sub-tasks<=2`.

```markdown
# <Name>

## Status

| Field      | Value                                                 |
|------------|-------------------------------------------------------|
| Status     | pending                                               |
| Progress   | `░░░░░░░░░░░░░░░░░░░░`  0 / <total> sub-tasks (0%)    |
| Branch     | `<feat/slug or current branch>`                       |
| Commits    | 0 since main · per-task cadence                       |
| Wall-clock | not started                                           |
| Tokens     | thinking 0k · worker 0k · total 0k                    |

## Goal

<one-line plain-English statement of what shipping this changes>

## Why

<one paragraph: what the user / system sees after this lands; the
single most important constraint the design honors>

## Scope at a glance

| Surface       | Files | Created | Modified | Risk   |
|---------------|------:|--------:|---------:|--------|
| <surface>     |     N |       N |        N | low    |
| **Total**     |  **N**|    **N**|     **N**|        |

## Affected files

**Created (N)**
- `<path>` — <one-line purpose>

**Modified (N)**
- `<path>` — <one-line change>

**Skipped (confirmed N)** *(omit section if N=0)*
- `<path>` — <reason it's not touched>

## Execution plan

```
Batch 1 — <theme>                       (<N> parallel)
  T1 · T2 · T3 · T4
       ↓
Batch 2 — <theme>                       (<N> parallel · depends on Batch 1)
  T5 · T6 · T7
       ↓
Batch 3 — <theme>                       (<N> sequential)
  T8
       ↓
Batch N — Final integration review      (1 sequential)
  T<N>
```

## Batches

### Batch 1 — <theme> (<parallel|sequential>)

- [ ] T1 — <Role> · <one-line task>
       Read: `<file>` · Modify: `<file>` · Complexity: <low|medium|high>
- [ ] T2 — <Role> · <one-line task>
       Create: `<file>` · Complexity: <low|medium|high>

### Batch 2 — <theme> (depends on Batch 1)
...

## Open questions

None. *(or numbered list if any remain)*

## Verification plan

1. <concrete test or smoke step>
2. <concrete test or smoke step>

## Estimated cost

| Tier      | Agents | Tokens   |
|-----------|-------:|---------:|
| Thinking  |      N |     ~Nk  |
| Worker    |      N |     ~Nk  |
| **Total** |  **N** | **~Nk**  |
```

The Status block is updated by dispatch after every sub-task PASS — see dispatch/SKILL.md Step 2. Progress bar uses 20 cells: `█` for completed, `░` for pending; percentage rounded to whole number. Wall-clock starts on first worker dispatch; ETA computes once ≥ 3 sub-tasks are done (linear extrapolation from completed mean).

### Step 5 — Output

Print the task file path and batch summary table:

```
Plan ready — .hyperflow/tasks/<slug>.md (3 batches, 7 sub-tasks)
```

### Step 6 — Memory (P3 concurrent with Step 4)

Agents — `Writer` (Sonnet) ⇒ **Reviewer** (Opus).

**P3 — concurrent dispatch:** this step fires in parallel with Step 4 (see Step 4 above). Both Writers receive the Planner's output and are independent — the memory Writer does not need the task file to be written, and the task file Writer does not need memory to be updated. Both must complete before Step 5 output.

1. Dispatch `Writer — appending decisions to .hyperflow/memory/decisions.md` (in parallel with Step 4 Writer — P3). Skip trivial ones. For complex features (3+ files, multiple subsystems) the Writer also produces `.hyperflow/specs/<feature-slug>.md` referenced from the task file.
2. Dispatch `**Reviewer** — checking memory entries` to catch duplicates or contradictions with existing entries before they land in `.hyperflow/memory/`.

**P3 rationale:** the task file and memory entries both derive from the Planner's batch graph but do not depend on each other. Running them concurrently cuts one sequential Writer round-trip from the flow. See [`../spec/references/latency-patterns.md`](../spec/references/latency-patterns.md) §P3.

See [task-tracking.md](references/task-tracking.md) and [worker-prompt.md](references/worker-prompt.md).

### Step 7 — Hand off to `/hyperflow:dispatch`

This step is trivial-inline per §12.1: one Skill tool invocation, no generation, no review needed. The orchestrator invokes the dispatch skill directly without an Agent dispatch wrapper.

**If `chain-mode=auto`** — immediately invoke `Skill` with `skill: dispatch` and `args: "chain-mode=auto <task-slug>"`. Print:

```
Auto-chaining to /hyperflow:dispatch…
```

**If `chain-mode=manual`** — ask via `AskUserQuestion`: "Plan done. Continue to /hyperflow:dispatch?" → yes / no / stop. On yes, invoke `Skill` with `skill: dispatch` and `args: "chain-mode=manual <task-slug>"`.

## Anti-patterns

- Writing implementation code
- Modifying source files outside `.hyperflow/` and `.hyperflow/specs/`
- Skipping the research step
- Single-batch plans for multi-file work
- Omitting the verification plan
- Pausing for "should I execute?" when `chain-mode=auto` — that was already answered at Step 0
- Asking the chain-mode question again when a `chain-mode=<…>` arg was passed in

## Overview

`/hyperflow:scope` decomposes a clear-enough task into a batched worker plan and writes it to `.hyperflow/tasks/<slug>.md`. Parallel Sonnet searchers map the affected surface, an Opus Planner produces the batch graph, and a Sonnet Writer emits the task file. Read-only with respect to source code — only `.hyperflow/tasks/`, `.hyperflow/memory/`, and `.hyperflow/specs/` are written. On completion, auto-chains into `/hyperflow:dispatch` (or asks first if `chain-mode=manual`).

## Prerequisites

- A clear-enough description of what to build. If ambiguous, scope will redirect to `/hyperflow:spec` and stop.
- `.hyperflow/` cache (recommended — improves planning context). Run `/hyperflow:scaffold` first if missing.
- Optional: prior `/hyperflow:spec` output passed via `chain-mode` arg propagates triage classification and recommended flow profile.

## Instructions

The numbered steps live in [Step 0 — Choose chain mode](#step-0--choose-chain-mode-first-tool-call--structural-gate) through [Step 7 — Hand off to /hyperflow:dispatch](#step-7--hand-off-to-hyperflowdispatch) above. Summary:

1. Ask `chain-mode` (auto / manual) if not propagated from a prior chain-starter.
2. Confirm the task is buildable, not a design question (else hand off to `/hyperflow:spec`).
3. Step 2 sub-phases (2a surface mapping, 2b semantic indexing, 2c convention scan) in parallel.
4. Step 3a Opus Planner produces batch graph; Sonnet Reviewer validates decomposition; 3b/3c (complexity sizing, acceptance criteria) in parallel after 3a.
5. Step 4 sub-phases (4a status/goal/why, then 4b scope/files ∥ 4c execution/verification) emit `.hyperflow/tasks/<slug>.md`; final Reviewer verifies plan vs design.
6. Append decisions to `.hyperflow/memory/decisions.md` (concurrent with Step 4 — P3).
7. Hand off to `/hyperflow:dispatch` (auto or via confirmation gate).

## Output

Single output line plus the task file path:

```
Plan ready — .hyperflow/tasks/<slug>.md (N batches, M sub-tasks)
Auto-chaining to /hyperflow:dispatch...
```

The written task file follows the template in [Step 4](#step-4--write-task-file) — Goal, Context, Affected files, Batches (with `[ ]` checkboxes), Open questions, Verification plan, Estimated cost, Status block.

## Error Handling

| Failure | Behavior |
|---|---|
| Ambiguous request (would need design exploration) | Stop and suggest `/hyperflow:spec`. Print: `This needs design exploration first. Try /hyperflow:spec` and exit. |
| Searcher returns empty (no affected files found) | Reviewer flags missing scope; redispatch with broader query. Max 2 retries. |
| Planner produces single-batch plan for multi-file work | Reviewer rejects; redispatch Planner with feedback to split into parallel + sequential batches. |
| Task file write fails (path locked, disk full) | Abort with explicit error; do not auto-chain. User retries after fix. |
| `chain-mode` arg malformed | Refuse and re-ask via `AskUserQuestion`. Never silently default. |
| `AskUserQuestion` popup unavailable in Codex | Print the gate as a `Hyperflow Question` chat block and wait for the user's answer. |
| No interactive channel at all | Print error stating chain-mode gate cannot fire; exit. |

## Examples

### Direct invocation (asks chain-mode first)

```
/hyperflow:scope add a rate-limit middleware: token bucket, per-IP, env-configurable

?  How should I advance through the chain after this phase?
   Auto (Recommended)  — chain forward through scope → dispatch with no gate.
   Manual              — pause between phases and ask before advancing.

[user picks Auto]

Step 2a: Searcher — glob discovery · Searcher — import-graph traversal → **Reviewer**
Step 2b: Searcher — type-system probe · Searcher — symbol-graph probe → **Reviewer**
Step 2c: Searcher — test patterns and lint config → **Reviewer**
Step 3a: **Planner** — producing batch graph → **Reviewer** — validating decomposition completeness and batch boundaries
Step 3b: Searcher — LOC estimation · Searcher — subsystem cross-cut check → **Reviewer**
Step 3c: Writer — acceptance criteria · Writer — verification hooks → **Reviewer**
Step 4a: Writer — status block · Writer — goal and why → **Reviewer**
Step 4b: Writer — scope-at-a-glance · Writer — affected-file listing → **Reviewer**
Step 4c: Writer — execution plan and batches · Writer — open questions and verification → **Reviewer**
**Reviewer** — verifying assembled task file vs design
Writer — appending decisions to .hyperflow/memory/decisions.md
**Reviewer** — checking memory entries

Plan ready — .hyperflow/tasks/rate-limit-middleware.md (3 batches, 7 sub-tasks)
Auto-chaining to /hyperflow:dispatch...
```

### Propagated from spec (no chain-mode prompt)

```
[Invoked from /hyperflow:spec with args: chain-mode=auto triage=<base64>]

Searcher — mapping affected files
...
Plan ready — .hyperflow/tasks/<slug>.md (2 batches, 4 sub-tasks)
Auto-chaining to /hyperflow:dispatch...
```

### Bounce back to spec on ambiguity

```
/hyperflow:scope should we switch to event sourcing?

This needs design exploration first. Try /hyperflow:spec — it'll ask the
right questions before any decomposition happens.
```

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (Layer 7 task templates, rule 8 structural gates).
- [task-templates.md](references/task-templates.md) — CRUD, API, UI, migration, refactor, bug-fix templates.
- [task-tracking.md](references/task-tracking.md) — task file format and lifecycle.
- [worker-prompt.md](references/worker-prompt.md) — what dispatch will inject into each Sonnet worker.
- [output-style.md](references/output-style.md) — agent label format.
- [../spec/references/latency-patterns.md](../spec/references/latency-patterns.md) — P1–P5 latency pattern definitions, wall-clock impact table, and `--thorough` disable rules.
