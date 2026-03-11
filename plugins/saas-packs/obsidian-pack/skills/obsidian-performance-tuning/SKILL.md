---
name: obsidian-performance-tuning
description: |
  Optimize Obsidian plugin performance for smooth operation.
  Use when experiencing lag, memory issues, or slow startup,
  or when optimizing plugin code for large vaults.
  Trigger with phrases like "obsidian performance", "obsidian slow",
  "optimize obsidian plugin", "obsidian memory usage".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Performance Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Obsidian plugin performance for smooth operation in large vaults using lazy loading, efficient file processing, and proper event handling.

## Prerequisites
- Working Obsidian plugin
- Developer Tools access (Ctrl/Cmd+Shift+I)
- Understanding of async JavaScript

## Performance Benchmarks

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Plugin load time | < 100ms | 100-500ms | > 500ms |
| Command execution | < 50ms | 50-200ms | > 200ms |
| File operation | < 10ms | 10-50ms | > 50ms |
| Memory increase | < 10MB | 10-50MB | > 50MB |

## Instructions

### Step 1: Profile Performance
Add timing instrumentation to identify bottlenecks. Measure plugin load, command execution, and file operations.

### Step 2: Implement Lazy Initialization
Defer expensive operations (index building, large data loading) until first actual use rather than loading in `onload()`.

### Step 3: Process Files Efficiently
Use `vault.cachedRead()`, process files in chunks (50 at a time) with pauses for UI updates, and cache results by mtime.

### Step 4: Use Memory-Efficient Structures
LRU cache for bounded memory, WeakMap for garbage-collectible references, string interning for repeated values.

### Step 5: Optimize Event Handlers
Debounce file modification handlers (500ms), throttle scroll handlers (100ms), batch rapid events into single callbacks.

### Step 6: Optimize UI Rendering
Use DocumentFragment for batch DOM updates, implement virtual scrolling for long lists, use requestAnimationFrame for smooth updates.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for profiler, lazy service, file processor, LRU cache, event optimizer, and render optimizer code.

## Output
- Performance profiler identifying bottlenecks
- Lazy initialization reducing load time
- Chunked file processing preventing UI freezes
- Bounded memory usage with LRU caches

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin slow to load | Heavy initialization | Use lazy loading pattern |
| UI freezes | Blocking operations | Use async + chunking |
| Memory growth | Unbounded caching | Use LRU cache with size limit |
| Event lag | Unthrottled handlers | Debounce/throttle events |

## Examples

### Pre-Release Performance Checklist
- [ ] Plugin loads in < 100ms
- [ ] No blocking operations in onload()
- [ ] File operations use cachedRead
- [ ] Event handlers debounced/throttled
- [ ] Caches have size limits
- [ ] Works smoothly with 1000+ files

## Resources
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Obsidian Performance Tips](https://docs.obsidian.md/Plugins/Guides/Performance)

## Next Steps
For resource optimization, see `obsidian-cost-tuning`.
