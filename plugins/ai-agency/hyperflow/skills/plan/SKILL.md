---
name: plan
description: |
  Use when a request needs shaping before any code is written — a rough or vague prompt to sharpen, an ambiguous idea to design, or a clear-enough task to decompose. One chain-starter that amplifies the prompt, designs the approach, and decomposes it into a batched task file, skipping whichever phases the request doesn't need, then STOPS at a build-location gate (build here, hand off to another session, or just keep the plan). Plan never implements.
  Trigger with /hyperflow:plan, "design this", "plan this", "decompose this", "how should we", "what's the best way to", "break this down", "enhance this prompt".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(python3:*), Bash(mv:*), Glob, Grep, Agent, AskUserQuestion, Skill
argument-hint: "<idea, prompt, or task> [--thorough | depth=max] [briefs=auto|terse] [noamplify]"
version: 2.0.1
license: MIT
compatibility: Designed for Claude Code
tags: [prompt-engineering, design, brainstorming, planning, decomposition, multi-agent]
---

# Plan

One chain-starter that folds three phases — **amplify** (sharpen the prompt), **design** (brainstorm and spec the approach), **decompose** (write the batched task file) — into a single flow, then **stops at a build-location gate** (Step 12). Each phase skips itself when the request doesn't need it: a clear task bounces straight to decomposition; an already-structured prompt skips amplify.

**Plan never implements.** It is **thinking, not building** — no source code is written here, and it does not silently chain into `/hyperflow:dispatch`. The only writes are to `.hyperflow/specs/`, `.hyperflow/tasks/`, `.hyperflow/features/`, `.hyperflow/memory/`, and (another-session mode) the committed `.hyperflow-handoff/` package. When the task file is ready, plan **always** asks where to build it (this session / another session / stop) — that gate fires on every run, and the user's choice is the only thing that ever starts a build. It drives **Layer 0.5 (Triage)**, **Layer 4 (Brainstorming/Spec)**, **Layer 0 (Project Analysis)**, **Layer 6 (Memory)**, and **Layer 7 (Task Templates)**.

**Plan runs at maximum thinking depth.** Engage extended / ultra reasoning across triage, analysis, design, and decomposition — plan is the chain's one think-heavy front door and pays the reasoning cost once so the build runs faithfully. Every substantive step **uses tools** (Agents to do the work, `Write` to persist artefacts); a plan that exists only in chat is a violation.

**Every agent runs on the current session model — there is no model-tier routing and no model configuration.** Roles (Classifier, Searcher, Writer, Analyst, Planner, Reviewer) differ by responsibility, not by model.

## Iron Rules

