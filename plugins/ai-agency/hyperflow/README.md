<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/hero-vertical.svg" />
    <img src="docs/assets/hero.svg" alt="Hyperflow — init once with scaffold, then the chain: amplify → spec → scope → dispatch → audit → deploy, with thinking/worker tiers and a Worker → Reviewer review at every step" width="100%" />
  </picture>
</p>

<h1 align="center">Hyperflow</h1>

<p align="center">
  <strong>Multi-agent orchestration for Codex App/CLI, Claude Code, OpenCode &amp; Antigravity.</strong><br/>
  Thinking models plan and review every step. Worker models execute in parallel. Learnings persist in local, per-project memory.
</p>

<p align="center">
  <code>amplify</code> → <code>spec</code> → <code>scope</code> → <code>dispatch</code> → <code>audit</code> → <code>deploy</code><br/>
  Start anywhere. Auto-advance forward. Memory persists across sessions.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v4.22.0-blueviolet?style=flat-square" alt="version v4.22.0" />
  &nbsp;
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license" />
  &nbsp;
  <img src="https://img.shields.io/badge/Claude%20marketplace-published-22C55E?style=flat-square" alt="Published on the official Claude plugin marketplace" />
  &nbsp;
  <img src="https://img.shields.io/badge/works%20with-Codex%20%7C%20Claude%20Code%20%7C%20OpenCode%20%7C%20Antigravity-2EA39F?style=flat-square" alt="works with Codex, Claude Code, OpenCode, and Antigravity" />
</p>

<p align="center">
  <a href="https://mohammed-abdelhady.github.io/hyperflow/">Landing site</a> &middot;
  <a href="docs/installation.md">Installation</a> &middot;
  <a href="docs/providers.md">Providers</a> &middot;
  <a href="docs/model-routing.md">Model Routing</a> &middot;
  <a href="docs/orchestration.md">Orchestration</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## What makes it different

Not just another orchestrator — three things set Hyperflow apart:

- **Every step is reviewed.** Worker → Reviewer is an iron rule at every granularity, sub-phases included. No worker output ships unreviewed.
- **Memory that's yours.** Learnings, decisions, and pitfalls persist in `.hyperflow/memory/` — plain markdown, committed with your repo, never uploaded, never mixed across projects. Hot/warm/cold tiering keeps injection cheap.
- **Depth that adapts.** Triage classifies every task and picks a flow profile (fast → scientific), so a 5-line fix never triggers a 300k-token deep run.
- **Compaction at the right boundary.** Automatic context compaction is held until dispatch reaches its end-of-chain gate, then checks estimated transcript usage and snapshots task state before compacting.

Underneath: a structural thinking/worker model split (expensive models plan & review, fast models execute), 15 persona-stitched experts, intent auto-routing, and four auto-detected providers — all local, no daemon.

## The chain

Start with a rough idea — the pipeline carries it to shipped. Start at any entry point; the orchestrator picks up and runs forward.

| # | Skill | What it does |
|---|-------|--------------|
| 1 | `amplify` | **Front door** — rewrite a rough prompt into the strongest version (persona standards + 8-dim rubric), then hand off into the chain |
| 2 | `spec` | Design-first — multi-dimensional analysis + alternatives; refuses to code before you approve |
| 3 | `scope` | Decompose the approved design into a parallel task graph |
| 4 | `dispatch` | Fan out persona-stitched workers under per-batch + final-integration review |
| 5 | `workflow` | Big-task lane — native Claude Code workflows, custom Codex/OpenCode adapter |
| 6 | `audit` | L1–L5 review on the result |
| 7 | `deploy` | Pre-push gates (lint · typecheck · build · tests · security) → commit → release → push |

`amplify` hands off to `spec`, then `spec → scope → dispatch` auto-chains; `audit` and `deploy` are gates that fire at the end. Enter at `spec` for design-first work, `scope` when the approach is clear, `dispatch` when a task file already exists. `scaffold` is a one-time project setup — run it once per repo to build the `.hyperflow/` cache.

`workflow` is the big-task lane. Hyperflow routes deep/scientific/system-wide work, large migrations, repo-wide audits, and high-confidence verification prompts to `/hyperflow:workflow`. In Claude Code v2.1.154+, it asks the native dynamic workflow runtime to create a background workflow with research, parallel execution, adversarial verification, quality gates, and final synthesis. In Codex and OpenCode, it runs the same phases through a portable workflow adapter using provider subagents/tasks when available and inline worker/reviewer phases otherwise.

