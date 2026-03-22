---
name: fireflies-observability
description: |
  Monitor Fireflies.ai integration health with metrics, alerts, and dashboards.
  Use when implementing monitoring, setting up alerting,
  or tracking transcript processing reliability.
  Trigger with phrases like "fireflies monitoring", "fireflies metrics",
  "fireflies observability", "monitor fireflies", "fireflies alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, monitoring, observability]

---
# Fireflies.ai Observability

## Overview
Monitor Fireflies.ai integration health: API connectivity, webhook delivery, transcript processing latency, and seat utilization. Built for Prometheus/Grafana but adaptable to any metrics system.

## Prerequisites
- Fireflies Business+ plan (for full API access)
- Prometheus + Grafana (or equivalent metrics stack)
- Webhook endpoint deployed and receiving events

## Instructions

### Step 1: Instrument the GraphQL Client
```typescript
// lib/fireflies-instrumented.ts
import { Counter, Histogram, Gauge } from "prom-client";

const apiRequests = new Counter({
  name: "fireflies_api_requests_total",
  help: "Total Fireflies API requests",
  labelNames: ["operation", "status"],
});

const apiLatency = new Histogram({
  name: "fireflies_api_latency_seconds",
  help: "Fireflies API request latency",
  labelNames: ["operation"],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
});

const FIREFLIES_API = "https://api.fireflies.ai/graphql";

export async function firefliesQueryInstrumented(
  operation: string,
  query: string,
  variables?: any
) {
  const timer = apiLatency.startTimer({ operation });

  try {
    const res = await fetch(FIREFLIES_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
      },
      body: JSON.stringify({ query, variables }),
    });

    const json = await res.json();

    if (json.errors) {
      apiRequests.inc({ operation, status: json.errors[0].code || "error" });
      throw new Error(json.errors[0].message);
    }

    apiRequests.inc({ operation, status: "success" });
    return json.data;
  } catch (err) {
    apiRequests.inc({ operation, status: "failure" });
    throw err;
  } finally {
    timer();
  }
}
```

### Step 2: Webhook Event Metrics
```typescript
const webhookEvents = new Counter({
  name: "fireflies_webhook_events_total",
  help: "Webhook events received",
  labelNames: ["event_type", "status"],
});

const webhookProcessingTime = new Histogram({
  name: "fireflies_webhook_processing_seconds",
  help: "Time to process webhook events",
  buckets: [0.1, 0.5, 1, 5, 10, 30],
});

const transcriptQueue = new Gauge({
  name: "fireflies_transcript_queue_depth",
  help: "Number of transcripts queued for processing",
});

export async function handleWebhookWithMetrics(event: any) {
  const timer = webhookProcessingTime.startTimer();
  transcriptQueue.inc();

  try {
    await processTranscriptReady(event.meetingId);
    webhookEvents.inc({ event_type: event.eventType, status: "success" });
  } catch (err) {
    webhookEvents.inc({ event_type: event.eventType, status: "error" });
    throw err;
  } finally {
    timer();
    transcriptQueue.dec();
  }
}
```

### Step 3: Health Check Probe
```typescript
const healthStatus = new Gauge({
  name: "fireflies_health_status",
  help: "Fireflies API health (1=healthy, 0=unhealthy)",
});

// Run every 5 minutes
async function healthProbe() {
  try {
    const start = Date.now();
    const data = await firefliesQueryInstrumented("health_check", "{ user { email } }");
    const latencyMs = Date.now() - start;

    healthStatus.set(1);
    console.log(`Fireflies health: OK (${latencyMs}ms)`);
  } catch (err) {
    healthStatus.set(0);
    console.error(`Fireflies health: FAILED - ${(err as Error).message}`);
  }
}

setInterval(healthProbe, 5 * 60 * 1000);
```

### Step 4: Seat Utilization Tracking
```typescript
const seatUtilization = new Gauge({
  name: "fireflies_seat_utilization",
  help: "Transcripts per user",
  labelNames: ["user_email"],
});

const totalSeats = new Gauge({
  name: "fireflies_total_seats",
  help: "Total Fireflies seats",
});

// Run daily
async function trackSeatUtilization() {
  const data = await firefliesQueryInstrumented("seat_audit", `{
    users { email num_transcripts }
  }`);

  totalSeats.set(data.users.length);
  for (const user of data.users) {
    seatUtilization.set({ user_email: user.email }, user.num_transcripts);
  }

  const inactive = data.users.filter((u: any) => u.num_transcripts < 2);
  if (inactive.length > 3) {
    console.warn(`${inactive.length} seats with <2 transcripts -- review for cost savings`);
  }
}
```

### Step 5: Alerting Rules
```yaml
# prometheus/rules/fireflies.yml
groups:
  - name: fireflies
    rules:
      - alert: FirefliesAPIDown
        expr: fireflies_health_status == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Fireflies API unreachable for 10+ minutes"

      - alert: FirefliesHighErrorRate
        expr: rate(fireflies_api_requests_total{status!="success"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Fireflies API error rate >10% over 5 minutes"

      - alert: FirefliesRateLimited
        expr: rate(fireflies_api_requests_total{status="too_many_requests"}[5m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Fireflies API rate limiting detected"

      - alert: FirefliesWebhookBacklog
        expr: fireflies_transcript_queue_depth > 50
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Webhook processing backlog exceeds 50 transcripts"

      - alert: FirefliesSlowProcessing
        expr: histogram_quantile(0.95, rate(fireflies_webhook_processing_seconds_bucket[1h])) > 30
        labels:
          severity: warning
        annotations:
          summary: "Webhook processing P95 exceeds 30 seconds"
```

### Step 6: Dashboard Panels (Grafana)
Key panels to create:
- **API Health**: `fireflies_health_status` (stat panel, green/red)
- **Request Rate**: `rate(fireflies_api_requests_total[5m])` by status
- **Latency P50/P95/P99**: `histogram_quantile` on `fireflies_api_latency_seconds`
- **Webhook Events/Hour**: `increase(fireflies_webhook_events_total[1h])`
- **Queue Depth**: `fireflies_transcript_queue_depth` (gauge)
- **Seat Utilization**: `fireflies_seat_utilization` (table, sorted ascending)

## Error Handling
| Alert | Cause | Response |
|-------|-------|----------|
| API Down | Fireflies outage or key revoked | Check status page, verify API key |
| High Error Rate | Schema change or auth issue | Inspect error codes in logs |
| Rate Limited | Burst of requests | Enable request queuing |
| Webhook Backlog | Processing bottleneck | Scale webhook workers |

## Output
- Instrumented GraphQL client with latency and error metrics
- Webhook event tracking with queue depth monitoring
- Health probe running on 5-minute interval
- Prometheus alerting rules for critical conditions

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Prometheus Client](https://github.com/siimon/prom-client)

## Next Steps
For incident response, see `fireflies-incident-runbook`.
