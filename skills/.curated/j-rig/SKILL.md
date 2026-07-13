---
name: j-rig
description: >-
  Skill Refiner, the eval-guided improvement loop for SKILL.md files. Runs the
  bootstrap, score, propose, apply, and status cycle as a thin wrapper over the
  published @intentsolutions/refiner CLI, proposing safe, minimal, bounded
  SKILL.md edits and accepting an edit only when a held-out eval score strictly
  improves with no regression on any other case. Ships a 3-layer cost-tiered
  hook architecture (sinker, line, hook) that gates skill quality at edit time,
  end of turn, and commit time. Use when improving an existing skill, refining a
  SKILL.md against measured behavior, bootstrapping an eval set for a skill, or
  gating skill edits before they ship. Trigger with "/j-rig", "refine this
  skill", "bootstrap an eval set", "propose a skill edit", "promote the
  candidate", or "skill refiner status".
allowed-tools: Read, Write, Edit, Glob, Bash(j-rig:*), Bash(git:*), Bash(python:*)
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Claude Code; the refine subcommands wrap the published @intentsolutions/jrig-cli binary and run anywhere that CLI installs
argument-hint: "[refine bootstrap|score|propose|promote|status] <skill-dir>"
tags:
  - skill-refiner
  - eval-guided
  - skill-md
  - meta-tooling
  - hooks
---

# j-rig — Skill Refiner

## Overview

The **Skill Refiner** is the eval-guided improvement loop for `SKILL.md` files.
It analyzes an existing skill against measured behavior, proposes safe, minimal,
bounded edits, and accepts an edit only when it strictly improves. It is the
second product in the Intent Solutions agent-rig stack:

```
J-Rig Skill Binary Eval   ->   Skill Refiner   ->   Rollout Gate
      (test)                     (improve)             (ship)
```

The refiner proposes bounded edits (add, delete, or replace operations on the
SKILL.md text) and accepts an edit **only if a held-out eval score strictly
improves** with no regression on any other case. It never rewrites a skill
wholesale, and it never lets a skill judge itself; scoring is delegated to the
separate `j-rig eval` harness.

This plugin is a **thin wrapper**. The refiner logic lives in the published
`@intentsolutions/refiner` package and is exposed through the `j-rig refine`
command group in the `@intentsolutions/jrig-cli` binary. This skill invokes that
CLI; it does not reimplement any refiner logic.

Use this skill when:

- Improving an existing skill whose behavior you can measure.
- Bootstrapping a held-out eval set for a skill so you have something to score
  against.
- Proposing a bounded SKILL.md edit and checking whether it strictly improves.
- Gating skill edits before they ship (the 3-layer hooks do this automatically).

Do NOT use it to hand-author a brand-new skill from scratch; use
`/skill-creator` for that. The refiner improves skills that already exist and
already have measurable behavior.

## Prerequisites

The subcommands wrap the published `j-rig` binary. Install it once:

```bash
# Global — gives you the `j-rig` command everywhere
npm install -g @intentsolutions/jrig-cli

# Or per-repo (recommended for CI version-pinning)
pnpm add -D @intentsolutions/jrig-cli   # then: pnpm exec j-rig --help
```

The `refine` command group is contributed by `@intentsolutions/refiner`, which
ships as a dependency of the CLI. Model-backed steps (`score`, `propose`)
require the `ANTHROPIC_API_KEY` environment variable; the deterministic steps
(`bootstrap`, `apply`, `status`) run fully offline.

## Instructions

Each `/j-rig` subcommand maps one-to-one onto a `j-rig refine` verb. Run them
against a **skill directory** (the folder containing the `SKILL.md`).

| `/j-rig` subcommand | Underlying CLI | What it does | Cost |
| --- | --- | --- | --- |
| `refine bootstrap <skill-dir>` | `j-rig refine bootstrap` | Synthesize a held-out eval set from the SKILL.md and store it (content-addressed). | $0 (deterministic) |
| `refine score <skill-dir>` | `j-rig refine score` | Delegate scoring to `j-rig eval` (Haiku or Sonnet tier; never Opus, which is validation-only). | $ |
| `refine propose <skill-dir>` | `j-rig refine propose` | Propose one bounded add/delete/replace edit via the tiered refiner model and store the proposal. Shadow-validation happens here: the candidate is scored against the held-out set before it is ever applied. | $$ |
| `refine promote <skill-dir>` | `j-rig refine apply` | Apply a stored, accepted proposal to the SKILL.md, producing a new immutable candidate version, then move the `best` pointer. Human-gated: you decide to promote. | $0 (deterministic) |
| `refine status <skill-id>` | `j-rig refine status` | Show the refiner store state plus the append-only event log for a skill. | $0 (deterministic) |

Naming note: this skill's user-facing verbs follow the ratified plan (bootstrap,
propose, shadow, promote, status). On the published CLI, **shadow-validation is
the acceptance gate inside `propose`**, and **promote is `j-rig refine apply`
plus the human-gated `best`-pointer move**. The wrappers call the real CLI verbs
(`bootstrap`, `score`, `propose`, `apply`, `status`).

### The 3-layer hook architecture (sinker, line, hook)

The plugin ships three hooks that automatically gate skill quality at three
points in the Claude Code lifecycle. They are **cost-tiered**: the cheapest
layer fires most often, the most expensive layer fires least and is
rate-limited. This mirrors Anthropic's `security-guidance` hook pattern.

