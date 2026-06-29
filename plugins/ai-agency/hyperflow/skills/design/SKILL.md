---
name: design
description: |
  Use when the user wants the visual/experiential design of a product done systematically — a design system, a screen, a landing page, or a visual identity — grounded in researched real-world prior art and free of AI slop. Establishes/extends the design system, invokes the matching local taste skill, dispatches the designer specialist, and reviews for taste + accessibility. Standalone — ends with a handoff gate into the chain.
  Trigger with /hyperflow:design, "design the UI", "make a design system", "design this screen", "give this a visual identity", "redesign this".
allowed-tools: Read, Glob, Grep, Agent, Skill, AskUserQuestion
argument-hint: "[target | brief]"
version: 1.0.0
license: MIT
compatibility: Designed for Claude Code
tags: [design, design-system, ui, creative, anti-slop, multi-agent]
---

# Design

Systematic, anti-slop product design. All agents inherit the session model. Reviewers bold-labeled; Workers plain.

This skill exercises **Layer 4 (Brainstorming/Spec)** and the design layer of **Layer 0 (Project Analysis)**. It is
**thinking, not building** — no source code is written here. The only writes are to `.hyperflow/design/system.md` and
`.hyperflow/specs/`. It ends with a handoff gate into `/hyperflow:plan` → `/hyperflow:dispatch` for the build.

## Iron Rules

- **Design system first.** Every run establishes or extends `.hyperflow/design/system.md` before designing a screen,
  per [`../hyperflow/design-system.md`](../hyperflow/design-system.md). The system is created once and extended, never
  regenerated.
- **Researched, not invented.** Ground every direction in **≥2** real products from the project's field, combine
  them, then diverge with one deliberate signature (the method in [`design-system.md`](../hyperflow/design-system.md)).
- **Local taste skills are invoked live.** The main session calls `Skill` to invoke the matching taste skill; the
  dispatched `designer` agent Reads the `SKILL.md` and applies it (it has no `Skill` tool).
- **Per-step agents (DOCTRINE rule 12).** No inline design — the [`designer`](../../agents/designer.md) specialist
  does the work; an `accessibility-reviewer` pass gates the result.
