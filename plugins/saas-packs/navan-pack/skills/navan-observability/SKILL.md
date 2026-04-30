---
name: navan-observability
description: 'Use when setting up monitoring, logging, and alerting for Navan API
  integrations in production environments.

  Trigger with "navan observability" or "navan monitoring" or "navan api dashboards".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Observability

## Overview

Navan exposes no built-in API metrics dashboard — monitoring is your responsibility. This skill implements structured logging, latency tracking, error classification, and alerting for Navan REST API integrations. Since Navan uses OAuth 2.0 with token expiration, observability must also cover the authentication lifecycle. Patterns are provided for Datadog, CloudWatch, and Prometheus/Grafana.

## Prerequisites

- **Running Navan API integration** with OAuth 2.0 credentials
- **Monitoring platform** — Datadog, AWS CloudWatch, or Prometheus/Grafana
- **Node.js 18+** or equivalent runtime for the instrumentation middleware
- API base URL: `https://api.navan.com/v1`

## Instructions

### Step 1 — Instrument API Calls with Structured Logging

Wrap every Navan API call with timing, status, and correlation tracking:

```typescript
import { randomUUID } from 'crypto';

interface NavanApiLog {
  event: 'navan.api.request';
  correlation_id: string;
  method: string;
  endpoint: string;
  status: number;
  duration_ms: number;
  error_type?: 'auth' | 'rate_limit' | 'server' | 'client' | 'network';
  timestamp: string;
}

async function navanRequest(
  method: string,
  endpoint: string,
  token: string,
  body?: object
): Promise<Response> {
  const correlationId = randomUUID();
  const start = performance.now();

  try {
    const response = await fetch(`https://api.navan.com/v1/${endpoint}`, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const log: NavanApiLog = {
      event: 'navan.api.request',
      correlation_id: correlationId,
      method,
      endpoint,
      status: response.status,
      duration_ms: Math.round(performance.now() - start),
      timestamp: new Date().toISOString(),
    };

    if (response.status === 401) log.error_type = 'auth';
    else if (response.status === 429) log.error_type = 'rate_limit';
    else if (response.status >= 500) log.error_type = 'server';
    else if (response.status >= 400) log.error_type = 'client';

    console.log(JSON.stringify(log));
    return response;
  } catch (err) {
    console.log(JSON.stringify({
      event: 'navan.api.request',
      correlation_id: correlationId,
      method,
      endpoint,
      status: 0,
      duration_ms: Math.round(performance.now() - start),
      error_type: 'network',
      error_message: (err as Error).message,
      timestamp: new Date().toISOString(),
    }));
    throw err;
  }
}
```

### Step 2 — Track OAuth Token Lifecycle

```typescript
async function refreshToken(clientId: string, clientSecret: string): Promise<string> {
  const start = performance.now();
  const response = await fetch('https://api.navan.com/ta-auth/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: clientId,
      client_secret: clientSecret,
    }),
  });

  console.log(JSON.stringify({
    event: 'navan.auth.refresh',
    status: response.status,
    duration_ms: Math.round(performance.now() - start),
    success: response.status === 200,
    timestamp: new Date().toISOString(),
  }));

  if (!response.ok) throw new Error(`Auth failed: HTTP ${response.status}`);
  const data = await response.json();
  return data.access_token;
}
```

### Step 3 — Define Alert Rules

**Datadog monitor configuration:**

```yaml
# datadog-monitors/navan-alerts.yaml
monitors:
  - name: "Navan API Auth Failures"
    type: metric alert
    query: >
      sum(last_5m):sum:navan.api.errors{error_type:auth}.as_count() > 3
    message: |
      Navan OAuth token may be expired or credentials rotated.
      Check: Admin > API Settings for credential status.
      Runbook: https://wiki.internal/navan-auth-rotation
    priority: P2

  - name: "Navan API Rate Limiting"
    type: metric alert
    query: >
      sum(last_15m):sum:navan.api.errors{error_type:rate_limit}.as_count() > 10
    message: |
      Navan API returning 429 rate limit responses.
      Action: Reduce sync frequency or implement backoff.
    priority: P3

  - name: "Navan API Latency Degradation"
    type: metric alert
    query: >
      avg(last_10m):p95:navan.api.duration_ms{*} > 5000
    message: |
      Navan API p95 latency exceeds 5 seconds.
      Impact: Expense sync and booking operations are slow.
    priority: P3

  - name: "Navan API Server Errors"
    type: metric alert
    query: >
      sum(last_5m):sum:navan.api.errors{error_type:server}.as_count() > 5
    message: |
      Navan API returning 5xx server errors.
      This is likely a Navan-side issue — check status page.
    priority: P2
```

### Step 4 — Build the Dashboard

**Key metrics to display:**

| Metric | Source | Panel Type |
|--------|--------|------------|
| Request rate (rpm) | `navan.api.request` count | Time series |
| Latency p50/p95/p99 | `navan.api.duration_ms` | Percentile graph |
| Error rate by type | `navan.api.errors` by `error_type` | Stacked bar |
| Token refresh success rate | `navan.auth.refresh` | Single stat |
| Active correlation IDs | `navan.api.request` unique `correlation_id` | Count |

**Prometheus queries:**

```promql
# Request rate per minute
rate(navan_api_requests_total[5m]) * 60

# p95 latency
histogram_quantile(0.95, rate(navan_api_duration_seconds_bucket[5m]))

# Error rate percentage
sum(rate(navan_api_errors_total[5m])) / sum(rate(navan_api_requests_total[5m])) * 100

# Auth failure spike detection
increase(navan_api_errors_total{error_type="auth"}[5m]) > 0
```

## Output

A fully instrumented Navan API integration with:
- **Structured JSON logs** with correlation IDs for request tracing
- **Real-time dashboards** showing latency, throughput, and error rates
- **Automated alerts** differentiating auth failures, rate limits, and server errors
- **Token lifecycle visibility** tracking refresh success and timing

## Error Handling

| HTTP Code | Error Type | Alert Severity | Action |
|-----------|-----------|----------------|--------|
| `401` | `auth` | P2 — page on-call | Rotate OAuth credentials immediately |
| `403` | `client` | P3 — notify | Verify API scopes in Navan Admin |
| `429` | `rate_limit` | P3 — notify | Reduce call frequency, check `navan-rate-limits` skill |
| `500` | `server` | P2 — page if sustained | Check Navan status; nothing to fix on your side |
| `502/503` | `server` | P3 — notify | Transient; retry with backoff |
| `0` (network) | `network` | P1 — page | DNS, firewall, or connectivity issue |

## Examples

**CloudWatch metric push from a Lambda integration:**

```bash
# Push custom metric after each Navan API call
aws cloudwatch put-metric-data \
  --namespace "Navan/API" \
  --metric-name "RequestLatency" \
  --value 342 \
  --unit Milliseconds \
  --dimensions Endpoint=bookings,Status=200
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — API documentation
- [Datadog Custom Metrics](https://docs.datadoghq.com/metrics/custom_metrics/) — Sending custom metrics
- [Prometheus Client Libraries](https://prometheus.io/docs/instrumenting/clientlibs/) — Instrumentation SDKs
- [AWS CloudWatch Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)

## Next Steps

- Add `navan-incident-runbook` for structured incident response procedures
- Add `navan-rate-limits` to understand Navan's specific throttling behavior
- See `navan-performance-tuning` to optimize the API calls being monitored
