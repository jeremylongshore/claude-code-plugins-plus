---
name: notion-observability
description: 'Set up observability for Notion integrations with metrics, traces, and
  alerts.

  Use when implementing monitoring for Notion API calls, setting up dashboards,

  or configuring alerting for Notion integration health.

  Trigger with phrases like "notion monitoring", "notion metrics",

  "notion observability", "monitor notion", "notion alerts", "notion tracing".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Observability

## Overview

Instrument Notion API calls with metrics, structured logging, and alerting. Track request rates, latencies, error rates, and rate limit headroom across a full observability stack: an instrumented client wrapper, Prometheus metrics, structured logging via pino, health check endpoints, and alerting rules.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Prometheus-compatible metrics backend (optional: Grafana, Datadog, or CloudWatch)
- Structured logging library: `pino` (Node.js) or `structlog` (Python)

## Authentication

All snippets read the integration token from the `NOTION_TOKEN` environment variable (never hard-code it) and pass it as `auth` to the Notion client constructor. Store it in your secret manager and inject it at runtime. The health check and metrics endpoints below expose no secrets — only aggregate counters and status.

## Instructions

The workflow layers three pieces. Build them in order; each is self-contained. Full code for every step lives in [references/implementation.md](references/implementation.md).

### Step 1: Instrumented client wrapper

Wrap every Notion call so timing, error classification, rate-limit detection, and structured logging happen automatically. The wrapper accumulates per-operation latency buckets and exposes `getMetrics()` for avg/p95. Skeleton:

```typescript
class InstrumentedNotionClient {
  async call<T>(operation: string, fn: (c: Client) => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      const result = await fn(this.client);
      this.recordLatency(operation, Math.round(performance.now() - start));
      return result;
    } catch (error) {
      if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
        this.metrics.rateLimitCount++;
      }
      throw error;
    }
  }
}
```

A Python (`notion-client`) equivalent is in the reference. Full TypeScript + Python wrappers: [references/implementation.md](references/implementation.md) (Step 1).

### Step 2: Prometheus metrics export

Register a request counter, a latency histogram (buckets tuned for Notion's typical 200-800ms responses), an error counter keyed by error code, and a rate-limit gauge. Wrap calls with `startTimer()` and expose a `/metrics` endpoint for scraping. Full export code: [references/implementation.md](references/implementation.md) (Step 2).

### Step 3: Health check, structured logging, and alerting

Add a `/health/notion` endpoint that probes `users.me` and returns 200/503 with aggregate metrics, wire pino for JSON logs with slow-query warnings (>2s), and ship Prometheus alerting rules for error-rate spikes, rate-limit exhaustion, high P95 latency, and outages. Full endpoint, logger, and alert rules: [references/implementation.md](references/implementation.md) (Step 3).

## Output

- Instrumented Notion client tracking all API calls with per-operation latency buckets
- Prometheus metrics for request rate, latency histograms, and error counters
- Structured JSON logging via pino with slow-query warnings (>2s)
- Health check endpoint with Notion connectivity status and aggregate metrics
- Alerting rules for error rate spikes, rate limiting, high latency, and outages

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| High cardinality metrics | Too many unique label values | Use fixed operation names (`databases.query`, `pages.create`) |
| Alert storms on Notion outage | All alerts fire simultaneously | Add `group_wait: 30s` in alertmanager config |
| Missing metrics for some calls | Not all API calls use wrapper | Enforce wrapper at architecture level |
| Log volume too high in prod | DEBUG level enabled | Set `LOG_LEVEL=info` or `warn` in production |
| P95 latency unreliable | Too few samples | Ensure minimum 100 requests in window |
| Rate limit counter never fires | Wrong error code check | Use `APIErrorCode.RateLimited` constant |

## Examples

Ready-to-run PromQL dashboard queries and a no-Prometheus inline console metrics snippet live in [references/examples.md](references/examples.md). Quickest smoke test — error percentage in PromQL:

```promql
100 * rate(notion_errors_total[5m]) / rate(notion_requests_total[5m])
```

## Resources

- [Notion Request Limits](https://developers.notion.com/reference/request-limits) — 3 requests/second average
- [Notion Error Codes](https://developers.notion.com/reference/errors) — full error code reference
- [Prometheus Naming Best Practices](https://prometheus.io/docs/practices/naming/)
- [pino Logger](https://getpino.io/) — fast structured logging for Node.js
- [Grafana Dashboard Templates](https://grafana.com/grafana/dashboards/) — pre-built API monitoring dashboards
- [references/implementation.md](references/implementation.md) — full instrumentation stack (client wrapper, metrics, health check, alerts)
- [references/examples.md](references/examples.md) — PromQL queries and inline metrics snippet

## Next Steps

For incident response procedures when monitoring detects failures, see the `notion-incident-runbook` skill. Once metrics flow, build a Grafana dashboard from the PromQL queries in [references/examples.md](references/examples.md) and tune alert thresholds to your traffic baseline.
