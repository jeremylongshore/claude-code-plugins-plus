---
name: hyperflow-scaffold
description: Hyperflow project setup. Use when starting hyperflow in a new project or refreshing its cache — "init hyperflow", "set up hyperflow", "refresh hyperflow", "scaffold hyperflow". One-shot setup of the .hyperflow/ project cache + memory and the .agent/workflows/hyperflow* slash commands. Does not start the spec → scope → dispatch chain.
---

# hyperflow-scaffold — project setup (Antigravity single-agent)

One-shot setup of hyperflow's project surfaces. Follow the `hyperflow` doctrine.

## Steps

1. **Create the `.hyperflow/` cache** at the repo root if absent:
   - `.hyperflow/memory/` with `decisions.md`, `learnings.md`, `pitfalls.md`, `patterns.md` (empty stubs, each with a one-line header).
   - `.hyperflow/tasks/`, `.hyperflow/specs/`, `.hyperflow/audits/` (empty dirs).
2. **Write context files** (`.hyperflow/profile.md`, `architecture.md`, `conventions.md`) by reading the repo: stack, top-level layout, test/lint conventions, commit conventions. Keep each short and factual.
3. **Install project slash commands**: copy the seven `hyperflow*` workflow files into `<repo>/.agent/workflows/` (so `/hyperflow`, `/hyperflow-spec`, … resolve in Antigravity's `/` menu). Source: the `templates/antigravity/workflows/` shipped with hyperflow.
4. **Note** that global hyperflow skills live in `~/.gemini/config/skills/` (auto-trigger) and global rules in `~/.gemini/AGENTS.md`.
5. Print a one-line summary of what was created. Do NOT start the chain.

## Rules

- Idempotent — never clobber existing `.hyperflow/` content; only create what's missing.
- `.hyperflow/tasks` and `.hyperflow/specs` are runtime artefacts; `.hyperflow/memory` is durable and worth committing.
