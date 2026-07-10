---
name: hyperflow
description: |
  Use when applying Hyperflow's orchestration doctrine in Codex, Antigravity, Grok, or another single-agent surface. Auto-invoke for non-trivial engineering work: build, implement, add, refactor, debug, fix, review, audit, plan, scope, design, brainstorm, ship, or deploy.
  Trigger with /hyperflow:hyperflow, "use hyperflow", "apply the doctrine", or automatically on any task-shaped message.
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Skill, AskUserQuestion, WebSearch, WebFetch, Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Bash(python3:*)
argument-hint: "[task]"
version: 1.0.0
license: MIT
compatibility: Portable doctrine — Claude Code, Codex App/CLI, OpenCode, Antigravity, Cursor, Grok
tags: [orchestration, doctrine, autonomy, multi-agent, portable]
---

# Hyperflow Doctrine (single-agent port)

Apply Hyperflow's behavioral floor in surfaces that load skills but do not provide the full Claude Code multi-agent runtime.

## Runtime Adaptation

Codex, OpenCode, Antigravity, and Grok often run one foreground agent (or a host-specific subagent API). Where the full doctrine says to dispatch parallel workers under reviewers:

- Prefer the host's subagent API when it exists (Codex spawn, OpenCode Task, Grok `spawn_subagent`).
- Otherwise do the work yourself, one coherent batch at a time.
- Self-review each batch before moving on.
- Run a final integration self-review over the cumulative diff.
- Preserve the same autonomy, clarification, commit cadence, file-first artefact, no-attribution, and security rules.

## Portable Function Router (Codex / OpenCode / Grok)

These hosts load Hyperflow as skills, not as native Claude-style slash commands. Treat these user messages as function aliases and execute the matching skill workflow inline in the current thread:

| User says | Run |
|---|---|
| `/hyperflow:plan`, `hyperflow plan`, `design with hyperflow`, `decompose with hyperflow` | `plan` |
| `/hyperflow:dispatch`, `hyperflow dispatch`, `run the hyperflow plan` | `dispatch` |
| `/hyperflow:workflow`, `hyperflow workflow`, `run a workflow` | `workflow` |
| `/hyperflow:trace`, `hyperflow trace`, `debug with hyperflow` | `trace` |
| `/hyperflow:audit`, `hyperflow audit`, `review with hyperflow` | `audit` |
| `/hyperflow:deploy`, `hyperflow deploy`, `ship with hyperflow` | `deploy` |
| `/hyperflow:cache`, `hyperflow cache` | `cache` |
| `/hyperflow:status`, `hyperflow status` | `status` |
| `/hyperflow:sticky`, `hyperflow sticky` | `sticky` |
| `/hyperflow:bridge`, `hyperflow bridge` | `bridge` |
| `/hyperflow:flush`, `hyperflow flush` | `flush` |
| `/hyperflow:background`, `hyperflow background` | `background` |
| `/hyperflow:scaffold`, `hyperflow scaffold` | `scaffold` |

Do not answer that `/hyperflow:*` is an unknown command on these surfaces. Strip the alias, load the matching `skills/<name>/SKILL.md`, and follow its workflow. If that workflow says to use unavailable Claude Code tools (`Agent`, `Skill`, or `AskUserQuestion`), emulate them: do worker/reviewer steps inline with visible labels, continue chained skills inline, and use the interaction fallback below when a structured question UI is missing.

## Subagents And Auto-Chain

### Codex

When Codex exposes multi-agent tools, map Hyperflow agent dispatches to Codex subagents instead of falling back to inline work:

- Hyperflow `Agent` worker/searcher/writer calls map to Codex worker or explorer subagents.
- If the callable tool is named `multi_agent_v1.spawn_agent`, use `agent_type: worker` for implementer/writer execution and `agent_type: explorer` for search/codebase-research tasks, then collect results before review.
- Spawn independent sibling workers together when the runtime supports parallel subagent calls.
- Every agent runs on the current session model — do not switch models per role. Match reasoning effort to task complexity: `low` for trivial docs/config checks, `medium` for normal planning/review, `high` for debugging, architecture, security, or final integration review.
- Never request or default to `xhigh`.

When Codex does not expose subagent tools in the current session, use the single-agent port above: execute worker/reviewer phases inline with clear labels and continue.

### Grok

Grok CLI / Grok Build loads skills from `~/.grok/skills/`, project `.grok/skills/`, and compatible Claude/Cursor skill dirs. Project rules come from `AGENTS.md` / `CLAUDE.md` and `.grok/rules/`. Runtime signal often includes `GROK_AGENT=1`.

