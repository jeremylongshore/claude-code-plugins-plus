---
name: miro-observability
description: |
  Set up observability for Miro REST API v2 integrations with Prometheus metrics,
  OpenTelemetry traces, structured logging, and Grafana dashboards.
  Trigger with phrases like "miro monitoring", "miro metrics",
  "miro observability", "monitor miro", "miro alerts", "miro tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, observability, monitoring]
compatible-with: claude-code
---

# Miro Observability

## Overview

Comprehensive monitoring for Miro REST API v2 integrations: Prometheus metrics for request rates and latency, OpenTelemetry traces for request flow, structured logging, and alerting for rate limit and error conditions.

## Key Metrics

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `miro_requests_total` | Counter | method, endpoint, status | Request volume |
| `miro_request_duration_seconds` | Histogram | method, endpoint | Latency distribution |
| `miro_errors_total` | Counter | error_type, endpoint | Error tracking |
| `miro_rate_limit_remaining` | Gauge | — | Credit headroom |
| `miro_rate_limit_credits_used` | Gauge | — | Credit consumption |
| `miro_webhook_events_total` | Counter | event_type, item_type | Webhook volume |
| `miro_token_refresh_total` | Counter | status | OAuth health |

## Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();
registry.setDefaultLabels({ app: 'miro-integration' });

const requestCounter = new Counter({
  name: 'miro_requests_total',
  help: 'Total Miro REST API v2 requests',
  labelNames: ['method', 'endpoint', 'status'] as const,
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'miro_request_duration_seconds',
  help: 'Miro API request latency',
  labelNames: ['method', 'endpoint'] as const,
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'miro_errors_total',
  help: 'Miro API errors by type',
  labelNames: ['error_type', 'endpoint'] as const,
  registers: [registry],
});

const rateLimitRemaining = new Gauge({
  name: 'miro_rate_limit_remaining',
  help: 'Miro rate limit credits remaining',
  registers: [registry],
});

const rateLimitUsed = new Gauge({
  name: 'miro_rate_limit_credits_used',
  help: 'Miro rate limit credits used in current window',
  registers: [registry],
});

const webhookCounter = new Counter({
  name: 'miro_webhook_events_total',
  help: 'Miro webhook events received',
  labelNames: ['event_type', 'item_type'] as const,
  registers: [registry],
});
```

## Instrumented API Client

```typescript
class InstrumentedMiroClient {
  async fetch<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const endpoint = this.normalizeEndpoint(path);
    const timer = requestDuration.startTimer({ method, endpoint });

    try {
      const response = await fetch(`https://api.miro.com${path}`, {
        method,
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });

      // Update rate limit metrics from response headers
      const remaining = response.headers.get('X-RateLimit-Remaining');
      const limit = response.headers.get('X-RateLimit-Limit');
      if (remaining) rateLimitRemaining.set(parseInt(remaining));
      if (remaining && limit) {
        rateLimitUsed.set(parseInt(limit) - parseInt(remaining));
      }

      requestCounter.inc({ method, endpoint, status: String(response.status) });

      if (!response.ok) {
        const errorType = response.status === 429 ? 'rate_limit'
          : response.status === 401 ? 'auth'
          : response.status >= 500 ? 'server'
          : 'client';
        errorCounter.inc({ error_type: errorType, endpoint });
        throw new MiroApiError(response.status, await response.text());
      }

      return response.status === 204 ? null as T : await response.json();
    } catch (error) {
      if (!(error instanceof MiroApiError)) {
        errorCounter.inc({ error_type: 'network', endpoint });
      }
      throw error;
    } finally {
      timer();
    }
  }

  // Normalize endpoints for metric cardinality control
  // /v2/boards/uXjVN123/items/345 → /v2/boards/{id}/items/{id}
  private normalizeEndpoint(path: string): string {
    return path
      .replace(/\/boards\/[^/]+/, '/boards/{id}')
      .replace(/\/items\/[^/]+/, '/items/{id}')
      .replace(/\/sticky_notes\/[^/]+/, '/sticky_notes/{id}')
      .replace(/\/shapes\/[^/]+/, '/shapes/{id}')
      .replace(/\/connectors\/[^/]+/, '/connectors/{id}')
      .replace(/\?.*$/, '');
  }
}
```

## OpenTelemetry Tracing

```typescript
import { trace, SpanStatusCode, context } from '@opentelemetry/api';

