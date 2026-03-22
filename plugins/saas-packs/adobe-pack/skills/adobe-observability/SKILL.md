---
name: adobe-observability
description: |
  Set up comprehensive observability for Adobe API integrations with
  Prometheus metrics, OpenTelemetry traces, structured logging, and
  alert rules covering Firefly, PDF Services, and Photoshop APIs.
  Trigger with phrases like "adobe monitoring", "adobe metrics",
  "adobe observability", "monitor adobe", "adobe alerts", "adobe tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Observability

## Overview

Set up comprehensive observability for Adobe API integrations covering four pillars: metrics (Prometheus), traces (OpenTelemetry), logs (structured JSON), and alerts. Each Adobe API has different latency profiles requiring specific monitoring.

## Prerequisites

- Prometheus or compatible metrics backend
- OpenTelemetry SDK (`@opentelemetry/api`)
- Grafana or similar dashboarding tool
- AlertManager or PagerDuty for alerts

## Instructions

### Step 1: Define Key Metrics by API

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `adobe_ims_token_requests_total` | Counter | `status` | Token generation attempts |
| `adobe_api_requests_total` | Counter | `api,operation,status` | API calls by type |
| `adobe_api_duration_seconds` | Histogram | `api,operation` | Latency per operation |
| `adobe_api_errors_total` | Counter | `api,error_code` | Errors by code (401,403,429,500) |
| `adobe_job_poll_count` | Histogram | `api` | Polls before async job completes |
| `adobe_rate_limit_retries_total` | Counter | `api` | 429 retries |
| `adobe_pdf_transactions_used` | Gauge | — | Monthly PDF Services usage |

### Step 2: Instrumented Adobe Client

```typescript
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const apiRequests = new Counter({
  name: 'adobe_api_requests_total',
  help: 'Total Adobe API requests',
  labelNames: ['api', 'operation', 'status'] as const,
  registers: [registry],
});

const apiDuration = new Histogram({
  name: 'adobe_api_duration_seconds',
  help: 'Adobe API request duration in seconds',
  labelNames: ['api', 'operation'] as const,
  buckets: [0.5, 1, 2, 5, 10, 20, 30, 60], // Adobe APIs are slow
  registers: [registry],
});

const apiErrors = new Counter({
  name: 'adobe_api_errors_total',
  help: 'Adobe API errors by code',
  labelNames: ['api', 'error_code'] as const,
  registers: [registry],
});

export async function instrumentedAdobeCall<T>(
  api: string,
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ api, operation });
  try {
    const result = await fn();
    apiRequests.inc({ api, operation, status: 'success' });
    return result;
  } catch (error: any) {
    const errorCode = error.status || error.httpStatus || 'unknown';
    apiRequests.inc({ api, operation, status: 'error' });
    apiErrors.inc({ api, error_code: String(errorCode) });
    throw error;
  } finally {
    timer();
  }
}

// Usage
const image = await instrumentedAdobeCall('firefly', 'generate', () =>
  generateImage({ prompt: 'sunset landscape' })
);
```

### Step 3: OpenTelemetry Distributed Tracing

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('adobe-integration');

export async function tracedAdobeCall<T>(
  api: string,
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`adobe.${api}.${operation}`, async (span) => {
    span.setAttribute('adobe.api', api);
    span.setAttribute('adobe.operation', operation);
    span.setAttribute('adobe.client_id', process.env.ADOBE_CLIENT_ID!);

    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.setAttribute('adobe.error_code', error.status || 'unknown');
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

### Step 4: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'adobe',
  level: process.env.LOG_LEVEL || 'info',
  redact: ['clientSecret', 'accessToken', 'req.headers.authorization'],
});

export function logAdobeOperation(entry: {
  api: string;
  operation: string;
  durationMs: number;
  status: 'success' | 'error';
  httpStatus?: number;
  jobId?: string;
  error?: string;
}) {
  if (entry.status === 'error') {
    logger.error(entry, `Adobe ${entry.api}.${entry.operation} failed`);
  } else {
    logger.info(entry, `Adobe ${entry.api}.${entry.operation} completed`);
  }
}
```

### Step 5: Alert Rules

```yaml
# prometheus/adobe-alerts.yml
groups:
  - name: adobe_alerts
    rules:
      - alert: AdobeAuthFailure
        expr: increase(adobe_api_errors_total{error_code="401"}[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Adobe authentication failure — credentials may be expired or revoked"

      - alert: AdobeRateLimited
        expr: rate(adobe_api_errors_total{error_code="429"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Adobe API rate limited — reduce throughput or upgrade tier"

      - alert: AdobeHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(adobe_api_duration_seconds_bucket{api="firefly"}[5m])
          ) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Adobe Firefly P95 latency > 30s"

      - alert: AdobeApiDown
        expr: |
          rate(adobe_api_errors_total{error_code=~"5.."}[5m]) /
          rate(adobe_api_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Adobe API server error rate > 10%"

      - alert: AdobePdfQuotaLow
        expr: adobe_pdf_transactions_used > 450
        labels:
          severity: warning
        annotations:
          summary: "PDF Services: < 50 free tier transactions remaining"
```

### Metrics Endpoint

```typescript
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Output

- Prometheus metrics for all Adobe API calls (latency, errors, rate limits)
- OpenTelemetry traces with Adobe-specific span attributes
- Structured JSON logging with credential redaction
- Alert rules for auth failures, rate limiting, latency, and quota

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality metrics | Too many label values | Use fixed set of operation names |
| Alert storms | Thresholds too sensitive | Increase `for` duration |
| Missing traces | No OTel propagation | Verify context propagation setup |
| Redacted data in logs | Over-aggressive redaction | Whitelist safe fields |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [Adobe Status Page](https://status.adobe.com)

## Next Steps

For incident response, see `adobe-incident-runbook`.
