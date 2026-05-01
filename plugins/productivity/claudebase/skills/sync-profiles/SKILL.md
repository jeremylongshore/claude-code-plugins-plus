---
name: sync-profiles
description: Use when the user wants to list, create, switch, delete, compare, or inspect config sync profiles.
argument-hint: "<list|create|switch|delete|diff|info> [name] [--from existing]"
user-invocable: true
allowed-tools: Bash(bash "${CLAUDE_PLUGIN_ROOT}/scripts/*"), Bash(gh *), Bash(git *), Read
version: 0.2.0
author: Rohit Hazra
license: MIT
---

# Config Sync Profiles

Manage multiple configuration profiles stored in your GitHub backup repo.

## Available actions

### List profiles
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" list
```
Shows all profiles with file counts, last push time, and which is active.

### Create a profile
```bash
# Empty profile
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" create NAME

# Clone from existing profile
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" create NAME --from EXISTING
```
Creates a new profile. Use `--from` to clone an existing profile as a starting point.

### Switch to a profile
Switching means pulling a different profile's config:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/sync-pull.sh" --profile NAME
```
This backs up current config, then applies the target profile. The active profile is updated automatically.

### Delete a profile
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" delete NAME
```
Cannot delete the active profile. Switch to a different one first.

### Compare two profiles
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" diff NAME1 NAME2
```
Shows files that exist in only one profile or differ between them.

### Profile info
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/profile-manager.sh" info NAME
```
Shows metadata and contents of a specific profile.

## Instructions

Parse the user's action from $ARGUMENTS and run the appropriate command above.

If the user says "switch" to a profile, use the pull script with `--profile` rather than the profile-manager (since switching = pulling a different profile).

If no action is specified, default to `list`.

## User Arguments

$ARGUMENTS
