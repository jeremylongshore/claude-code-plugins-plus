---
name: guidewire-upgrade-migration
description: |
  Upgrade Guidewire InsuranceSuite versions and migrate between environments.
  Use when planning version upgrades, handling breaking changes,
  or migrating from self-managed to Cloud.
  Trigger with phrases like "guidewire upgrade", "version migration",
  "insurancesuite update", "cloud migration", "upgrade path".
allowed-tools: Read, Write, Edit, Bash(gradle:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Plan and execute Guidewire InsuranceSuite version upgrades and migrations between self-managed and cloud environments.

## Prerequisites
- Current version documentation
- Access to Guidewire Community and documentation
- Test environment for validation
- Backup of current system

## Instructions

### Step 1: Version Upgrade Planning
Current Version     Target Version      Recommended Path
### Step 2: Instructions
echo "=== Guidewire Version Assessment ==="
### Step 3: Cloud Migration Checklist
Implement cloud migration checklist.
### Step 4: Rollback Procedure
echo "=== Upgrade Rollback ==="

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Version Upgrade Planning
- Instructions
- Cloud Migration Checklist
- Rollback Procedure

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Guidewire Release Notes](https://docs.guidewire.com/cloud/release-notes/)
- [Cloud Migration Guide](https://docs.guidewire.com/cloud/migration/)
- [Upgrade Best Practices](https://docs.guidewire.com/education/)

## Next Steps
For CI/CD integration, see `guidewire-ci-integration`.

## Examples

**Basic usage**: Apply guidewire upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire upgrade migration for production environments with multiple constraints and team-specific requirements.