const tracer = trace.getTracer('miro-client', '1.0.0');

async function tracedMiroFetch<T>(
  path: string,
  method: string,
  body?: unknown,
): Promise<T> {
  const endpoint = normalizeEndpoint(path);

  return tracer.startActiveSpan(`miro.${method} ${endpoint}`, async (span) => {
    span.setAttribute('miro.method', method);
    span.setAttribute('miro.endpoint', endpoint);
    span.setAttribute('miro.api_version', 'v2');

    try {
      const result = await instrumentedClient.fetch<T>(path, method, body);
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.setAttribute('miro.error_status', error.status ?? 0);
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'miro-integration',
  level: process.env.LOG_LEVEL ?? 'info',
  redact: ['token', 'accessToken', 'refreshToken', 'Authorization'],
});

function logMiroRequest(method: string, path: string, status: number, durationMs: number) {
  logger.info({
    service: 'miro',
    event: 'api_request',
    method,
    path: normalizeEndpoint(path),
    status,
    durationMs: Math.round(durationMs),
    rateLimitRemaining: currentRateLimitRemaining,
  });
}

function logWebhookEvent(event: MiroBoardEvent) {
  logger.info({
    service: 'miro',
    event: 'webhook_received',
    eventType: event.type,           // create | update | delete
    itemType: event.item.type,       // sticky_note | shape | card | etc.
    boardId: event.boardId,
    itemId: event.item.id,
  });
}
```

## Alert Rules (Prometheus AlertManager)

```yaml
# alerts/miro.yaml
groups:
  - name: miro_alerts
    rules:
      - alert: MiroHighErrorRate
        expr: |
          rate(miro_errors_total[5m]) /
          rate(miro_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Miro API error rate > 5%"
          dashboard: "https://grafana.myapp.com/d/miro"

      - alert: MiroHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(miro_request_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Miro API P95 latency > 3 seconds"

      - alert: MiroRateLimitLow
        expr: miro_rate_limit_remaining < 5000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Miro rate limit credits < 5000 remaining"
          runbook: "Reduce request rate immediately. See miro-rate-limits skill."

      - alert: MiroAuthFailures
        expr: rate(miro_errors_total{error_type="auth"}[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Miro authentication failures detected"
          runbook: "Check token expiry. Verify OAuth scopes."

      - alert: MiroDown
        expr: |
          sum(rate(miro_requests_total{status=~"5.."}[5m])) /
          sum(rate(miro_requests_total[5m])) > 0.5
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Miro API >50% server errors — check status.miro.com"
```

## Grafana Dashboard Panels

```json
{
  "panels": [
    {
      "title": "Miro Request Rate (req/s)",
      "targets": [{ "expr": "sum(rate(miro_requests_total[1m]))" }]
    },
    {
      "title": "Miro Latency P50/P95/P99",
      "targets": [
        { "expr": "histogram_quantile(0.50, rate(miro_request_duration_seconds_bucket[5m]))", "legendFormat": "P50" },
        { "expr": "histogram_quantile(0.95, rate(miro_request_duration_seconds_bucket[5m]))", "legendFormat": "P95" },
        { "expr": "histogram_quantile(0.99, rate(miro_request_duration_seconds_bucket[5m]))", "legendFormat": "P99" }
      ]
    },
    {
      "title": "Rate Limit Credits Remaining",
      "targets": [{ "expr": "miro_rate_limit_remaining" }]
    },
    {
      "title": "Error Rate by Type",
      "targets": [{ "expr": "sum by(error_type) (rate(miro_errors_total[5m]))" }]
    },
    {
      "title": "Webhook Events by Type",
      "targets": [{ "expr": "sum by(event_type, item_type) (rate(miro_webhook_events_total[5m]))" }]
    }
  ]
}
```

## Metrics Endpoint

```typescript
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality metrics | Board/item IDs in labels | Normalize endpoint paths |
| Missing traces | No context propagation | Check OpenTelemetry SDK init |
| Token in logs | Inadequate redaction | Use pino `redact` option |
| Alert storms | Thresholds too sensitive | Increase `for` duration |

## Resources

- [Prometheus Client (prom-client)](https://github.com/siimon/prom-client)
- [OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://getpino.io/)
- [Miro Rate Limiting](https://developers.miro.com/reference/rate-limiting)

## Next Steps

For incident response, see `miro-incident-runbook`.
