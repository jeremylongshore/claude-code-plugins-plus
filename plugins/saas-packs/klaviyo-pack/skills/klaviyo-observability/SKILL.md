---
name: klaviyo-observability
description: |
  Set up observability for Klaviyo integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Klaviyo API operations, setting up dashboards,
  or configuring alerting for Klaviyo integration health.
  Trigger with phrases like "klaviyo monitoring", "klaviyo metrics",
  "klaviyo observability", "monitor klaviyo", "klaviyo alerts", "klaviyo tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Observability

## Overview

Comprehensive observability for Klaviyo integrations: Prometheus metrics for API call tracking, OpenTelemetry tracing, structured logging, and alerting rules tuned to Klaviyo's rate limits and error patterns.

## Prerequisites

- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed (optional)
- Grafana or similar dashboarding tool (optional)
- `klaviyo-api` SDK installed

## Key Metrics to Track

| Metric | Type | Why It Matters |
|--------|------|---------------|
| `klaviyo_api_requests_total` | Counter | Track total API volume by endpoint |
| `klaviyo_api_duration_seconds` | Histogram | Detect latency degradation |
| `klaviyo_api_errors_total` | Counter | 4xx/5xx error rates |
| `klaviyo_rate_limit_remaining` | Gauge | Predict when you'll hit 429s |
| `klaviyo_profiles_synced_total` | Counter | Profile sync throughput |
| `klaviyo_events_tracked_total` | Counter | Event tracking volume |
| `klaviyo_webhook_received_total` | Counter | Inbound webhook volume |

## Instructions

### Step 1: Instrumented API Wrapper

```typescript
// src/klaviyo/instrumented-client.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const apiRequests = new Counter({
  name: 'klaviyo_api_requests_total',
  help: 'Total Klaviyo API requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [registry],
});

const apiDuration = new Histogram({
  name: 'klaviyo_api_duration_seconds',
  help: 'Klaviyo API request duration in seconds',
  labelNames: ['method', 'endpoint'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const apiErrors = new Counter({
  name: 'klaviyo_api_errors_total',
  help: 'Klaviyo API errors by status code',
  labelNames: ['endpoint', 'status_code', 'error_code'],
  registers: [registry],
});

const rateLimitRemaining = new Gauge({
  name: 'klaviyo_rate_limit_remaining',
  help: 'Remaining requests in current rate limit window',
  registers: [registry],
});

export async function instrumentedCall<T>(
  endpoint: string,
  method: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ method, endpoint });

  try {
    const result = await operation();
    apiRequests.inc({ method, endpoint, status: 'success' });

    // Extract rate limit headers if available
    const headers = (result as any)?.headers;
    if (headers?.['ratelimit-remaining']) {
      rateLimitRemaining.set(parseInt(headers['ratelimit-remaining']));
    }

    return result;
  } catch (error: any) {
    const statusCode = error.status || 'unknown';
    const errorCode = error.body?.errors?.[0]?.code || 'unknown';
    apiRequests.inc({ method, endpoint, status: 'error' });
    apiErrors.inc({ endpoint, status_code: statusCode, error_code: errorCode });
    throw error;
  } finally {
    timer();
  }
}

export { registry };
```

### Step 2: Usage in Service Layer

```typescript
// Wrap all Klaviyo calls with instrumentation
import { instrumentedCall } from '../klaviyo/instrumented-client';

// Profile creation with metrics
const profile = await instrumentedCall('profiles', 'POST', () =>
  profilesApi.createOrUpdateProfile({
    data: {
      type: 'profile' as any,
      attributes: { email: user.email, firstName: user.name },
    },
  })
);

// Event tracking with metrics
await instrumentedCall('events', 'POST', () =>
  eventsApi.createEvent({
    data: {
      type: 'event',
      attributes: {
        metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
        profile: { data: { type: 'profile', attributes: { email: order.email } } },
        properties: { orderId: order.id },
        value: order.total,
        time: new Date().toISOString(),
      },
    },
  })
);
```

