---
name: windsurf-observability
description: |
  Set up comprehensive observability for Windsurf integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Windsurf operations, setting up dashboards,
  or configuring alerting for Windsurf integration health.
  Trigger with phrases like "windsurf monitoring", "windsurf metrics",
  "windsurf observability", "monitor windsurf", "windsurf alerts", "windsurf tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, windsurf]
---

# Windsurf Observability

## Overview
Set up comprehensive observability for Windsurf integrations.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Metrics Collection

### Key Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `windsurf_requests_total` | Counter | Total API requests |
| `windsurf_request_duration_seconds` | Histogram | Request latency |
| `windsurf_errors_total` | Counter | Error count by type |
| `windsurf_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'windsurf_requests_total',
  help: 'Total Windsurf API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'windsurf_request_duration_seconds',
  help: 'Windsurf request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'windsurf_errors_total',
  help: 'Windsurf errors by type',
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

const tracer = trace.getTracer('windsurf-client');

async function tracedWindsurfCall<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`windsurf.${operationName}`, async (span) => {
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
  name: 'windsurf',
  level: process.env.LOG_LEVEL || 'info',
});

function logWindsurfOperation(
  operation: string,
  data: Record<string, any>,
  duration: number
) {
  logger.info({
    service: 'windsurf',
    operation,
    duration_ms: duration,
    ...data,
  });
}
```

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# windsurf_alerts.yaml
groups:
  - name: windsurf_alerts
    rules:
      - alert: WindsurfHighErrorRate
        expr: |
          rate(windsurf_errors_total[5m]) /
          rate(windsurf_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Windsurf error rate > 5%"

      - alert: WindsurfHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(windsurf_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Windsurf P95 latency > 2s"

      - alert: WindsurfDown
        expr: up{job="windsurf"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Windsurf integration is down"
```

## Dashboard

### Grafana Panel Queries

```json
{
  "panels": [
    {
      "title": "Windsurf Request Rate",
      "targets": [{
        "expr": "rate(windsurf_requests_total[5m])"
      }]
    },
    {
      "title": "Windsurf Latency P50/P95/P99",
      "targets": [{
        "expr": "histogram_quantile(0.5, rate(windsurf_request_duration_seconds_bucket[5m]))"
      }]
    }
  ]
}
```

## Instructions

### Step 1: Set Up Metrics Collection
Implement Prometheus counters, histograms, and gauges for key operations.

### Step 2: Add Distributed Tracing
Integrate OpenTelemetry for end-to-end request tracing.

### Step 3: Configure Structured Logging
Set up JSON logging with consistent field names.

### Step 4: Create Alert Rules
Define Prometheus alerting rules for error rates and latency.

## Output
- Metrics collection enabled
- Distributed tracing configured
- Structured logging implemented
- Alert rules deployed

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Wrap client calls |
| Trace gaps | Missing propagation | Check context headers |
| Alert storms | Wrong thresholds | Tune alert rules |
| High cardinality | Too many labels | Reduce label values |

## Examples

### Quick Metrics Endpoint
```typescript
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Windsurf Observability Guide](https://docs.windsurf.com/observability)

## Next Steps
For incident response, see `windsurf-incident-runbook`.