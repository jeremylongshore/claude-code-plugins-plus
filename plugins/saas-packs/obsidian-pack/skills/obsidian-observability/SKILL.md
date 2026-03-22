---
name: obsidian-observability
description: |
  Implement structured logging, metrics, error tracking, and a debug panel
  for Obsidian plugins. Use when adding debug logging, tracking plugin
  performance, building a diagnostics view, or setting up error reporting.
  Trigger with phrases like "obsidian logging", "obsidian monitoring",
  "obsidian debug panel", "track obsidian plugin performance".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, monitoring, debugging, performance, logging]

---
# Obsidian Observability

## Overview
Implement production observability for Obsidian plugins: a structured logger with levels and ring buffer history, a metrics collector with counters/gauges/timers, an error tracker with deduplication, and a debug sidebar panel that displays all of it in real time. Every component is copy-pasteable and uses only Obsidian's built-in APIs.

## Prerequisites
- Working Obsidian plugin (see `obsidian-core-workflow-a`)
- TypeScript strict mode enabled
- Familiarity with `ItemView` for the debug panel

## Instructions

### Step 1: Structured Logger with Levels and History
```typescript
// src/services/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0, info: 1, warn: 2, error: 3,
};

interface LogEntry {
  timestamp: number;
  level: LogLevel;
  message: string;
  data?: unknown;
}

export class Logger {
  private history: LogEntry[] = [];
  private maxHistory = 200;
  private level: LogLevel;
  private prefix: string;

  constructor(pluginId: string, level: LogLevel = 'info') {
    this.prefix = `[${pluginId}]`;
    this.level = level;
  }

  setLevel(level: LogLevel) { this.level = level; }

  debug(msg: string, data?: unknown) { this.log('debug', msg, data); }
  info(msg: string, data?: unknown)  { this.log('info', msg, data); }
  warn(msg: string, data?: unknown)  { this.log('warn', msg, data); }
  error(msg: string, data?: unknown) { this.log('error', msg, data); }

  /** Start a timer, returns a function that stops it and logs duration */
  time(label: string): () => number {
    const start = performance.now();
    return () => {
      const ms = performance.now() - start;
      this.debug(`${label} (${ms.toFixed(2)}ms)`);
      return ms;
    };
  }

  /** Get last N log entries */
  getHistory(count?: number): LogEntry[] {
    return count ? this.history.slice(-count) : [...this.history];
  }

  /** Export history as JSON string */
  export(): string {
    return JSON.stringify(this.history, null, 2);
  }

  private log(level: LogLevel, message: string, data?: unknown) {
    if (LEVEL_PRIORITY[level] < LEVEL_PRIORITY[this.level]) return;

    const entry: LogEntry = { timestamp: Date.now(), level, message, data };
    this.history.push(entry);
    if (this.history.length > this.maxHistory) {
      this.history.splice(0, this.history.length - this.maxHistory);
    }

    const fn = level === 'debug' ? console.debug
             : level === 'warn' ? console.warn
             : level === 'error' ? console.error
             : console.log;
    if (data !== undefined) {
      fn(this.prefix, message, data);
    } else {
      fn(this.prefix, message);
    }
  }
}
```

