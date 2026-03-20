---
name: juicebox-observability
description: |
  Set up Juicebox monitoring and observability with structured logging,
  Prometheus metrics, health checks, and alerting rules.
  Use when instrumenting search latency, tracking enrichment success rates,
  monitoring API quota usage, or building Grafana dashboards for Juicebox.
  Trigger with phrases like "juicebox monitoring", "juicebox metrics",
  "juicebox logging", "juicebox observability".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Observability

## Overview

Juicebox API calls (search, enrichment, contact reveal) are billable with rate limits and need full observability. This skill implements structured logging, Prometheus metrics (latency, success rate, quota), health check endpoints, and alerting rules for error spikes, quota exhaustion, and enrichment failures.

## Prerequisites

- Juicebox API credentials (`username` and `api_token`)
- Node.js 18+ with TypeScript and Express
- `prom-client` for Prometheus metrics (`npm install prom-client`)
- `pino` for structured logging (`npm install pino`)
- Prometheus server scraping your `/metrics` endpoint
- Grafana instance (optional, for dashboards)

## Instructions

### Step 1: Instrument structured logging for all Juicebox API calls

Log every search query, enrichment request, and API response with structured fields that log aggregators can parse.

```typescript
// lib/juicebox-logger.ts
import pino from 'pino';

const baseLogger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label })
  },
  base: {
    service: 'juicebox-integration',
    env: process.env.NODE_ENV
  }
});

export function createLogger(operation: string) {
  return baseLogger.child({ operation, provider: 'juicebox' });
}

// Usage in a search wrapper
export async function loggedSearch(
  client: JuiceboxClient,
  query: string,
  userId: string
): Promise<SearchResult> {
  const log = createLogger('search');
  const start = Date.now();

  log.info({ query, userId }, 'search_started');

  try {
    const response = await fetch('https://api.juicebox.ai/api/search', {
      method: 'POST',
      headers: {
        'Authorization': `token ${process.env.JB_USERNAME}:${process.env.JB_API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, limit: 25 })
    });

    const data = await response.json();
    const duration = Date.now() - start;

    log.info({
      resultCount: data.results?.length ?? 0,
      duration_ms: duration,
      status: response.status,
      userId
    }, 'search_completed');

    return data;
  } catch (err) {
    const duration = Date.now() - start;
    log.error({
      error: (err as Error).message,
      duration_ms: duration,
      userId
    }, 'search_failed');
    throw err;
  }
}
```

### Step 2: Collect Prometheus metrics for latency, success rate, and quota

Track four metric families: request count, latency histogram, cache hits, and quota consumption.

```typescript
// lib/juicebox-metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

export const juiceboxRequests = new Counter({
  name: 'juicebox_requests_total',
  help: 'Total Juicebox API requests by operation and status',
  labelNames: ['operation', 'status'] as const,
  registers: [registry]
});

export const juiceboxLatency = new Histogram({
  name: 'juicebox_request_duration_seconds',
  help: 'Juicebox API request latency in seconds',
  labelNames: ['operation'] as const,
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry]
});

export const juiceboxEnrichmentSuccess = new Counter({
  name: 'juicebox_enrichment_results_total',
  help: 'Enrichment outcomes: found, not_found, error',
  labelNames: ['outcome'] as const,
  registers: [registry]
});

export const juiceboxQuotaRemaining = new Gauge({
  name: 'juicebox_quota_remaining',
  help: 'Remaining API quota from last response header',
  labelNames: ['type'] as const,
  registers: [registry]
});

// Wrap any Juicebox call with metrics
export async function withMetrics<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const end = juiceboxLatency.startTimer({ operation });

  try {
    const result = await fn();
    juiceboxRequests.inc({ operation, status: 'success' });
    return result;
  } catch (error) {
    juiceboxRequests.inc({ operation, status: 'error' });
    throw error;
  } finally {
    end();
  }
}

// Expose metrics endpoint
import { Router } from 'express';
export const metricsRouter = Router();