In Codex App/CLI, `/hyperflow:*` entries are treated as plugin skill aliases, not native host slash commands. If the host does not expose Hyperflow's `AskUserQuestion` popup UI, required gates still fire as concise `Hyperflow Question` chat blocks with numbered choices, then Hyperflow waits for your answer. When Codex subagents are available, Hyperflow maps worker/searcher/writer dispatches to them; otherwise those phases run inline and the chain continues in the same thread.

## Quick start

```bash
claude plugin marketplace add Mohammed-Abdelhady/hyperflow
claude plugin install hyperflow@hyperflow-marketplace
```

Codex App/CLI:

```bash
codex plugin marketplace add Mohammed-Abdelhady/hyperflow
codex plugin add hyperflow@hyperflow-marketplace
```

First initialize the project (once), then invoke any skill:

```text
/hyperflow:scaffold                                        # first: set up the project (once per repo)
/hyperflow:amplify "make a login page"                     # turn a rough idea into a strong prompt
/hyperflow:spec "add user auth with login + middleware"    # design → scope → dispatch
/hyperflow:workflow "large migration across the repo"      # big-task workflow lane
/hyperflow:trace "tests fail after the auth refactor"      # root-cause a bug
/hyperflow:deploy                                          # pre-push gates + ship
```

Codex-safe equivalent:

```text
hyperflow scaffold
hyperflow amplify "make a login page"
hyperflow workflow "large migration across the repo"
hyperflow trace "tests fail after the auth refactor"
```

Auto-routing is on by default — say "audit the diff" or "debug this test" and the right skill runs without the `/hyperflow:*` prefix.

Setup, model routing, and per-provider notes → [Installation](docs/installation.md) · [Providers](docs/providers.md).

## How it works

Invoke a skill. Chain-starters auto-advance through the rest — no always-on orchestrator, no background process, everything in your terminal.

### Thinking / worker split

The split is structural, not a setting — each tier does only what it's best at.

| Tier | Models | Role |
|------|--------|------|
| **Thinking** | GPT-5.5 · Opus 4.8 · Gemini 3 Pro | Orchestrate, triage, brainstorm, review every output, run the final integration pass |
| **Worker** | GPT-5.4 fast mode · Sonnet 4.6 · Gemini 3.5 Flash | Execute in parallel — implement, search, write |

### Review at every granularity

Worker → Reviewer is an iron rule. Independent sub-tasks fan out in parallel; each worker feeds its own thinking-tier reviewer before the batch advances. Every non-trivial phase decomposes into named sub-phases (`2a`, `2b`, `2c`…), each with its own reviewer. Per-batch reviewers do L1–L2 spot-checks; a final integration reviewer runs once over the cumulative diff. Each reviewer returns a verdict — `APPROVE` or `NEEDS_REVISION` (retry once with findings injected).

### Triage picks the depth

Every task is classified — complexity, scope, risk, ambiguity — and assigned a flow profile, so effort matches the work instead of always running deep:

| Profile | Use when | Workers | Budget |
|---------|----------|---------|--------|
| `fast` | trivial single-file, reversible | 1 | ≤30k |
| `standard` | simple/moderate, 2–5 files | 1–2 | ≤100k |
| `deep` | complex / cross-cutting / system-wide | 3+ | 300k |
| `research` | unknown territory, evaluation | 3+ searchers | ≤80k |
| `creative` | UI/UX exploration | 1–2 | ≤150k |
| `scientific` | correctness-critical, proof work | 2–3 + TDD | 300k |

### Persona stitching

15 composable expert personas — architect, api, db, frontend, ui, security, performance, scientific, refactor, bugfix, test, research, creative, devops, docs. Each task is tagged and the matching personas are stitched into the worker prompt in priority order: `security` frames every decision first, `creative` adapts last.

### Workflows for big tasks

Hyperflow routes very large tasks to `/hyperflow:workflow` instead of forcing everything through turn-by-turn dispatch. Use it for system-wide changes, large migrations, repo-wide audits, and verification-heavy work.

