---
name: webflow-observability
description: |
  Set up observability for Webflow integrations — Prometheus metrics for API calls,
  OpenTelemetry tracing, structured logging with pino, Grafana dashboards,
  and alerting for rate limits, errors, and latency.
  Trigger with phrases like "webflow monitoring", "webflow metrics",
  "webflow observability", "monitor webflow", "webflow alerts", "webflow tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Observability

## Overview

Full observability stack for Webflow Data API v2 integrations: Prometheus metrics
for API call counting and latency, OpenTelemetry distributed tracing, structured
JSON logging, and alerting rules for error rate and rate limit exhaustion.

## Prerequisites

- `prom-client` for Prometheus metrics
- `@opentelemetry/api` for tracing (optional)
- `pino` for structured logging
- Prometheus + Grafana (or compatible backend)

## Instructions

### Step 1: Prometheus Metrics

```typescript
// src/observability/metrics.ts
import { Registry, Counter, Histogram, Gauge } from "prom-client";

export const registry = new Registry();

// API request counter (by operation and status)
export const apiRequests = new Counter({
  name: "webflow_api_requests_total",
  help: "Total Webflow API requests",
  labelNames: ["operation", "status_code", "method"] as const,
  registers: [registry],
});

// Request duration histogram
export const apiDuration = new Histogram({
  name: "webflow_api_request_duration_seconds",
  help: "Webflow API request duration in seconds",
  labelNames: ["operation"] as const,
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

// Error counter by type
export const apiErrors = new Counter({
  name: "webflow_api_errors_total",
  help: "Webflow API errors by status code",
  labelNames: ["operation", "status_code", "error_type"] as const,
  registers: [registry],
});

// Rate limit remaining gauge
export const rateLimitRemaining = new Gauge({
  name: "webflow_rate_limit_remaining",
  help: "Remaining API calls before rate limit",
  registers: [registry],
});

// CMS items gauge (track total items across collections)
export const cmsItemCount = new Gauge({
  name: "webflow_cms_items_total",
  help: "Total CMS items by collection",
  labelNames: ["collection", "site"] as const,
  registers: [registry],
});

// Webhook event counter
export const webhookEvents = new Counter({
  name: "webflow_webhook_events_total",
  help: "Received webhook events by trigger type",
  labelNames: ["trigger_type", "status"] as const,
  registers: [registry],
});
```

### Step 2: Instrumented Client Wrapper

```typescript
// src/observability/instrumented-client.ts
import { WebflowClient } from "webflow-api";
import { apiRequests, apiDuration, apiErrors, rateLimitRemaining } from "./metrics.js";

export async function instrumentedCall<T>(
  operation: string,
  method: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ operation });

  try {
    const result = await fn();

    apiRequests.inc({ operation, status_code: "200", method });
    timer();
    return result;
  } catch (error: any) {
    const statusCode = String(error.statusCode || error.status || "unknown");

    apiRequests.inc({ operation, status_code: statusCode, method });
    apiErrors.inc({
      operation,
      status_code: statusCode,
      error_type: statusCode === "429" ? "rate_limit" : statusCode >= "500" ? "server" : "client",
    });

    timer();
    throw error;
  }
}

// Usage
const { sites } = await instrumentedCall("sites.list", "GET", () =>
  webflow.sites.list()
);

const { items } = await instrumentedCall("items.listLive", "GET", () =>
  webflow.collections.items.listItemsLive(collectionId)
);

const item = await instrumentedCall("items.create", "POST", () =>
  webflow.collections.items.createItem(collectionId, {
    fieldData: { name: "Test", slug: "test" },
  })
);
```

### Step 3: Metrics Endpoint

```typescript
// api/metrics.ts
import express from "express";
import { registry } from "../observability/metrics.js";

const app = express();

app.get("/metrics", async (req, res) => {
  res.set("Content-Type", registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 4: OpenTelemetry Distributed Tracing

```typescript
// src/observability/tracing.ts
import { trace, SpanStatusCode, context } from "@opentelemetry/api";

const tracer = trace.getTracer("webflow-integration", "1.0.0");

export async function tracedCall<T>(
  operationName: string,
  attributes: Record<string, string>,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`webflow.${operationName}`, async (span) => {
    span.setAttributes({
      "webflow.operation": operationName,
      ...attributes,
    });

    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.recordException(error);
      span.setAttributes({
        "webflow.error.status_code": String(error.statusCode || "unknown"),
      });
      throw error;
    } finally {
      span.end();
    }
  });
}