metricsRouter.get('/metrics', async (_req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 3: Build a health check endpoint that validates Juicebox connectivity

Probe the Juicebox API and your database. Return structured status for Kubernetes liveness/readiness.

```typescript
// routes/health.ts
import { Router } from 'express';

interface HealthCheck {
  status: 'pass' | 'fail';
  latency_ms?: number;
  message?: string;
}

interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, HealthCheck>;
  timestamp: string;
}

const router = Router();

// Liveness — always 200 if process is running
router.get('/health/live', (_req, res) => {
  res.json({ status: 'ok' });
});

// Readiness — checks Juicebox API and database
router.get('/health/ready', async (_req, res) => {
  const health: HealthResponse = {
    status: 'healthy',
    checks: {},
    timestamp: new Date().toISOString()
  };

  // Check Juicebox API
  try {
    const start = Date.now();
    const resp = await fetch('https://api.juicebox.ai/api/search', {
      method: 'POST',
      headers: {
        'Authorization': `token ${process.env.JB_USERNAME}:${process.env.JB_API_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query: 'health check test', limit: 1 })
    });
    health.checks.juicebox_api = {
      status: resp.ok ? 'pass' : 'fail',
      latency_ms: Date.now() - start,
      message: resp.ok ? undefined : `HTTP ${resp.status}`
    };
    if (!resp.ok) health.status = 'degraded';
  } catch (err) {
    health.checks.juicebox_api = {
      status: 'fail',
      message: (err as Error).message
    };
    health.status = 'degraded';
  }

  // Check database
  try {
    const start = Date.now();
    await db.$queryRaw`SELECT 1`;
    health.checks.database = {
      status: 'pass',
      latency_ms: Date.now() - start
    };
  } catch (err) {
    health.checks.database = {
      status: 'fail',
      message: (err as Error).message
    };
    health.status = 'unhealthy';
  }

  res.status(health.status === 'healthy' ? 200 : 503).json(health);
});

