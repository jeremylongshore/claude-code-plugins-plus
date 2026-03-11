---
name: obsidian-sdk-patterns
description: |
  Apply production-ready Obsidian plugin patterns for TypeScript.
  Use when implementing complex features, refactoring plugins,
  or establishing coding standards for Obsidian development.
  Trigger with phrases like "obsidian patterns", "obsidian best practices",
  "obsidian code patterns", "idiomatic obsidian plugin".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian SDK Patterns

## Overview
Production patterns for Obsidian plugin development using the Obsidian TypeScript API. Covers vault operations, workspace management, event handling, and UI components with proper lifecycle management.

## Prerequisites
- Obsidian development environment set up
- TypeScript compilation configured
- Understanding of Obsidian's plugin lifecycle

## Instructions

### Step 1: Type-Safe Settings with Migration

### Step 2: Safe Vault Operations

### Step 3: Event Registration with Cleanup

### Step 4: Custom View with State Persistence

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `null` file reference | File deleted between check and use | Always re-check with `getAbstractFileByPath` |
| Stale metadata cache | Cache not updated | Use `this.app.metadataCache.on('changed')` |
| Settings lost on update | Missing migration logic | Version settings, migrate on load |
| Memory leak | Unregistered events | Use `this.registerEvent()` always |

## Resources
- [Obsidian Plugin API](https://docs.obsidian.md/Reference/TypeScript+API)
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Obsidian Sdk Patterns implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply obsidian sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian sdk patterns for production environments with multiple constraints and team-specific requirements.