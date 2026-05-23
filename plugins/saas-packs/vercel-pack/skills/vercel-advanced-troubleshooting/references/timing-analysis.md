# Timing Analysis

## Timing Analysis

```typescript
class TimingAnalyzer {
  private timings: Map<string, number[]> = new Map();

  async measure<T>(label: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      const duration = performance.now() - start;
      const existing = this.timings.get(label) || [];
      existing.push(duration);
      this.timings.set(label, existing);
    }
  }

  report(): TimingReport {
    const report: TimingReport = {};
    for (const [label, times] of this.timings) {
      report[label] = {
        count: times.length,
        min: Math.min(...times),
        max: Math.max(...times),
        avg: times.reduce((a, b) => a + b, 0) / times.length,
        p95: this.percentile(times, 95),
      };
    }
    return report;
  }
}
```
