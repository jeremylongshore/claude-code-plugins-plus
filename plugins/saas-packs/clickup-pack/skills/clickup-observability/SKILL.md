---
name: clickup-observability
description: |
  Monitor ClickUp API integrations with metrics, tracing, structured logging,
  and alerting using Prometheus, OpenTelemetry, and Grafana.
  Trigger: "clickup monitoring", "clickup metrics", "clickup observability",
  "monitor clickup", "clickup alerts", "clickup tracing", "clickup dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Observability

## Overview

Monitor ClickUp API v2 integrations with metrics (request rate, latency, errors, rate limit usage), distributed tracing, and alerting.

## Key Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `clickup_requests_total` | Counter | method, endpoint, status | Total API requests |
| `clickup_request_duration_seconds` | Histogram | method, endpoint | Request latency |
| `clickup_errors_total` | Counter | status_code, error_type | Errors by type |
| `clickup_rate_limit_remaining` | Gauge | token_hash | Rate limit headroom |
| `clickup_rate_limit_resets_total` | Counter | | Times we hit 429 |

## Prometheus Instrumentation

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'clickup_requests_total',
  help: 'Total ClickUp API v2 requests',
  labelNames: ['method', 'endpoint', 'status'] as const,
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'clickup_request_duration_seconds',
  help: 'ClickUp API request duration in seconds',
  labelNames: ['method', 'endpoint'] as const,
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2, 5],
  registers: [registry],
});

const rateLimitGauge = new Gauge({
  name: 'clickup_rate_limit_remaining',
  help: 'ClickUp rate limit remaining requests',
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'clickup_errors_total',
  help: 'ClickUp API errors by status code',
  labelNames: ['status_code', 'error_type'] as const,
  registers: [registry],
});
```

## Instrumented Client

```typescript
async function instrumentedClickUpRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const method = options.method ?? 'GET';
  // Normalize endpoint for cardinality control (replace UUIDs)
  const endpoint = path.replace(/\/[a-zA-Z0-9]{6,}(?=\/|$|\?)/g, '/:id');
  const timer = requestDuration.startTimer({ method, endpoint });

  try {
    const response = await fetch(`https://api.clickup.com/api/v2${path}`, {
      ...options,
      headers: {
        'Authorization': process.env.CLICKUP_API_TOKEN!,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Update rate limit gauge
    const remaining = response.headers.get('X-RateLimit-Remaining');
    if (remaining) rateLimitGauge.set(parseInt(remaining));

    const status = response.ok ? 'success' : `${response.status}`;
    requestCounter.inc({ method, endpoint, status });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      errorCounter.inc({
        status_code: String(response.status),
        error_type: body.ECODE ?? 'unknown',
      });
      throw new Error(`ClickUp ${response.status}: ${body.err}`);
    }

    return response.json();
  } catch (error) {
    if (!(error instanceof Error && error.message.startsWith('ClickUp'))) {
      errorCounter.inc({ status_code: 'network', error_type: 'fetch_error' });
    }
    throw error;
  } finally {
    timer();
  }
}
```

## OpenTelemetry Tracing

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('clickup-integration', '1.0.0');

async function tracedClickUpCall<T>(
  operationName: string,
  path: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`clickup.${operationName}`, async (span) => {
    span.setAttribute('clickup.path', path);
    span.setAttribute('clickup.method', 'GET');

    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
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

const logger = pino({ name: 'clickup', level: process.env.LOG_LEVEL ?? 'info' });

function logClickUpCall(data: {
  method: string;
  path: string;
  status: number;
  durationMs: number;
  rateLimitRemaining?: number;
  error?: string;
}): void {
  const level = data.status >= 500 ? 'error' : data.status >= 400 ? 'warn' : 'info';
  logger[level]({
    service: 'clickup',
    ...data,
  }, `ClickUp ${data.method} ${data.path} -> ${data.status} (${data.durationMs}ms)`);
}
```

## Alert Rules

```yaml
# prometheus/clickup_alerts.yaml
groups:
  - name: clickup
    rules:
      - alert: ClickUpHighErrorRate
        expr: rate(clickup_errors_total[5m]) / rate(clickup_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "ClickUp API error rate > 5%"

      - alert: ClickUpHighLatency
        expr: histogram_quantile(0.95, rate(clickup_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "ClickUp P95 latency > 3s"

      - alert: ClickUpRateLimitLow
        expr: clickup_rate_limit_remaining < 10
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "ClickUp rate limit nearly exhausted"

      - alert: ClickUpAuthFailures
        expr: increase(clickup_errors_total{status_code="401"}[5m]) > 0
        labels: { severity: critical }
        annotations:
          summary: "ClickUp authentication failures detected"
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
| High cardinality | Dynamic IDs in labels | Normalize paths (replace IDs with `:id`) |
| Missing metrics | Uninstrumented code path | Wrap all API calls through instrumented client |
| Alert storm | Threshold too sensitive | Tune `for` duration and threshold |
| Trace gaps | Missing context propagation | Ensure span context is passed |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry JS SDK](https://opentelemetry.io/docs/languages/js/)
- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)

## Next Steps

For incident response, see `clickup-incident-runbook`.
