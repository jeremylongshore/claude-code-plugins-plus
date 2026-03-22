---
name: customerio-observability
description: |
  Set up Customer.io monitoring and observability.
  Use when implementing metrics, structured logging, alerting,
  or Grafana dashboards for Customer.io integrations.
  Trigger: "customer.io monitoring", "customer.io metrics",
  "customer.io dashboard", "customer.io alerts", "customer.io observability".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, monitoring, observability, prometheus]

---
# Customer.io Observability

## Overview

Implement comprehensive observability for Customer.io integrations: Prometheus metrics (latency, error rates, delivery funnel), structured JSON logging with PII redaction, OpenTelemetry tracing, and Grafana dashboard definitions.

## Prerequisites

- Customer.io integration deployed
- Prometheus + Grafana (or compatible metrics stack)
- Structured logging system (pino recommended)

## Key Metrics to Track

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|----------------|
| `cio_api_duration_ms` | Histogram | API call latency | p99 > 5000ms |
| `cio_api_requests_total` | Counter | Total API requests by operation | N/A (rate) |
| `cio_api_errors_total` | Counter | API errors by status code | > 1% error rate |
| `cio_email_sent_total` | Counter | Transactional + campaign emails | N/A |
| `cio_email_bounced_total` | Counter | Bounce count | > 5% of sends |
| `cio_email_complained_total` | Counter | Spam complaints | > 0.1% of sends |
| `cio_webhook_received_total` | Counter | Webhook events by metric type | N/A |
| `cio_queue_depth` | Gauge | Pending items in event queue | > 10K |

## Instructions

### Step 1: Prometheus Metrics

```typescript
// lib/customerio-metrics.ts
import { Counter, Histogram, Gauge, Registry } from "prom-client";

const registry = new Registry();

export const cioMetrics = {
  apiDuration: new Histogram({
    name: "cio_api_duration_ms",
    help: "Customer.io API call duration in milliseconds",
    labelNames: ["operation", "status"] as const,
    buckets: [10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    registers: [registry],
  }),

  apiRequests: new Counter({
    name: "cio_api_requests_total",
    help: "Total Customer.io API requests",
    labelNames: ["operation"] as const,
    registers: [registry],
  }),

  apiErrors: new Counter({
    name: "cio_api_errors_total",
    help: "Customer.io API errors",
    labelNames: ["operation", "status_code"] as const,
    registers: [registry],
  }),

  emailSent: new Counter({
    name: "cio_email_sent_total",
    help: "Emails sent via Customer.io",
    labelNames: ["type"] as const,  // "transactional" or "campaign"
    registers: [registry],
  }),

  emailBounced: new Counter({
    name: "cio_email_bounced_total",
    help: "Email bounces from Customer.io webhooks",
    registers: [registry],
  }),

  emailComplained: new Counter({
    name: "cio_email_complained_total",
    help: "Spam complaints from Customer.io webhooks",
    registers: [registry],
  }),

  webhookReceived: new Counter({
    name: "cio_webhook_received_total",
    help: "Webhook events received",
    labelNames: ["metric"] as const,
    registers: [registry],
  }),

  queueDepth: new Gauge({
    name: "cio_queue_depth",
    help: "Pending items in Customer.io event queue",
    labelNames: ["queue"] as const,
    registers: [registry],
  }),
};

export { registry };
```

### Step 2: Instrumented Client

```typescript
// lib/customerio-instrumented.ts
import { TrackClient, APIClient, SendEmailRequest, RegionUS } from "customerio-node";
import { cioMetrics } from "./customerio-metrics";

export class InstrumentedCioClient {
  private track: TrackClient;
  private app: APIClient;

  constructor(siteId: string, trackKey: string, appKey: string) {
    this.track = new TrackClient(siteId, trackKey, { region: RegionUS });
    this.app = new APIClient(appKey, { region: RegionUS });
  }

  async identify(userId: string, attrs: Record<string, any>): Promise<void> {
    const timer = cioMetrics.apiDuration.startTimer({ operation: "identify" });
    cioMetrics.apiRequests.inc({ operation: "identify" });

    try {
      await this.track.identify(userId, attrs);
      timer({ status: "success" });
    } catch (err: any) {
      const code = String(err.statusCode ?? "unknown");
      timer({ status: "error" });
      cioMetrics.apiErrors.inc({ operation: "identify", status_code: code });
      throw err;
    }
  }

  async trackEvent(
    userId: string,
    name: string,
    data?: Record<string, any>
  ): Promise<void> {
    const timer = cioMetrics.apiDuration.startTimer({ operation: "track" });
    cioMetrics.apiRequests.inc({ operation: "track" });

    try {
      await this.track.track(userId, { name, data });
      timer({ status: "success" });
    } catch (err: any) {
      timer({ status: "error" });
      cioMetrics.apiErrors.inc({
        operation: "track",
        status_code: String(err.statusCode ?? "unknown"),
      });
      throw err;
    }
  }

  async sendEmail(request: SendEmailRequest): Promise<any> {
    const timer = cioMetrics.apiDuration.startTimer({ operation: "send_email" });
    cioMetrics.apiRequests.inc({ operation: "send_email" });

    try {
      const result = await this.app.sendEmail(request);
      timer({ status: "success" });
      cioMetrics.emailSent.inc({ type: "transactional" });
      return result;
    } catch (err: any) {
      timer({ status: "error" });
      cioMetrics.apiErrors.inc({
        operation: "send_email",
        status_code: String(err.statusCode ?? "unknown"),
      });
      throw err;
    }
  }
}
```

