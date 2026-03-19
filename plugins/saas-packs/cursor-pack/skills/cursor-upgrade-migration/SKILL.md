---
name: "cursor-upgrade-migration"
description: |
  Execute upgrade Cursor versions and migrate settings. Triggers on "upgrade cursor",
  "update cursor", "cursor migration", "cursor new version", "cursor changelog". Use when working with cursor upgrade migration functionality. Trigger with phrases like "cursor upgrade migration", "cursor migration", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

Provides guidance for upgrading Cursor IDE versions and migrating settings between installations. It covers version checking, upgrade methods, settings backup, and troubleshooting common migration issues.

## Prerequisites

- Current Cursor installation to upgrade
- Backup of current settings (recommended)
- Admin rights for installation (if required)
- Network access for download

## Instructions

1. Check current version (Help > About)
2. Backup settings and extensions list
3. Check release notes for breaking changes
4. Apply update (auto-update or manual download)
5. Verify settings preserved
6. Test AI features working
7. Reinstall extensions if needed

## Output

- Updated Cursor installation
- Preserved settings and configurations
- Verified working AI features
- Documented changes and fixes

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Changelog](https://cursor.com/changelog)
- [Cursor Downloads](https://cursor.com/download)
- [Settings Sync Documentation](https://cursor.com/docs/sync)
- [Cursor GitHub Releases](https://github.com/getcursor/cursor/releases)