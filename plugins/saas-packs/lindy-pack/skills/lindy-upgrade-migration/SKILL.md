---
name: lindy-upgrade-migration
description: |
  Manage Lindy SDK upgrades and migrate between versions.
  Use when upgrading SDK versions, migrating agents,
  or handling breaking changes.
  Trigger with phrases like "upgrade lindy", "lindy migration",
  "lindy breaking changes", "update lindy SDK".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for safely upgrading Lindy SDK versions and migrating configurations.

## Prerequisites
- Current SDK version identified
- Changelog reviewed for target version
- Backup of current configuration
- Test environment available

## Instructions

### Step 1: Check Current Version
### Step 2: Review Breaking Changes
### Step 3: Update Dependencies
### Step 4: Update Code
### Step 5: Run Migration Tests

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Migration Checklist
## Output
- Updated SDK to target version
- Migrated code patterns
- Passing test suite
- Documented changes

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import error | Named exports changed | Check new import syntax |
| Type error | Interface changed | Update TypeScript types |
| Runtime error | Method signature changed | Check new API |

## Examples

### Automated Migration Script
## Resources
- [Lindy Changelog](https://docs.lindy.ai/changelog)
- [Migration Guide](https://docs.lindy.ai/migration)
- [SDK Reference](https://docs.lindy.ai/sdk)

## Next Steps
Proceed to Pro tier skills for advanced features.