- **Plan never implements.** It always stops at the build-location gate (Step 12) and asks where to build — this session / another session / stop. It does NOT silently chain into `dispatch`. The gate fires **every run**, even when a `session=` / `commit=` / `branch=` arg was somehow propagated — never skip it.
- **Max thinking, always.** Run at maximum reasoning depth (ultrathink) through triage, analysis, design, and decomposition. Plan is the one think-heavy phase; do not shortcut the reasoning to save tokens.
- **Always produce the artefacts on disk.** Every run that reaches decomposition uses tools to `Write` the spec (when the design phase ran) and the task file + briefs. A plan described only in chat — no `.hyperflow/tasks/<slug>.md` written — is a failed run, not a plan.
- **No code in the design phase.** Plan produces a prompt, a spec, and a task file; `dispatch` executes them.
- **Author build-ready briefs (`briefs=auto`).** Every non-trivial sub-task gets a full, self-contained implementation brief at plan time (Step 9c), stored at `.hyperflow/tasks/<slug>/T<id>.md`. The strong planning model pays the authoring cost once so the build runs faithfully on a cheaper model or a second session — dispatch transcribes, it doesn't re-derive. Trivial sub-tasks stay terse.
- **Project rules win on conflict.** A rule in `CLAUDE.md` / `AGENTS.md` / `.hyperflow/memory/` overrides a generic persona standard — it is the user's explicit instruction.
- **Economy is mandatory.** Amplify enhances to the task's level, never inflates a one-line ask into a spec (rubric dim 8).
- **Names responsible specialists; never runs their web-research.** The `Responsible specialists:` annotation is an announcement — each specialist's web-research-first pass fires later inside `dispatch`, not here.
- **No AI attribution** in any prompt, spec, task file, or memory entry — describe the work, never the author.
- **Failure recovery (rule 14).** Worker/Reviewer errors, malformed output, and NEEDS_REVISION cadence follow [`../hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Retry → escalate → abort. Chain budget: 3 cumulative aborts.

## Per-Step Agent Map (DOCTRINE rule 12 + 12.2)

Every substantive step dispatches at least one Agent; trivial steps (§12.1) and single-pair atomic steps (§12.2.8) run as noted. All roles run on the session model — the table assigns responsibility, not tier.

| Step | Sub-phase | Workers | Reviewers / decision agents | Notes |
|---|---|---|---|---|
| 0 — Setup | atomic | — | — | Silent: parse flags, set max-thinking. NO startup gate, NO questions |
| 1 — Triage | atomic | Classifier | **Triage Reviewer** | P4-skip Reviewer; P3-concurrent with Step 3 |
| 2 — Amplify (skippable) | atomic | Writer — rewrite prompt | **Reviewer** — 8-dim rubric, one revision | Skips on clear/structured prompt |
| 3 — Context | 3a + 3b (P1) | Searcher ×2 per sub-phase | **Reviewer** per sub-phase | 3a surface map · 3b semantic + convention scan |
| 4 — Multi-dim analysis (P4) | 4a + 4b + 4c (P1) | Writer ×1–2 per sub-phase | **Reviewer** per sub-phase + **Analyst** synthesis | Skips when ambiguity < 0.6 ∧ complexity ≠ high |
| 5 — Clarify (gate) | atomic | — | — | `AskUserQuestion`; design path floor 2 · bounce path 0–3 |
| 6 — Synthesis + approaches (P4) | 6a + 6b | Writer ×1–2 per sub-phase | **Reviewer** (batched) | Skips approaches when ambiguity < 0.6 ∧ complexity ≠ high |
| 7 — Design sections (P1+P2) | 7a + 7b + 7c | Writer ×1–2 per sub-phase (**`architect`** authors 7a §1/§2 on architect-typed / high-complexity / multi-subsystem tasks — embeds Mermaid graphs; **`designer`** authors the visual/experiential decisions on ui/creative-typed tasks — grounds them in `.hyperflow/design/system.md`; **`mobile`** authors the platform/device decisions on mobile/native-typed tasks — grounds them in `../hyperflow/mobile.md`) | **Reviewer** per sub-phase + 1 batched | File-first; one combined approval gate |
| 8 — Spec finalize | atomic | Writer | **Reviewer** (final-integration) | Renames draft → `.hyperflow/specs/<slug>.md` |
| 9 — Decompose | 9a + 9b + 9c | Planner ×1 (9a) · Searcher ×2 (9b) · **brief Writer ×1 per non-trivial sub-task (9c)** | **Reviewer** per sub-phase | 9a batch graph → 9b sizing → 9c authors a full build-ready brief per non-trivial sub-task (`briefs=auto`) |
| 10 — Write task file (P3 w/ 11) | 10a + 10b + 10c | Writer ×2 per sub-phase | **Reviewer** per sub-phase + 1 final verify | Flat task file or feature/phase tree |
| 11 — Memory (P3 w/ 10) | atomic | Writer appends | **Reviewer** dup/contradiction check | Concurrent with Step 10 |
| 12 — Build-location gate | atomic | — | — | `AskUserQuestion` (ALWAYS fires): this session → `Skill` dispatch · another session → write handoff package · stop |

**Skippable / bounce summary:** Step 2 skips for clear prompts; Step 4 and Step 6-approaches are P4-skippable; Step 5 **bounces** the design phase (Steps 6–8) entirely when the request is clear, jumping to Step 9. `--thorough` / `depth=max` disables P1/P2/P4 (sequential, every step runs, per-section reviewers, standalone final-integration pass added); P3/P5 stay on. **No step is a startup gate** — plan asks the user nothing until the Step 5 clarify questions, and the build decision waits until Step 12.

## Approval Gates

| Gate | When | Format |
|---|---|---|
| Smart questions | Step 5, design path | `AskUserQuestion` — 2–5 questions (floor 2) |
| Synthesis + approach | Step 6, after batched review | `AskUserQuestion` — confirm synthesis · pick approach |
| Design section approval | Step 7, one combined gate | `AskUserQuestion` — approve all / revise §N |
| **Build location** | Step 12, after the task file is written — **ALWAYS** | `AskUserQuestion` — this session / another session / stop (+ handoff: review / deploy when another session) |

The build-location gate fires on **every** run (it is the only thing that ever starts a build); the design-phase gates fire at most once each and are skipped on the bounce path. Plan asks **no startup gates** — the session/build decision and the operational choices (commit cadence · branch · push) are no longer front-loaded. When the user picks "this session," `dispatch` fires its own operational gate (its Step 0.5) before building. Markers follow DOCTRINE rule 8: multi-option/named-workflow choices carry `(Recommended)`; binary action gates (Approve/Revise) carry none.

## Flow

### Step 0 — Setup (silent · max thinking · NO gate)

Plan asks the user **nothing** at startup. There is no session-strategy gate and no operational gate here — both decisions move to the Step 12 build-location gate (and `dispatch` owns the operational gate when a build actually starts). Defaulting silently is correct: plan is think-only, so there is nothing to decide until a task file exists.

At Step 0, the orchestrator only:

1. **Engages maximum thinking depth** (ultra reasoning) for the whole run — triage, analysis, design, and decomposition all reason at full depth.
2. **Parses flags** from the args: `--thorough` / `depth=max` (disable P1/P2/P4 — see the skippable summary), `noamplify` (skip Step 2), `briefs=auto|terse` (Step 9c). Record them; do not ask about them. **GitHub-native pass-through:** `gh_issue=` / `pr=` / `comment=` (set by `/hyperflow:issue`) and `spec=` (a pre-built spec path, e.g. from `/hyperflow:issue` or the audit fix-gate) are recorded verbatim — plan never acts on them, it forwards them to dispatch at Step 12.

Then proceed straight to Step 1. Any `session=` / `commit=` / `branch=` / `push=` args that happen to be present are **ignored for gating** — the build decision is always made fresh at Step 12.

### Step 1 — Triage (Layer 0.5 · P3-concurrent with Step 3)

Step 1 (Classifier) and Step 3 (context Searchers) are independent — dispatch both in one message, wait for both. Under `--thorough`, run Step 1 first, then Step 3.

Dispatch `Classifier — triaging request` per [`../hyperflow/task-triage.md`](../hyperflow/task-triage.md), producing `{ types[], complexity, risk, scope, ambiguity, flow, personas[], specialists[] }`. This drives: the P4 gates (Steps 4/6) and bounce gate (Step 5); the question budget at Step 5 (`0.0–0.5` → 2, `0.5–0.8` → 3, `0.8–1.0` → 4–5); the downstream flow profile ([`../hyperflow/flow-profiles.md`](../hyperflow/flow-profiles.md)); and persona/specialist stitching. On a gated flow the responsible specialist roster is finalized once via the [Brain](../../agents/brain.md) (DOCTRINE rule 17) and inherited by every later phase. Persist and propagate as `triage=<base64-json>`.

**Triage Reviewer (rule 15).** P4-skip when ALL of `complexity == low`, `ambiguity < 0.2`, `scope ∈ {0-file, 1-file}`, `risk != high` — consume the Classifier output as-is and print the skip line. Otherwise dispatch `**Triage Reviewer** — validating classification against request and project profile` (reads the request + `.hyperflow/profile.md`). Verdict ∈ {`PASS`, `RECLASSIFY` (use corrected triage, print one line), `ESCALATE` (add ambiguity to Step 5's queue)}. On Reviewer error follow failure-recovery §5 — never consume unvalidated triage.

### Step 2 — Amplify / prompt hygiene (atomic · skippable)

**Skip when** `ambiguity < 0.4`, OR the incoming prompt is already well-structured (role/task/constraints/output present), OR the `noamplify` flag is set — print `Amplify skipped — prompt already specific.` and proceed to Step 4 with the prompt as-is. Amplify exists to sharpen rough input before design; a sharp prompt gains nothing.

Otherwise a single Writer → Reviewer pair with a one-shot revision loop:

1. `Writer — drafting the amplified prompt` rewrites the raw prompt into its single strongest version following the skeleton in [`references/prompt-rubric.md`](references/prompt-rubric.md): role · task · context · constraints (persona doctrine from triage `personas[]` + project rules) · output spec · out-of-scope. Economy is a constraint.
2. `**Reviewer** — scoring against the prompt-quality rubric` scores all 8 dimensions 1–5. **All ≥ 4** → `PASS`. **Any < 4** → `NEEDS_REVISION` with specifics; the Writer revises **once**, then ships regardless (no infinite loop). The Reviewer also produces a 2–4 line rationale naming the domain doctrine and project rules it injected.

The amplified prompt becomes the working prompt for analysis and design. Print it once in a copy-ready block with its rationale + a `Responsible specialists:` line (omit when no specialist applies).

### Step 3 — Context exploration (P1 sub-phases · P3-concurrent with Step 1)

Read `.hyperflow/profile.md`, `architecture.md`, `conventions.md`, `.hyperflow/memory/index.md` before dispatching to surface past learnings. Sub-phases are independent — dispatch in one message, run per-sub-phase Reviewers, then advance. No Step-level coverage Reviewer; a downstream Writer flags `MISSING CONTEXT: <subsystem>` and the orchestrator redispatches the relevant Searcher (max 2 retries). Do not ask the user what the code reveals.

- **3a — Surface mapping:** `Searcher — glob discovery: file tree + entry points`; `Searcher — import-graph traversal: dependency edges`. → `**Reviewer**`.
- **3b — Semantic + convention scan:** `Searcher — type/symbol probe: interfaces, schemas, call sites, re-exports`; `Searcher — test patterns + lint/config: naming, runner, lint rules`. → `**Reviewer**`.

### Step 4 — Multi-dimensional analysis (P4-skippable)

**P4 gate:** skip entirely (jump to Step 5) when `ambiguity < 0.6 AND complexity != high` — round up on the border (0.59 → run). `--thorough` always runs. If run, sub-phases fan out in parallel (P1), then the Analyst aggregates:

- **4a — Intent + technical-fit:** `Writer — user-intent: real need + success` ∥ `Writer — technical-fit: how it fits existing architecture`. → `**Reviewer**`.
- **4b — Scope + risks:** `Writer — scope/constraints: MVP vs max, limits` ∥ `Writer — risks: failure modes, irreversibility`. → `**Reviewer**`.
- **4c — Alternatives:** `Writer — alternatives: ≥3 distinct solutions, brief notes` (single canonical set). → `**Reviewer**`.
- **4d — Analyst synthesis (sequential):** `**Analyst** — 6-dimension aggregation` consolidates 4a/4b/4c into the unified brief; unknowns become Step 5 questions.

### Step 5 — Clarify (`AskUserQuestion` · two modes)

Pre-flight: read `.hyperflow/memory/project-decisions.md`; skip any candidate already answered there (print one line) unless the cached answer conflicts with this task (then ask "decisions say X — does this task change that?").

**Bounce gate (decompose-only path):** when `ambiguity < 0.4 AND complexity == low`, the request is clear — skip the design phase (Steps 6–8). Ask **0–3** post-analysis questions tied to specific findings the Searchers surfaced (no floor — zero when research is conclusive), then jump to **Step 9**. Print `That's clear enough to skip the design phase — decomposing directly.`

**Design path (everything else):** ask via `AskUserQuestion`, **floor of 2 questions always** (the two minimums give the user a place to redirect even when the request looks unambiguous). Budget by triage depth: light 2 · standard 3 · deep 4–5. Never stack more than 2 questions per call. Multi-option lists (3+) mark a `(Recommended)` choice (the Analyst's leading hypothesis first); binary lists carry no marker. Question order: intent → constraints → assumptions → scope → edge-case stance (pick the first N for depth N).

After answers, append structural decisions (database, auth, testing, framework defaults) to `.hyperflow/memory/project-decisions.md` under a category heading with date + source slug — inline write, §12.1-trivial. Skip task-specific answers.

### Step 6 — Synthesis + approaches (P3 + P2 · P4-skippable)

Step 5 (synthesis) and 6a both depend on the answers but not on each other — dispatch concurrently (P3); one batched Reviewer covers both (P2). `--thorough` runs them sequentially.

- **Synthesis:** `Writer — requirement synthesis` produces a one-paragraph "the goal is X, constraints Y, excluding Z."
- **6a — Approach candidates (P4-skip when `ambiguity < 0.6 ∧ complexity != high`):** `Writer — lightweight candidates` ∥ `Writer — heavyweight candidates`. Each approach: Name · What · Pros · Cons · Fit.
- **6b — Trade-off eval (sequential on 6a):** `Writer — fit analysis` ∥ `Writer — risk analysis` scoring each candidate.

`**Reviewer** — batched: synthesis + approaches` ([`../hyperflow/reviewer-prompt-batched.md`](../hyperflow/reviewer-prompt-batched.md)) returns per-draft verdicts; re-dispatch only the failing draft. When 6a/6b are P4-skipped, annotate "Approach: derived from synthesis (ambiguity low)". Then present synthesis + approaches and confirm via `AskUserQuestion` — recommend one approach, the choice is the user's.

### Step 7 — Section-by-section design (P1 + P2 · file-first · one combined gate)

**File-first (rule 8):** each section Writer writes directly to `.hyperflow/specs/<slug>.draft.md` at a stable H2 anchor — never returns content for inline paste. Pre-seed the file with 5 H2 headers before dispatching. Run `python3 $PLUGIN_ROOT/scripts/resolve-mode.py $PROJECT_ROOT --from-args "$CHAIN_ARGS"` once and propagate `mode=<default|lean|thorough>` (lean → workers get the path-only Project Context block per [`../hyperflow/worker-prompt-lean.md`](../hyperflow/worker-prompt-lean.md)).

Sub-phases dispatch in ONE parallel message (P1), each with a per-sub-phase Reviewer firing as it returns; then one batched Reviewer (P2) reads all 5 sections for cross-section coherence. Each section Writer records a `Responsible specialist(s):` line from the Brain-finalized roster, carried into the Step 8 status block.

**System-design tasks produce architecture graphs.** On architect-typed / high-complexity / multi-subsystem work the [`architect`](../../agents/architect.md) agent owns §1/§2 and embeds a Mermaid component/container graph (§1) and a Mermaid data-flow diagram (§2) directly in the draft — the diagram precedes the implementation. The Step 7 approval gate already points the user at the draft file, so the graphs are reviewed there with no extra gate.

**Design-time consultation.** Any decision agent in this phase may consult a peer directly (its own `Agent` tool, ≤ 3 consults, depth-1, allowlist = the `agents/` registry) per [`../hyperflow/consultation.md`](../hyperflow/consultation.md) — e.g. the `architect` asks `motion` whether a proposed interaction is feasible before committing it to §2, or the `designer` asks `motion` for a motion-heavy screen. Agent-agnostic: future decision agents inherit this without an edit here.

**Design-typed tasks ground in the design system.** On ui/creative-typed work the [`designer`](../../agents/designer.md) agent owns the visual/experiential decisions: it first ensures `.hyperflow/design/system.md` exists (creating it if missing, extending it if present per [`../hyperflow/design-system.md`](../hyperflow/design-system.md)), researches ≥2 real-world references in the project's field and combines them with one deliberate signature, applies the matching local taste skill, and records the bound design-system tokens in §3. When a **motion surface** is in scope (animation / transition / scroll-driven / gesture), the designer brings in the [`motion`](../../agents/motion.md) agent to author the Motion-language decisions in §3 (compositor-only props, library choice, spring params, reduced-motion fallback per [`../hyperflow/motion.md`](../hyperflow/motion.md)) — composing within §3, not a separate section. No source code is written — only the design system and the spec draft.

**Mobile-typed tasks define the platform & device strategy.** On mobile / native / responsive-app work the [`mobile`](../../agents/mobile.md) agent authors the mobile decisions — framework choice + rationale (React Native / Flutter / native iOS / Android), app architecture (navigation / offline-first / lifecycle-aware state), the platform accessibility floor (VoiceOver/TalkBack, 44pt/48dp targets, Dynamic Type), and the device-size test matrix + tooling (Maestro/Detox/XCUITest/Espresso) — into §1 (architecture, composing with the `architect`) and §3 (decisions), grounded in [`../hyperflow/mobile.md`](../hyperflow/mobile.md). No source code is written.

- **7a — Structural:** when triage `types` includes `architect`, OR `complexity == high`, OR the surface spans ≥ 2 subsystems, dispatch the [`architect`](../../agents/architect.md) agent to author both sections — `architect — §1 Architecture (C4 decomposition + Mermaid component/container graph)` ∥ `architect — §2 Data flow (Mermaid data-flow diagram per new cross-boundary path)`; it folds the frontend-at-scale decisions (debounce/virtualize/paginate/cache/code-split/state-topology) into §1 or §3 when a frontend surface is in scope and flags every hard-to-reverse choice for an ADR in §3. Otherwise (clear single-component task) `Writer — §1 Architecture` ∥ `Writer — §2 Data flow`. → `**Reviewer**` (the section reviewer is a separate agent; the architect's reviewer role applies later, on structural change in `dispatch`/`audit`).
- **7b — Decisions:** when triage `types` includes `ui` OR `creative`, dispatch the [`designer`](../../agents/designer.md) agent to author the visual/experiential half — `designer — §3 Design decisions (design-system tokens + signature + references)` ∥ `Writer — §4 Edge cases`; the designer ensures `.hyperflow/design/system.md` exists first and applies the matching taste skill. Otherwise `Writer — §3 Key decisions` ∥ `Writer — §4 Edge cases`. → `**Reviewer**`.
- **7c — File structure:** `Writer — §5 File structure`. → `**Reviewer**`.

On batched `NEEDS_FIX` for a section, re-dispatch only that section's Writer (rewrites its own H2 block). **4+ of 5 sections NEEDS_FIX** → the approach is likely wrong; bounce to Step 6 and re-pick. Worker failure: retry (max 2), then `ESCALATE` — inline drafting in chat is BANNED (violates file-first). `--thorough`: draft each section sequentially with its own approve/revise gate, then a standalone final-integration Reviewer.

After review passes, fire ONE combined `AskUserQuestion` — body is a one-line section roster + the file path (NOT the content):

```
Design draft ready at .hyperflow/specs/<slug>.draft.md
§1 Architecture · §2 Data flow · §3 Key decisions · §4 Edge cases · §5 File structure
  Approve all   — finalize and decompose
  Revise §<N>   — send the named section back with your feedback (free-form)
```

Per-section revise loops only that Writer (max 3 cycles per section); the rest of the file is untouched.

### Step 8 — Spec finalize (atomic)

`Writer — finalizing spec at .hyperflow/specs/<slug>.draft.md` prepends the status block + TL;DR (2–3 plain-English sentences from the synthesis) + Components, appends `Trade-offs accepted/rejected` to §3, and renames `mv .hyperflow/specs/<slug>.draft.md .hyperflow/specs/<slug>.md`. Format per [`../hyperflow/artefact-format.md`](../hyperflow/artefact-format.md): Status table (incl. `Specialists` row), TL;DR, Components, §1–5. Then `**Reviewer** — final spec sanity check` (always runs) verifies the status block, TL;DR length, all sections present, H2 ordering 1–5, trade-offs present, no cross-section contradiction, and — when the `architect` agent authored the design — the Mermaid graphs in §1/§2. No inline-summary fallback — the spec lives in a file.

### Step 9 — Decompose (Planner · 9a sequential then 9b/9c parallel)

9a fires first; 9b/9c depend on it and run concurrently.

- **9a — Batch graph:** `**Planner** — producing batch graph` with the Step 3 context aggregate + triage + applicable templates — when the `architect` agent authored §1, the Planner consumes its decomposition as the batch-boundary source rather than re-deriving it from [`../hyperflow/task-templates.md`](../hyperflow/task-templates.md) (CRUD / API / UI / Migration / Refactor / Bug Fix, else bespoke). Per sub-task: Worker role · Read/Modify/Create files · parallel-vs-sequential deps · complexity estimate · **≥1 responsible specialist** (from the Brain-finalized triage `specialists[]`, inherited from the spec status block when the design phase ran). Then `**Reviewer** — validating decomposition completeness + batch boundaries` (every finding maps to ≥1 sub-task; no sub-task spans >1 subsystem without a split; topological ordering). **Oversize-split mandate (Layer 3):** split any sub-task hitting >5 files, >500 LOC, 2+ subsystems, `complexity=high`, mixed concerns, or >10-min human review — until every piece is low/medium. Splitting is a cost AND quality optimisation. **Mode:** Planner emits `mode: flat | feature` per [`../hyperflow/feature-phases.md`](../hyperflow/feature-phases.md) — `feature` only when ≥2 sequential dependent stages/milestones exist; a 1-phase "feature" is `NEEDS_REVISION`.
- **9b — Complexity sizing:** `Searcher — LOC estimation` ∥ `Searcher — subsystem cross-cut check`. → `**Reviewer**`.
- **9c — Per-sub-task briefs (the heavy lift; `briefs=auto` default):** for each **non-trivial** sub-task, a `Writer — authoring brief T<id>` writes the full [`../hyperflow/worker-prompt.md`](../hyperflow/worker-prompt.md) body to `.hyperflow/tasks/<slug>/T<id>.md` — Task · Why · Scope IN/OUT · Files-in-scope with the **exact change described** (spec-level prose, no code skeletons) · Acceptance criteria · the **realistic Test-case set + ≥1 end-to-end/integration scenario** (named tool, real input→outcome; or explicit `E2E: N/A — <why>`) · Related context (file:line patterns to mirror) · Gotchas. Grounded in the Step 3 context aggregate + the spec; names ≥1 responsible specialist. **Trivial** sub-tasks (1 file ∧ ~≤10 LOC ∧ obvious) get NO brief — only the terse roster line. Brief Writers fan out in parallel (one per non-trivial sub-task), then `**Reviewer** — briefs vs design + completeness`: every non-trivial sub-task has a brief; every brief carries Acceptance criteria + ≥1 E2E case + a populated specialist; no brief contradicts the spec. `briefs=terse` skips 9c entirely (one-liner roster only — the legacy output; use when the same strong model will build).

### Step 10 — Write task file (P3 sub-phases · concurrent with Step 11)

10a anchors first (status + Goal + Why); 10b/10c run concurrently after. `--thorough` disables P1 here only (sequential drafts) — P3 (Steps 10 + 11) stays on.

- **10a — Status + Goal + Why:** `Writer — status block` ∥ `Writer — goal + why`. → `**Reviewer**`.
- **10b — Scope + affected files:** `Writer — scope-at-a-glance table` ∥ `Writer — affected-file listing`. → `**Reviewer**`.
- **10c — Execution plan + batches + verification:** `Writer — execution plan + batch checklist (terse roster, each non-trivial line carrying a `Brief: <slug>/T<id>.md` pointer)` ∥ `Writer — open questions + verification plan`. → `**Reviewer**`.
- **10d — Final verify:** `**Reviewer** — assembled task file vs design + briefs` — every design requirement maps to ≥1 sub-task, no orphans, every sub-task names ≥1 specialist, `Specialists` status row populated, and **roster↔brief consistency** (every non-trivial roster line resolves to an existing `<slug>/T<id>.md`; every brief maps back to a roster line).

**Mode branch:** `flat` → the terse roster `.hyperflow/tasks/<slug>.md` + the brief dir `.hyperflow/tasks/<slug>/T<id>.md` (one full brief per non-trivial sub-task, written in 9c; template + lifecycle in [`../hyperflow/task-tracking.md`](../hyperflow/task-tracking.md); brief format in [`../hyperflow/artefact-format.md`](../hyperflow/artefact-format.md) + [`../hyperflow/worker-prompt.md`](../hyperflow/worker-prompt.md)); `feature` → the feature tree per [`../hyperflow/feature-phases.md`](../hyperflow/feature-phases.md) (briefs land in each `phase-*/tasks/T<id>.md`) (`feature.md` + `phase-<n>-<name>/` folders each with `phase.md` + `tasks/`), final-verify additionally checks phase ordering, `Depends on` references, and one-phase-per-task placement. The status block is updated by `dispatch` after each sub-task PASS.

### Step 11 — Memory (P3 · concurrent with Step 10)

`Writer — appending decisions to .hyperflow/memory/decisions.md` (skip trivial; for complex features also seed `.hyperflow/specs/<feature-slug>.md` referenced from the task file) → `**Reviewer** — checking memory entries` for duplicates/contradictions. Both Writers (Step 10 + 11) derive from the Planner output and are independent — dispatch concurrently.

### Step 12 — Build-location gate (ALWAYS fires · plan never auto-implements)

The task file is written; plan is done thinking. Fire ONE `AskUserQuestion` — this gate fires on **every** run and is the **only** thing that ever starts a build. Never skip it, never default it, never silently chain into `dispatch`, regardless of any propagated args or autonomy directive. Q1 is a named-workflow choice → recommended option first with `(Recommended)`:

```
Plan ready — .hyperflow/tasks/<slug>.md (N batches, M sub-tasks)
Where should this be built?
  This session (Recommended) — run /hyperflow:dispatch here now, straight through.
  Another session            — write a committed handoff package and STOP; a second
                               session (another environment, e.g. Codex/Gemini) builds it.
  Stop                       — keep the plan only; build later with /hyperflow:dispatch <slug>.
```

**Q2 fires only when Q1 = Another session** — binary action gate, NO `(Recommended)` marker, structural default `Return for review`:

```
When the second session finishes building, what should it do?
  Return for review   — stop after the build; come back to THIS session and run /hyperflow:audit on the diff.
  Complete to deploy  — the second session continues to /hyperflow:deploy after the build.
```

Branch on the answer:

- **This session** → invoke `Skill` with `skill: dispatch`, `args: "<slug> triage=… mode=… briefs=…"` — appending `gh_issue=… pr=… comment=…` verbatim when present (the GitHub-native pass-through from Step 0; dispatch's Step 5 PR exit needs them). Do **not** pass `commit=` / `branch=` / `push=` — `dispatch` fires its own operational gate (its Step 0.5) before building. Print `Building here — handing to /hyperflow:dispatch…`.
- **Another session** → do NOT invoke dispatch. Write the committed handoff package and STOP at the dispatch boundary (full contract: [`../hyperflow/session-handoff.md`](../hyperflow/session-handoff.md)) — create `.hyperflow-handoff/<slug>/` with `HANDOFF.md` (manifest: slug, artefact type/path, resolved chain args, `on_complete` from Q2, originating commit, `Specialists` roster), `STATUS` (`planned`), a committed copy of the gitignored artefact, and `context/` copies of `.hyperflow/{conventions,profile,architecture}.md` + memory index; `git add` + commit `chore(handoff): plan <slug> for second-session build`; then print the start-session-2 instructions.
- **Stop** → write nothing further. Print `Plan kept at .hyperflow/tasks/<slug>.md — run /hyperflow:dispatch <slug> when you're ready to build.`

Portable-surface fallback (Codex / OpenCode / Grok): print the same gate as a `Hyperflow Question` chat block and wait; if no interactive channel exists, error and stop (never silently default to building).

## Anti-Patterns

- Writing code during the design phase, or letting plan implement anything — plan stops at the Step 12 build-location gate, full stop.
- Auto-chaining into `dispatch` without firing the build-location gate, or treating a propagated `session=` arg as permission to skip it — the gate fires **every** run.
- Front-loading a session-strategy or operational (commit/branch/push) gate at startup — those are gone; the build decision waits for Step 12 and `dispatch` owns operational.
- Producing a plan only in chat — every run that decomposes must `Write` the task file to `.hyperflow/tasks/<slug>.md`.
- Shortcutting the reasoning to save tokens — plan runs at max thinking.
- Asking > 5 questions total, or < 2 on the design path (the floor is mandatory even when the request looks clear), or stacking 3+ questions in one call.
- Skipping alternatives unless P4 skip or the bounce path is in effect.
- Asking what the codebase reveals; adding features the user didn't request (YAGNI).
- Sequentializing independent siblings (Steps 1+3, 7a/7b/7c, 9b/9c, 10 + 11) when P1/P3 apply.
- Per-section reviewers when one batched reviewer covers the same review-level cap.
- Single-batch plans for multi-file work; omitting the verification plan.
- Wrapping a §12.1-trivial step (hand-off, memory append) in an Agent dispatch.

## Overview

`plan` is the chain's single front door and runs at maximum thinking depth. It asks nothing at startup. Triage and context map concurrently (P3); amplify sharpens a rough prompt only when one is given; multi-dim analysis and approach proposals skip on low ambiguity (P4). A clear-enough request bounces past the design phase straight to decomposition; an ambiguous one walks the spec section-by-section (file-first, P1+P2) under a 2-question floor. The Planner then produces the batch graph (oversize-split enforced), Writers emit the flat task file or feature/phase tree (P3 with the memory append). Plan then **stops** and fires the build-location gate — it never implements: the user chooses to build here (hands to `/hyperflow:dispatch`), build in another session (writes a committed handoff package), or keep the plan for later.

## Prerequisites

- `.hyperflow/` cache (run `/hyperflow:scaffold` first if missing — improves triage and planning context).
- `AskUserQuestion` available — required for the gates. Headless / non-interactive mode is rejected at the first gate plan reaches (the Step 5 clarify questions, or the Step 12 build-location gate on the bounce path).
- An idea, prompt, or task. Pure "should we?" design questions exercise the full flow; clear decompositions bounce past design automatically.

## Error Handling

| Failure | Behavior |
|---|---|
| `AskUserQuestion` unavailable (headless) | Refuse at the first gate reached (Step 5 clarify, else Step 12 build-location); print error and exit. Never silently build. |
| Classifier rejects request (off-topic/abuse) | Stop. Print neutral reason. |
| User picks "revise" on a design section | Loop that Writer with feedback. Max 3 cycles per section, then suggest a different approach. |
| Searcher returns no/empty context | Downstream Writer flags `MISSING CONTEXT`; redispatch with the gap. Max 2 retries, then proceed with a caveat. |
| User rejects all proposed approaches | Writer drafts a 4th incorporating the stated objection. |
| Batched Reviewer NEEDS_FIX on 4+/5 sections | Approach likely wrong — bounce to Step 6 and re-pick. |
| Planner produces single-batch plan for multi-file work | Reviewer rejects; redispatch with split feedback. |
| Task file write fails (path locked/disk full) | Abort with explicit error; do not reach the build gate. |
| User picks "Stop" at the build-location gate | Leave the task file in place; print the `/hyperflow:dispatch <slug>` resume hint and exit cleanly. |
| Concurrent dispatch rate-limited | Cap parallel section drafts at 5, concurrent pre-conditions at 2; degrade to sequential — quality unchanged, latency reverts. |

## Resources

- [DOCTRINE.md](../hyperflow/DOCTRINE.md) — shared rules (rule 8 structural gates, rule 12 per-step agents, rule 17 Brain roster).
- [prompt-rubric.md](references/prompt-rubric.md) — 8-dimension prompt-quality rubric + domain-injection skeleton (Step 2).
- [examples.md](references/examples.md) — worked transcripts (illustrative, not load-bearing).
- [latency-patterns.md](../hyperflow/latency-patterns.md) — P1–P5 patterns, wall-clock table, `--thorough` rules.
- [task-triage.md](../hyperflow/task-triage.md) · [flow-profiles.md](../hyperflow/flow-profiles.md) — Classifier schema + execution profiles.
- [brainstorming-advanced.md](../hyperflow/brainstorming-advanced.md) — deeper question framework (Step 5).
- [task-templates.md](../hyperflow/task-templates.md) · [feature-phases.md](../hyperflow/feature-phases.md) — decomposition patterns + phase mode (Step 9).
- [task-tracking.md](../hyperflow/task-tracking.md) · [artefact-format.md](../hyperflow/artefact-format.md) — task-file format + artefact templates (Steps 8/10).
- [worker-prompt.md](../hyperflow/worker-prompt.md) · [worker-prompt-lean.md](../hyperflow/worker-prompt-lean.md) · [reviewer-prompt-batched.md](../hyperflow/reviewer-prompt-batched.md) — dispatched-agent templates.
- [memory-system.md](../hyperflow/memory-system.md) · [session-handoff.md](../hyperflow/session-handoff.md) — persistence + two-session contract.
- [output-style.md](../hyperflow/output-style.md) — agent label + status-line format.
