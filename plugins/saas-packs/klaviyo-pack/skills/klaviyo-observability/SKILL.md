---
name: klaviyo-observability
description: 'Set up observability for Klaviyo integrations with metrics, traces,
  and alerts.

  Use when implementing monitoring for Klaviyo API operations, setting up dashboards,

  or configuring alerting for Klaviyo integration health.

  Trigger with phrases like "klaviyo monitoring", "klaviyo metrics",

  "klaviyo observability", "monitor klaviyo", "klaviyo alerts", "klaviyo tracing".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Observability

## Overview

Comprehensive observability for Klaviyo integrations: Prometheus metrics for API call tracking, OpenTelemetry tracing, structured logging, and alerting rules tuned to Klaviyo's rate limits and error patterns. The pattern centers on one instrumentation wrapper that every Klaviyo call routes through, so metrics, traces, and logs stay consistent across profiles, events, and webhooks.

## Prerequisites

- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed (optional)
- Grafana or similar dashboarding tool (optional)
- `klaviyo-api` SDK installed

## Key Metrics to Track

| Metric | Type | Why It Matters |
|--------|------|---------------|
| `klaviyo_api_requests_total` | Counter | Track total API volume by endpoint |
| `klaviyo_api_duration_seconds` | Histogram | Detect latency degradation |
| `klaviyo_api_errors_total` | Counter | 4xx/5xx error rates |
| `klaviyo_rate_limit_remaining` | Gauge | Predict when you'll hit 429s |
| `klaviyo_profiles_synced_total` | Counter | Profile sync throughput |
| `klaviyo_events_tracked_total` | Counter | Event tracking volume |
| `klaviyo_webhook_received_total` | Counter | Inbound webhook volume |

## Instructions

Read any existing Klaviyo client code first, then build the layers in order. Each
step writes one module; steps 5–6 wire the alerting and scrape endpoint.

1. **Instrumented API wrapper** — write `src/klaviyo/instrumented-client.ts` with the
   Prometheus counters, histogram, and gauge, exposed through a single
   `instrumentedCall()` helper.
2. **Route every call** through `instrumentedCall(endpoint, method, () => ...)` in
   the service layer so profile/event/webhook traffic is all counted.
3. **OpenTelemetry tracing** (optional) — add `tracedKlaviyoCall()` to emit spans
   with Klaviyo operation + error attributes.
4. **Structured logging** — add a `pino` logger with an email-redacting serializer.
5. **Alert rules** — drop `prometheus/klaviyo-alerts.yml` in place for error-rate,
   429, latency, down, and low-headroom alerts.
6. **Metrics endpoint** — expose `GET /metrics` from the shared registry.

The wrapper is the load-bearing piece — the skeleton is:

```typescript
export async function instrumentedCall<T>(
  endpoint: string,
  method: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ method, endpoint });
  try {
    const result = await operation();
    apiRequests.inc({ method, endpoint, status: 'success' });
    return result;
  } catch (error: any) {
    apiErrors.inc({ endpoint, status_code: error.status || 'unknown', error_code: error.body?.errors?.[0]?.code || 'unknown' });
    throw error;
  } finally {
    timer();
  }
}
```

Full source for all six steps — counters, tracing, logging, and the metrics
endpoint — is in [references/instrumentation.md](references/instrumentation.md).
Alert rules and Grafana panels are in [references/alerting.md](references/alerting.md).

## Output

Applying this skill produces:

- `src/klaviyo/instrumented-client.ts` — Prometheus registry + `instrumentedCall()` wrapper
- `src/klaviyo/tracing.ts` — OpenTelemetry `tracedKlaviyoCall()` (optional)
- `src/klaviyo/logger.ts` — `pino` logger with PII-redacting serializers
- `prometheus/klaviyo-alerts.yml` — five alert rules (error rate, 429s, latency, down, low headroom)
- `GET /metrics` route exposing the registry in Prometheus text format

Once wired, `curl localhost:PORT/metrics` returns the `klaviyo_*` series, and the
Grafana panels in [references/alerting.md](references/alerting.md) render request
rate, error rate, P95 latency, and rate-limit headroom.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation wrapper | Wrap all API calls with `instrumentedCall()` |
| High cardinality | Too many label values | Use endpoint groups, not full URLs |
| Alert storms | Thresholds too low | Tune alert rules to your traffic pattern |
| PII in logs | Email in log messages | Use serializer to redact emails |

## Examples

**Instrument a profile upsert** — wrap the SDK call so it counts toward
`klaviyo_api_requests_total` and records latency:

```typescript
const profile = await instrumentedCall('profiles', 'POST', () =>
  profilesApi.createOrUpdateProfile({
    data: { type: 'profile', attributes: { email: user.email, firstName: user.name } },
  })
);
```

**Alert on rate-limit pressure** — fire before you start getting 429s:

```yaml
- alert: KlaviyoRateLimitLow
  expr: klaviyo_rate_limit_remaining < 20
  for: 30s
  labels: { severity: warning }
  annotations:
    summary: "Klaviyo rate limit headroom below 20 requests"
```

More worked examples — event tracking, tracing, structured logging, and the full
alert group — are in [references/instrumentation.md](references/instrumentation.md)
and [references/alerting.md](references/alerting.md).

## Resources

- [references/instrumentation.md](references/instrumentation.md) — full metrics, tracing, logging, and metrics-endpoint source
- [references/alerting.md](references/alerting.md) — Prometheus alert rules and Grafana dashboard panels
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [pino Logger](https://github.com/pinojs/pino)

## Next Steps

For incident response, see the `klaviyo-incident-runbook` skill, which pairs these
metrics and alerts with triage and escalation procedures.
