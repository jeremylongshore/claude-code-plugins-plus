---
name: supabase-observability
description: |
  Supabase metrics, traces, and alerts baseline configuration.
  Trigger phrases: "supabase monitoring", "supabase metrics",
  "supabase observability", "monitor supabase".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Observability

## Overview
Set up comprehensive observability for Supabase integrations.

## Metrics Collection

### Key Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `supabase_requests_total` | Counter | Total API requests |
| `supabase_request_duration_seconds` | Histogram | Request latency |
| `supabase_errors_total` | Counter | Error count by type |
| `supabase_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'supabase_requests_total',
  help: 'Total Supabase API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'supabase_request_duration_seconds',
  help: 'Supabase request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'supabase_errors_total',
  help: 'Supabase errors by type',
  labelNames: ['error_type'],
  registers: [registry],
});
```

### Instrumented Client

```typescript
async function instrumentedRequest<T>(
  method: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = requestDuration.startTimer({ method });

  try {
    const result = await operation();
    requestCounter.inc({ method, status: 'success' });
    return result;
  } catch (error: any) {
    requestCounter.inc({ method, status: 'error' });
    errorCounter.inc({ error_type: error.code || 'unknown' });
    throw error;
  } finally {
    timer();
  }
}
```

## Distributed Tracing

### OpenTelemetry Setup

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('supabase-client');

async function tracedSupabaseCall<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`supabase.${operationName}`, async (span) => {
    try {
      const result = await operation();
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

## Logging Strategy

### Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'supabase',
  level: process.env.LOG_LEVEL || 'info',
});

function logSupabaseOperation(
  operation: string,
  data: Record<string, any>,
  duration: number
) {
  logger.info({
    service: 'supabase',
    operation,
    duration_ms: duration,
    ...data,
  });
}
```

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# supabase_alerts.yaml
groups:
  - name: supabase_alerts
    rules:
      - alert: SupabaseHighErrorRate
        expr: |
          rate(supabase_errors_total[5m]) /
          rate(supabase_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Supabase error rate > 5%"

      - alert: SupabaseHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(supabase_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Supabase P95 latency > 2s"

      - alert: SupabaseDown
        expr: up{job="supabase"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Supabase integration is down"
```

## Dashboard

### Grafana Panel Queries

```json
{
  "panels": [
    {
      "title": "Supabase Request Rate",
      "targets": [{
        "expr": "rate(supabase_requests_total[5m])"
      }]
    },
    {
      "title": "Supabase Latency P50/P95/P99",
      "targets": [{
        "expr": "histogram_quantile(0.5, rate(supabase_request_duration_seconds_bucket[5m]))"
      }]
    }
  ]
}
```

## Next Steps
For incident response, see `supabase-incident-runbook`.