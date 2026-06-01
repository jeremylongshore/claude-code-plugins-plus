---
title: "Fixing Claude Code Hooks: The New Matcher Format"
description: "Fixing Claude Code Hooks: The New Matcher Format"
date: "2026-02-04"
tags: ["claude-code", "debugging", "configuration", "hooks"]
featured: false
---
Claude Code recently changed their hooks format, and if you haven't updated your project settings, you'll see this cryptic error:

```
hooks: Expected array, but received undefined
Files with errors are skipped entirely, not just the invalid settings.
```

## The Problem

The old hook format put `command` at the top level:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "command": "bash .claude/hooks/my-script.sh"
      }
    ]
  }
}
```

This silently breaks - your entire settings file gets skipped.

## The Fix

The new format requires a nested `hooks` array with explicit `type`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/my-script.sh"
          }
        ]
      }
    ]
  }
}
```

Key changes:

1. **`matcher`** - Must be a valid regex (`".*"` matches everything, empty string doesn't work)
2. **`hooks`** - Now an array inside the matcher object
3. **`type`** - Required field, set to `"command"` for shell commands

## Quick Migration

Find all your `.claude/settings.json` files and update them:

```bash
# Find all Claude settings files
find ~/projects -name "settings.json" -path "*/.claude/*" 2>/dev/null
```

Then update each one to the new format.

## Related

- [Fixing Claude Code EACCES Multi-User Linux Permissions](/blog/fixing-claude-code-eacces-multi-user-linux-permissions/)
- [Debugging Claude Code Slash Commands](/blog/debugging-claude-code-slash-commands-silent-deployment-failures/)
