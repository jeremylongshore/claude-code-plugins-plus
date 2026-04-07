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

## Overview

Grammarly API integrations process user text through scoring, AI rewriting, and plagiarism endpoints where latency and accuracy directly affect user experience. Monitor text check response times, suggestion quality signals, API error rates, and token consumption to stay within rate limits. Catching degradation early prevents users from seeing stale suggestions or silent failures in real-time editing flows.

## Key Metrics

| Metric | Type | Target | Alert Threshold |
|--------|------|--------|-----------------|
| Text check latency p95 | Histogram | < 300ms | > 800ms |
| API error rate | Gauge | < 1% | > 5% |
| Suggestion acceptance rate | Gauge | > 40% | < 20% (quality signal) |
| Token usage (daily) | Counter | < 80% quota | > 90% quota |
| Plagiarism check latency | Histogram | < 2s | > 5s |
| AI rewrite throughput | Counter | Stable | Drop > 30% |

## Instrumentation

```typescript
async function trackGrammarlyCall(api: 'score' | 'ai' | 'plagiarism', textLen: number, fn: () => Promise<any>) {
  const start = Date.now();
  try {
    const result = await fn();
    metrics.histogram('grammarly.api.latency', Date.now() - start, { api });
    metrics.increment('grammarly.api.calls', { api });
    metrics.gauge('grammarly.text.length', textLen, { api });
    return result;
  } catch (err) {
    metrics.increment('grammarly.api.errors', { api, status: err.status });
    throw err;
  }
}
```

## Health Check Dashboard

```typescript
async function grammarlyHealth(): Promise<Record<string, string>> {
  const latencyP95 = await metrics.query('grammarly.api.latency', 'p95', '5m');
  const errorRate = await metrics.query('grammarly.api.error_rate', 'avg', '5m');
  const quotaUsed = await grammarlyAdmin.getQuotaUsage();
  return {
    api_latency: latencyP95 < 300 ? 'healthy' : 'slow',
    error_rate: errorRate < 0.01 ? 'healthy' : 'degraded',
    quota: quotaUsed < 0.8 ? 'healthy' : 'at_risk',
  };
}
```

## Alerting Rules

```typescript
const alerts = [
  { metric: 'grammarly.api.latency_p95', condition: '> 800ms', window: '10m', severity: 'warning' },
  { metric: 'grammarly.api.error_rate', condition: '> 0.05', window: '5m', severity: 'critical' },
  { metric: 'grammarly.quota.daily_pct', condition: '> 0.90', window: '1h', severity: 'warning' },
  { metric: 'grammarly.ai.throughput', condition: 'drop > 30%', window: '15m', severity: 'critical' },
];
```

## Structured Logging

```typescript
function logGrammarlyEvent(api: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    service: 'grammarly', api,
    duration_ms: data.latency, status: data.status,
    text_length: data.textLen, suggestion_count: data.suggestions,
    // Never log user text content — only metadata
    timestamp: new Date().toISOString(),
  }));
}
```

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| 429 rate limit | Token quota exhausted | Back off, check daily usage, request limit increase |
| Latency spike on /score | Grammarly service degradation | Check status page, enable local cache fallback |
| Suggestion count drops to 0 | API schema change or auth failure | Verify API key, check response format |
| Plagiarism timeout > 5s | Large document or service overload | Chunk text, retry with exponential backoff |

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)

## Next Steps

See `grammarly-incident-runbook`.