| Layer | Hook event | Fires when | Mechanism | Cost / model |
| --- | --- | --- | --- | --- |
| **Sinker (L1)** | `PostToolUse` matcher `Edit\|Write` | any SKILL.md is edited | Deterministic `validate-skillmd` Tier-2 frontmatter check (agentskills.io plus Claude Code extension-layer compliance). Advisory: surfaces warnings, never blocks. | **$0** (no model call) |
| **Line (L2)** | `Stop` | end of turn, if a skill was invoked and its rollouts are scored | Append the rollout to `.j-rig/refiner/log.jsonl`; once N rollouts accumulate on one skill, fire the refiner in the **background** and surface the candidate next turn. | **$** (Haiku scores, Sonnet refines, paid off-turn) |
| **Hook (L3)** | `PreToolUse` matcher `Bash` | before a `git commit` / `git push` whose staged diff touches a SKILL.md | Agentic gate: read the surrounding skills directory, check the edit against the rejected-edit buffer, optionally shadow-validate against the held-out set. **Can block the commit** via exit code 2. | **$$** (Opus agentic gate, **rate-limited**) |

Why L3 is `PreToolUse:Bash`, not `PostToolUse:Bash` (the plan's v4.1 mechanism
fix): `PreToolUse` is in the Anthropic hooks "Can block" allowlist, so exiting
with code 2 (or emitting `permissionDecision: deny`) blocks the bash call
**before it runs**. `PostToolUse` fires **after** the bash has already executed,
so it cannot prevent the commit or push that triggered it. Only `PreToolUse` can
actually gate the commit.

L3 rate limit: the Opus agentic gate is the most expensive layer, so it is
rate-limited to at most once per `JRIG_HOOK_RATELIMIT_SECONDS` (default 300s /
5 min) via a stamp file at `.j-rig/refiner/.hook-last-run`. Inside the window the
gate is skipped with an advisory note; it only ever **blocks** on a real
regression finding, never on a cost-control skip.

### Design principles inherited from j-rig

- **Criteria are binary**: an edit strictly improves the held-out score or it is
  rejected. No fuzzy gradients.
- **The evaluator is always separate**: the skill under test never scores itself.
- **Observed behavior outranks claimed behavior**: grade what the skill does, not
  what its description says.
- **One change at a time**: each proposal is exactly one atomic edit.
- **Promotion is human-gated**: the refiner proposes and validates; a human moves
  the `best` pointer.

## Output

Every refiner pass writes to two places under the working directory:

- The append-only event log at `.j-rig/refiner/log.jsonl` (one value-record per
  line: rollout captures, stored versions, `best`-pointer moves).
- The content-addressed store under `.j-rig/refiner/store/` (immutable eval sets,
  score records, edit proposals, and skill versions keyed by SHA-256).

Read the trajectory any time with `j-rig refine status <skill-id>`. The refiner
also renders a signed Evidence Report (markdown plus self-contained HTML) via
`j-rig refine render-report <report-md-path>`.

## Error Handling

- **`propose` / `score` fail without a key**: both require `ANTHROPIC_API_KEY`.
  They fail loudly with guidance rather than fabricating a result. Set the key,
  or run the deterministic verbs (`bootstrap`, `apply`, `status`) offline.
- **`apply` rejects a proposal**: `apply` throws on a parent-hash mismatch or a
  bad anchor. This is the immutability guard, not a bug. Re-run `propose` against
  the current version.
- **Non-strict edit rejected**: if a proposed edit does not strictly improve the
  held-out score, the acceptance gate rejects it and logs it to the rejected
  buffer. That is the intended behavior; refine again with a different strategy.
- **L3 hook blocks a commit**: the commit-time agentic gate exits 2 when a staged
  SKILL.md regresses the held-out set. Fix the regression, or run
  `/j-rig refine status <skill-id>` to inspect what tripped it.
- **CLI not installed**: the hooks degrade to advisory notes when the `j-rig`
  binary is absent. Install `@intentsolutions/jrig-cli` to enable the model-backed
  layers.

## Examples

A full refine loop against a skill directory:

```bash
# 1. Create a held-out eval set for the skill (deterministic, offline).
j-rig refine bootstrap skills/my-skill

# 2. Establish the baseline score (Sonnet tier).
j-rig refine score skills/my-skill --model sonnet

# 3. Propose one bounded edit; the acceptance gate shadow-validates it.
ANTHROPIC_API_KEY=... j-rig refine propose skills/my-skill --strategy skill-opt-style

# 4. If accepted, apply it, producing a new candidate version (human-gated promote).
j-rig refine apply skills/my-skill --proposal "<hash>"

# 5. Inspect the trajectory, best pointer, and event log any time.
j-rig refine status my-skill
```

Render the Evidence Report for a completed pass:

```bash
j-rig refine render-report .j-rig/refiner/report.md --output report.html
```

## Resources

- `@intentsolutions/refiner` (refiner orchestrator + the `j-rig refine` command
  group): <https://www.npmjs.com/package/@intentsolutions/refiner>
- `@intentsolutions/jrig-cli` (the `j-rig` binary): <https://www.npmjs.com/package/@intentsolutions/jrig-cli>
- `/skill-creator` — author a new skill from scratch (the refiner improves
  existing skills; skill-creator makes new ones).
- `/validate-skillmd` — the deterministic Tier-2 frontmatter check the L1 Sinker
  hook runs on every SKILL.md edit.
