---
name: notion-observability
description: |
  Set up observability for Notion integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Notion API calls, setting up dashboards,
  or configuring alerting for Notion integration health.
  Trigger with phrases like "notion monitoring", "notion metrics",
  "notion observability", "monitor notion", "notion alerts", "notion tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Observability

## Overview

Instrument Notion API calls with metrics, structured logging, and alerting. Track request rates, latencies, error rates, and rate limit headroom. This skill covers a full observability stack: an instrumented client wrapper, Prometheus metrics with histogram buckets tuned for Notion's typical 200-800ms latency, structured logging via pino, health check endpoints, and Prometheus alerting rules for error rate spikes, rate limit exhaustion, high latency, and service outages.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Prometheus-compatible metrics backend (optional: Grafana, Datadog, or CloudWatch)
- Structured logging library: `pino` (Node.js) or `structlog` (Python)

## Instructions

### Step 1: Instrumented Notion Client Wrapper

Wrap every Notion API call with timing, error classification, and structured logging:

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

interface NotionMetrics {
  requestCount: number;
  errorCount: number;
  rateLimitCount: number;
  totalLatencyMs: number;
  latencyBuckets: Map<string, number[]>;
  lastError: { code: string; message: string; timestamp: string } | null;
}

class InstrumentedNotionClient {
  private client: Client;
  private metrics: NotionMetrics = {
    requestCount: 0,
    errorCount: 0,
    rateLimitCount: 0,
    totalLatencyMs: 0,
    latencyBuckets: new Map(),
    lastError: null,
  };

  constructor(auth: string, timeoutMs = 30_000) {
    this.client = new Client({ auth, timeoutMs });
  }

  async call<T>(operation: string, fn: (client: Client) => Promise<T>): Promise<T> {
    const start = performance.now();
    this.metrics.requestCount++;

    try {
      const result = await fn(this.client);
      const durationMs = Math.round(performance.now() - start);
      this.metrics.totalLatencyMs += durationMs;
      this.recordLatency(operation, durationMs);

      console.log(JSON.stringify({
        level: 'info',
        service: 'notion',
        operation,
        durationMs,
        status: 'ok',
        timestamp: new Date().toISOString(),
      }));

      return result;
    } catch (error) {
      const durationMs = Math.round(performance.now() - start);
      this.metrics.totalLatencyMs += durationMs;
      this.metrics.errorCount++;
      this.recordLatency(operation, durationMs);

      let errorInfo: { code: string; message: string; status: number };

      if (isNotionClientError(error)) {
        errorInfo = { code: error.code, message: error.message, status: error.status };

        if (error.code === APIErrorCode.RateLimited) {
          this.metrics.rateLimitCount++;
        }
      } else {
        errorInfo = { code: 'unknown', message: String(error), status: 0 };
      }

      this.metrics.lastError = {
        code: errorInfo.code,
        message: errorInfo.message,
        timestamp: new Date().toISOString(),
      };

      console.log(JSON.stringify({
        level: 'error',
        service: 'notion',
        operation,
        durationMs,
        status: 'error',
        errorCode: errorInfo.code,
        httpStatus: errorInfo.status,
        message: errorInfo.message,
        timestamp: new Date().toISOString(),
      }));

      throw error;
    }
  }

  private recordLatency(operation: string, durationMs: number) {
    const existing = this.metrics.latencyBuckets.get(operation) || [];
    existing.push(durationMs);
    this.metrics.latencyBuckets.set(operation, existing);
  }

  getMetrics(): NotionMetrics & { avgLatencyMs: number; p95LatencyMs: number } {
    const allLatencies = Array.from(this.metrics.latencyBuckets.values()).flat().sort((a, b) => a - b);
    const p95Index = Math.floor(allLatencies.length * 0.95);

    return {
      ...this.metrics,
      avgLatencyMs: this.metrics.requestCount > 0
        ? Math.round(this.metrics.totalLatencyMs / this.metrics.requestCount)
        : 0,
      p95LatencyMs: allLatencies[p95Index] ?? 0,
    };
  }
}

