---
name: lokalise-observability
description: |
  Set up comprehensive observability for Lokalise integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Lokalise operations, setting up dashboards,
  or configuring alerting for Lokalise integration health.
  Trigger with phrases like "lokalise monitoring", "lokalise metrics",
  "lokalise observability", "monitor lokalise", "lokalise alerts", "lokalise tracing".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lokalise, monitoring, observability, dashboard]

---
# Lokalise Observability

## Overview
Monitor Lokalise translation pipeline health: API response times, rate limit consumption, translation completion rates, webhook delivery reliability, file upload/download status, and per-word cost tracking. Built around the `@lokalise/node-api` SDK with Prometheus-compatible metrics and alerting rules.

## Prerequisites
- `@lokalise/node-api` SDK installed
- Metrics backend (Prometheus, Datadog, CloudWatch, or OpenTelemetry collector)
- Lokalise API token with read access
- Optional: webhook endpoint for real-time event monitoring

## Instructions

### Step 1: Instrument API Calls with Metrics

Wrap every SDK call to emit duration, success/failure counts, and rate limit status.

```typescript
import { LokaliseApi } from "@lokalise/node-api";

interface MetricLabels {
  operation: string;
  status: "ok" | "error";
  code?: string;
}

// Implement this to emit to your metrics backend
declare function emitHistogram(name: string, value: number, labels: MetricLabels): void;
declare function emitCounter(name: string, value: number, labels: MetricLabels): void;

const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

async function trackedApiCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const durationMs = performance.now() - start;

    emitHistogram("lokalise_api_duration_ms", durationMs, {
      operation,
      status: "ok",
    });
    emitCounter("lokalise_api_requests_total", 1, {
      operation,
      status: "ok",
    });

    return result;
  } catch (err: unknown) {
    const code = (err as { code?: number })?.code?.toString() ?? "unknown";
    const durationMs = performance.now() - start;

    emitHistogram("lokalise_api_duration_ms", durationMs, {
      operation,
      status: "error",
      code,
    });
    emitCounter("lokalise_api_requests_total", 1, {
      operation,
      status: "error",
      code,
    });

    throw err;
  }
}

// Usage — wrap every SDK call
const keys = await trackedApiCall("keys.list", () =>
  lok.keys().list({ project_id: projectId, limit: 500 })
);

const bundle = await trackedApiCall("files.download", () =>
  lok.files().download(projectId, {
    format: "json",
    filter_langs: ["en"],
    original_filenames: false,
  })
);
```

### Step 2: Monitor Translation Completion

Poll project statistics and emit per-locale progress as gauge metrics.

```typescript
declare function emitGauge(name: string, value: number, labels: Record<string, string>): void;

async function collectTranslationMetrics(projectId: string): Promise<void> {
  const project = await trackedApiCall("projects.get", () =>
    lok.projects().get(projectId)
  );

  // Overall progress
  emitGauge("lokalise_translation_progress_pct", project.statistics?.progress_total ?? 0, {
    project: projectId,
    locale: "all",
  });

  emitGauge("lokalise_keys_total", project.statistics?.keys_total ?? 0, {
    project: projectId,
  });

  // Per-language progress
  const languages = await trackedApiCall("languages.list", () =>
    lok.languages().list({ project_id: projectId, limit: 100 })
  );

  for (const lang of languages.items) {
    emitGauge("lokalise_translation_progress_pct", lang.statistics?.progress ?? 0, {
      project: projectId,
      locale: lang.lang_iso,
    });
    emitGauge("lokalise_words_to_do", lang.statistics?.words_to_do ?? 0, {
      project: projectId,
      locale: lang.lang_iso,
    });
  }
}

// Run on a schedule (every 5 minutes)
// setInterval(() => collectTranslationMetrics(projectId), 5 * 60_000);
```

### Step 3: Track Rate Limit Consumption

```bash
set -euo pipefail
# Quick rate limit check — call from a monitoring cron job
HEADERS=$(curl -sI "https://api.lokalise.com/api2/projects?limit=1" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" 2>/dev/null)

LIMIT=$(echo "$HEADERS" | grep -i "x-ratelimit-limit" | awk '{print $2}' | tr -d '\r')
REMAINING=$(echo "$HEADERS" | grep -i "x-ratelimit-remaining" | awk '{print $2}' | tr -d '\r')
RESET=$(echo "$HEADERS" | grep -i "x-ratelimit-reset" | awk '{print $2}' | tr -d '\r')

echo "Rate limit: ${REMAINING}/${LIMIT} remaining (resets at ${RESET})"

# Emit as metrics for Prometheus/Datadog
# lokalise_rate_limit_remaining ${REMAINING}
# lokalise_rate_limit_max ${LIMIT}
```

### Step 4: Monitor Webhook Delivery

Track webhook processing success and latency in your webhook handler.

