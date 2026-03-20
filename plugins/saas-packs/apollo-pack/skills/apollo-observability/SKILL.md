---
name: apollo-observability
description: |
  Set up Apollo.io monitoring and observability.
  Use when implementing logging, metrics, tracing, and alerting
  for Apollo integrations.
  Trigger with phrases like "apollo monitoring", "apollo metrics",
  "apollo observability", "apollo logging", "apollo alerts".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Observability

## Overview
Comprehensive observability setup for Apollo.io integrations covering Prometheus metrics, structured logging with PII redaction, OpenTelemetry tracing, and alerting rules for errors, rate limits, and latency.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Instrument Prometheus Metrics
```typescript
// src/observability/metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

export const registry = new Registry();

export const apolloRequestsTotal = new Counter({
  name: 'apollo_api_requests_total',
  help: 'Total Apollo API requests',
  labelNames: ['method', 'endpoint', 'status'] as const,
  registers: [registry],
});

export const apolloRequestDuration = new Histogram({
  name: 'apollo_api_request_duration_seconds',
  help: 'Apollo API request duration in seconds',
  labelNames: ['endpoint'] as const,
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

export const apolloRateLimitRemaining = new Gauge({
  name: 'apollo_rate_limit_remaining',
  help: 'Remaining Apollo API rate limit quota',
  registers: [registry],
});

export const apolloCreditsUsed = new Gauge({
  name: 'apollo_credits_used_total',
  help: 'Apollo enrichment credits consumed',
  registers: [registry],
});
```

### Step 2: Add Metrics Collection via Axios Interceptors
```typescript
// src/observability/instrument-client.ts
import { AxiosInstance } from 'axios';
import {
  apolloRequestsTotal,
  apolloRequestDuration,
  apolloRateLimitRemaining,
} from './metrics';

export function instrumentClient(client: AxiosInstance) {
  client.interceptors.request.use((config) => {
    (config as any)._startTime = Date.now();
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      const endpoint = response.config.url ?? 'unknown';
      const duration = (Date.now() - (response.config as any)._startTime) / 1000;

      apolloRequestsTotal.inc({
        method: response.config.method?.toUpperCase() ?? 'GET',
        endpoint,
        status: String(response.status),
      });
      apolloRequestDuration.observe({ endpoint }, duration);

      const remaining = response.headers['x-rate-limit-remaining'];
      if (remaining) apolloRateLimitRemaining.set(parseInt(remaining, 10));

      return response;
    },
    (err) => {
      const endpoint = err.config?.url ?? 'unknown';
      apolloRequestsTotal.inc({
        method: err.config?.method?.toUpperCase() ?? 'GET',
        endpoint,
        status: String(err.response?.status ?? 0),
      });
      return Promise.reject(err);
    },
  );
}
```

### Step 3: Set Up Structured Logging
```typescript
// src/observability/logger.ts
import pino from 'pino';
import { redactPII } from '../apollo/redact';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: {
    paths: ['req.params.api_key', 'res.data.*.email', 'res.data.*.phone_numbers'],
    censor: '[REDACTED]',
  },
  formatters: {
    level(label) { return { level: label }; },
  },
  transport: process.env.NODE_ENV !== 'production'
    ? { target: 'pino-pretty' }
    : undefined,
});

// Apollo-specific child logger
export const apolloLogger = logger.child({ service: 'apollo-integration' });

// Usage:
// apolloLogger.info({ endpoint: '/people/search', results: 25 }, 'Search completed');
// apolloLogger.warn({ endpoint: '/people/match', status: 429 }, 'Rate limited');
// apolloLogger.error({ err, endpoint: '/contacts' }, 'Request failed');
```

### Step 4: Add OpenTelemetry Tracing
```typescript
// src/observability/tracing.ts
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { AxiosInstance } from 'axios';

const tracer = trace.getTracer('apollo-integration');

export function addTracing(client: AxiosInstance) {
  client.interceptors.request.use((config) => {
    const span = tracer.startSpan(`apollo.${config.method?.toUpperCase()} ${config.url}`);
    span.setAttribute('apollo.endpoint', config.url ?? '');
    span.setAttribute('apollo.method', config.method?.toUpperCase() ?? '');
    (config as any)._span = span;
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      const span = (response.config as any)._span;
      if (span) {
        span.setAttribute('http.status_code', response.status);
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
      }
      return response;
    },
    (err) => {
      const span = (err.config as any)?._span;
      if (span) {
        span.setAttribute('http.status_code', err.response?.status ?? 0);
        span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
        span.end();
      }
      return Promise.reject(err);
    },
  );
}
```

### Step 5: Define Alerting Rules
```yaml
# prometheus/apollo-alerts.yml
groups:
  - name: apollo-integration
    rules:
      - alert: ApolloHighErrorRate
        expr: rate(apollo_api_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Apollo API error rate > 10% for 5 minutes"

      - alert: ApolloRateLimitLow
        expr: apollo_rate_limit_remaining < 50
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Apollo rate limit below 50 remaining requests"

      - alert: ApolloHighLatency
        expr: histogram_quantile(0.95, rate(apollo_api_request_duration_seconds_bucket[5m])) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Apollo API p95 latency > 5s for 10 minutes"

      - alert: ApolloDown
        expr: up{job="apollo-integration"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Apollo integration service is down"
```

### Step 6: Expose Metrics Endpoint
```typescript
// src/observability/metrics-server.ts
import express from 'express';
import { registry } from './metrics';

const metricsApp = express();

metricsApp.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});

metricsApp.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'apollo-integration' });
});

metricsApp.listen(9090, () => {
  console.log('Metrics server on port 9090');
});
```

## Output
- Prometheus metrics: request count, duration histogram, rate limit gauge, credits gauge
- Axios interceptors for automatic metrics collection
- Pino structured logger with PII redaction and `apollo-integration` service tag
- OpenTelemetry tracing spans for all Apollo API calls
- Prometheus alerting rules for errors, rate limits, latency, and downtime
- `/metrics` and `/health` HTTP endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing metrics | Verify `instrumentClient()` is called on your Apollo client instance |
| Alert noise | Tune `for` duration and thresholds in alert rules |
| Log volume | Adjust `LOG_LEVEL` env var; use `warn` in production |
| Trace gaps | Ensure OpenTelemetry SDK is initialized before client creation |

## Examples

### Quick Health Check
```bash
# Check metrics endpoint
curl -s http://localhost:9090/metrics | grep apollo_api_requests_total

# Check health
curl -s http://localhost:9090/health
# {"status":"ok","service":"apollo-integration"}
```

## Resources
- [Prometheus Client for Node.js](https://github.com/siimon/prom-client)
- [OpenTelemetry JavaScript](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://getpino.io/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

## Next Steps
Proceed to `apollo-incident-runbook` for incident response.
