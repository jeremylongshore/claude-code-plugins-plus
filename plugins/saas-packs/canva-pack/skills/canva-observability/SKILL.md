---
name: canva-observability
description: |
  Set up observability for Canva Connect API integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Canva API operations, setting up dashboards,
  or configuring alerting for Canva integration health.
  Trigger with phrases like "canva monitoring", "canva metrics",
  "canva observability", "monitor canva", "canva alerts", "canva tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Observability

## Overview

Instrument Canva Connect API calls with metrics, traces, and structured logging. Track latency, error rates, rate limit headroom, and export job completion times.

## Key Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `canva_api_requests_total` | Counter | `method`, `endpoint`, `status` | Total API calls |
| `canva_api_duration_seconds` | Histogram | `method`, `endpoint` | Request latency |
| `canva_api_errors_total` | Counter | `endpoint`, `error_code` | Error count |
| `canva_export_duration_seconds` | Histogram | `format` | Export completion time |
| `canva_token_refresh_total` | Counter | `status` | Token refresh attempts |
| `canva_rate_limit_remaining` | Gauge | `endpoint` | Rate limit headroom |

## Prometheus Instrumentation

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'canva_api_requests_total',
  help: 'Total Canva Connect API requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'canva_api_duration_seconds',
  help: 'Canva API request duration',
  labelNames: ['method', 'endpoint'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const rateLimitGauge = new Gauge({
  name: 'canva_rate_limit_remaining',
  help: 'Remaining rate limit for endpoint',
  labelNames: ['endpoint'],
  registers: [registry],
});

const exportDuration = new Histogram({
  name: 'canva_export_duration_seconds',
  help: 'Time from export request to completion',
  labelNames: ['format'],
  buckets: [1, 2, 5, 10, 20, 30, 60],
  registers: [registry],
});
```

## Instrumented Client Wrapper

```typescript
async function instrumentedCanvaRequest<T>(
  method: string,
  endpoint: string,
  fn: () => Promise<Response>
): Promise<T> {
  const timer = requestDuration.startTimer({ method, endpoint });

  try {
    const res = await fn();

    // Track rate limit headroom
    const remaining = res.headers.get('X-RateLimit-Remaining');
    if (remaining) {
      rateLimitGauge.set({ endpoint }, parseInt(remaining));
    }

    const status = res.ok ? 'success' : `error_${res.status}`;
    requestCounter.inc({ method, endpoint, status });

    if (!res.ok) {
      const body = await res.text();
      throw new CanvaAPIError(res.status, body, endpoint);
    }

    return res.json();
  } catch (error) {
    requestCounter.inc({ method, endpoint, status: 'exception' });
    throw error;
  } finally {
    timer();
  }
}
```

## OpenTelemetry Tracing

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('canva-connect-api');

async function tracedCanvaCall<T>(
  operationName: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`canva.${operationName}`, async (span) => {
    span.setAttribute('canva.base_url', 'api.canva.com/rest/v1');

    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.setAttribute('canva.error_code', error.status || 'unknown');
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

const logger = pino({ name: 'canva', level: process.env.LOG_LEVEL || 'info' });

function logCanvaRequest(data: {
  method: string;
  endpoint: string;
  status: number;
  durationMs: number;
  rateLimitRemaining?: number;
}) {
  // NEVER log access tokens or refresh tokens
  logger.info({
    service: 'canva-connect-api',
    ...data,
  });
}
```

## Alert Rules

```yaml
# prometheus/canva-alerts.yml
groups:
  - name: canva_connect_api
    rules:
      - alert: CanvaHighErrorRate
        expr: |
          rate(canva_api_errors_total[5m]) /
          rate(canva_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Canva API error rate > 5%"

      - alert: CanvaHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(canva_api_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Canva API P95 latency > 3s"

      - alert: CanvaRateLimitLow
        expr: canva_rate_limit_remaining < 5
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Canva rate limit nearly exhausted"

      - alert: CanvaTokenRefreshFailing
        expr: increase(canva_token_refresh_total{status="error"}[15m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Canva token refresh failing — users may lose access"

      - alert: CanvaExportSlow
        expr: |
          histogram_quantile(0.95,
            rate(canva_export_duration_seconds_bucket[15m])
          ) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Canva exports taking > 30s at P95"
```

## Grafana Dashboard Queries

```
# Request rate by endpoint
rate(canva_api_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(canva_api_duration_seconds_bucket[5m]))

# Error rate percentage
100 * rate(canva_api_requests_total{status=~"error.*"}[5m]) / rate(canva_api_requests_total[5m])

# Rate limit headroom
canva_rate_limit_remaining

# Export completion time P50/P95
histogram_quantile(0.5, rate(canva_export_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(canva_export_duration_seconds_bucket[5m]))
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Wrap all API calls |
| High cardinality | Too many label values | Use endpoint patterns, not full paths |
| Alert storms | Thresholds too sensitive | Tune for-duration and threshold |
| Token in logs | Missing redaction | Never log Authorization headers |

## Resources

- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Prometheus](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry](https://opentelemetry.io/docs/)

## Next Steps

For incident response, see `canva-incident-runbook`.
