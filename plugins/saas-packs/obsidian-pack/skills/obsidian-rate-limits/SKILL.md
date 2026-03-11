---
name: obsidian-rate-limits
description: |
  Handle Obsidian file system operations and throttling patterns.
  Use when processing many files, handling bulk operations,
  or preventing performance issues from excessive operations.
  Trigger with phrases like "obsidian rate limit", "obsidian bulk operations",
  "obsidian file throttling", "obsidian performance limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Rate Limits

## Overview
Throttling patterns for Obsidian plugin file system operations. Obsidian runs on Electron with single-threaded UI -- excessive vault operations freeze the interface and risk data corruption.

## Prerequisites
- Understanding of Obsidian's event loop
- Familiarity with async JavaScript patterns
- Awareness of vault size impact on operations

## Instructions

### Step 1: Throttled File Operations

### Step 2: Batch Read with UI Yielding

### Step 3: Debounced Event Handlers

### Step 4: Progress Feedback for Long Operations

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| UI freezes | Too many sync operations | Batch with UI yielding |
| Data corruption | Concurrent writes to same file | Queue writes, serialize per file |
| Memory pressure | Reading all files at once | Process in batches |
| Missed events | Over-debouncing | Set reasonable debounce (300-500ms) |

## Resources
- [Obsidian Performance Tips](https://docs.obsidian.md/Plugins/Guides/Performance)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply obsidian rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian rate limits for production environments with multiple constraints and team-specific requirements.