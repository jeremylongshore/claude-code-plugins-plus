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
tags: [saas, apollo, monitoring, observability, logging]

---
# Apollo Observability

## Overview
Comprehensive observability for Apollo.io integrations: Prometheus metrics (request count, latency, rate limits, credits), structured logging with PII redaction, OpenTelemetry tracing, and alerting rules. Tracks the metrics that matter: credit burn rate, enrichment success rate, and API health.

## Prerequisites
- Valid Apollo API key
- Node.js 18+

## Instructions

### Step 1: Prometheus Metrics
```typescript
// src/observability/metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

export const registry = new Registry();

export const requestsTotal = new Counter({
  name: 'apollo_requests_total',
  help: 'Total Apollo API requests by endpoint and status',
  labelNames: ['endpoint', 'method', 'status'] as const,
  registers: [registry],
});

export const requestDuration = new Histogram({
  name: 'apollo_request_duration_seconds',
  help: 'Apollo API request duration',
  labelNames: ['endpoint'] as const,
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

export const rateLimitRemaining = new Gauge({
  name: 'apollo_rate_limit_remaining',
  help: 'Remaining requests in current rate limit window',
  labelNames: ['endpoint'] as const,
  registers: [registry],
});

export const creditsUsed = new Counter({
  name: 'apollo_credits_used_total',
  help: 'Total Apollo enrichment credits consumed',
  labelNames: ['type'] as const,  // 'person', 'organization', 'bulk'
  registers: [registry],
});

export const enrichmentSuccessRate = new Gauge({
  name: 'apollo_enrichment_success_rate',
  help: 'Percentage of enrichment calls that found a match',
  registers: [registry],
});
```

### Step 2: Axios Interceptors for Auto-Collection
```typescript
// src/observability/instrument.ts
import { AxiosInstance } from 'axios';
import { requestsTotal, requestDuration, rateLimitRemaining, creditsUsed } from './metrics';

const CREDIT_ENDPOINTS = ['/people/match', '/people/bulk_match', '/organizations/enrich'];

export function instrumentClient(client: AxiosInstance) {
  client.interceptors.request.use((config) => {
    (config as any)._startTime = Date.now();
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      const endpoint = response.config.url ?? 'unknown';
      const duration = (Date.now() - (response.config as any)._startTime) / 1000;

      requestsTotal.inc({ endpoint, method: response.config.method?.toUpperCase() ?? 'GET', status: String(response.status) });
      requestDuration.observe({ endpoint }, duration);

      // Rate limit tracking
      const remaining = response.headers['x-rate-limit-remaining'];
      if (remaining) rateLimitRemaining.set({ endpoint }, parseInt(remaining, 10));

      // Credit tracking
      if (CREDIT_ENDPOINTS.some((ep) => endpoint.includes(ep))) {
        const type = endpoint.includes('bulk') ? 'bulk' : endpoint.includes('organization') ? 'organization' : 'person';
        const count = response.data?.matches?.length ?? 1;
        creditsUsed.inc({ type }, count);
      }

      return response;
    },
    (err) => {
      requestsTotal.inc({
        endpoint: err.config?.url ?? 'unknown',
        method: err.config?.method?.toUpperCase() ?? 'GET',
        status: String(err.response?.status ?? 0),
      });
      return Promise.reject(err);
    },
  );
}
```

### Step 3: Structured Logging with PII Redaction
```typescript
// src/observability/logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: {
    paths: ['*.email', '*.phone_numbers', '*.linkedin_url', 'headers.x-api-key'],
    censor: '[REDACTED]',
  },
  formatters: { level: (label) => ({ level: label }) },
  transport: process.env.NODE_ENV !== 'production' ? { target: 'pino-pretty' } : undefined,
});

export const apolloLog = logger.child({ service: 'apollo' });

// Usage:
// apolloLog.info({ endpoint: '/mixed_people/api_search', results: 25 }, 'Search completed');
// apolloLog.warn({ endpoint: '/people/match', status: 429 }, 'Rate limited');
// apolloLog.error({ err, endpoint: '/contacts' }, 'Request failed');
```

### Step 4: OpenTelemetry Tracing
```typescript
// src/observability/tracing.ts
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { AxiosInstance } from 'axios';

const tracer = trace.getTracer('apollo-integration');

export function addTracing(client: AxiosInstance) {
  client.interceptors.request.use((config) => {
    const span = tracer.startSpan(`apollo.${config.method?.toUpperCase()} ${config.url}`);
    span.setAttribute('apollo.endpoint', config.url ?? '');
    (config as any)._span = span;
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      const span = (response.config as any)._span;
      if (span) {
        span.setAttribute('http.status_code', response.status);
        span.setAttribute('apollo.rate_limit_remaining', response.headers['x-rate-limit-remaining'] ?? 'unknown');
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

### Step 5: Alerting Rules
```yaml
# prometheus/apollo-alerts.yml
groups:
  - name: apollo-integration
    rules:
      - alert: ApolloHighErrorRate
        expr: rate(apollo_requests_total{status=~"4..|5.."}[5m]) / rate(apollo_requests_total[5m]) > 0.1
        for: 5m
        labels: { severity: critical }
        annotations: { summary: "Apollo API error rate > 10% for 5 minutes" }

      - alert: ApolloRateLimitLow
        expr: apollo_rate_limit_remaining < 20
        for: 1m
        labels: { severity: warning }
        annotations: { summary: "Apollo rate limit below 20 remaining requests" }

      - alert: ApolloHighLatency
        expr: histogram_quantile(0.95, rate(apollo_request_duration_seconds_bucket[5m])) > 5
        for: 10m
        labels: { severity: warning }
        annotations: { summary: "Apollo p95 latency > 5s for 10 minutes" }

      - alert: ApolloCreditBurnRate
        expr: rate(apollo_credits_used_total[1h]) * 24 > 500
        for: 30m
        labels: { severity: warning }
        annotations: { summary: "Apollo credit burn rate projects > 500/day" }
```

### Step 6: Metrics Endpoint
```typescript
import express from 'express';
import { registry } from './metrics';

const metricsApp = express();
metricsApp.get('/metrics', async (_, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});
metricsApp.get('/health', (_, res) => res.json({ status: 'ok' }));
metricsApp.listen(9090, () => console.log('Metrics on :9090'));
```

## Output
- Prometheus metrics: requests, duration, rate limits, credits, enrichment success
- Axios interceptors for automatic collection on every API call
- Pino structured logger with PII redaction
- OpenTelemetry tracing spans for distributed tracing
- Alerting rules for errors, rate limits, latency, and credit burn rate
- `/metrics` and `/health` HTTP endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing metrics | Verify `instrumentClient()` called before first API call |
| Alert noise | Tune `for` duration and thresholds |
| Log volume | Use `LOG_LEVEL=warn` in production |
| Credit burn alert | Review enrichment scoring thresholds in `apollo-cost-tuning` |

## Resources
- [Prometheus Node.js Client](https://github.com/siimon/prom-client)
- [OpenTelemetry JavaScript](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://getpino.io/)
- [Apollo API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

## Next Steps
Proceed to `apollo-incident-runbook` for incident response.