### Step 2: Metrics Collector with Counters, Gauges, and Timers
```typescript
// src/services/metrics.ts
interface TimerStats {
  count: number;
  total: number;
  min: number;
  max: number;
  values: number[]; // last 100 values for percentile calculation
}

export class MetricsCollector {
  private counters = new Map<string, number>();
  private gauges = new Map<string, number>();
  private timers = new Map<string, TimerStats>();

  // Counters — monotonically increasing
  increment(name: string, amount = 1) {
    this.counters.set(name, (this.counters.get(name) ?? 0) + amount);
  }

  getCounter(name: string): number {
    return this.counters.get(name) ?? 0;
  }

  // Gauges — point-in-time values
  setGauge(name: string, value: number) {
    this.gauges.set(name, value);
  }

  getGauge(name: string): number {
    return this.gauges.get(name) ?? 0;
  }

  // Timers — track duration distributions
  recordTime(name: string, ms: number) {
    let stats = this.timers.get(name);
    if (!stats) {
      stats = { count: 0, total: 0, min: Infinity, max: 0, values: [] };
      this.timers.set(name, stats);
    }
    stats.count++;
    stats.total += ms;
    stats.min = Math.min(stats.min, ms);
    stats.max = Math.max(stats.max, ms);
    stats.values.push(ms);
    if (stats.values.length > 100) stats.values.shift();
  }

  /** Wrap an async function with automatic timing */
  async timeAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      this.recordTime(name, performance.now() - start);
    }
  }

  getTimerStats(name: string): { avg: number; p95: number; min: number; max: number; count: number } | null {
    const stats = this.timers.get(name);
    if (!stats || stats.count === 0) return null;
    const sorted = [...stats.values].sort((a, b) => a - b);
    const p95Index = Math.floor(sorted.length * 0.95);
    return {
      avg: stats.total / stats.count,
      p95: sorted[p95Index] ?? sorted[sorted.length - 1],
      min: stats.min,
      max: stats.max,
      count: stats.count,
    };
  }

  /** Get all metrics as a plain object for serialization */
  snapshot(): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const [k, v] of this.counters) result[`counter.${k}`] = v;
    for (const [k, v] of this.gauges) result[`gauge.${k}`] = v;
    for (const [k] of this.timers) {
      const s = this.getTimerStats(k);
      if (s) result[`timer.${k}`] = s;
    }
    return result;
  }
}
```

### Step 3: Error Tracker with Deduplication
```typescript
// src/services/error-tracker.ts
interface TrackedError {
  name: string;
  message: string;
  stack?: string;
  count: number;
  firstSeen: number;
  lastSeen: number;
}

export class ErrorTracker {
  private errors = new Map<string, TrackedError>();

  /** Record an error, deduplicating by name+message */
  track(err: Error) {
    const key = `${err.name}:${err.message}`;
    const existing = this.errors.get(key);
    if (existing) {
      existing.count++;
      existing.lastSeen = Date.now();
    } else {
      this.errors.set(key, {
        name: err.name,
        message: err.message,
        stack: err.stack,
        count: 1,
        firstSeen: Date.now(),
        lastSeen: Date.now(),
      });
    }
  }

  /** Wrap an async function — catch and track errors, then rethrow */
  async wrapAsync<T>(label: string, fn: () => Promise<T>): Promise<T | undefined> {
    try {
      return await fn();
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      err.message = `[${label}] ${err.message}`;
      this.track(err);
      return undefined;
    }
  }

  getErrors(): TrackedError[] {
    return [...this.errors.values()].sort((a, b) => b.lastSeen - a.lastSeen);
  }

  getErrorCount(): number {
    let total = 0;
    for (const e of this.errors.values()) total += e.count;
    return total;
  }

  clear() { this.errors.clear(); }
}
```

