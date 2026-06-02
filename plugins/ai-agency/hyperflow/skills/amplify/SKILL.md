---
name: amplify
description: |
  Use when a prompt is rough, vague, or under-specified and you want it rewritten to high quality before running it. Domain-aware: detects the prompt's domain, stitches the matching specialist standards, reads project rules, and scores the result against an 8-dimension rubric. Standalone — ends with a handoff gate to push the amplified prompt into the chain.
  Trigger with /hyperflow:amplify, "enhance this prompt", "make this prompt better", "improve my prompt", "rewrite this prompt".
allowed-tools: Read, Glob, Grep, Agent, AskUserQuestion, Skill
argument-hint: "<raw prompt to enhance> (omit to amplify your previous message)"
version: 1.0.0
license: MIT
compatibility: Designed for Claude Code
tags: [prompt-engineering, enhancement, quality, personas, multi-agent]
---

# Amplify

Turn a rough prompt into a high-signal one. Detect the domain, inject the standards that domain demands, score it against a rubric — then offer to run it.

Dispatcher and reviewer — Opus 4.8 (thinking-tier). Searcher/Writer — Sonnet 4.6 (worker-tier).

Amplify does **one** thing well: it rewrites the prompt you give it into the single strongest version, then hands it off. It does not write code itself — it produces a prompt other skills (or you) execute.

## Per-Step Agent Map (DOCTRINE rule 12)

Every substantive step dispatches at least one Agent. Atomic steps (DOCTRINE 12.2.8) are a single Worker → Reviewer pair with no independent angles to fan out.

| Step | Status | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 1 — Read intent | Atomic (12.2.8) | Searcher (Sonnet) — domain signals + project rules | **Analyst** (Opus) — triage + gap analysis + persona selection | Single Worker → Reviewer; reads `CLAUDE.md`, `AGENTS.md`, `.hyperflow/memory/*` |
| 2 — Amplify | Atomic (12.2.8) | Writer (Sonnet) — draft the enhanced prompt | **Reviewer** (Opus) — rubric score, one targeted revision | Writer drafts → Opus scores against the 8-dim rubric → revise once if any dim < 4 |
| 3 — Present + handoff | §12.1 inline | — | — | Print the amplified prompt + rationale; fire the handoff gate (`AskUserQuestion`) |

## Inputs

- `$ARGUMENTS` — the raw prompt to amplify. If empty, amplify the user's previous message in the conversation.
- No flags. Amplify always produces the single best version (per the design decision); the rubric, not a flag, governs depth.

## Flow

### Step 1 — Read intent (atomic · 12.2.8)

Atomic — a single Searcher → Analyst pair. No parallel angles: understanding one prompt is one scope.

1. Dispatch `Searcher — detecting prompt domain + gathering project rules` (Sonnet). It returns:
   - **Domain signals** — does the prompt concern frontend/ui/creative, api/db backend, mobile, security, performance, refactor/bugfix/test, devops, docs? (A prompt can span several.)
   - **Project rules** — read, when present: `CLAUDE.md`, `AGENTS.md`, `.hyperflow/memory/conventions.md`, `.hyperflow/memory/project-decisions.md`, `.hyperflow/memory/anti-patterns.md`. Extract any rule that should constrain the prompt.
   - **The raw prompt's gaps** — what a senior engineer would have to guess to act on it.

2. Dispatch `**Analyst** — triaging intent + selecting personas` (Opus). It returns `{ domain[], intent, ambiguities[], personas[], project_rules[] }` — the matching hyperflow persona(s) from [`../hyperflow/personas-A.md`](../hyperflow/personas-A.md) / [`personas-B.md`](../hyperflow/personas-B.md), plus the project rules to layer on top.

If the prompt is too ambiguous to amplify without a decision the rewrite can't make (`ambiguity` high on a dimension that changes the deliverable), the Analyst flags it — Step 3's handoff gate surfaces it as a clarifying note rather than guessing.

### Step 2 — Amplify (atomic · 12.2.8)

Atomic — a single Writer → Reviewer pair with a one-shot revision loop.

1. Dispatch `Writer — drafting the amplified prompt` (Sonnet) with the Step 1 output. The Writer rewrites the raw prompt into the single strongest version following the skeleton in [`references/prompt-rubric.md`](references/prompt-rubric.md): role framing · precise task · context · constraints (persona doctrine + project rules) · output spec · out-of-scope. **Economy is a constraint** — enhance to the level the task warrants, never inflate a one-line ask into a spec.

2. Dispatch `**Reviewer** — scoring against the prompt-quality rubric` (Opus) with the draft. It scores all 8 dimensions (see [`references/prompt-rubric.md`](references/prompt-rubric.md)) 1–5. Verdict:
   - **All dimensions ≥ 4** → `PASS`. Ship the draft.
   - **Any dimension < 4** → `NEEDS_REVISION` with the specific dimensions + what's missing. The Writer revises **once** with the findings injected, then the result ships regardless (no infinite loop — DOCTRINE rule 14 NEEDS_REVISION cadence: surface after the second pass).

The Reviewer also produces the **rationale** — a 2–4 line "what changed and why," naming the domain doctrine and project rules it injected.

### Step 3 — Present + handoff (inline · §12.1)

Trivial-inline — no Agent dispatch. The orchestrator prints, then gates.

1. **Print the amplified prompt** in a single copy-ready fenced block.
2. **Print the rationale** beneath it — what changed, which persona standards + project rules were injected, and any ambiguity the Analyst flagged.
3. **Fire the handoff gate** — `AskUserQuestion`:

   > **Run this amplified prompt now?**
   > - **Send to spec** *(recommended)* — start the chain design-first; spec brainstorms + designs with the amplified prompt, then auto-chains to scope → dispatch
   > - **Send to scope** — the approach is clear, go straight to decomposition (`/hyperflow:scope`)
   > - **Send to dispatch** — a task file already exists (`/hyperflow:dispatch`)
   > - **Copy only** — keep the prompt, run nothing

   This is a multi-option gate (4 options) → it carries the `(Recommended)` marker on **Send to spec** (DOCTRINE rule 8 — named-workflow choice).

   On a `Send to …` selection, invoke the chosen skill via the `Skill` tool, passing the **amplified prompt** as the argument. Spec is the default because a freshly-amplified prompt is a design starting point — spec's brainstorming + section-by-section design is exactly what it feeds. On `Copy only`, stop — the prompt is already printed for the user to take.

   **Codex fallback:** if the host does not expose the `AskUserQuestion` popup UI, print the same gate as a `Hyperflow Question` chat block with the four numbered choices and wait for the user's reply. Do not auto-select `Send to spec`.

## Iron Rules

- **Amplify never writes code.** It produces a prompt; downstream skills execute it. If the user wanted code, the handoff gate routes there.
- **Project rules win on conflict.** A rule in `CLAUDE.md` / `AGENTS.md` / `.hyperflow/memory/` overrides the generic persona standard — it is the user's explicit instruction.
- **Economy is mandatory (rubric dim 8).** Never inflate a trivial prompt. The rubric enhances to the task's level, not beyond.
- **Failure recovery (rule 14).** Worker/Reviewer errors and the NEEDS_REVISION cadence follow [`../hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md).
- **No AI attribution** in the amplified prompt or rationale — describe the work, never the author.

## Doctrine

Shared rules in [`../hyperflow/DOCTRINE.md`](../hyperflow/DOCTRINE.md). Personas in [`../hyperflow/personas-A.md`](../hyperflow/personas-A.md) + [`personas-B.md`](../hyperflow/personas-B.md). Rubric in [`references/prompt-rubric.md`](references/prompt-rubric.md).
