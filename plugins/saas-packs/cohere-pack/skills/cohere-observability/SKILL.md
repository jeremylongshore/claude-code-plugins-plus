---
name: cohere-observability
description: |
  Set up comprehensive observability for Cohere API v2 with metrics, traces, and alerts.
  Use when implementing monitoring for Chat/Embed/Rerank operations,
  setting up dashboards, or configuring alerts for Cohere integrations.
  Trigger with phrases like "cohere monitoring", "cohere metrics",
  "cohere observability", "monitor cohere", "cohere alerts", "cohere tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Observability

## Overview
Set up production observability for Cohere API v2 with Prometheus metrics, OpenTelemetry tracing, and AlertManager rules. Tracks per-endpoint latency, token usage, error rates, and costs.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- `cohere-ai` SDK v7+

## Instructions

### Step 1: Metrics Collection

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

// Per-endpoint request counter
const requestCounter = new Counter({
  name: 'cohere_requests_total',
  help: 'Total Cohere API requests',
  labelNames: ['endpoint', 'model', 'status'],
  registers: [registry],
});

// Latency histogram
const requestDuration = new Histogram({
  name: 'cohere_request_duration_seconds',
  help: 'Cohere request duration',
  labelNames: ['endpoint', 'model'],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30],
  registers: [registry],
});

// Token usage tracking
const tokenCounter = new Counter({
  name: 'cohere_tokens_total',
  help: 'Total tokens consumed',
  labelNames: ['endpoint', 'model', 'direction'], // direction: input|output
  registers: [registry],
});

// Error counter by type
const errorCounter = new Counter({
  name: 'cohere_errors_total',
  help: 'Cohere errors by status code',
  labelNames: ['endpoint', 'status_code'],
  registers: [registry],
});

// Rate limit headroom
const rateLimitGauge = new Gauge({
  name: 'cohere_rate_limit_remaining',
  help: 'Remaining rate limit capacity',
  labelNames: ['endpoint'],
  registers: [registry],
});
```

### Step 2: Instrumented Client Wrapper

```typescript
import { CohereClientV2, CohereError, CohereTimeoutError } from 'cohere-ai';

const cohere = new CohereClientV2();

async function instrumentedCall<T>(
  endpoint: string,
  model: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = requestDuration.startTimer({ endpoint, model });

  try {
    const result = await operation();
    requestCounter.inc({ endpoint, model, status: 'success' });
    timer();

    // Track tokens from response
    const usage = (result as any)?.usage?.billedUnits;
    if (usage) {
      if (usage.inputTokens) {
        tokenCounter.inc({ endpoint, model, direction: 'input' }, usage.inputTokens);
      }
      if (usage.outputTokens) {
        tokenCounter.inc({ endpoint, model, direction: 'output' }, usage.outputTokens);
      }
    }

    return result;
  } catch (err) {
    requestCounter.inc({ endpoint, model, status: 'error' });
    timer();

    if (err instanceof CohereError) {
      errorCounter.inc({ endpoint, status_code: String(err.statusCode) });
    } else if (err instanceof CohereTimeoutError) {
      errorCounter.inc({ endpoint, status_code: 'timeout' });
    }

    throw err;
  }
}

// Usage
const response = await instrumentedCall('chat', 'command-a-03-2025', () =>
  cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: query }],
  })
);
```

### Step 3: OpenTelemetry Tracing

```typescript
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';

const tracer = trace.getTracer('cohere-client', '1.0.0');

async function tracedCohereCall<T>(
  endpoint: string,
  model: string,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    `cohere.${endpoint}`,
    { kind: SpanKind.CLIENT },
    async (span) => {
      span.setAttribute('cohere.model', model);
      span.setAttribute('cohere.endpoint', endpoint);

      try {
        const result = await operation();

        // Add token usage to span
        const usage = (result as any)?.usage?.billedUnits;
        if (usage) {
          span.setAttribute('cohere.tokens.input', usage.inputTokens ?? 0);
          span.setAttribute('cohere.tokens.output', usage.outputTokens ?? 0);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (err: any) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
        span.recordException(err);

        if (err instanceof CohereError) {
          span.setAttribute('cohere.error.status', err.statusCode ?? 0);
        }
        throw err;
      } finally {
        span.end();
      }
    }
  );
}
```

### Step 4: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({ name: 'cohere', level: process.env.LOG_LEVEL ?? 'info' });

function logCohereCall(
  endpoint: string,
  model: string,
  durationMs: number,
  status: 'success' | 'error',
  meta?: Record<string, unknown>
) {
  logger[status === 'error' ? 'error' : 'info']({
    service: 'cohere',
    endpoint,
    model,
    durationMs,
    status,
    ...meta,
  });
}

// Combined instrumentation
async function observedCall<T>(
  endpoint: string,
  model: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracedCohereCall(endpoint, model, () =>
    instrumentedCall(endpoint, model, async () => {
      const start = Date.now();
      try {
        const result = await fn();
        logCohereCall(endpoint, model, Date.now() - start, 'success', {
          tokens: (result as any)?.usage?.billedUnits,
        });
        return result;
      } catch (err) {
        logCohereCall(endpoint, model, Date.now() - start, 'error', {
          error: err instanceof CohereError ? err.statusCode : 'timeout',
        });
        throw err;
      }
    })
  );
}
```

### Step 5: Alert Rules

```yaml
# prometheus/cohere-alerts.yml
groups:
  - name: cohere
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
          description: "{{ $labels.endpoint }} error rate: {{ $value | humanizePercentage }}"

      - alert: CohereRateLimited
        expr: rate(cohere_errors_total{status_code="429"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Cohere rate limiting detected"

      - alert: CohereHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(cohere_request_duration_seconds_bucket[5m])
          ) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cohere P95 latency > 10s"

      - alert: CohereAuthFailure
        expr: cohere_errors_total{status_code="401"} > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Cohere authentication failure — check API key"

      - alert: CohereHighTokenBurn
        expr: rate(cohere_tokens_total[1h]) > 100000
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Cohere token burn rate > 100K/hour"
```

### Step 6: Metrics Endpoint

```typescript
// GET /metrics
import express from 'express';

const app = express();

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Dashboard Panels (Grafana)

| Panel | Query | Type |
|-------|-------|------|
| Request Rate | `rate(cohere_requests_total[5m])` | Time series |
| Error Rate | `rate(cohere_errors_total[5m]) / rate(cohere_requests_total[5m])` | Stat |
| P50/P95 Latency | `histogram_quantile(0.95, rate(cohere_request_duration_seconds_bucket[5m]))` | Time series |
| Token Usage | `rate(cohere_tokens_total[1h])` | Bar chart |
| Errors by Code | `sum by (status_code)(rate(cohere_errors_total[5m]))` | Pie chart |

## Output
- Prometheus metrics for requests, latency, tokens, and errors
- OpenTelemetry traces with Cohere-specific attributes
- Structured JSON logging with pino
- AlertManager rules for error rate, latency, auth, and cost

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing token metrics | Usage not in response | Check `response.usage.billedUnits` |
| High cardinality | Too many model labels | Use model family, not exact version |
| Alert storm | Threshold too low | Tune thresholds for your traffic |
| Trace gaps | Missing context propagation | Ensure OTel context flows through async |

## Resources
- [Prometheus Naming Conventions](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)
- [Cohere API Reference](https://docs.cohere.com/reference/about)

## Next Steps
For incident response, see `cohere-incident-runbook`.
