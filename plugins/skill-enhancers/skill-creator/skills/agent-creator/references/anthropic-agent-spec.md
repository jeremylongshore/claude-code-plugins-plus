# Anthropic Agent Spec — Official Reference

Source: https://code.claude.com/docs/en/sub-agents (fetched 2026-04-05)

## Supported Frontmatter Fields

Only `name` and `description` are required.

| Field | Required | Description |
|:------|:---------|:------------|
| `name` | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | Yes | When Claude should delegate to this subagent |
| `tools` | No | Tools the subagent can use (allowlist). Inherits all tools if omitted |
| `disallowedTools` | No | Tools to deny, removed from inherited or specified list |
| `model` | No | `sonnet`, `opus`, `haiku`, a full model ID, or `inherit`. Defaults to `inherit` |
| `permissionMode` | No | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, or `plan` |
| `maxTurns` | No | Maximum number of agentic turns before the subagent stops |
| `skills` | No | Skills to load into the subagent's context at startup (full content injected) |
| `mcpServers` | No | MCP servers available to this subagent (inline definition or string reference) |
| `hooks` | No | Lifecycle hooks scoped to this subagent |
| `memory` | No | Persistent memory scope: `user`, `project`, or `local` |
| `background` | No | Set to `true` to always run as background task. Default: `false` |
| `effort` | No | `low`, `medium`, `high`, `max` (Opus 4.6 only). Default: inherits from session |
| `isolation` | No | `worktree` — run in temporary git worktree |
| `color` | No | Display color: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |
| `initialPrompt` | No | Auto-submitted as first user turn when running as main agent via `--agent` |

Total: 16 official fields.

## Key Facts

- The **body** (markdown after frontmatter) becomes the **system prompt** that guides the subagent
- Subagents receive ONLY the system prompt + basic environment details, NOT the full Claude Code system prompt
- `tools` is an **allowlist** (like skills' `allowed-tools`)
- `disallowedTools` is a **denylist** — if both set, disallowed applied first, then tools resolved
- Subagents **cannot spawn other subagents** (no nesting)
- Subagents **don't inherit skills** from parent conversation — must list explicitly via `skills` field

## Plugin Agent Restrictions

Plugin agents (`plugins/*/agents/*.md`) do NOT support:

- `hooks` — ignored when loading from plugin
- `mcpServers` — ignored when loading from plugin
- `permissionMode` — ignored when loading from plugin

These are standalone-only features. If needed, copy the agent to `.claude/agents/` or `~/.claude/agents/`.

## Tool Scoping

Subagents can use `Agent(type)` syntax to restrict which subagents they can spawn (only for main-thread agents via `--agent`).

## Skills Preloading

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

Full content of each skill is injected at startup. This is the inverse of `context: fork` in skills.

## Model Resolution Order

1. `CLAUDE_CODE_SUBAGENT_MODEL` env var
2. Per-invocation `model` parameter
3. Subagent definition's `model` frontmatter
4. Main conversation's model

## Example Agent File

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

## Scope Priority (highest to lowest)

1. Managed settings (organization-wide)
2. `--agents` CLI flag (current session only)
3. `.claude/agents/` (project)
4. `~/.claude/agents/` (personal)
5. Plugin `agents/` directory (where plugin enabled)
