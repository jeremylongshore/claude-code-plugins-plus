---
name: obsidian-webhooks-events
description: |
  Handle Obsidian events and workspace callbacks for plugin development.
  Use when implementing reactive features, handling file changes,
  or responding to user interactions in your plugin.
  Trigger with phrases like "obsidian events", "obsidian callbacks",
  "obsidian file change", "obsidian workspace events".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Webhooks & Events

## Overview
Comprehensive guide to handling events in Obsidian plugins - workspace events, vault events, and custom event patterns.

## Prerequisites
- Understanding of Obsidian plugin lifecycle
- Familiarity with TypeScript event patterns
- Basic plugin setup completed

## Instructions

### Step 1: Workspace Events

### Step 2: Vault Events

### Step 3: MetadataCache Events

### Step 4: Debounced Event Handling

### Step 5: Custom Event Emitter

### Step 6: File Watcher Pattern

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Workspace event handlers for UI state
- Vault event handlers for file operations
- MetadataCache handlers for content changes
- Debounced handlers for frequent events
- Custom event bus for internal communication
- Filtered file watchers

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Memory leak | Unregistered events | Use `registerEvent` |
| Performance issues | Too many handlers | Debounce frequent events |
| Missed events | Late registration | Register in `onload` |
| Stale data | Cache not updated | Use `metadataCache.on('changed')` |

## Resources
- [Obsidian Events API](https://docs.obsidian.md/Reference/TypeScript+API/Events)
- [Workspace Events](https://docs.obsidian.md/Reference/TypeScript+API/Workspace)
- [Vault Events](https://docs.obsidian.md/Reference/TypeScript+API/Vault)

## Next Steps
For performance optimization, see `obsidian-performance-tuning`.
