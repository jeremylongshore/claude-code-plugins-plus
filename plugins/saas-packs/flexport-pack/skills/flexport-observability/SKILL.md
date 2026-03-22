---
name: flexport-observability
description: |
  Set up observability for Flexport logistics integrations with metrics,
  structured logging, distributed tracing, and alerting dashboards.
  Trigger: "flexport monitoring", "flexport observability", "flexport metrics", "flexport alerts".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Observability

## Overview

Full observability stack for Flexport integrations: Prometheus metrics for API health, pino structured logging for debugging, OpenTelemetry tracing for latency analysis, and Grafana dashboards for monitoring.

## Instructions

### Step 1: Prometheus Metrics

```typescript
import { Counter, Histogram, Gauge, register } from 'prom-client';

const flexportRequests = new Counter({
  name: 'flexport_api_requests_total',
  help: 'Total Flexport API requests',
  labelNames: ['method', 'endpoint', 'status'],
});

const flexportLatency = new Histogram({
  name: 'flexport_api_latency_seconds',
  help: 'Flexport API response time',
  labelNames: ['endpoint'],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});

const flexportRateLimit = new Gauge({
  name: 'flexport_rate_limit_remaining',
  help: 'Remaining API calls in current window',
});

// Instrumented fetch wrapper
async function instrumentedFlexport(path: string, options: RequestInit = {}) {
  const endpoint = path.split('?')[0];
  const timer = flexportLatency.startTimer({ endpoint });
  try {
    const res = await fetch(`https://api.flexport.com${path}`, { ...options, headers: { ...headers, ...options.headers } });
    flexportRequests.inc({ method: options.method || 'GET', endpoint, status: res.status.toString() });
    const remaining = res.headers.get('X-RateLimit-Remaining');
    if (remaining) flexportRateLimit.set(parseInt(remaining));
    timer();
    return res;
  } catch (err) {
    flexportRequests.inc({ method: options.method || 'GET', endpoint, status: 'error' });
    timer();
    throw err;
  }
}
```

### Step 2: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'flexport-integration',
  level: process.env.LOG_LEVEL || 'info',
  redact: ['headers.Authorization', 'apiKey'],
});

// Log every API call with context
async function loggedFlexport(path: string, options: RequestInit = {}) {
  const start = Date.now();
  const res = await instrumentedFlexport(path, options);
  logger.info({
    service: 'flexport',
    path,
    method: options.method || 'GET',
    status: res.status,
    latencyMs: Date.now() - start,
    rateRemaining: res.headers.get('X-RateLimit-Remaining'),
  }, 'Flexport API call');
  return res;
}
```

### Step 3: Alert Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: flexport
    rules:
      - alert: FlexportAPIErrors
        expr: rate(flexport_api_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Flexport API error rate elevated"

      - alert: FlexportRateLimitLow
        expr: flexport_rate_limit_remaining < 10
        for: 1m
        labels: { severity: warning }
        annotations:
          summary: "Flexport rate limit nearly exhausted"

      - alert: FlexportHighLatency
        expr: histogram_quantile(0.99, flexport_api_latency_seconds_bucket) > 5
        for: 5m
        labels: { severity: warning }
```

### Grafana Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| Request rate | `rate(flexport_api_requests_total[5m])` | Throughput |
| Error rate | `rate(flexport_api_requests_total{status=~"4..|5.."}[5m])` | Reliability |
| p99 latency | `histogram_quantile(0.99, rate(flexport_api_latency_seconds_bucket[5m]))` | Performance |
| Rate limit headroom | `flexport_rate_limit_remaining` | Quota |

## Resources

- [prom-client](https://github.com/siimon/prom-client)
- [pino](https://github.com/pinojs/pino)
- [Flexport Status](https://status.flexport.com)

## Next Steps

For incident response, see `flexport-incident-runbook`.
