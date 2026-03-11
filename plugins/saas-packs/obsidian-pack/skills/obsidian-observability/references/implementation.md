# Obsidian Observability - Implementation Details

## Structured Logger

```typescript
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export class Logger {
  private pluginId: string;
  private level: LogLevel;
  private history: LogEntry[] = [];
  private maxHistory = 100;
  private readonly levelPriority = { debug: 0, info: 1, warn: 2, error: 3 };

  constructor(pluginId: string, level: LogLevel = 'info') {
    this.pluginId = pluginId;
    this.level = level;
  }

  debug(message: string, context?: Record<string, any>): void { this.log('debug', message, context); }
  info(message: string, context?: Record<string, any>): void { this.log('info', message, context); }
  warn(message: string, context?: Record<string, any>): void { this.log('warn', message, context); }
  error(message: string, error?: Error, context?: Record<string, any>): void {
    const errorContext = error ? { ...context, error: { name: error.name, message: error.message, stack: error.stack } } : context;
    this.log('error', message, errorContext);
  }

  time(label: string): () => void {
    const start = performance.now();
    return () => {
      const duration = performance.now() - start;
      this.history.push({ timestamp: new Date().toISOString(), level: 'debug', message: label, duration });
    };
  }

  exportLogs(): string {
    return this.history.map(e => {
      let line = `${e.timestamp} [${e.level}] ${e.message}`;
      if (e.duration) line += ` (${e.duration}ms)`;
      return line;
    }).join('\n');
  }
}
```

## Metrics Collector

```typescript
export class MetricsCollector {
  private counters = new Map<string, number>();
  private gauges = new Map<string, number>();
  private timers = new Map<string, { value: number; timestamp: number }[]>();

  increment(name: string, value = 1): void {
    this.counters.set(name, (this.counters.get(name) || 0) + value);
  }

  setGauge(name: string, value: number): void { this.gauges.set(name, value); }

  recordTiming(name: string, durationMs: number): void {
    const timings = this.timers.get(name) || [];
    timings.push({ value: durationMs, timestamp: Date.now() });
    while (timings.length > 100) timings.shift();
    this.timers.set(name, timings);
  }

  async timeAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try { return await fn(); }
    finally { this.recordTiming(name, performance.now() - start); }
  }

  getTimerStats(name: string) {
    const timings = this.timers.get(name);
    if (!timings?.length) return null;
    const values = timings.map(t => t.value).sort((a, b) => a - b);
    const sum = values.reduce((a, b) => a + b, 0);
    return {
      count: values.length, avg: sum / values.length,
      min: values[0], max: values[values.length - 1],
      p95: values[Math.floor(values.length * 0.95)],
    };
  }
}
```

## Error Tracker

```typescript
export class ErrorTracker {
  private errors = new Map<string, TrackedError>();

  track(error: Error, context: Record<string, any> = {}): void {
    const key = `${error.name}:${error.message}`;
    const existing = this.errors.get(key);
    if (existing) { existing.count++; existing.timestamp = new Date().toISOString(); }
    else {
      if (this.errors.size >= 50) this.errors.delete(this.errors.keys().next().value);
      this.errors.set(key, {
        timestamp: new Date().toISOString(),
        error: { name: error.name, message: error.message, stack: error.stack },
        context, count: 1,
      });
    }
  }

  getMostCommon(limit = 5) {
    return Array.from(this.errors.values()).sort((a, b) => b.count - a.count).slice(0, limit);
  }

  wrapAsync<T>(fn: () => Promise<T>, context = {}): Promise<T> {
    return fn().catch((error: Error) => { this.track(error, context); throw error; });
  }
}
```

## Debug Panel View

```typescript
export class DebugView extends ItemView {
  async onOpen() {
    const container = this.containerEl.children[1];
    this.render(container);
    this.refreshInterval = window.setInterval(() => this.render(container), 5000);
  }

  private render(container: Element) {
    container.empty();
    // Render: Metrics (counters, timer stats), Recent Errors (top 5), Recent Logs (last 10)
    // Export button: downloads JSON with metrics + errors + logs
    // Clear button: resets all data
  }

  private exportDebugData() {
    const data = {
      timestamp: new Date().toISOString(),
      plugin: this.plugin.manifest.id,
      version: this.plugin.manifest.version,
      metrics: this.plugin.metrics.getAllMetrics(),
      errors: this.plugin.errorTracker.getErrors(),
      logs: this.plugin.logger.exportLogs(),
    };
    // Create downloadable JSON blob
  }
}
```

## Debug View Styles
```css
.plugin-debug-view { padding: 16px; }
.debug-section { margin-bottom: 24px; padding: 12px; background: var(--background-secondary); border-radius: 4px; }
.log-output { font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
.log-debug { color: var(--text-muted); }
.log-warn { color: var(--text-warning); }
.log-error { color: var(--text-error); }
```

## Plugin Integration Example

```typescript
export default class MyPlugin extends Plugin {
  logger: Logger;
  metrics: MetricsCollector;
  errorTracker: ErrorTracker;

  async onload() {
    this.logger = new Logger(this.manifest.id, 'debug');
    this.metrics = new MetricsCollector();
    this.errorTracker = new ErrorTracker();

    const endLoadTime = this.logger.time('plugin-load');

    this.addCommand({
      id: 'my-command', name: 'My Command',
      callback: async () => {
        this.metrics.increment('command.my-command');
        await this.metrics.timeAsync('command.duration', async () => { /* impl */ });
      },
    });

    endLoadTime();
    this.logger.info('Plugin loaded');
  }
}
```
