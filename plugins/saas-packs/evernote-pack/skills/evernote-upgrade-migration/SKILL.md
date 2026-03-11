---
name: evernote-upgrade-migration
description: |
  Upgrade Evernote SDK versions and migrate between API versions.
  Use when upgrading SDK, handling breaking changes,
  or migrating to newer API patterns.
  Trigger with phrases like "upgrade evernote sdk", "evernote migration",
  "update evernote", "evernote breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Upgrade & Migration

## Overview
Guide for upgrading Evernote SDK versions, handling breaking changes, and migrating legacy integrations to current API patterns.

## Prerequisites
- Existing Evernote integration
- Test environment for validation
- Understanding of current implementation

## Instructions

### Step 1: Check Current Version

### Step 2: Review Breaking Changes

### Step 3: Migration Script

### Step 4: Convert Callbacks to Promises

### Step 5: Upgrade Dependencies

### Step 6: Test Suite Updates

### Step 7: Compatibility Layer

### Step 8: Deprecation Warnings

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- SDK version comparison
- Automated migration script
- Callback to Promise conversion
- Compatibility layer for gradual migration
- Migration test suite
- Deprecation warning system

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `Evernote.Note is not a constructor` | Old import style | Use `Evernote.Types.Note` |
| `callback is not a function` | Mixed patterns | Use Promise or callback, not both |
| `Cannot read property 'then'` | Using old callback-only method | Update to Promise-based method |

## Resources
- [Evernote SDK JS](https://github.com/Evernote/evernote-sdk-js)
- [SDK Changelog](https://github.com/Evernote/evernote-sdk-js/releases)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For CI/CD integration, see `evernote-ci-integration`.

## Examples

**Basic usage**: Apply evernote upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote upgrade migration for production environments with multiple constraints and team-specific requirements.