---
name: sync-config
description: Use when the user wants to view or change claudebase settings like global sync, agent skills sync, auto-push, or machine ID.
argument-hint: "[show] | [set <key> <value>] | [get <key>] | [reset <key>]"
user-invocable: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/scripts/*"), Read
version: 0.2.0
author: Rohit Hazra
license: MIT
---

# Config Sync Settings

View and modify claudebase configuration.

## Instructions

Run the config manager script with the appropriate action:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/config-manager.sh" ACTION [KEY] [VALUE]
```

### Actions

- **show** (default) — Display all current settings
- **set `<key>` `<value>`** — Change a setting
- **get `<key>`** — Read a single setting
- **reset `<key>`** — Remove a setting (revert to default)

### Configurable keys

| Key | Values | Description |
|-----|--------|-------------|
| `include_global` | `true`/`false` | Sync `~/.claude/settings.json` on push/pull |
| `sync_agent_skills` | `true`/`false` | Sync `skills-lock.json` (lock file only; prints install commands on pull) |
| `auto_push` | `true`/`false` | Auto-push config when a Claude Code session ends |
| `machine_id` | any string | Identifier for this machine (used in multi-machine warnings) |

### Examples

- `/sync-config` — show all settings
- `/sync-config set include_global true` — enable global settings sync
- `/sync-config set auto_push false` — disable auto-push

## User Arguments

$ARGUMENTS
