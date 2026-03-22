---
name: linear-observability
description: |
  Implement monitoring, logging, and alerting for Linear integrations.
  Use when setting up metrics collection, dashboards,
  or configuring alerts for Linear API usage.
  Trigger: "linear monitoring", "linear observability",
  "linear metrics", "linear logging", "monitor linear",
  "linear Prometheus", "linear Grafana".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, monitoring, observability]

---
# Linear Observability

## Overview
Production monitoring for Linear integrations using Prometheus metrics, structured logging with pino, health checks, and alerting rules. Track API latency, error rates, rate limit headroom, and webhook throughput.

## Prerequisites
- Linear integration deployed
- Prometheus or Datadog for metrics
- Structured logging (pino, winston)
- Alerting system (PagerDuty, OpsGenie, Slack)

## Instructions

### Step 1: Define Metrics
```typescript
// src/metrics/linear-metrics.ts
import { Counter, Histogram, Gauge, register } from "prom-client";

export const metrics = {
  // API request tracking
  apiRequests: new Counter({
    name: "linear_api_requests_total",
    help: "Total Linear API requests",
    labelNames: ["operation", "status"],
  }),

  // Request duration
  apiLatency: new Histogram({
    name: "linear_api_request_duration_seconds",
    help: "Linear API request duration",
    labelNames: ["operation"],
    buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  }),

  // Rate limit headroom
  rateLimitRemaining: new Gauge({
    name: "linear_rate_limit_remaining",
    help: "Remaining rate limit budget",
    labelNames: ["type"], // "requests" or "complexity"
  }),

  // Webhook tracking
  webhooksReceived: new Counter({
    name: "linear_webhooks_received_total",
    help: "Total webhooks received",
    labelNames: ["type", "action"],
  }),

  webhookProcessingDuration: new Histogram({
    name: "linear_webhook_processing_seconds",
    help: "Webhook processing duration",
    labelNames: ["type"],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  }),

  // Cache effectiveness
  cacheHits: new Counter({
    name: "linear_cache_hits_total",
    help: "Cache hit count",
    labelNames: ["key"],
  }),
  cacheMisses: new Counter({
    name: "linear_cache_misses_total",
    help: "Cache miss count",
    labelNames: ["key"],
  }),
};

// Expose metrics endpoint
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});
```

### Step 2: Instrumented Client Wrapper
```typescript
import { LinearClient } from "@linear/sdk";

function instrumentedCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = metrics.apiLatency.startTimer({ operation });

  return fn()
    .then((result) => {
      metrics.apiRequests.inc({ operation, status: "success" });
      timer();
      return result;
    })
    .catch((error: any) => {
      const status = error.status === 429 ? "rate_limited" : "error";
      metrics.apiRequests.inc({ operation, status });
      timer();
      throw error;
    });
}

// Usage
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

const teams = await instrumentedCall("teams", () => client.teams());
const issues = await instrumentedCall("issues", () =>
  client.issues({ first: 50 })
);
```

### Step 3: Structured Logging
```typescript
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
});

const linearLog = logger.child({ component: "linear" });

// Log API calls
function logApiCall(operation: string, durationMs: number, success: boolean, meta?: any) {
  linearLog.info({
    event: "api_call",
    operation,
    durationMs,
    success,
    ...meta,
  });
}

// Log webhook events
function logWebhook(type: string, action: string, deliveryId: string, meta?: any) {
  linearLog.info({
    event: "webhook",
    type,
    action,
    deliveryId,
    ...meta,
  });
}

// Log errors with context
function logError(operation: string, error: any) {
  linearLog.error({
    event: "error",
    operation,
    errorMessage: error.message,
    errorStatus: error.status,
    errorType: error.type,
    // Never log API keys or tokens
  });
}
```