// Usage
const notion = new InstrumentedNotionClient(process.env.NOTION_TOKEN!);

const pages = await notion.call('databases.query', (client) =>
  client.databases.query({ database_id: dbId, page_size: 50 })
);

const user = await notion.call('users.me', (client) =>
  client.users.me({})
);
```

**Python — instrumented wrapper:**

```python
import time
import json
import logging
from notion_client import Client, APIResponseError

logger = logging.getLogger("notion")

class InstrumentedNotion:
    def __init__(self, token: str):
        self.client = Client(auth=token, timeout_ms=30_000)
        self.request_count = 0
        self.error_count = 0
        self.rate_limit_count = 0
        self.total_latency_ms = 0.0

    def call(self, operation: str, fn):
        start = time.monotonic()
        self.request_count += 1
        try:
            result = fn(self.client)
            duration_ms = round((time.monotonic() - start) * 1000)
            self.total_latency_ms += duration_ms
            logger.info(json.dumps({
                "service": "notion", "operation": operation,
                "duration_ms": duration_ms, "status": "ok",
            }))
            return result
        except APIResponseError as e:
            duration_ms = round((time.monotonic() - start) * 1000)
            self.total_latency_ms += duration_ms
            self.error_count += 1
            if e.status == 429:
                self.rate_limit_count += 1
            logger.error(json.dumps({
                "service": "notion", "operation": operation,
                "duration_ms": duration_ms, "status": "error",
                "error_code": e.code, "http_status": e.status,
            }))
            raise

# Usage
notion = InstrumentedNotion(os.environ["NOTION_TOKEN"])
pages = notion.call("databases.query",
    lambda c: c.databases.query(database_id=db_id, page_size=50))
```

### Step 2: Prometheus Metrics Export

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const notionRequests = new Counter({
  name: 'notion_requests_total',
  help: 'Total Notion API requests',
  labelNames: ['operation', 'status'],
  registers: [registry],
});

const notionDuration = new Histogram({
  name: 'notion_request_duration_seconds',
  help: 'Notion API request latency in seconds',
  labelNames: ['operation'],
  // Buckets tuned for Notion's typical 200-800ms response times
  buckets: [0.1, 0.25, 0.5, 0.8, 1, 2, 5, 10],
  registers: [registry],
});

const notionErrors = new Counter({
  name: 'notion_errors_total',
  help: 'Notion API errors by error code',
  labelNames: ['code'],
  registers: [registry],
});

const notionRateLimitRemaining = new Gauge({
  name: 'notion_rate_limit_remaining',
  help: 'Estimated remaining rate limit headroom',
  registers: [registry],
});

// Wrap every Notion call with Prometheus instrumentation
async function instrumentedCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = notionDuration.startTimer({ operation });
  try {
    const result = await fn();
    notionRequests.inc({ operation, status: 'success' });
    return result;
  } catch (error) {
    notionRequests.inc({ operation, status: 'error' });
    if (isNotionClientError(error)) {
      notionErrors.inc({ code: error.code });
    }
    throw error;
  } finally {
    timer();
  }
}

// Expose /metrics endpoint for Prometheus scraping
app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 3: Health Check, Structured Logging, and Alerting

**Health check endpoint:**

```typescript
app.get('/health/notion', async (_req, res) => {
  const checks: Record<string, any> = {};

  // Test Notion API connectivity
  const start = Date.now();
  try {
    const me = await notion.call('health.users.me', (c) => c.users.me({}));
    checks.notion = {
      status: 'connected',
      latencyMs: Date.now() - start,
      botName: me.name,
    };
  } catch (error) {
    checks.notion = {
      status: 'disconnected',
      latencyMs: Date.now() - start,
      error: isNotionClientError(error) ? error.code : 'unknown',
    };
  }

  const healthy = checks.notion.status === 'connected';
  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    checks,
    metrics: notion.getMetrics(),
    timestamp: new Date().toISOString(),
  });
});
```

**Structured logging with pino:**

```typescript
import pino from 'pino';

