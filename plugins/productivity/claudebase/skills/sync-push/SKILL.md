---
name: sync-push
description: Use when the user wants to back up, save, or push their current Claude Code config to GitHub.
argument-hint: "[--profile NAME] [--force] [--dry-run] [--include-global]"
user-invocable: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/scripts/*"), Bash(gh *), Bash(git *), Read
version: 0.2.0
author: Rohit Hazra
license: MIT
---

# Config Sync Push

Push your current local Claude Code configuration to the GitHub backup repo.

## What gets pushed

All syncable files from the current project and global config:
- `.mcp.json`, `.claude/settings.json`
- `.claude/agents/`, `.claude/commands/`, `.claude/skills/`
- `.claude/hooks/` (scripts, config, sounds)
- `.claude/rules/`, `.claude/agent-memory/`
- `.auto-memory/` (memory files)
- `~/.claude/settings.json` (global settings, opt-in via `--include-global`)

Files that are **never** pushed: `CLAUDE.md` (version-controlled with project), `settings.local.json`, `hooks-config.local.json`, conversations, sessions.

## Instructions

Parse user arguments and run the push script:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/sync-push.sh" [OPTIONS]
```

**Options:**
- `--profile NAME` — Push to a specific profile (default: active profile)
- `--force` — Skip multi-machine safety check and secret warnings
- `--dry-run` — Show what would be pushed without actually pushing
- `--include-global` — Also push `~/.claude/settings.json` (global settings are opt-in)

### Multi-machine warning

If the script warns about another machine having pushed more recently, advise the user to pull first (`/sync-pull`) or use `--force` if they're sure.

### Secret detection

If the script warns about potential secrets, tell the user which files were flagged and suggest reviewing them before using `--force`.

## User Arguments

$ARGUMENTS