### Step 4: Health Check Endpoint
```typescript
interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  checks: Record<string, {
    status: string;
    latencyMs?: number;
    error?: string;
  }>;
  timestamp: string;
}

async function checkLinearHealth(client: LinearClient): Promise<HealthCheck> {
  const checks: HealthCheck["checks"] = {};

  // Check API connectivity
  const apiStart = Date.now();
  try {
    const viewer = await client.viewer;
    checks.linear_api = {
      status: "healthy",
      latencyMs: Date.now() - apiStart,
    };
  } catch (error: any) {
    checks.linear_api = {
      status: "unhealthy",
      latencyMs: Date.now() - apiStart,
      error: error.message,
    };
  }

  // Check rate limit headroom
  try {
    const resp = await fetch("https://api.linear.app/graphql", {
      method: "POST",
      headers: {
        Authorization: process.env.LINEAR_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: "{ viewer { id } }" }),
    });
    const remaining = parseInt(resp.headers.get("x-ratelimit-requests-remaining") ?? "5000");
    metrics.rateLimitRemaining.set({ type: "requests" }, remaining);

    checks.rate_limit = {
      status: remaining > 100 ? "healthy" : "degraded",
      latencyMs: remaining,
    };
  } catch {
    checks.rate_limit = { status: "unknown" };
  }

  const overall = Object.values(checks).some(c => c.status === "unhealthy")
    ? "unhealthy"
    : Object.values(checks).some(c => c.status === "degraded")
    ? "degraded"
    : "healthy";

  return { status: overall, checks, timestamp: new Date().toISOString() };
}

app.get("/health/linear", async (req, res) => {
  const health = await checkLinearHealth(client);
  res.status(health.status === "unhealthy" ? 503 : 200).json(health);
});
```

### Step 5: Alerting Rules (Prometheus)
```yaml
# prometheus/linear-alerts.yml
groups:
  - name: linear
    rules:
      - alert: LinearHighErrorRate
        expr: |
          rate(linear_api_requests_total{status="error"}[5m])
          / rate(linear_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Linear API error rate > 5%"

      - alert: LinearRateLimitLow
        expr: linear_rate_limit_remaining{type="requests"} < 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Linear rate limit remaining < 100 requests"

      - alert: LinearHighLatency
        expr: |
          histogram_quantile(0.95, rate(linear_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Linear API p95 latency > 2 seconds"

      - alert: LinearWebhookProcessingSlow
        expr: |
          histogram_quantile(0.95, rate(linear_webhook_processing_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webhook processing p95 > 5 seconds"
```

### Step 6: Webhook Instrumentation
```typescript
// Instrument webhook handler
app.post("/webhooks/linear", express.raw({ type: "*/*" }), async (req, res) => {
  const start = Date.now();
  // ... signature verification ...

  const event = JSON.parse(req.body.toString());
  const delivery = req.headers["linear-delivery"] as string;

  metrics.webhooksReceived.inc({ type: event.type, action: event.action });
  logWebhook(event.type, event.action, delivery);

  res.json({ ok: true });

  try {
    await processEvent(event);
    metrics.webhookProcessingDuration.observe(
      { type: event.type },
      (Date.now() - start) / 1000
    );
  } catch (error: any) {
    logError("webhook_processing", error);
  }
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Metrics not collecting | Missing instrumentation | Wrap all client calls with `instrumentedCall()` |
| Alerts not firing | Thresholds too high | Adjust based on actual traffic patterns |
| Health check timeout | Linear API slow | Add 10s timeout to health check |
| Log volume too high | Debug level in production | Set `LOG_LEVEL=info` in prod |

## Examples

### Quick Health Check
```bash
curl -s http://localhost:3000/health/linear | jq .
# { "status": "healthy", "checks": { "linear_api": { "status": "healthy", "latencyMs": 150 } } }
```

## Resources
- [Prometheus Client](https://github.com/siimon/prom-client)
- [Pino Logger](https://getpino.io/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Linear API Status](https://status.linear.app)
