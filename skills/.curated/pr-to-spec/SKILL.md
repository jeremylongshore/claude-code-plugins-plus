---
name: pr-to-spec
description: Analyze code changes and detect intent drift using the pr-to-spec CLI — converts a branch, staged edits, or recent commits into a structured, agent-consumable spec. Use when declaring intent before a change, checking a finished change for drift against that intent, or generating a spec for agent review. Trigger with "/pr-to-spec", "pr-to-spec scan", "pr-to-spec check", or "pr-to-spec intent".
version: 0.8.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Requires the pr-to-spec CLI on PATH (Node.js 18+; ships with this plugin) and a git repository to analyze. Runs in Claude Code or any agent runtime with shell access.
tags: [git, pr, spec, intent-drift, code-review, agent-protocol]
argument-hint: "[scan | check | intent set | intent show]"
allowed-tools: ["Bash(pr-to-spec:*)"]
---

# pr-to-spec Skill

## Overview

Convert code changes into structured, agent-consumable specs with intent
drift detection. The workflow is: declare what a change is supposed to do
(`intent set`), make the changes, then `check` — the CLI produces a spec of
what actually changed plus drift signals against the declared intent, wrapped
in a versioned JSON envelope any agent can consume.

## Prerequisites

- The `pr-to-spec` CLI on PATH (it ships with this plugin; standalone install
  and MCP-server usage are covered in the repo README).
- A git repository with something to analyze — a branch diverging from main,
  staged edits, or recent commits.

## Usage

### /pr-to-spec scan
Analyze current branch changes vs main and output a structured spec.

```bash
pr-to-spec scan --branch main --json
```

Use `--diff N` to scan last N commits, or `--staged` for staged changes only.

### /pr-to-spec check
Scan current changes AND check for drift against declared intent.

```bash
pr-to-spec check --json
```

Returns exit code 3 if drift is detected, 2 if high-risk, 0 if clean.

### /pr-to-spec intent set
Declare what this change is supposed to do.

```bash
pr-to-spec intent set --goal "Add rate limiting to API" --scope "src/middleware/**" --forbid "src/db/**" --max-risk medium
```

### /pr-to-spec intent show
Show the current intent declaration.

```bash
pr-to-spec intent show --json
```

## Output format

All `--json` output is wrapped in the agent protocol envelope:

```json
{
  "version": 1,
  "command": "check",
  "status": "drift_detected",
  "exit_code": 3,
  "signals": [...],
  "spec": {...},
  "intent": {...}
}
```

The `spec` field is the structured description of what changed, `intent` is
the declared intent (when one exists), and `signals` carries the drift and
risk findings that produced the `status` and `exit_code`.

## Error Handling

Interpret exit codes — they are the contract:

| Code | Meaning |
|------|---------|
| 0 | Clean — no issues |
| 1 | Error |
| 2 | High-risk changes detected |
| 3 | Drift detected |

- **Exit 3 (drift)** — the change touched files outside the declared scope,
  hit a `--forbid` pattern, or diverged from the declared goal. Stop and
  investigate before continuing; either fix the change or re-declare intent
  deliberately.
- **Exit 2 (high-risk)** — the change exceeds the declared `--max-risk`
  ceiling. Review the `signals` array for which risk flags fired.
- **Exit 1 (error)** — the CLI itself failed (not a git repo, no intent
  declared for `check`, malformed arguments). The message on stderr says
  which; fix the invocation rather than the code.

## Examples

Full declare → change → check loop:

```bash
pr-to-spec intent set --goal "Add rate limiting to API" --scope "src/middleware/**" --forbid "src/db/**" --max-risk medium
# ...make the changes...
pr-to-spec check --json    # exit 0 = clean, 2 = high-risk, 3 = drift
```

Wire it into a project's CLAUDE.md so every significant change runs the loop:

```markdown
## Change Validation

Before any significant code change:
1. Set intent: `pr-to-spec intent set --goal "..." --scope "..." --max-risk medium`
2. After changes: `pr-to-spec check --json` — exit 3 means drift, investigate before continuing
```

## Resources

- [Repository README](https://github.com/jeremylongshore/pr-to-prompt/blob/main/README.md) — quick start, GitHub PR analysis, and the MCP server
- [Documentation site](https://jeremylongshore.github.io/pr-to-prompt/) — full CLI and agent-protocol reference
- [Examples directory](https://github.com/jeremylongshore/pr-to-prompt/tree/main/examples) — sample envelopes and integrations
