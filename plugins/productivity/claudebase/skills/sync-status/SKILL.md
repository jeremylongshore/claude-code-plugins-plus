---
name: sync-status
description: Use when the user wants to check what config has changed, see sync status, or compare local vs remote config.
user-invocable: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/scripts/*"), Bash(gh *), Bash(git *), Read
version: 0.2.0
author: Rohit Hazra
license: MIT
---

# Config Sync Status

Compare your local Claude Code configuration against what's stored in the GitHub backup repo.

## Instructions

Run the diff script:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/diff-config.sh" --profile PROFILE_NAME
```

If the user doesn't specify a profile, omit the `--profile` flag (uses active profile).

### Interpreting output

The script shows each tracked file/directory with a status:

- `+ local only` (green) — Exists locally but hasn't been pushed yet
- `+ remote only` (cyan) — Exists in the repo but hasn't been pulled yet
- `~ modified` (yellow) — Exists in both but differs

### Recommendations

Based on the output, suggest the appropriate action:
- Local-only files → suggest `/sync-push`
- Remote-only files → suggest `/sync-pull`
- Modified files → suggest checking what changed, then push or pull

## User Arguments

$ARGUMENTS
