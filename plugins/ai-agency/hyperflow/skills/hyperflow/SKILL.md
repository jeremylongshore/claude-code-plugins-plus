---
name: hyperflow
description: "Use when applying Hyperflow's orchestration doctrine in Codex, Antigravity, or another single-agent surface. Auto-invoke for non-trivial engineering work: build, implement, add, refactor, debug, fix, review, audit, plan, scope, design, brainstorm, ship, or deploy."
---

# Hyperflow Doctrine (single-agent port)

Apply Hyperflow's behavioral floor in surfaces that load skills but do not provide the full Claude Code multi-agent runtime.

## Runtime Adaptation

Codex and Antigravity run one foreground agent. Where the full doctrine says to dispatch parallel workers under reviewers:

- Do the work yourself, one coherent batch at a time.
- Self-review each batch before moving on.
- Run a final integration self-review over the cumulative diff.
- Preserve the same autonomy, clarification, commit cadence, file-first artefact, no-attribution, and security rules.

## Codex Function Router

Codex loads Hyperflow as skills, not as native Claude-style slash commands. Treat these user messages as function aliases and execute the matching skill workflow inline in the current thread:

| User says | Run |
|---|---|
| `/hyperflow:amplify`, `hyperflow amplify`, `use hyperflow amplify` | `amplify` |
| `/hyperflow:spec`, `hyperflow spec`, `design with hyperflow` | `spec` |
| `/hyperflow:scope`, `hyperflow scope`, `decompose with hyperflow` | `scope` |
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

Do not answer that `/hyperflow:*` is an unknown command in Codex. Strip the alias, load the matching `skills/<name>/SKILL.md`, and follow its workflow. If that workflow says to use unavailable Claude Code tools (`Agent`, `Skill`, or `AskUserQuestion`), emulate them: do worker/reviewer steps inline with visible labels, continue chained skills inline, and use the Codex question fallback below.

## Codex Subagents And Auto-Chain

When Codex exposes multi-agent tools, map Hyperflow agent dispatches to Codex subagents instead of falling back to inline work:

- Hyperflow `Agent` worker/searcher/writer calls map to Codex worker or explorer subagents.
- If the callable tool is named `multi_agent_v1.spawn_agent`, use `agent_type: worker` for implementer/writer execution and `agent_type: explorer` for search/codebase-research tasks, then collect results before review.
- Spawn independent sibling workers together when the runtime supports parallel subagent calls.
- Worker roles use `gpt-5.4` with `low` reasoning in fast mode when model overrides are available and Hyperflow Codex defaults are active.
- Thinking roles stay in the foreground on `gpt-5.5` with task-adaptive reasoning: `low` for trivial docs/config checks, `medium` for normal planning/review, and `high` for debugging, architecture, security, or final integration review.
- Never request or default to `xhigh`.

When Codex does not expose subagent tools in the current session, use the single-agent port above: execute worker/reviewer phases inline with clear labels and continue.

For `/hyperflow:workflow`, use the Codex portable workflow adapter instead of falling back to `scope`: research and planning, `.hyperflow/tasks/` progress tracking when needed, parallel subagents when exposed, inline worker/reviewer phases otherwise, adversarial verification, quality gates, per-task conventional commits, and final synthesis. Do not describe this as native Claude Code dynamic workflow support.

Codex also may not expose Claude Code's `Skill` handoff tool. Treat every Hyperflow handoff as an inline auto-chain:

- `amplify` handoff continues into `spec` after the required handoff gate.
- `spec` continues into `scope` after the approved spec.
- `scope` continues into `dispatch` after writing the task file.
- `dispatch` offers `audit` and `deploy` structural gates, then runs the selected follow-up inline.
- `audit` fix gates continue into `scope` with the generated audit-fix spec.

Do not stop with "Skill tool unavailable" in Codex. Auto-chain is a behavior contract, not a host API requirement.

## Codex Interaction Fallback

Codex may load Hyperflow skills without exposing the full `AskUserQuestion` popup UI. In that case, do not skip the question or silently choose the recommended option. Render the same structural gate as a concise chat block and wait for the user's answer:

```text
Hyperflow Question
<question>

1. <recommended option> (Recommended) — <short consequence>
2. <option> — <short consequence>
```

Use this fallback for every required clarification or structural gate: Amplify handoff, Spec chain mode, Spec brainstorming questions, Scope ambiguity questions, Dispatch audit/deploy gates, Audit fix gate, Deploy commit-inclusion and push gates, and any security/irreversibility escalation. It is still banned to ask invented confirmation questions such as "should I proceed?".

## Codex Model Policy

- Thinking roles use `gpt-5.5`.
- Worker roles use `gpt-5.4` in fast mode.
- Resolve thinking reasoning by task/profile: `low` for trivial docs/config checks, `medium` for normal planning/review, and `high` for debugging, architecture, security, and final integration.
- Never default Codex reasoning to `xhigh`.

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
| `big task`, `large migration`, `repo-wide audit`, `run a workflow`, `dynamic workflow` | Use the workflow skill: Claude Code native workflow, Codex/OpenCode portable adapter, otherwise decompose through `scope` |
| `build`, `implement`, `add`, `refactor` | Decompose, execute batches, self-review, commit per task |
| `debug`, `fix it`, "why is X failing" | Root-cause before patching |
| `audit`, `review`, "check for issues" | Review findings first, then offer/apply fixes |
| `ship`, `push`, `release`, `deploy` | Run gates, commit/release, ask before push |

For full multi-agent doctrine, read `DOCTRINE.md` and the linked reference files in this directory.