export default router;
```

### Step 4: Define Prometheus alerting rules

Detect rate-limit approach, error spikes, high latency, and enrichment failures before they impact operations.

```yaml
# prometheus/juicebox-alerts.yaml
groups:
  - name: juicebox_alerts
    rules:
      - alert: JuiceboxHighErrorRate
        expr: |
          rate(juicebox_requests_total{status="error"}[5m])
          / rate(juicebox_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox error rate above 5%"
          description: "{{ $labels.operation }} error rate is {{ $value | humanizePercentage }}"

      - alert: JuiceboxHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(juicebox_request_duration_seconds_bucket[5m])
          ) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox P95 latency above 5s"
          description: "{{ $labels.operation }} P95 is {{ $value }}s"

      - alert: JuiceboxQuotaLow
        expr: juicebox_quota_remaining < 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Juicebox API quota nearly exhausted"
          description: "Only {{ $value }} requests remaining for {{ $labels.type }}"

      - alert: JuiceboxEnrichmentFailureSpike
        expr: |
          rate(juicebox_enrichment_results_total{outcome="error"}[10m])
          / rate(juicebox_enrichment_results_total[10m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox enrichment failure rate above 10%"

      - alert: JuiceboxApiDown
        expr: |
          up{job="juicebox-integration"} == 0
          or absent(juicebox_requests_total)
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Juicebox integration is down"
```

### Step 5: Build a Grafana dashboard config

Pre-built panels for the four key signals: request rate, latency, enrichment outcomes, and quota.

```json
{
  "title": "Juicebox Integration",
  "uid": "juicebox-overview",
  "panels": [
    {
      "title": "Request Rate by Operation",
      "type": "timeseries",
      "targets": [{
        "expr": "rate(juicebox_requests_total[5m])",
        "legendFormat": "{{operation}} — {{status}}"
      }],
      "gridPos": { "x": 0, "y": 0, "w": 12, "h": 8 }
    },
    {
      "title": "P95 Latency",
      "type": "timeseries",
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(juicebox_request_duration_seconds_bucket[5m]))",
        "legendFormat": "{{operation}}"
      }],
      "gridPos": { "x": 12, "y": 0, "w": 12, "h": 8 }
    },
    {
      "title": "Enrichment Outcomes",
      "type": "piechart",
      "targets": [{
        "expr": "increase(juicebox_enrichment_results_total[1h])",
        "legendFormat": "{{outcome}}"
      }],
      "gridPos": { "x": 0, "y": 8, "w": 8, "h": 8 }
    },
    {
      "title": "API Quota Remaining",
      "type": "gauge",
      "targets": [{
        "expr": "juicebox_quota_remaining"
      }],
      "gridPos": { "x": 8, "y": 8, "w": 8, "h": 8 },
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              { "value": 0, "color": "red" },
              { "value": 100, "color": "yellow" },
              { "value": 500, "color": "green" }
            ]
          }
        }
      }
    }
  ]
}
```

## Output

- `lib/juicebox-logger.ts` — pino-based structured logger with operation context
- `lib/juicebox-metrics.ts` — Prometheus counters, histograms, gauges + `/metrics` endpoint
- `routes/health.ts` — `/health/live` and `/health/ready` with Juicebox API + DB probes
- `prometheus/juicebox-alerts.yaml` — five alert rules (error rate, latency, quota, enrichment, downtime)
- Grafana dashboard JSON — four panels (request rate, P95 latency, enrichment outcomes, quota gauge)

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `401 Unauthorized` on health check | API token expired or malformed | Regenerate token at juicebox.ai; verify `token username:api_token` format |
| `ECONNREFUSED` on `/metrics` scrape | Metrics endpoint not mounted or wrong port | Confirm `metricsRouter` is mounted at `/metrics` and Prometheus `scrape_configs` targets the correct host:port |
| `503` from `/health/ready` | Juicebox API or database unreachable | Check Juicebox status page; verify database connection string; the response body `checks` object shows which dependency failed |
| `histogram_quantile returns NaN` | No traffic in the query window | Alert `for` duration prevents false alarms; ensure at least 1 request/minute in staging via synthetic probe |
| `prom-client registry collision` | Metric name registered twice (hot reload) | Use a singleton registry; guard with `registry.getSingleMetric('name')` before creating |

## Examples

**Instrument a Juicebox search call with both logging and metrics:**

```typescript
import { createLogger, loggedSearch } from './lib/juicebox-logger';
import { withMetrics, juiceboxQuotaRemaining } from './lib/juicebox-metrics';

async function searchCandidates(query: string, userId: string) {
  return withMetrics('search', async () => {
    const result = await loggedSearch(client, query, userId);

    // Update quota gauge from response headers if available
    if (result.quota_remaining !== undefined) {
      juiceboxQuotaRemaining.set({ type: 'search' }, result.quota_remaining);
    }

    return result;
  });
}

const results = await searchCandidates('senior rust engineer in Austin', 'u_42');
// Logs: {"level":"info","operation":"search","query":"senior rust engineer in Austin","userId":"u_42","msg":"search_started"}
// Logs: {"level":"info","operation":"search","resultCount":25,"duration_ms":1240,"status":200,"msg":"search_completed"}
// Metrics: juicebox_requests_total{operation="search",status="success"} incremented
// Metrics: juicebox_request_duration_seconds{operation="search"} observed at 1.24s
```

**Test the health endpoint with curl:**

```bash
curl -s http://localhost:3000/health/ready | jq .
# {
#   "status": "healthy",
#   "checks": {
#     "juicebox_api": { "status": "pass", "latency_ms": 340 },
#     "database": { "status": "pass", "latency_ms": 2 }
#   },
#   "timestamp": "2026-03-19T14:22:00.000Z"
# }
```

## Resources

- [Juicebox API docs](https://juicebox.ai/docs)
- [prom-client npm](https://www.npmjs.com/package/prom-client)
- [Pino structured logger](https://getpino.io/)
- [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Grafana dashboard JSON model](https://grafana.com/docs/grafana/latest/dashboards/json-model/)

## Next Steps

After observability, see `juicebox-incident-runbook` for responding to the alerts this skill creates.
