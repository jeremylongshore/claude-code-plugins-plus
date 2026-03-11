---
name: obsidian-observability
description: |
  Set up comprehensive logging and monitoring for Obsidian plugins.
  Use when implementing debug logging, tracking plugin performance,
  or setting up error reporting for your Obsidian plugin.
  Trigger with phrases like "obsidian logging", "obsidian monitoring",
  "obsidian debug", "track obsidian plugin".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement comprehensive logging, metrics collection, error tracking, and a debug panel for Obsidian plugins.

## Prerequisites
- Working Obsidian plugin
- Understanding of Developer Tools
- Basic TypeScript knowledge

## Key Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| Command execution time | Timer | Performance tracking |
| File operations count | Counter | Usage patterns |
| Error rate | Counter | Reliability |
| Cache hit ratio | Gauge | Efficiency |
| Memory usage | Gauge | Resource health |

## Instructions

### Step 1: Add Structured Logger
Create a Logger class with levels (debug/info/warn/error), history buffer, formatted output, and timing helpers.

### Step 2: Implement Metrics Collection
Build MetricsCollector with counters, gauges, and timers. Add `timeAsync()` wrapper for measuring function duration with percentile stats (p95).

### Step 3: Set Up Error Tracking
Create ErrorTracker that deduplicates errors by name+message, counts occurrences, and provides `wrapAsync()` for safe error capture.

### Step 4: Build Debug Panel View
Register a sidebar view (dev mode only) that auto-refreshes every 5 seconds showing counters, timer stats, recent errors, and log history. Add export button for downloadable JSON debug bundle.

### Step 5: Integrate in Main Plugin
Initialize logger, metrics, and error tracker in `onload()`. Wrap commands with metrics timing. Track command usage with counters.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Logger, MetricsCollector, ErrorTracker, DebugView classes and CSS styles.

## Output
- Structured logger with levels and history
- Metrics collection (counters, gauges, timers with p95)
- Error tracking with deduplication
- Debug panel for runtime inspection
- Exportable debug bundle for support

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Too much logging | Debug level in prod | Set level to 'error' in production |
| Memory growth | Unbounded history | Limit history to 100 entries |
| Performance impact | Sync logging | Use async patterns for file logging |
| Missing context | No error tracking | Wrap async calls with errorTracker |

## Examples

### Quick Timing Check
```typescript
const endTimer = logger.time('my-operation');
await doExpensiveWork();
endTimer(); // Logs: [plugin-id] my-operation (245.32ms)
```

## Resources
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Obsidian Developer Tools](https://docs.obsidian.md/Plugins/Guides/Developer+tools)

## Next Steps
For incident response, see `obsidian-incident-runbook`.
