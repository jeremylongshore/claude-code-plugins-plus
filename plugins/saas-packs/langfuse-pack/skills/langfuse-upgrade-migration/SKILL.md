---
name: langfuse-upgrade-migration
description: |
  Upgrade Langfuse SDK versions and migrate between API changes.
  Use when upgrading Langfuse SDK, handling breaking changes,
  or migrating between Langfuse versions.
  Trigger with phrases like "upgrade langfuse", "langfuse migration",
  "update langfuse SDK", "langfuse breaking changes", "langfuse version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Guide for upgrading Langfuse SDK versions, handling breaking changes between v2 and v3 (TypeScript) or v1 and v2 (Python), with automated codemod support.

## Prerequisites
- Existing Langfuse integration
- Access to test environment
- Version control (git)

## Instructions

### Step 1: Check Current Version
Run `npm list langfuse` (Node) or `pip show langfuse` (Python) and review changelogs.

### Step 2: Review Breaking Changes
Key v3 changes: named exports, sync `trace()`, `flushAsync()` replaces `flush()`, camelCase usage keys.

### Step 3: Create Upgrade Branch and Update
Create `chore/upgrade-langfuse` branch. Run `npm install langfuse@latest`. Run tests.

### Step 4: Apply TypeScript API Changes
Change `import Langfuse` to `import { Langfuse }`. Remove `await` from `trace()`. Replace `flush()` with `flushAsync()`.

### Step 5: Apply Python API Changes
Update decorator from `@langfuse.observe()` to `@observe()`. Import from `langfuse.decorators`.

### Step 6: Run Migration Codemod
Use `ts-morph` script to auto-update imports and flush calls across the codebase.

### Step 7: Verify with Migration Tests
Run tests verifying trace creation, generation usage format, and flush behavior.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Updated SDK to latest version
- Migrated deprecated API calls
- All tests passing
- No breaking changes in functionality

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import error | Changed export | Use named import `{ Langfuse }` |
| Type error on usage | Key name change | Use camelCase keys |
| flush() not found | Method renamed | Use `flushAsync()` |
| Decorator error | New import path | Import from `langfuse.decorators` |

## Examples

### Version Compatibility Matrix
| Feature | v2.x | v3.x | Migration |
|---------|------|------|-----------|
| Default import | `import Langfuse` | `import { Langfuse }` | Update imports |
| `trace()` return | `Promise<Trace>` | `Trace` | Remove `await` |
| `flush()` | Sync | N/A | Use `flushAsync()` |
| Usage keys | `snake_case` | `camelCase` | Update all usage objects |

## Resources
- [Langfuse JS Changelog](https://github.com/langfuse/langfuse-js/releases)
- [Langfuse Python Changelog](https://github.com/langfuse/langfuse-python/releases)
- [Langfuse Migration Guide](https://langfuse.com/docs/sdk)