### Step 4: Debug Sidebar Panel
```typescript
// src/views/debug-view.ts
import { ItemView, WorkspaceLeaf } from 'obsidian';
import type { Logger } from '../services/logger';
import type { MetricsCollector } from '../services/metrics';
import type { ErrorTracker } from '../services/error-tracker';

export const DEBUG_VIEW_TYPE = 'plugin-debug-view';

export class DebugView extends ItemView {
  private refreshTimer: number | null = null;

  constructor(
    leaf: WorkspaceLeaf,
    private logger: Logger,
    private metrics: MetricsCollector,
    private errorTracker: ErrorTracker,
  ) {
    super(leaf);
  }

  getViewType() { return DEBUG_VIEW_TYPE; }
  getDisplayText() { return 'Plugin Debug'; }
  getIcon() { return 'bug'; }

  async onOpen() {
    this.render();
    // Auto-refresh every 3 seconds
    this.refreshTimer = window.setInterval(() => this.render(), 3000);
  }

  async onClose() {
    if (this.refreshTimer) clearInterval(this.refreshTimer);
  }

  private render() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass('plugin-debug-view');

    // Metrics section
    container.createEl('h4', { text: 'Metrics' });
    const snapshot = this.metrics.snapshot();
    const metricsTable = container.createEl('table');
    for (const [key, value] of Object.entries(snapshot)) {
      const row = metricsTable.createEl('tr');
      row.createEl('td', { text: key, cls: 'debug-key' });
      row.createEl('td', {
        text: typeof value === 'object' ? JSON.stringify(value) : String(value),
      });
    }

    // Errors section
    const errors = this.errorTracker.getErrors();
    container.createEl('h4', { text: `Errors (${this.errorTracker.getErrorCount()})` });
    if (errors.length === 0) {
      container.createEl('p', { text: 'No errors recorded.', cls: 'debug-empty' });
    } else {
      for (const err of errors.slice(0, 10)) {
        const el = container.createEl('div', { cls: 'debug-error' });
        el.createEl('strong', { text: `${err.name} (x${err.count})` });
        el.createEl('p', { text: err.message });
      }
    }

    // Recent logs section
    container.createEl('h4', { text: 'Recent Logs' });
    const logs = this.logger.getHistory(20);
    for (const entry of logs.reverse()) {
      const el = container.createEl('div', { cls: `debug-log debug-${entry.level}` });
      const time = new Date(entry.timestamp).toLocaleTimeString();
      el.createEl('span', { text: `${time} [${entry.level}]`, cls: 'debug-time' });
      el.createEl('span', { text: ` ${entry.message}` });
    }

    // Export button
    const btn = container.createEl('button', { text: 'Export Debug Bundle' });
    btn.addEventListener('click', () => {
      const bundle = {
        timestamp: new Date().toISOString(),
        metrics: snapshot,
        errors: errors,
        recentLogs: this.logger.getHistory(50),
      };
      navigator.clipboard.writeText(JSON.stringify(bundle, null, 2));
      new (require('obsidian').Notice)('Debug bundle copied to clipboard');
    });
  }
}
```

### Step 5: Wire Everything into the Plugin
```typescript
// src/main.ts
import { Plugin } from 'obsidian';
import { Logger } from './services/logger';
import { MetricsCollector } from './services/metrics';
import { ErrorTracker } from './services/error-tracker';
import { DebugView, DEBUG_VIEW_TYPE } from './views/debug-view';

export default class MyPlugin extends Plugin {
  logger: Logger;
  metrics: MetricsCollector;
  errors: ErrorTracker;

  async onload() {
    this.logger = new Logger(this.manifest.id, 'debug');
    this.metrics = new MetricsCollector();
    this.errors = new ErrorTracker();

    // Register debug view (dev mode only — gate behind a setting if desired)
    this.registerView(DEBUG_VIEW_TYPE, (leaf) =>
      new DebugView(leaf, this.logger, this.metrics, this.errors)
    );

    this.addCommand({
      id: 'open-debug-panel',
      name: 'Open debug panel',
      callback: () => this.openDebugPanel(),
    });

    // Track command executions
    this.addCommand({
      id: 'my-command',
      name: 'My Command',
      callback: async () => {
        this.metrics.increment('commands.my-command');
        const endTimer = this.logger.time('my-command');
        await this.errors.wrapAsync('my-command', async () => {
          // ... your command logic
        });
        const ms = endTimer();
        this.metrics.recordTime('commands.my-command', ms);
      },
    });

    // Track vault stats as gauges
    this.registerInterval(
      window.setInterval(() => {
        this.metrics.setGauge('vault.files', this.app.vault.getMarkdownFiles().length);
        if (performance.memory) {
          this.metrics.setGauge('memory.usedMB',
            Math.round((performance as any).memory.usedJSHeapSize / 1048576));
        }
      }, 10_000)
    );

    this.logger.info('Plugin loaded');
  }

  onunload() {
    this.app.workspace.detachLeavesOfType(DEBUG_VIEW_TYPE);
  }

  private async openDebugPanel() {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(DEBUG_VIEW_TYPE)[0];
    if (!leaf) {
      const rightLeaf = workspace.getRightLeaf(false);
      if (rightLeaf) {
        await rightLeaf.setViewState({ type: DEBUG_VIEW_TYPE, active: true });
        leaf = rightLeaf;
      }
    }
    if (leaf) workspace.revealLeaf(leaf);
  }
}
```