- **No code in the design phase.** Design produces a system file and a design spec; `dispatch` executes them.
- **Failure recovery (DOCTRINE rule 14)** per [`../hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md).
- **No AI attribution** in any file written.

## Per-Step Agent Map (DOCTRINE rule 12)

| Step | Sub-phase | Workers | Reviewers | Notes |
|---|---|---|---|---|
| 1 — Triage | — | — | — | Mechanical classification (exempt) per [`../hyperflow/task-triage.md`](../hyperflow/task-triage.md) |
| 2 — Design system | 2a — establish/extend `.hyperflow/design/system.md` | `designer` | **Reviewer** | Creates if missing; extends if present |
| 3 — Research + direction | 3a — prior-art research + combine + diverge | `designer` (fan-out ≤ 3 by dimension) | **Reviewer** | Web-research-first; ≥2 references |
| 4 — Design spec | 4a — translate direction into tokens/spec | `designer` | **Reviewer** | Written to `.hyperflow/specs/<slug>.md` |
| 5 — Taste + a11y review | — | — | **`designer`** verdict + **`accessibility-reviewer`** | Anti-slop floor + WCAG floor |
| 6 — Handoff gate | — | — | — | `AskUserQuestion` only (exempt — structural gate) |

## Approval Gates

| Gate | When | Format |
|---|---|---|
| Handoff gate | Step 6, after the spec is written | `AskUserQuestion` — build now / plan first / stop |

## Flow

### Step 1 — Triage

Classify the request per [`../hyperflow/task-triage.md`](../hyperflow/task-triage.md). `types` will include `ui`
and/or `creative`; the [Brain](../../agents/brain.md) confirms `designer` on the roster.

### Step 2 — Design system

Read `.hyperflow/design/system.md`. If missing, dispatch `designer — establish design system` to create it (domain,
tokens, type scale, spacing, motion, voice, components, references, anti-patterns) per
[`design-system.md`](../hyperflow/design-system.md). If present, dispatch `designer — extend design system` to add
only what this brief needs. Then `**Reviewer** — design-system coverage check`.

### Step 3 — Research + direction

Invoke the matching local taste skill(s) live via `Skill` (per the index in `design-system.md`). Then dispatch
`designer — research prior art + propose direction` (fan-out ≤ 3 by visual language / motion+interaction / IA when
the surface is broad): study ≥2 real systems in the field, combine, diverge with one named signature. Then
`**Reviewer** — direction grounding check` (≥2 references combined, not copied; signature is deliberate).

### Step 4 — Design spec

Dispatch `designer — author design spec` to translate the chosen direction into the bound design-system tokens and
write it to `.hyperflow/specs/<slug>.md` (format per [`../hyperflow/artefact-format.md`](../hyperflow/artefact-format.md)).
Then `**Reviewer** — spec sanity check`.

### Step 5 — Taste + accessibility review

Dispatch in parallel: `**designer** — taste verdict` (anti-slop floor) ∥ `**accessibility-reviewer** — a11y floor`
(WCAG AA, focus, reduced-motion, RTL). On a11y conflict, the floor wins (Step 5 defers to the a11y verdict).

### Step 6 — Handoff gate (STRUCTURAL GATE · DOCTRINE rule 8)

```
?  Design spec ready at .hyperflow/specs/<slug>.md — build it?

   Build now (Recommended)  — chain to /hyperflow:plan → /hyperflow:dispatch
   Plan first               — open /hyperflow:plan to decompose without building yet
   Stop                     — leave the spec; build later
```

On **Build now** → invoke `Skill` with `skill: plan` and `args: "session=one spec=.hyperflow/specs/<slug>.md"`. On
**Plan first** → invoke `plan` without auto-dispatch. On **Stop** → print one line and stop. If `AskUserQuestion` is
unavailable, print the gate as a `Hyperflow Question` block and wait — never auto-build silently.

## Output Format

Two outputs:

1. **The design system** at `.hyperflow/design/system.md` — living token document (created or extended this run).
2. **The design spec** at `.hyperflow/specs/<slug>.md` — the direction, tokens, signature, and `References:` block.

Chat shows one status box pointing at the files, never the token dump (file-first, rule 8):

```
── Design Result ─────────────────────
Brief:    <one line>
System:   .hyperflow/design/system.md (created | extended)
Spec:     .hyperflow/specs/<slug>.md
Verdict:  taste PASS · a11y PASS
─────────────────────────────────────
```

## Hand-off

- **Plan it** — auto-chain to `/hyperflow:plan` for decomposition; plan then stops at its build-location gate and asks where to build (it never auto-implements).
- **Stop** — spec persists for a later build.

## Doctrine

Full rules in [DOCTRINE.md](../hyperflow/DOCTRINE.md). Design method, taste-skill index, and anti-slop floor in
[design-system.md](../hyperflow/design-system.md). Persona standards (`ui`, `creative`) in
[personas-A.md](../hyperflow/personas-A.md) — bound by the `designer`, never restated.

## Overview

`/hyperflow:design` runs systematic product design: it establishes or extends the project's design system, researches
real-world prior art in the project's field, invokes the matching local taste skill, dispatches the `designer`
specialist to combine references and diverge with one deliberate signature, and gates the result on a taste +
accessibility review before handing off to the build chain.

## Prerequisites

- `.hyperflow/` cache recommended (Layer 0 analysis improves design context). Run `/hyperflow:scaffold` first if
  missing.
- Local taste skills installed under `~/.claude/skills/` (the skill degrades gracefully to the anti-slop floor in
  `design-system.md` when a specific taste skill is absent).