### Step 3: Structured Logging with PII Redaction

```typescript
// lib/customerio-logger.ts
import pino from "pino";

const logger = pino({
  name: "customerio",
  level: process.env.CUSTOMERIO_LOG_LEVEL ?? "info",
  redact: {
    paths: [
      "*.email",
      "*.phone",
      "*.ip_address",
      "*.password",
      "attrs.email",
      "attrs.phone",
    ],
    censor: "[REDACTED]",
  },
});

export function logCioOperation(
  operation: string,
  data: {
    userId?: string;
    event?: string;
    latencyMs?: number;
    statusCode?: number;
    error?: string;
    attrs?: Record<string, any>;
  }
): void {
  if (data.error) {
    logger.error({ operation, ...data }, `CIO ${operation} failed`);
  } else {
    logger.info({ operation, ...data }, `CIO ${operation} completed`);
  }
}

// Usage:
// logCioOperation("identify", {
//   userId: "user-123",
//   latencyMs: 85,
//   attrs: { email: "user@example.com", plan: "pro" }
// });
// Output: {"level":"info","operation":"identify","userId":"user-123",
//          "latencyMs":85,"attrs":{"email":"[REDACTED]","plan":"pro"},
//          "msg":"CIO identify completed"}
```

### Step 4: Webhook Metrics Collection

```typescript
// Integrate with webhook handler (see customerio-webhooks-events skill)
function recordWebhookMetrics(event: { metric: string }): void {
  cioMetrics.webhookReceived.inc({ metric: event.metric });

  switch (event.metric) {
    case "bounced":
      cioMetrics.emailBounced.inc();
      break;
    case "spammed":
      cioMetrics.emailComplained.inc();
      break;
    case "sent":
      cioMetrics.emailSent.inc({ type: "campaign" });
      break;
  }
}
```

### Step 5: Prometheus Metrics Endpoint

```typescript
// routes/metrics.ts
import { Router } from "express";
import { registry } from "../lib/customerio-metrics";

const router = Router();

router.get("/metrics", async (_req, res) => {
  res.set("Content-Type", registry.contentType);
  res.end(await registry.metrics());
});

export default router;
```

### Step 6: Grafana Dashboard (JSON Model)

```json
{
  "title": "Customer.io Integration",
  "panels": [
    {
      "title": "API Latency (p50/p95/p99)",
      "type": "timeseries",
      "targets": [
        { "expr": "histogram_quantile(0.50, rate(cio_api_duration_ms_bucket[5m]))" },
        { "expr": "histogram_quantile(0.95, rate(cio_api_duration_ms_bucket[5m]))" },
        { "expr": "histogram_quantile(0.99, rate(cio_api_duration_ms_bucket[5m]))" }
      ]
    },
    {
      "title": "Request Rate by Operation",
      "type": "timeseries",
      "targets": [
        { "expr": "rate(cio_api_requests_total[5m])" }
      ]
    },
    {
      "title": "Error Rate %",
      "type": "stat",
      "targets": [
        { "expr": "rate(cio_api_errors_total[5m]) / rate(cio_api_requests_total[5m]) * 100" }
      ]
    },
    {
      "title": "Email Delivery Funnel",
      "type": "bargauge",
      "targets": [
        { "expr": "cio_email_sent_total" },
        { "expr": "cio_email_bounced_total" },
        { "expr": "cio_email_complained_total" }
      ]
    }
  ]
}
```

### Step 7: Alerting Rules

```yaml
# prometheus/customerio-alerts.yml
groups:
  - name: customerio
    rules:
      - alert: CioHighErrorRate
        expr: rate(cio_api_errors_total[5m]) / rate(cio_api_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Customer.io API error rate > 5%"

      - alert: CioHighLatency
        expr: histogram_quantile(0.99, rate(cio_api_duration_ms_bucket[5m])) > 5000
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Customer.io p99 latency > 5 seconds"

      - alert: CioHighBounceRate
        expr: rate(cio_email_bounced_total[1h]) / rate(cio_email_sent_total[1h]) > 0.05
        for: 15m
        labels: { severity: warning }
        annotations:
          summary: "Email bounce rate > 5%"

      - alert: CioSpamComplaints
        expr: rate(cio_email_complained_total[1h]) / rate(cio_email_sent_total[1h]) > 0.001
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Spam complaint rate > 0.1% — sender reputation at risk"
```

## Error Handling

| Issue | Solution |
|-------|----------|
| High cardinality metrics | Don't use userId as a label — use operation + status only |
| Log volume too high | Set `CUSTOMERIO_LOG_LEVEL=warn` in production |
| Missing metrics | Check metric registration and scrape config |
| PII in logs | Verify pino redact paths cover all sensitive fields |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Provisioning](https://grafana.com/docs/grafana/latest/dashboards/)
- [pino Logger](https://getpino.io/)

## Next Steps

After observability setup, proceed to `customerio-advanced-troubleshooting` for debugging.