```typescript
import express from "express";

const webhookMetrics = {
  received: 0,
  processed: 0,
  failed: 0,
  totalLatencyMs: 0,
};

app.post("/webhooks/lokalise", async (req: express.Request, res: express.Response) => {
  webhookMetrics.received++;
  const start = performance.now();

  // Respond immediately — Lokalise times out after 8 seconds
  res.status(200).json({ received: true });

  try {
    await processWebhookEvent(req.body);
    webhookMetrics.processed++;
  } catch (error) {
    webhookMetrics.failed++;
    console.error("Webhook processing failed:", error);
  }

  const latencyMs = performance.now() - start;
  webhookMetrics.totalLatencyMs += latencyMs;

  emitCounter("lokalise_webhook_received_total", 1, {
    event: req.body.event,
    status: webhookMetrics.failed > 0 ? "error" : "ok",
  });
  emitHistogram("lokalise_webhook_processing_ms", latencyMs, {
    event: req.body.event,
    status: "ok",
  });
});

// Health endpoint exposing webhook metrics
app.get("/metrics/webhooks", (_req, res) => {
  res.json({
    received: webhookMetrics.received,
    processed: webhookMetrics.processed,
    failed: webhookMetrics.failed,
    avgLatencyMs: webhookMetrics.received > 0
      ? Math.round(webhookMetrics.totalLatencyMs / webhookMetrics.received)
      : 0,
  });
});
```

### Step 5: Register Webhooks for Key Events

```bash
set -euo pipefail
# Subscribe to events that matter for pipeline monitoring
curl -s -X POST "https://api.lokalise.com/api2/projects/${LOKALISE_PROJECT_ID}/webhooks" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.company.com/lokalise",
    "events": [
      "project.imported",
      "project.exported",
      "project.key.added",
      "project.key.modified",
      "project.translation.updated",
      "project.translation.proofread",
      "project.task.closed",
      "project.contributor.added"
    ]
  }' | jq '{webhook_id: .webhook.webhook_id, events: .webhook.events}'
```

### Step 6: Prometheus Alerting Rules

```yaml
groups:
  - name: lokalise
    rules:
      - alert: LokaliseApiRateLimited
        expr: rate(lokalise_api_requests_total{status="error", code="429"}[5m]) > 0
        for: 2m
        annotations:
          summary: "Lokalise API rate limit hit — requests being throttled"
          runbook: "Check for runaway loops. Lokalise limit is 6 req/sec per token."

      - alert: LokaliseApiErrors
        expr: rate(lokalise_api_requests_total{status="error", code=~"5.."}[10m]) > 0.1
        for: 5m
        annotations:
          summary: "Lokalise API returning 5xx errors"
          runbook: "Check https://status.lokalise.com. Enable fallback translations."

      - alert: TranslationProgressStalled
        expr: lokalise_translation_progress_pct < 80 and changes(lokalise_translation_progress_pct[24h]) == 0
        for: 24h
        annotations:
          summary: "Translation progress stalled at {{ $value }}% for 24+ hours"

      - alert: WebhookDeliveryFailing
        expr: rate(lokalise_webhook_received_total{status="error"}[1h]) > 3
        annotations:
          summary: "Lokalise webhook deliveries failing ({{ $value }} errors/hour)"

      - alert: LokaliseApiLatencyHigh
        expr: histogram_quantile(0.95, rate(lokalise_api_duration_ms_bucket[5m])) > 5000
        for: 10m
        annotations:
          summary: "Lokalise API P95 latency above 5 seconds"
```

### Step 7: Translation Pipeline Dashboard Spec

Key panels for Grafana/Datadog:

| Panel | Metric | Type |
|-------|--------|------|
| API Request Rate | `rate(lokalise_api_requests_total[5m])` | Time series |
| API Latency P50/P95 | `histogram_quantile(0.5/0.95, ...)` | Time series |
| Rate Limit Remaining | `lokalise_rate_limit_remaining` | Gauge |
| Translation Progress | `lokalise_translation_progress_pct` by locale | Bar chart |
| Words Remaining | `lokalise_words_to_do` by locale | Bar chart |
| Webhook Success Rate | `rate(lokalise_webhook_received_total{status="ok"}[5m])` | Time series |
| Error Rate by Code | `rate(lokalise_api_requests_total{status="error"}[5m])` by code | Stacked area |

## Output
- `trackedApiCall()` wrapper emitting duration and error metrics for every Lokalise API operation
- Translation progress gauge metrics broken down by project and locale
- Rate limit consumption monitoring via response headers
- Webhook delivery tracking with latency and error counters
- Prometheus alerting rules for rate limiting, API errors, stalled progress, and webhook failures
- Dashboard specification with 7 panels covering the full translation pipeline

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded 6 req/sec rate limit | Add request throttling with p-queue |
| Webhook not firing | Wrong event type registered | Verify event names match API reference |
| Progress metric stuck at 0 | Language not added to project | Add target locale in Lokalise project settings |
| Stale metrics | Polling interval too long | Reduce collection interval to 5 minutes |
| High cardinality | Too many label values | Limit `operation` labels to top-level SDK methods |

## Resources
- [Lokalise Webhooks API](https://developers.lokalise.com/reference/create-a-webhook)
- [Lokalise Webhook Events](https://developers.lokalise.com/docs/webhook-events)
- [Lokalise API Rate Limits](https://developers.lokalise.com/reference/api-rate-limits)
- [Lokalise Project Statistics](https://developers.lokalise.com/reference/retrieve-a-project)
- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [p-queue](https://github.com/sindresorhus/p-queue) — rate-limited request queue

## Next Steps
For setting up real-time automation based on webhook events, see `lokalise-webhooks-events`. For incident response procedures when alerts fire, see `lokalise-incident-runbook`.
