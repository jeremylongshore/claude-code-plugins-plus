---
name: grammarly-observability
description: |
  Implement Grammarly observability with metrics and logging.
  Use when setting up monitoring, tracking API performance,
  or implementing alerting for Grammarly integrations.
  Trigger with phrases like "grammarly monitoring", "grammarly metrics",
  "grammarly observability", "grammarly logging", "grammarly alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Observability

## Instructions

### Step 1: API Call Metrics

```typescript
class GrammarlyMetrics {
  private calls = { score: 0, ai: 0, plagiarism: 0 };
  private errors = 0;
  private latencies: number[] = [];

  recordCall(api: 'score' | 'ai' | 'plagiarism', latencyMs: number) {
    this.calls[api]++;
    this.latencies.push(latencyMs);
  }

  recordError() { this.errors++; }

  report() {
    const sorted = [...this.latencies].sort((a, b) => a - b);
    return {
      totalCalls: Object.values(this.calls).reduce((a, b) => a + b, 0),
      callsByAPI: this.calls,
      errors: this.errors,
      p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
    };
  }
}
```

### Step 2: Structured Logging

```typescript
function logGrammarlyCall(api: string, duration: number, status: number, textLength: number) {
  console.log(JSON.stringify({
    service: 'grammarly',
    api,
    duration_ms: duration,
    status,
    text_length: textLength,
    timestamp: new Date().toISOString(),
  }));
}
```

### Step 3: Alerting

```typescript
// Alert on error rate > 10%
const errorRate = metrics.errors / (metrics.totalCalls || 1);
if (errorRate > 0.1) {
  console.error(`ALERT: Grammarly error rate ${(errorRate * 100).toFixed(1)}%`);
}
```

## Resources

- [Grammarly API](https://developer.grammarly.com/)