// Usage
const { collections } = await tracedCall(
  "collections.list",
  { "webflow.site_id": siteId },
  () => webflow.collections.list(siteId)
);
```

### Step 5: Structured Logging

```typescript
// src/observability/logger.ts
import pino from "pino";

export const logger = pino({
  name: "webflow-integration",
  level: process.env.LOG_LEVEL || "info",
  serializers: {
    err: pino.stdSerializers.err,
  },
  // Redact sensitive fields
  redact: {
    paths: ["accessToken", "apiToken", "*.authorization", "req.headers.authorization"],
    censor: "[REDACTED]",
  },
});

// Log API calls with consistent structure
export function logApiCall(
  operation: string,
  durationMs: number,
  status: "success" | "error",
  metadata?: Record<string, any>
) {
  const logFn = status === "error" ? logger.error.bind(logger) : logger.info.bind(logger);

  logFn({
    service: "webflow",
    operation,
    durationMs,
    status,
    ...metadata,
  }, `webflow.${operation} ${status} (${durationMs}ms)`);
}

// Log webhook events
export function logWebhook(triggerType: string, status: "processed" | "failed" | "skipped") {
  logger.info({
    service: "webflow",
    event: "webhook",
    triggerType,
    status,
  }, `webhook.${triggerType} ${status}`);
}
```

### Step 6: AlertManager Rules

```yaml
# prometheus/webflow-alerts.yml
groups:
  - name: webflow
    rules:
      - alert: WebflowHighErrorRate
        expr: |
          (
            rate(webflow_api_errors_total[5m]) /
            rate(webflow_api_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webflow API error rate > 5%"
          description: "{{ $value | humanizePercentage }} errors in last 5m"

      - alert: WebflowRateLimited
        expr: |
          rate(webflow_api_errors_total{status_code="429"}[5m]) > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Webflow API rate limited"

      - alert: WebflowHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(webflow_api_request_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webflow P95 latency > 3s"

      - alert: WebflowDown
        expr: |
          sum(rate(webflow_api_requests_total{status_code=~"5.."}[5m])) /
          sum(rate(webflow_api_requests_total[5m])) > 0.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Webflow API > 50% server errors"

      - alert: WebflowRateLimitLow
        expr: webflow_rate_limit_remaining < 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Webflow rate limit nearly exhausted"
```

### Step 7: Grafana Dashboard Queries

```json
{
  "panels": [
    {
      "title": "Request Rate by Operation",
      "targets": [{ "expr": "sum by (operation) (rate(webflow_api_requests_total[5m]))" }]
    },
    {
      "title": "Error Rate",
      "targets": [{ "expr": "sum(rate(webflow_api_errors_total[5m])) / sum(rate(webflow_api_requests_total[5m]))" }]
    },
    {
      "title": "Latency P50 / P95 / P99",
      "targets": [
        { "expr": "histogram_quantile(0.5, rate(webflow_api_request_duration_seconds_bucket[5m]))", "legendFormat": "p50" },
        { "expr": "histogram_quantile(0.95, rate(webflow_api_request_duration_seconds_bucket[5m]))", "legendFormat": "p95" },
        { "expr": "histogram_quantile(0.99, rate(webflow_api_request_duration_seconds_bucket[5m]))", "legendFormat": "p99" }
      ]
    },
    {
      "title": "Rate Limit Remaining",
      "targets": [{ "expr": "webflow_rate_limit_remaining" }]
    },
    {
      "title": "Webhook Events by Type",
      "targets": [{ "expr": "sum by (trigger_type) (rate(webflow_webhook_events_total[5m]))" }]
    }
  ]
}
```

## Output

- Prometheus metrics: request count, latency histogram, error rate, rate limit gauge
- OpenTelemetry tracing for end-to-end request visibility
- Structured JSON logging with PII redaction
- AlertManager rules for error rate, latency, and rate limits
- Grafana dashboard panels

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | Calls not instrumented | Wrap with `instrumentedCall()` |
| High cardinality | Too many label values | Limit `operation` to known set |
| Trace gaps | Missing context propagation | Pass OTel context in async calls |
| Alert storms | Thresholds too sensitive | Increase `for` duration |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)
- [pino Documentation](https://github.com/pinojs/pino)

## Next Steps

For incident response, see `webflow-incident-runbook`.
