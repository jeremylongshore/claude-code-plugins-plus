---
name: clerk-upgrade-migration
description: |
  Manage Clerk SDK version upgrades and handle breaking changes.
  Use when upgrading Clerk packages, migrating to new SDK versions,
  or handling deprecation warnings.
  Trigger with phrases like "upgrade clerk", "clerk migration",
  "update clerk SDK", "clerk breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Upgrade & Migration

## Overview
Safely upgrade Clerk SDK versions and handle breaking changes.

## Prerequisites
- Current Clerk integration working
- Git repository with clean working state
- Test environment available

## Instructions
1. Step 1: Check Current Version and Available Updates
2. Step 2: Review Breaking Changes
3. Step 3: Upgrade Process
4. Step 4: Handle Common Migration Patterns
5. Step 5: Update Import Paths
6. Step 6: Test Upgrade
7. Step 7: Rollback Plan

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Updated Clerk SDK
- Migrated breaking changes
- All tests passing
- Production deployment ready

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Type errors after upgrade | API changes | Check changelog, update types |
| Middleware not executing | Matcher syntax changed | Update matcher regex |
| auth() returns Promise | Now async in v6 | Add await to auth() calls |
| Import errors | Path changes | Update to @clerk/nextjs/server |

## Resources
- [Clerk Changelog](https://clerk.com/changelog)
- [Migration Guides](https://clerk.com/docs/upgrade-guides)
- [GitHub Releases](https://github.com/clerk/javascript/releases)

## Next Steps
After upgrade, review `clerk-ci-integration` for CI/CD updates.

## Examples

**Basic usage**: Apply clerk upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk upgrade migration for production environments with multiple constraints and team-specific requirements.