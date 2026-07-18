---
name: intercom-observability
description: |
  Use when you need production monitoring for an Intercom integration — instrumenting
  API calls with metrics and traces, standing up dashboards, or wiring alerts for
  error rate, latency, and rate-limit health.
  Set up observability for Intercom integrations with Prometheus metrics,
  OpenTelemetry traces, structured logging, and alert rules.
  Trigger with phrases like "intercom monitoring", "intercom metrics",
  "intercom observability", "monitor intercom", "intercom alerts", "intercom tracing".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Observability

## Overview

Comprehensive observability for Intercom integrations covering Prometheus metrics,
OpenTelemetry traces, structured logging, and alert rules for error rates, latency,
and rate-limit usage. Read this page for the workflow and shape of each layer, then
drill into [`references/implementation.md`](references/implementation.md) for the full,
copy-pasteable code and [`references/examples.md`](references/examples.md) for
end-to-end worked scenarios.

## Prerequisites

- Prometheus or compatible metrics backend
- OpenTelemetry SDK (optional, for tracing)
- Pino or similar structured logger
- Grafana or alerting system

## Instructions

Build the six observability layers in order. Each step below is the summary and the
essential skeleton — the complete implementation for every step lives in
[`references/implementation.md`](references/implementation.md).

### Step 1: Prometheus metrics

Define five instruments on a shared `Registry`: a request counter, a duration
histogram, an error counter, a rate-limit gauge, and a webhook counter. Label by
`endpoint`/`method`/`status` (never by unbounded IDs — see Error Handling).

```typescript
import { Registry, Counter, Histogram, Gauge } from "prom-client";
const registry = new Registry();
const intercomRequests = new Counter({
  name: "intercom_api_requests_total",
  help: "Total Intercom API requests",
  labelNames: ["endpoint", "method", "status"] as const,
  registers: [registry],
});
// + duration Histogram, error Counter, rate-limit Gauge, webhook Counter
```

Full metric set → [references/implementation.md](references/implementation.md), Step 1.

### Step 2: Instrumented client wrapper

Wrap `IntercomClient` in a `Proxy` that times every service method, increments the
success/error counters, records error/status codes on `IntercomError`, and zeros the
rate-limit gauge on a 429 — so instrumentation is automatic for all endpoints.
Full proxy → [references/implementation.md](references/implementation.md), Step 2.

### Step 3: Structured logging

Configure Pino with a `contact` serializer that emits only `id`/`role` and **never**
logs email, name, or phone. Add `logIntercomOp` and `logWebhook` helpers for
consistent operation/webhook log lines.
Full logger → [references/implementation.md](references/implementation.md), Step 3.

### Step 4: OpenTelemetry tracing

Wrap calls in `tracedIntercomCall`, which opens a per-operation `intercom.*` span, sets
OK/ERROR status, records exceptions, and attaches `status_code`/`error_code`/`request_id`
attributes on Intercom errors.
Full tracer → [references/implementation.md](references/implementation.md), Step 4.

### Step 5: Alert rules

Ship the Prometheus rule group with five alerts: high error rate (>5%), high P95
latency (>3s), low rate limit (<1000), auth failures (401s), and webhook failures.
Full YAML → [references/implementation.md](references/implementation.md), Step 5.

### Step 6: Metrics endpoint

Expose the registry on `GET /metrics` for Prometheus to scrape.
Full route → [references/implementation.md](references/implementation.md), Step 6.

## Output

Applying this skill produces:

- **Instrumented client** — an `IntercomClient` proxy that emits metrics on every call, with zero per-call changes to existing code.
- **Metrics** — `intercom_api_requests_total`, `intercom_api_request_duration_seconds`, `intercom_api_errors_total`, `intercom_rate_limit_remaining`, `intercom_webhooks_processed_total`, scraped at `GET /metrics`.
- **Traces** — one per-operation `intercom.*` span per call, with Intercom error attributes on failures.
- **Structured logs** — PII-redacted JSON operation and webhook log lines.
- **Alerts** — a Prometheus rule group covering error rate, latency, rate limit, auth, and webhooks.

### Key metrics summary

| Metric | Type | Alert Threshold |
|--------|------|----------------|
| `intercom_api_requests_total` | Counter | N/A (baseline) |
| `intercom_api_request_duration_seconds` | Histogram | P95 > 3s |
| `intercom_api_errors_total` | Counter | > 5% error rate |
| `intercom_rate_limit_remaining` | Gauge | < 1000 |
| `intercom_webhooks_processed_total` | Counter | Failed > 10% |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality | Too many unique labels | Use endpoint groups, not IDs |
| Missing metrics | Uninstrumented calls | Wrap client with proxy |
| Alert storms | Wrong thresholds | Tune based on baseline data |
| Log volume too high | Debug logging in prod | Set LOG_LEVEL=info |

## Examples

The following scenarios are covered in full in
[`references/examples.md`](references/examples.md):

- **Contact lookup end-to-end** — one `contacts.find` call producing a counter increment, a histogram sample, a span, and a PII-redacted log line.
- **Rate-limit (429) event** — how the proxy zeros the rate-limit gauge and which alerts fire.
- **Webhook success/failure accounting** — counting processed vs. failed webhooks per topic.
- **Scraping `/metrics`** — the raw Prometheus exposition and how it feeds Grafana and the alert rules.

Minimal end-to-end skeleton:

```typescript
const client = instrumentedClient(new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! }));
const contact = await tracedIntercomCall(
  "contacts.find",
  { "intercom.contact_id": contactId },
  () => client.contacts.find({ contactId })
);
```

## Resources

- [full implementation walkthrough](references/implementation.md) — every step's complete code
- [worked examples](references/examples.md) — end-to-end scenarios and observed output
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://getpino.io/)

## Next Steps

For incident response once these signals are firing, see the `intercom-incident-runbook`
skill, which turns these alerts into a triage-and-mitigation procedure.
