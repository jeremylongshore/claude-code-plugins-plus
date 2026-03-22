---
name: cohere-observability
description: |
  Set up comprehensive observability for Cohere integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Cohere operations, setting up dashboards,
  or configuring alerting for Cohere integration health.
  Trigger with phrases like "cohere monitoring", "cohere metrics",
  "cohere observability", "monitor cohere", "cohere alerts", "cohere tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cohere]
---

# Cohere Observability

## Overview
Set up comprehensive observability for Cohere integrations.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Metrics Collection

### Key Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `cohere_requests_total` | Counter | Total API requests |
| `cohere_request_duration_seconds` | Histogram | Request latency |
| `cohere_errors_total` | Counter | Error count by type |
| `cohere_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'cohere_requests_total',
  help: 'Total Cohere API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'cohere_request_duration_seconds',
  help: 'Cohere request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'cohere_errors_total',
  help: 'Cohere errors by type',
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

const tracer = trace.getTracer('cohere-client');

async function tracedCohereCall<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`cohere.${operationName}`, async (span) => {
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
  name: 'cohere',
  level: process.env.LOG_LEVEL || 'info',
});

function logCohereOperation(
  operation: string,
  data: Record<string, any>,
  duration: number
) {
  logger.info({
    service: 'cohere',
    operation,
    duration_ms: duration,
    ...data,
  });
}
```

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# cohere_alerts.yaml
groups:
  - name: cohere_alerts
    rules:
      - alert: CohereHighErrorRate
        expr: |
          rate(cohere_errors_total[5m]) /
          rate(cohere_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cohere error rate > 5%"

      - alert: CohereHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(cohere_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cohere P95 latency > 2s"

      - alert: CohereDown
        expr: up{job="cohere"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Cohere integration is down"
```

## Dashboard

### Grafana Panel Queries

```json
{
  "panels": [
    {
      "title": "Cohere Request Rate",
      "targets": [{
        "expr": "rate(cohere_requests_total[5m])"
      }]
    },
    {
      "title": "Cohere Latency P50/P95/P99",
      "targets": [{
        "expr": "histogram_quantile(0.5, rate(cohere_request_duration_seconds_bucket[5m]))"
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
- [Cohere Observability Guide](https://docs.cohere.com/observability)

## Next Steps
For incident response, see `cohere-incident-runbook`.