When Grok exposes `spawn_subagent`, map Hyperflow dispatches as follows:

| Hyperflow role | Grok `subagent_type` |
|---|---|
| implementer / writer / general worker | `general-purpose` |
| searcher / codebase research | `explore` |
| plan-only research (no file writes) | `plan` |
| domain specialists (`architect`, `security-reviewer`, …) | matching type if registered; else `general-purpose` with the specialist charter in the prompt |

- Spawn independent sibling workers together when the runtime supports parallel subagent calls.
- If subagents are disabled (`GROK_SUBAGENTS=0` or config), run worker/reviewer phases inline with clear labels.
- Prefer the native `AskUserQuestion` tool for structural gates when available.
- Every agent runs on the current session model — no per-role model selection.
- Do not invent Claude Code `Agent` tool calls; use `spawn_subagent` or inline work.

### Auto-chain (all portable hosts)

For `/hyperflow:workflow`, use the portable workflow adapter (Codex / OpenCode / Grok branches in the workflow skill) instead of falling back to `scope`: research and planning, `.hyperflow/tasks/` progress tracking when needed, parallel subagents when exposed, inline worker/reviewer phases otherwise, adversarial verification, quality gates, per-task conventional commits, and final synthesis. Do not describe this as native Claude Code dynamic workflow support.

These hosts may not expose Claude Code's `Skill` handoff tool. Treat every Hyperflow handoff as an inline auto-chain:

- `plan` runs amplify → design → decompose inline, then **stops at its build-location gate** (always asked). It never auto-implements: on "this session" it continues into `dispatch` inline; on "another session" it writes a handoff package; on "stop" it keeps the plan.
- `dispatch` offers `audit` and `deploy` structural gates, then runs the selected follow-up inline.
- `audit` fix gates continue into `plan` with the generated audit-fix task (which then stops at its own build-location gate).

Do not stop with "Skill tool unavailable". Auto-chain is a behavior contract, not a host API requirement.

## Interaction Fallback

When a host lacks a structured question UI (or `AskUserQuestion` is unavailable), do not skip the question or silently choose the recommended option. Render the same structural gate as a concise chat block and wait for the user's answer:

```text
Hyperflow Question
<question>

1. <recommended option> (Recommended) — <short consequence>
2. <option> — <short consequence>
```

Use this fallback for every required clarification or structural gate: Amplify handoff, Spec chain mode, Spec brainstorming questions, Scope ambiguity questions, Dispatch audit/deploy gates, Audit fix gate, Deploy commit-inclusion and push gates, and any security/irreversibility escalation. It is still banned to ask invented confirmation questions such as "should I proceed?".

On Grok, prefer the native `AskUserQuestion` tool when present; use the chat-block fallback only if that tool is missing.

## Reasoning Policy

- Every agent runs on the current session model — there is no per-role model selection.
- Resolve reasoning effort by task/profile: `low` for trivial docs/config checks, `medium` for normal planning/review, and `high` for debugging, architecture, security, and final integration.
- Never default portable hosts to exotic max-effort modes (e.g. Codex `xhigh`).

## Core Rules

1. Execute task-shaped requests without confirmation.
2. Clarify only after reading the relevant code and only for genuine ambiguity.
3. Keep long-form plans, specs, task decompositions, and audits under `.hyperflow/`.
4. Use conventional commits, one distinct user task per commit.
5. Never reference the model as the actor in commits, docs, comments, task files, or memory.
6. Respect the security blocklist in `security.md`.

## Workflow Routing

| Intent | Workflow |
|---|---|
| `brainstorm`, `design`, `explore`, "should we" | Research first, ask material questions, then propose approaches |
| `scope`, `decompose`, "plan out" | Map affected files, then write a task graph under `.hyperflow/tasks/` |
| `big task`, `large migration`, `repo-wide audit`, `run a workflow`, `dynamic workflow` | Use the workflow skill: Claude Code native workflow, or Codex/OpenCode/Grok portable adapter, otherwise decompose through `scope` |
| `build`, `implement`, `add`, `refactor` | Decompose, execute batches, self-review, commit per task |
| `debug`, `fix it`, "why is X failing" | Root-cause before patching |
| `audit`, `review`, "check for issues" | Review findings first, then offer/apply fixes |
| `ship`, `push`, `release`, `deploy` | Run gates, commit/release, ask before push |

For full multi-agent doctrine, read `DOCTRINE.md` and the linked reference files in this directory.