### Step 3: OpenTelemetry Tracing

```typescript
// src/klaviyo/tracing.ts
import { trace, SpanStatusCode, Span } from '@opentelemetry/api';

const tracer = trace.getTracer('klaviyo-integration', '1.0.0');

export async function tracedKlaviyoCall<T>(
  operationName: string,
  attributes: Record<string, string>,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`klaviyo.${operationName}`, async (span: Span) => {
    span.setAttributes({
      'klaviyo.operation': operationName,
      'klaviyo.revision': '2024-10-15',
      ...attributes,
    });

    try {
      const result = await operation();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.setAttributes({
        'klaviyo.error.status': error.status?.toString() || 'unknown',
        'klaviyo.error.code': error.body?.errors?.[0]?.code || 'unknown',
      });
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
// src/klaviyo/logger.ts
import pino from 'pino';

const logger = pino({
  name: 'klaviyo',
  level: process.env.KLAVIYO_LOG_LEVEL || 'info',
  serializers: {
    // Redact sensitive data from logs
    profile: (profile: any) => ({
      id: profile.id,
      email: profile.email ? `${profile.email.substring(0, 3)}***` : undefined,
    }),
    err: pino.stdSerializers.err,
  },
});

export function logApiCall(operation: string, durationMs: number, status: 'ok' | 'error', meta?: Record<string, any>) {
  logger.info({
    msg: `klaviyo.${operation}`,
    service: 'klaviyo',
    operation,
    durationMs: Math.round(durationMs),
    status,
    ...meta,
  });
}

export function logWebhook(topic: string, eventId: string, durationMs: number) {
  logger.info({
    msg: `klaviyo.webhook.${topic}`,
    service: 'klaviyo',
    topic,
    eventId,
    durationMs: Math.round(durationMs),
  });
}

export { logger };
```

### Step 5: Alert Rules (Prometheus)

```yaml
# prometheus/klaviyo-alerts.yml
groups:
  - name: klaviyo
    rules:
      - alert: KlaviyoHighErrorRate
        expr: |
          rate(klaviyo_api_errors_total[5m]) /
          rate(klaviyo_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo API error rate above 5%"
          description: "Error rate: {{ $value | humanizePercentage }}"

      - alert: KlaviyoRateLimited
        expr: |
          increase(klaviyo_api_errors_total{status_code="429"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo rate limit being hit frequently"

      - alert: KlaviyoHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(klaviyo_api_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo API P95 latency above 3 seconds"

      - alert: KlaviyoDown
        expr: |
          increase(klaviyo_api_errors_total{status_code=~"5.."}[5m]) > 20
          and increase(klaviyo_api_requests_total{status="success"}[5m]) == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Klaviyo API appears to be down"

      - alert: KlaviyoRateLimitLow
        expr: klaviyo_rate_limit_remaining < 20
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo rate limit headroom below 20 requests"
```

### Step 6: Metrics Endpoint

```typescript
// src/routes/metrics.ts
import { registry } from '../klaviyo/instrumented-client';

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Grafana Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| Request Rate | `rate(klaviyo_api_requests_total[5m])` | API call volume |
| Error Rate | `rate(klaviyo_api_errors_total[5m])` | Error trend |
| Latency P50/P95 | `histogram_quantile(0.95, rate(klaviyo_api_duration_seconds_bucket[5m]))` | Performance |
| Rate Limit | `klaviyo_rate_limit_remaining` | Rate limit headroom |
| Error by Code | `topk(5, sum by (status_code) (rate(klaviyo_api_errors_total[5m])))` | Error breakdown |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation wrapper | Wrap all API calls with `instrumentedCall()` |
| High cardinality | Too many label values | Use endpoint groups, not full URLs |
| Alert storms | Thresholds too low | Tune alert rules to your traffic pattern |
| PII in logs | Email in log messages | Use serializer to redact emails |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [pino Logger](https://github.com/pinojs/pino)

## Next Steps

For incident response, see `klaviyo-incident-runbook`.
