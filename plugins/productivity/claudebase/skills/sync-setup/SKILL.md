---
name: sync-setup
description: Use when the user wants to set up config sync for the first time, connect to GitHub, or re-initialize the backup repo.
argument-hint: "[repo-name] [profile-name]"
user-invocable: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/scripts/*"), Bash(gh *), Bash(git *), Read, Write
version: 0.2.0
author: Rohit Hazra
license: MIT
---

# Config Sync Setup

Initialize Claude Config Sync by connecting to GitHub and creating the backup repository.

## What this does

1. Verifies `gh` CLI is installed and authenticated
2. Creates a **private** GitHub repo for config storage (or connects to existing)
3. Initializes the repo structure with a default profile
4. Performs the first push of your current Claude Code config

## Instructions

Run the setup script. Parse user arguments for custom repo name and profile:

- First argument (if provided): repo name (default: `claude-config`)
- Second argument (if provided): initial profile name (default: `default`)

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/ensure-repo.sh" REPO_NAME PROFILE_NAME
```

Replace REPO_NAME and PROFILE_NAME with the user's values or defaults.

### If `gh` is not installed

Guide the user to install it:
- **macOS**: `brew install gh`
- **Linux**: `sudo apt install gh` or `sudo dnf install gh`
- **Windows**: `winget install --id GitHub.cli`

Then authenticate: `gh auth login`

### After setup succeeds

Run the first push automatically:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/sync-push.sh" --profile PROFILE_NAME
```

Tell the user what was synced and show all available commands: `/sync-push`, `/sync-pull`, `/sync-status`, `/sync-profiles`, `/sync-config`.

## User Arguments

$ARGUMENTS