In Claude Code, the skill uses native dynamic workflows. This requires Claude Code v2.1.154+ with workflows enabled; workflows can be disabled by `/config`, managed settings, `~/.claude/settings.json`, or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`. Hyperflow does not set `/effort ultracode` or `xhigh` automatically. Use `/effort ultracode` yourself if you want Claude Code's session-wide automatic workflow selection.

In Codex and OpenCode, the same command runs a custom Hyperflow workflow adapter: research and planning, provider subagents/tasks or inline worker phases, adversarial verification, quality gates, per-task commits, and final synthesis. This is not native Claude-style saved workflow support; repeatability comes from the skill, `.hyperflow/tasks/`, memory, and provider-specific subagent/task configuration.

## Memory that persists

Learnings live at `.hyperflow/memory/` — plain markdown, committed with your repo, **never uploaded, never mixed across projects**.

- **Three tiers** — `hot` (≤7 days, always injected), `warm` (8–30 days, tag-matched), `cold` (30+ days, on-demand, compressed).
- **Lazy injection** — only tag-matched entries load for a given task, so injection cost stays bounded.
- **Auto-written by the chain** — `audit` records recurring findings to `anti-patterns.md` (hot); `spec` records structural answers to `project-decisions.md`, so the same questions aren't asked twice.

Full walkthrough → [Orchestration](docs/orchestration.md) · [Landing site](https://mohammed-abdelhady.github.io/hyperflow/).

## Skills

Fifteen skills. Three chain-starters auto-advance through the chain; the rest are standalone. Auto-routing is on by default — say the verb and the right skill runs without the `/hyperflow:*` prefix. In Codex, `hyperflow <skill>` is the safest portable spelling, with `/hyperflow:*` handled as an alias.

| Skill | Command | Type | Purpose |
|-------|---------|------|---------|
| `spec` | `/hyperflow:spec` | Chain starter | Design-first analysis + alternatives; auto-chains to scope → dispatch |
| `scope` | `/hyperflow:scope` | Chain starter | Decompose into parallel worker subtasks; auto-chains to dispatch |
| `dispatch` | `/hyperflow:dispatch` | Endpoint | Fan out persona-stitched workers under per-batch + final review |
| `workflow` | `/hyperflow:workflow` | Big-task lane | Native Claude Code workflows; custom Codex/OpenCode adapter for migrations, audits, and verification-heavy work |
| `scaffold` | `/hyperflow:scaffold` | Standalone | Project setup — `.hyperflow/` cache + multi-tool shims |
| `amplify` | `/hyperflow:amplify` | Front door | Rewrite a rough prompt into the strongest version (persona standards + 8-dim rubric), then hand off into the chain |
| `trace` | `/hyperflow:trace` | Standalone | Systematic root-cause debugging — 5 Whys, never patches symptoms |
| `audit` | `/hyperflow:audit` | Standalone | L1 quick → L5 exhaustive review on changes, files, or PRs |
| `deploy` | `/hyperflow:deploy` | Standalone | Pre-push gates → commit → release → push (push always asks) |
| `cache` | `/hyperflow:cache` | Standalone | Memory CRUD — show, search, add, prune, archive, compact |
| `status` | `/hyperflow:status` | Standalone | Read-only snapshot — version, memory count, live per-task progress |
| `background` | `/hyperflow:background` | Standalone | List, show, cancel, prune task-level background agents |
| `sticky` | `/hyperflow:sticky` | Standalone | `on` / `auto` / `off` — per-project auto-routing mode |
| `bridge` | `/hyperflow:bridge` | Standalone | Embed the portable doctrine into `CLAUDE.md` for Desktop / web / IDE |
| `flush` | `/hyperflow:flush` | Standalone | Flush a deferred-commit queue from a prior or crashed chain |

## Providers

| Provider | Thinking | Worker |
|----------|----------|--------|
| Codex App/CLI | GPT-5.5 (adaptive reasoning) | GPT-5.4 (fast mode) |
| Claude Code | Opus 4.8 | Sonnet 4.6 |
| OpenCode | Claude Opus 4.8 | Sonnet 4.6 |
| Antigravity | Gemini 3 Pro | Gemini 3.5 Flash |

Auto-detected at session start. Override in `~/.hyperflow/config.json`. See [Model Routing](docs/model-routing.md).

## Documentation

- [Landing site](https://mohammed-abdelhady.github.io/hyperflow/) — the full overview
- [Installation](docs/installation.md) · [Providers](docs/providers.md) · [Model Routing](docs/model-routing.md) · [Orchestration](docs/orchestration.md)
- [Changelog](CHANGELOG.md) · [Privacy](PRIVACY.md) · contributor guide in [`CLAUDE.md`](CLAUDE.md)

## License

MIT
