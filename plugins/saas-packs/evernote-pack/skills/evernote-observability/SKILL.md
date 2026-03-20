---
name: evernote-observability
description: |
  Implement observability for Evernote integrations.
  Use when setting up monitoring, logging, tracing,
  or alerting for Evernote applications.
  Trigger with phrases like "evernote monitoring", "evernote logging",
  "evernote metrics", "evernote observability".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Observability

## Overview
Comprehensive observability setup for Evernote integrations: Prometheus metrics for API call tracking, structured JSON logging, OpenTelemetry tracing, health check endpoints, and alerting rules.

## Prerequisites
- Monitoring infrastructure (Prometheus, Datadog, or CloudWatch)
- Log aggregation (ELK, Loki, or CloudWatch Logs)
- Alerting system (PagerDuty, Opsgenie, or Slack webhooks)

## Instructions

### Step 1: Metrics Collection

Track key metrics with Prometheus counters and histograms: `evernote_api_calls_total` (by method and status), `evernote_api_duration_seconds` (latency histogram), `evernote_rate_limits_total` (rate limit hits), `evernote_quota_usage_bytes` (upload quota consumption).

```javascript
const { Counter, Histogram } = require('prom-client');

const apiCalls = new Counter({
  name: 'evernote_api_calls_total',
  help: 'Total Evernote API calls',
  labelNames: ['method', 'status']
});

const apiDuration = new Histogram({
  name: 'evernote_api_duration_seconds',
  help: 'Evernote API call duration',
  labelNames: ['method'],
  buckets: [0.1, 0.5, 1, 2, 5, 10]
});
```

### Step 2: Instrumented Client

Wrap the NoteStore with a Proxy that automatically records metrics for every API call. Increment counters on success/failure, observe latency in histograms, and count rate limit events.

### Step 3: Structured Logging

Use JSON-formatted logs with consistent fields: `timestamp`, `level`, `method`, `duration`, `userId` (hashed), `noteGuid`. Redact access tokens from all log output.

```javascript
function logApiCall(method, duration, error) {
  const entry = {
    timestamp: new Date().toISOString(),
    service: 'evernote-integration',
    method,
    duration_ms: duration,
    status: error ? 'error' : 'success',
    error_code: error?.errorCode
  };
  console.log(JSON.stringify(entry));
}
```

### Step 4: Health and Readiness Endpoints

Implement `/health` (liveness: is the process running?) and `/ready` (readiness: can we reach Evernote API?). Include cache connectivity check.

### Step 5: Alert Rules

Configure Prometheus alerts: rate limit hits > 5 in 10 minutes, API error rate > 10%, p95 latency > 5 seconds, quota usage > 90%.

```yaml
# prometheus-alerts.yml
groups:
  - name: evernote
    rules:
      - alert: EvernoteRateLimited
        expr: rate(evernote_rate_limits_total[10m]) > 0.5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Evernote rate limits detected"
```

For the complete metrics setup, Grafana dashboard JSON, tracing configuration, and alert rules, see [Implementation Guide](references/implementation-guide.md).

## Output
- Prometheus metrics: API calls, latency histogram, rate limits, quota usage
- Instrumented NoteStore client with automatic metric recording
- Structured JSON logging with token redaction
- Health and readiness endpoints
- Prometheus alert rules for rate limits, errors, and latency

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Metrics endpoint not scraped | Prometheus target missing | Add service to Prometheus scrape config |
| Missing trace context | OpenTelemetry not initialized | Initialize tracer before creating Evernote client |
| Log volume too high | Logging every API call | Sample debug logs, always log errors and rate limits |
| Alert fatigue | Thresholds too low | Tune alert thresholds based on baseline metrics |

## Resources
- [Prometheus](https://prometheus.io/docs/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/languages/js/)
- [Grafana](https://grafana.com/docs/)
- [prom-client npm](https://www.npmjs.com/package/prom-client)

## Next Steps
For incident handling, see `evernote-incident-runbook`.

## Examples

**Grafana dashboard**: Display API call rate, p50/p95/p99 latency, error rate, rate limit frequency, and quota usage on a single dashboard. Set time range to last 24 hours.

**Rate limit alerting**: Alert on-call when rate limit hits exceed 5 per 10-minute window. Include runbook link to `evernote-rate-limits` in the alert annotation.