const logger = pino({
  name: 'notion-integration',
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
});

function logNotionCall(
  operation: string,
  durationMs: number,
  result: 'ok' | 'error',
  details?: Record<string, unknown>
) {
  const entry = {
    service: 'notion',
    operation,
    durationMs,
    result,
    ...details,
  };

  if (result === 'error') {
    logger.error(entry, `notion.${operation} failed (${durationMs}ms)`);
  } else if (durationMs > 2000) {
    logger.warn(entry, `notion.${operation} slow (${durationMs}ms)`);
  } else {
    logger.info(entry, `notion.${operation} ok (${durationMs}ms)`);
  }
}

function logRateLimit(operation: string, retryAfterMs: number) {
  logger.warn({
    service: 'notion',
    event: 'rate_limited',
    operation,
    retryAfterMs,
  }, `Rate limited on ${operation}. Retry in ${retryAfterMs}ms`);
}
```

**Prometheus alerting rules:**

```yaml
groups:
  - name: notion_alerts
    rules:
      - alert: NotionHighErrorRate
        expr: >
          rate(notion_errors_total[5m]) /
          rate(notion_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion API error rate exceeds 5%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: NotionRateLimited
        expr: increase(notion_errors_total{code="rate_limited"}[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Notion rate limit hits increasing"

      - alert: NotionHighLatency
        expr: >
          histogram_quantile(0.95,
            rate(notion_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion P95 latency exceeds 3 seconds"

      - alert: NotionDown
        expr: increase(notion_errors_total{code="service_unavailable"}[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Notion API appears down (repeated 503 errors)"
```

## Output

- Instrumented Notion client tracking all API calls with per-operation latency buckets
- Prometheus metrics for request rate, latency histograms, and error counters
- Structured JSON logging via pino with slow-query warnings (>2s)
- Health check endpoint with Notion connectivity status and aggregate metrics
- Alerting rules for error rate spikes, rate limiting, high latency, and outages

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality metrics | Too many unique label values | Use fixed operation names (`databases.query`, `pages.create`) |
| Alert storms on Notion outage | All alerts fire simultaneously | Add `group_wait: 30s` in alertmanager config |
| Missing metrics for some calls | Not all API calls use wrapper | Enforce wrapper at architecture level |
| Log volume too high in prod | DEBUG level enabled | Set `LOG_LEVEL=info` or `warn` in production |
| P95 latency unreliable | Too few samples | Ensure minimum 100 requests in window |
| Rate limit counter never fires | Wrong error code check | Use `APIErrorCode.RateLimited` constant |

## Examples

### Quick Metrics Dashboard Query (PromQL)

```promql
# Request rate by operation
rate(notion_requests_total[5m])

# Error percentage
100 * rate(notion_errors_total[5m]) / rate(notion_requests_total[5m])

# P95 latency per operation
histogram_quantile(0.95, rate(notion_request_duration_seconds_bucket[5m]))

# Rate limit events in last hour
increase(notion_errors_total{code="rate_limited"}[1h])
```

### Inline Metrics Check (No Prometheus)

```typescript
// Quick console-based metrics for debugging
setInterval(() => {
  const m = notion.getMetrics();
  console.log(
    `[Notion] requests=${m.requestCount} errors=${m.errorCount} ` +
    `rate_limits=${m.rateLimitCount} avg_latency=${m.avgLatencyMs}ms ` +
    `p95_latency=${m.p95LatencyMs}ms`
  );
}, 60_000); // Log every minute
```

## Resources

- [Notion Request Limits](https://developers.notion.com/reference/request-limits) — 3 requests/second average
- [Notion Error Codes](https://developers.notion.com/reference/errors) — full error code reference
- [Prometheus Naming Best Practices](https://prometheus.io/docs/practices/naming/)
- [pino Logger](https://getpino.io/) — fast structured logging for Node.js
- [Grafana Dashboard Templates](https://grafana.com/grafana/dashboards/) — pre-built API monitoring dashboards

## Next Steps

For incident response procedures when monitoring detects failures, see `notion-incident-runbook`.
