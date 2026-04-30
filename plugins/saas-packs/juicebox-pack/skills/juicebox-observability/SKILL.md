---
name: juicebox-observability
description: 'Set up Juicebox monitoring.

  Trigger: "juicebox monitoring", "juicebox metrics".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Observability

## Overview

Juicebox provides AI-powered people search and analysis where query performance, dataset ingestion rates, and quota consumption are the primary observability concerns. Monitor analysis completion times to ensure interactive UX, track ingestion pipeline health for data freshness, and watch quota usage to prevent mid-workflow cutoffs. Slow queries or failed ingestions degrade recruiter productivity and data accuracy.

## Key Metrics

| Metric | Type | Target | Alert Threshold |
|--------|------|--------|-----------------|
| Search latency p95 | Histogram | < 2s | > 5s |
| Analysis completion time | Histogram | < 10s | > 30s |
| Dataset ingestion rate | Gauge | > 100 records/s | < 50 records/s |
| API error rate | Gauge | < 1% | > 5% |
| Quota usage (daily) | Gauge | < 70% | > 85% |
| Query result relevance | Gauge | > 80% precision | < 60% |

## Instrumentation

```typescript
async function trackJuiceboxCall(operation: string, fn: () => Promise<any>) {
  const start = Date.now();
  try {
    const result = await fn();
    metrics.histogram('juicebox.api.latency', Date.now() - start, { operation });
    metrics.increment('juicebox.api.calls', { operation, status: 'ok' });
    return result;
  } catch (err) {
    metrics.increment('juicebox.api.errors', { operation, error: err.code });
    throw err;
  }
}
```

## Health Check Dashboard

```typescript
async function juiceboxHealth(): Promise<Record<string, string>> {
  const searchP95 = await metrics.query('juicebox.api.latency', 'p95', '5m');
  const errorRate = await metrics.query('juicebox.api.error_rate', 'avg', '5m');
  const quota = await juiceboxAdmin.getQuotaUsage();
  return {
    search_latency: searchP95 < 2000 ? 'healthy' : 'slow',
    error_rate: errorRate < 0.01 ? 'healthy' : 'degraded',
    quota: quota.pct < 0.7 ? 'healthy' : 'at_risk',
  };
}
```

## Alerting Rules

```typescript
const alerts = [
  { metric: 'juicebox.search.latency_p95', condition: '> 5s', window: '10m', severity: 'warning' },
  { metric: 'juicebox.api.error_rate', condition: '> 0.05', window: '5m', severity: 'critical' },
  { metric: 'juicebox.quota.daily_pct', condition: '> 0.85', window: '1h', severity: 'warning' },
  { metric: 'juicebox.ingestion.rate', condition: '< 50/s', window: '15m', severity: 'critical' },
];
```

## Structured Logging

```typescript
function logJuiceboxEvent(event: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    service: 'juicebox', event,
    operation: data.operation, duration_ms: data.latency,
    result_count: data.resultCount, query_length: data.queryLen,
    // Redact candidate PII — log only aggregate counts
    timestamp: new Date().toISOString(),
  }));
}
```

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| 429 rate limit | Quota exhausted for period | Pause queries, check daily allocation |
| Search timeout > 5s | Complex query or service load | Simplify filters, retry with narrower scope |
| Ingestion stall | Dataset too large or format error | Check upload logs, validate schema |
| Empty result set | Index gap or query mismatch | Verify dataset freshness, adjust search params |

## Resources

- [Juicebox Dashboard](https://app.juicebox.ai/analytics)

## Next Steps

See `juicebox-incident-runbook`.
