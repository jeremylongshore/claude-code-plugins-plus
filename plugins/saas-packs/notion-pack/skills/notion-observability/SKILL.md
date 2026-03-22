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
Instrument Notion API calls with metrics, structured logging, and alerting. Track request rates, latencies, error rates, and rate limit headroom.

## Prerequisites
- `@notionhq/client` installed
- Prometheus or compatible metrics backend (optional)
- Structured logging library (pino, winston)

## Instructions

### Step 1: Instrumented Notion Wrapper
```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

interface NotionMetrics {
  requestCount: number;
  errorCount: number;
  rateLimitCount: number;
  totalLatencyMs: number;
  lastError: { code: string; message: string; timestamp: string } | null;
}

class InstrumentedNotionClient {
  private client: Client;
  private metrics: NotionMetrics = {
    requestCount: 0, errorCount: 0, rateLimitCount: 0,
    totalLatencyMs: 0, lastError: null,
  };

  constructor(auth: string) {
    this.client = new Client({ auth, timeoutMs: 30_000 });
  }

  async call<T>(operation: string, fn: (client: Client) => Promise<T>): Promise<T> {
    const start = performance.now();
    this.metrics.requestCount++;

    try {
      const result = await fn(this.client);
      const durationMs = performance.now() - start;
      this.metrics.totalLatencyMs += durationMs;

      console.log(JSON.stringify({
        level: 'info', service: 'notion', operation,
        durationMs: Math.round(durationMs), status: 'ok',
      }));

      return result;
    } catch (error) {
      const durationMs = performance.now() - start;
      this.metrics.totalLatencyMs += durationMs;
      this.metrics.errorCount++;

      const errorInfo = isNotionClientError(error)
        ? { code: error.code, message: error.message, status: error.status }
        : { code: 'unknown', message: String(error), status: 0 };

      if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
        this.metrics.rateLimitCount++;
      }

      this.metrics.lastError = {
        code: errorInfo.code,
        message: errorInfo.message,
        timestamp: new Date().toISOString(),
      };

      console.log(JSON.stringify({
        level: 'error', service: 'notion', operation,
        durationMs: Math.round(durationMs), status: 'error', ...errorInfo,
      }));

      throw error;
    }
  }

  getMetrics(): NotionMetrics & { avgLatencyMs: number } {
    return {
      ...this.metrics,
      avgLatencyMs: this.metrics.requestCount > 0
        ? Math.round(this.metrics.totalLatencyMs / this.metrics.requestCount)
        : 0,
    };
  }
}

// Usage
const notion = new InstrumentedNotionClient(process.env.NOTION_TOKEN!);

const pages = await notion.call('databases.query', (client) =>
  client.databases.query({ database_id: dbId, page_size: 50 })
);
```

### Step 2: Prometheus Metrics
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
  help: 'Notion API request latency',
  labelNames: ['operation'],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

const notionErrors = new Counter({
  name: 'notion_errors_total',
  help: 'Notion API errors by code',
  labelNames: ['code'],
  registers: [registry],
});

// Wrap every Notion call
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

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 3: Structured Logging with pino
```typescript
import pino from 'pino';

const logger = pino({
  name: 'notion-integration',
  level: process.env.LOG_LEVEL || 'info',
});

// Log every Notion API call
function logNotionCall(operation: string, durationMs: number, result: 'ok' | 'error', details?: any) {
  logger.info({
    service: 'notion',
    operation,
    durationMs,
    result,
    ...details,
  }, `notion.${operation}: ${result} (${durationMs}ms)`);
}

// Log rate limit events specifically
function logRateLimit(operation: string, retryAfter: number) {
  logger.warn({
    service: 'notion',
    event: 'rate_limited',
    operation,
    retryAfterSeconds: retryAfter,
  }, `Rate limited on ${operation}. Retry after ${retryAfter}s`);
}
```

### Step 4: Health Check Endpoint
```typescript
app.get('/health', async (req, res) => {
  const checks: Record<string, any> = {};

  // Notion connectivity
  const start = Date.now();
  try {
    await notion.call('health', (c) => c.users.me({}));
    checks.notion = { status: 'connected', latencyMs: Date.now() - start };
  } catch (error) {
    checks.notion = {
      status: 'disconnected',
      latencyMs: Date.now() - start,
      error: isNotionClientError(error) ? error.code : 'unknown',
    };
  }

  // Overall status
  const healthy = checks.notion.status === 'connected';
  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    checks,
    metrics: notion.getMetrics(),
    timestamp: new Date().toISOString(),
  });
});
```

### Step 5: Alerting Rules (Prometheus)
```yaml
groups:
  - name: notion_alerts
    rules:
      - alert: NotionHighErrorRate
        expr: rate(notion_errors_total[5m]) / rate(notion_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion error rate > 5%"

      - alert: NotionRateLimited
        expr: increase(notion_errors_total{code="rate_limited"}[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Notion rate limit hits increasing"

      - alert: NotionHighLatency
        expr: histogram_quantile(0.95, rate(notion_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion P95 latency > 3s"

      - alert: NotionDown
        expr: increase(notion_errors_total{code="service_unavailable"}[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Notion API appears down"
```

## Output
- Instrumented Notion client tracking all API calls
- Prometheus metrics for request rate, latency, and errors
- Structured JSON logging for searchability
- Health check endpoint with Notion connectivity status
- Alerting rules for error rate, rate limits, latency, and outages

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality metrics | Too many label values | Use fixed operation names |
| Alert storms | Thresholds too sensitive | Tune `for` durations |
| Missing metrics | Calls not instrumented | Use wrapper for all API calls |
| Log volume too high | DEBUG level in production | Set LOG_LEVEL=info or warn |

## Examples

### Quick Metrics Check
```typescript
const metrics = notion.getMetrics();
console.log(`Requests: ${metrics.requestCount}, Errors: ${metrics.errorCount}, Avg Latency: ${metrics.avgLatencyMs}ms`);
```

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [pino Logger](https://getpino.io/)
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)

## Next Steps
For incident response, see `notion-incident-runbook`.
