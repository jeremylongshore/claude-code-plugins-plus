---
name: veeva-observability
description: |
  Set up comprehensive observability for Veeva integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Veeva operations, setting up dashboards,
  or configuring alerting for Veeva integration health.
  Trigger with phrases like "veeva monitoring", "veeva metrics",
  "veeva observability", "monitor veeva", "veeva alerts", "veeva tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva Observability

## Overview
Set up comprehensive observability for Veeva integrations.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Metrics Collection

### Key Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `veeva_requests_total` | Counter | Total API requests |
| `veeva_request_duration_seconds` | Histogram | Request latency |
| `veeva_errors_total` | Counter | Error count by type |
| `veeva_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'veeva_requests_total',
  help: 'Total Veeva API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'veeva_request_duration_seconds',
  help: 'Veeva request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'veeva_errors_total',
  help: 'Veeva errors by type',
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

const tracer = trace.getTracer('veeva-client');

async function tracedVeevaCall<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`veeva.${operationName}`, async (span) => {
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
  name: 'veeva',
  level: process.env.LOG_LEVEL || 'info',
});

function logVeevaOperation(
  operation: string,
  data: Record<string, any>,
  duration: number
) {
  logger.info({
    service: 'veeva',
    operation,
    duration_ms: duration,
    ...data,
  });
}
```

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# veeva_alerts.yaml
groups:
  - name: veeva_alerts
    rules:
      - alert: VeevaHighErrorRate
        expr: |
          rate(veeva_errors_total[5m]) /
          rate(veeva_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Veeva error rate > 5%"

      - alert: VeevaHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(veeva_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Veeva P95 latency > 2s"

      - alert: VeevaDown
        expr: up{job="veeva"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Veeva integration is down"
```

## Dashboard

### Grafana Panel Queries

```json
{
  "panels": [
    {
      "title": "Veeva Request Rate",
      "targets": [{
        "expr": "rate(veeva_requests_total[5m])"
      }]
    },
    {
      "title": "Veeva Latency P50/P95/P99",
      "targets": [{
        "expr": "histogram_quantile(0.5, rate(veeva_request_duration_seconds_bucket[5m]))"
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
- [Veeva Observability Guide](https://docs.veeva.com/observability)

## Next Steps
For incident response, see `veeva-incident-runbook`.