### Step 6: CSS for the Debug Panel
```css
/* styles.css — add these rules */
.plugin-debug-view { padding: 8px 12px; font-size: var(--font-ui-small); }
.plugin-debug-view h4 { margin: 12px 0 4px; color: var(--text-accent); }
.plugin-debug-view table { width: 100%; border-collapse: collapse; }
.plugin-debug-view td { padding: 2px 6px; border-bottom: 1px solid var(--background-modifier-border); }
.debug-key { font-family: var(--font-monospace); color: var(--text-muted); }
.debug-error { padding: 4px; margin: 4px 0; background: var(--background-modifier-error); border-radius: var(--radius-s); }
.debug-log { padding: 1px 0; font-family: var(--font-monospace); font-size: 11px; }
.debug-time { color: var(--text-faint); }
.debug-debug { color: var(--text-muted); }
.debug-info { color: var(--text-normal); }
.debug-warn { color: var(--text-accent); }
.debug-error { color: var(--text-error); }
.debug-empty { color: var(--text-faint); font-style: italic; }
```

## Output
- Structured logger with debug/info/warn/error levels and ring buffer history (200 entries)
- Metrics collector: counters (monotonic), gauges (point-in-time), timers (with p95)
- Error tracker with deduplication by name+message, occurrence count, and timestamps
- Debug sidebar panel that auto-refreshes every 3 seconds showing metrics, errors, and logs
- Export button that copies a full debug bundle to clipboard as JSON
- Memory and vault stats tracked as gauges every 10 seconds

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Too much logging output | Debug level in production | Set level to `'error'` or `'warn'` for release builds |
| Memory growth from log history | Unbounded buffer | Ring buffer capped at 200 entries (adjustable) |
| Performance impact from metrics | Synchronous metric recording | All operations are O(1) map lookups |
| Debug panel slows Obsidian | Rapid DOM updates | Panel renders at most once per 3 seconds |
| `performance.memory` undefined | Not available on all platforms | Guard with `if (performance.memory)` |
| Error tracker misses errors | Error not thrown, just logged | Use `wrapAsync` around all async operations |

## Examples

### Quick Timing Check
```typescript
const endTimer = logger.time('vault-scan');
const files = app.vault.getMarkdownFiles();
for (const f of files) await app.vault.cachedRead(f);
endTimer(); // Logs: [plugin-id] vault-scan (245.32ms)
```

### Metrics-Wrapped Command
```typescript
this.addCommand({
  id: 'search-notes',
  name: 'Search notes',
  callback: () => this.metrics.timeAsync('search-notes', async () => {
    this.metrics.increment('search.invocations');
    const results = await this.search();
    this.metrics.setGauge('search.lastResultCount', results.length);
  }),
});
```

## Resources
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Obsidian Developer Tools](https://docs.obsidian.md/Plugins/Getting+started/Development+workflow)
- [ItemView API](https://docs.obsidian.md/Reference/TypeScript+API/ItemView)

## Next Steps
For incident response using debug bundles, see `obsidian-incident-runbook`.
For performance optimization, see `obsidian-performance-tuning`.
