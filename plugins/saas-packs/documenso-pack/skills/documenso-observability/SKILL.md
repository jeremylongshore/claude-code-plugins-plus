---
name: documenso-observability
description: |
  Implement monitoring, logging, and tracing for Documenso integrations.
  Use when setting up observability, implementing metrics collection,
  or debugging production issues.
  Trigger with phrases like "documenso monitoring", "documenso metrics",
  "documenso logging", "documenso tracing", "documenso observability".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, monitoring, observability, debugging]

---
# Documenso Observability

## Overview

Implement monitoring, structured logging, and health checks for Documenso integrations. Since Documenso does not expose rate limit headers or usage metrics via API, observability is built around your API call patterns, latency, error rates, and webhook delivery.

## Prerequisites

- Working Documenso integration
- Monitoring stack (Prometheus/Grafana, Datadog, or CloudWatch)
- Logging infrastructure

## Instructions

### Step 1: Instrumented Client Wrapper

```typescript
// src/observability/documenso-metrics.ts
import { Documenso } from "@documenso/sdk-typescript";

interface Metrics {
  requestCount: number;
  errorCount: number;
  totalLatencyMs: number;
  errorsByStatus: Record<number, number>;
}

const metrics: Metrics = {
  requestCount: 0,
  errorCount: 0,
  totalLatencyMs: 0,
  errorsByStatus: {},
};

export function createInstrumentedClient(): Documenso {
  const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });

  return new Proxy(client, {
    get(target, prop) {
      const value = (target as any)[prop];
      if (typeof value === "object" && value !== null) {
        return new Proxy(value, {
          get(innerTarget, method) {
            const fn = (innerTarget as any)[method];
            if (typeof fn !== "function") return fn;

            return async (...args: any[]) => {
              const start = Date.now();
              metrics.requestCount++;

              try {
                const result = await fn.apply(innerTarget, args);
                metrics.totalLatencyMs += Date.now() - start;
                return result;
              } catch (err: any) {
                metrics.errorCount++;
                const status = err.statusCode ?? 0;
                metrics.errorsByStatus[status] = (metrics.errorsByStatus[status] || 0) + 1;
                metrics.totalLatencyMs += Date.now() - start;
                throw err;
              }
            };
          },
        });
      }
      return value;
    },
  });
}

// Expose metrics for Prometheus scraping
export function getMetrics() {
  return {
    ...metrics,
    avgLatencyMs: metrics.requestCount > 0
      ? Math.round(metrics.totalLatencyMs / metrics.requestCount)
      : 0,
    errorRate: metrics.requestCount > 0
      ? (metrics.errorCount / metrics.requestCount * 100).toFixed(2) + "%"
      : "0%",
  };
}
```

### Step 2: Structured Logging

```typescript
// src/observability/logger.ts
import { createLogger, format, transports } from "winston";

const logger = createLogger({
  level: process.env.LOG_LEVEL ?? "info",
  format: format.combine(
    format.timestamp(),
    format.json()
  ),
  defaultMeta: { service: "documenso-integration" },
  transports: [
    new transports.Console(),
    // Add file or cloud transport for production
  ],
});

// Log Documenso operations with structured context
export function logDocumensoOperation(
  operation: string,
  documentId?: number,
  extra?: Record<string, any>
) {
  logger.info("documenso_operation", {
    operation,
    documentId,
    ...extra,
  });
}

// Log errors with full context
export function logDocumensoError(
  operation: string,
  error: any,
  documentId?: number
) {
  logger.error("documenso_error", {
    operation,
    documentId,
    statusCode: error.statusCode,
    message: error.message,
    // Never log API keys
  });
}
```

### Step 3: Health Check Endpoint

```typescript
// src/api/health.ts
import { Documenso } from "@documenso/sdk-typescript";

interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  message: string;
}

async function checkDocumensoHealth(): Promise<HealthStatus> {
  const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
  const start = Date.now();

  try {
    await client.documents.findV0({ page: 1, perPage: 1 });
    const latencyMs = Date.now() - start;

    if (latencyMs > 5000) {
      return { status: "degraded", latencyMs, message: "High latency" };
    }
    return { status: "healthy", latencyMs, message: "OK" };
  } catch (err: any) {
    return {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      message: `${err.statusCode ?? "unknown"}: ${err.message}`,
    };
  }
}

// Express endpoint
app.get("/health/documenso", async (req, res) => {
  const health = await checkDocumensoHealth();
  const httpStatus = health.status === "healthy" ? 200 : health.status === "degraded" ? 200 : 503;
  res.status(httpStatus).json(health);
});
```

### Step 4: Prometheus Metrics Endpoint

```typescript
// src/api/metrics.ts
import { getMetrics } from "../observability/documenso-metrics";

app.get("/metrics/documenso", (req, res) => {
  const m = getMetrics();
  res.type("text/plain").send(`
# HELP documenso_requests_total Total API requests
# TYPE documenso_requests_total counter
documenso_requests_total ${m.requestCount}

# HELP documenso_errors_total Total API errors
# TYPE documenso_errors_total counter
documenso_errors_total ${m.errorCount}

# HELP documenso_avg_latency_ms Average request latency
# TYPE documenso_avg_latency_ms gauge
documenso_avg_latency_ms ${m.avgLatencyMs}
  `.trim());
});
```

### Step 5: Webhook Delivery Monitoring

```typescript
// Track webhook delivery success/failure
const webhookMetrics = {
  received: 0,
  processed: 0,
  failed: 0,
  byEvent: {} as Record<string, number>,
};

app.post("/webhooks/documenso", async (req, res) => {
  webhookMetrics.received++;
  const { event } = req.body;
  webhookMetrics.byEvent[event] = (webhookMetrics.byEvent[event] || 0) + 1;

  res.status(200).json({ received: true });

  try {
    await processWebhookEvent(req.body);
    webhookMetrics.processed++;
  } catch (err) {
    webhookMetrics.failed++;
    logDocumensoError("webhook_processing", err);
  }
});

// Expose webhook metrics
app.get("/metrics/webhooks", (req, res) => {
  res.json(webhookMetrics);
});
```

### Step 6: Alerting Rules

```yaml
# alerting-rules.yml (Prometheus)
groups:
  - name: documenso
    rules:
      - alert: DocumensoHighErrorRate
        expr: rate(documenso_errors_total[5m]) / rate(documenso_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Documenso error rate above 5%"

      - alert: DocumensoUnhealthy
        expr: up{job="documenso-health"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Documenso health check failing"

      - alert: DocumensoHighLatency
        expr: documenso_avg_latency_ms > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Documenso average latency above 5s"
```

## Key Metrics to Monitor

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| API error rate | < 1% | 1-5% | > 5% |
| Average latency | < 1s | 1-5s | > 5s |
| Health check | Passing | Degraded | Failing |
| Webhook delivery | > 99% | 95-99% | < 95% |

## Error Handling

| Observability Issue | Cause | Solution |
|--------------------|-------|----------|
| Metrics not appearing | Scrape config wrong | Verify Prometheus targets |
| Logs missing | Log level too high | Set `LOG_LEVEL=debug` temporarily |
| False alerts | Thresholds too sensitive | Adjust to match your traffic patterns |
| Health check flapping | Transient network issues | Add `for: 2m` to alert rules |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Winston Logger](https://github.com/winstonjs/winston)

## Next Steps

For incident response, see `documenso-incident-runbook`.
