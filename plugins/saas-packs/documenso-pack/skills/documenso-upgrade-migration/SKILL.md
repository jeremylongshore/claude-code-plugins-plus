---
name: documenso-upgrade-migration
description: |
  Manage Documenso API version upgrades and SDK migrations.
  Use when upgrading from v1 to v2 API, updating SDK versions,
  or migrating between Documenso versions.
  Trigger with phrases like "documenso upgrade", "documenso v2 migration",
  "update documenso SDK", "documenso API version".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Documenso SDK versions and migrating from API v1 to v2.

## Prerequisites
- Current Documenso integration working
- Test environment available
- Feature flag system (recommended)
- Backup/rollback plan

## Instructions

### Step 1: API Version Differences
Implement api version differences.
### Step 2: Migration Steps
npm uninstall your-documenso-v1-wrapper
### Step 3: Gradual Migration Strategy
import { getDocumenso } from "./documenso-v2";
### Step 4: ID Migration
If you store document IDs in your database:
### Step 5: Testing Migration
// Run both versions and compare
### Step 6: Rollback Plan
featureFlags.disable("documenso_v2")

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- API Version Differences
- Migration Steps
- Gradual Migration Strategy
- ID Migration
- Testing Migration
- Rollback Plan

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| ID mismatch | v1 vs v2 format | Use adapter to normalize |
| Missing field | API change | Update to new field names |
| 404 on template | ID format changed | Fetch new template ID |
| Enum errors | Case sensitivity | Use uppercase enums |

## Resources
- [Documenso API v2 Documentation](https://openapi.documenso.com/)
- [SDK Changelog](https://github.com/documenso/sdk-typescript/releases)
- [Migration Guide](https://docs.documenso.com/developers/public-api)

## Next Steps
For CI/CD integration, see `documenso-ci-integration`.

## Examples

**Basic usage**: Apply documenso upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso upgrade migration for production environments with multiple constraints and team-specific requirements.