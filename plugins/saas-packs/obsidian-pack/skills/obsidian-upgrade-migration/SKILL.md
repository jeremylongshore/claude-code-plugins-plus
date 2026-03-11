---
name: obsidian-upgrade-migration
description: |
  Migrate Obsidian plugins between API versions and handle breaking changes.
  Use when upgrading to new Obsidian versions, handling API deprecations,
  or migrating plugin code to new patterns.
  Trigger with phrases like "obsidian upgrade", "obsidian migration",
  "obsidian API changes", "update obsidian plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Upgrade Migration

## Overview
Guide for migrating Obsidian plugins to new API versions and handling breaking changes.

## Prerequisites
- Existing Obsidian plugin
- Understanding of current plugin code
- Access to Obsidian changelog

## Instructions

### Step 1: Check Current Compatibility

### Step 2: Common Migration: CodeMirror 5 to 6

### Step 3: Settings Migration

### Step 4: Event API Migration

### Step 5: Vault API Changes

### Step 6: Editor API Migration

### Step 7: Update Dependencies

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Updated plugin code for new API version
- Migrated settings with version tracking
- Replaced deprecated event patterns
- Updated editor API calls
- Updated manifest and versions.json

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Property not found | API removed | Check changelog for replacement |
| Type errors | Type definitions changed | Update `obsidian` package |
| Runtime errors | API behavior changed | Add version checks |
| Settings lost | Migration not implemented | Add migration logic |

## Resources
- [Obsidian Changelog](https://obsidian.md/changelog)
- [Obsidian API Breaking Changes](https://docs.obsidian.md/Plugins/Releasing/Breaking+changes)
- [Obsidian Developer Docs](https://docs.obsidian.md/Plugins)

## Next Steps
For CI/CD setup, see `obsidian-ci-integration`.

## Examples

**Basic usage**: Apply obsidian upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian upgrade migration for production environments with multiple constraints and team-specific requirements.