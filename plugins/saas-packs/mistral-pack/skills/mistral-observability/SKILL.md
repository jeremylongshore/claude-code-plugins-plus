---
name: mistral-observability
description: |
  Set up comprehensive observability for Mistral AI with metrics, traces, and alerts.
  Use when implementing monitoring for Mistral AI operations, setting up dashboards,
  or configuring alerting for integration health.
  Trigger with phrases like "mistral monitoring", "mistral metrics",
  "mistral observability", "monitor mistral", "mistral alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, monitoring, observability, dashboard]

---
# Mistral AI Observability

## Overview
Monitor Mistral AI API usage, latency, token consumption, error rates, and costs. Covers instrumented client wrapper, Prometheus metrics, Grafana dashboard panels, alerting rules, and structured logging.

## Prerequisites
- Mistral API integration in production
- Prometheus or OpenTelemetry-compatible metrics backend
- Alerting system (Alertmanager, PagerDuty, or similar)

## Instructions

### Step 1: Instrumented Client Wrapper

```typescript
import { Mistral } from '@mistralai/mistralai';

const PRICING: Record<string, { input: number; output: number }> = {
  'mistral-small-latest':  { input: 0.10, output: 0.30 },
  'mistral-large-latest':  { input: 0.50, output: 1.50 },
  'codestral-latest':      { input: 0.30, output: 0.90 },
  'mistral-embed':         { input: 0.10, output: 0 },
};

interface MetricsEvent {
  model: string;
  endpoint: string;
  durationMs: number;
  status: 'success' | 'error';
  statusCode?: number;
  inputTokens?: number;
  outputTokens?: number;
  costUsd?: number;
}

function emitMetrics(event: MetricsEvent): void {
  // Push to your metrics backend (Prometheus, Datadog, etc.)
  console.log(JSON.stringify({ type: 'mistral_metric', ...event }));
}

async function instrumentedChat(
  client: Mistral,
  model: string,
  messages: any[],
  options?: any,
) {
  const start = performance.now();
  try {
    const response = await client.chat.complete({ model, messages, ...options });
    const duration = Math.round(performance.now() - start);
    const pricing = PRICING[model] ?? PRICING['mistral-small-latest'];
    const pt = response.usage?.promptTokens ?? 0;
    const ct = response.usage?.completionTokens ?? 0;

    emitMetrics({
      model,
      endpoint: 'chat.complete',
      durationMs: duration,
      status: 'success',
      inputTokens: pt,
      outputTokens: ct,
      costUsd: (pt / 1e6) * pricing.input + (ct / 1e6) * pricing.output,
    });

    return response;
  } catch (error: any) {
    emitMetrics({
      model,
      endpoint: 'chat.complete',
      durationMs: Math.round(performance.now() - start),
      status: 'error',
      statusCode: error.status,
    });
    throw error;
  }
}
```

### Step 2: Prometheus Metrics

```typescript
// Using prom-client
import { Counter, Histogram, Gauge } from 'prom-client';

const mistralRequests = new Counter({
  name: 'mistral_requests_total',
  help: 'Total Mistral API requests',
  labelNames: ['model', 'endpoint', 'status'],
});

const mistralDuration = new Histogram({
  name: 'mistral_request_duration_ms',
  help: 'Mistral request duration in milliseconds',
  labelNames: ['model', 'endpoint'],
  buckets: [100, 250, 500, 1000, 2500, 5000, 10000],
});

const mistralTokens = new Counter({
  name: 'mistral_tokens_total',
  help: 'Total tokens consumed',
  labelNames: ['model', 'direction'], // direction: input | output
});

const mistralCost = new Counter({
  name: 'mistral_cost_usd_total',
  help: 'Estimated cost in USD',
  labelNames: ['model'],
});

const mistralErrors = new Counter({
  name: 'mistral_errors_total',
  help: 'Total Mistral errors',
  labelNames: ['model', 'status_code'],
});

// Record metrics from instrumented wrapper
function recordPrometheusMetrics(event: MetricsEvent): void {
  mistralRequests.inc({ model: event.model, endpoint: event.endpoint, status: event.status });
  mistralDuration.observe({ model: event.model, endpoint: event.endpoint }, event.durationMs);

  if (event.status === 'success') {
    if (event.inputTokens) mistralTokens.inc({ model: event.model, direction: 'input' }, event.inputTokens);
    if (event.outputTokens) mistralTokens.inc({ model: event.model, direction: 'output' }, event.outputTokens);
    if (event.costUsd) mistralCost.inc({ model: event.model }, event.costUsd);
  } else {
    mistralErrors.inc({ model: event.model, status_code: String(event.statusCode ?? 'unknown') });
  }
}
```

### Step 3: Alerting Rules

```yaml
# prometheus/mistral-alerts.yaml
groups:
  - name: mistral
    rules:
      - alert: MistralHighErrorRate
        expr: rate(mistral_errors_total[5m]) / rate(mistral_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Mistral error rate exceeds 5%"
          runbook: "See mistral-incident-runbook skill"

      - alert: MistralHighLatency
        expr: histogram_quantile(0.95, rate(mistral_request_duration_ms_bucket[5m])) > 5000
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Mistral P95 latency exceeds 5 seconds"

      - alert: MistralRateLimited
        expr: rate(mistral_errors_total{status_code="429"}[5m]) > 0
        for: 2m
        labels: { severity: warning }
        annotations:
          summary: "Mistral rate limiting detected"

      - alert: MistralCostSpike
        expr: increase(mistral_cost_usd_total[1h]) > 10
        labels: { severity: warning }
        annotations:
          summary: "Mistral spend exceeds $10/hour"

      - alert: MistralAuthFailure
        expr: increase(mistral_errors_total{status_code="401"}[5m]) > 0
        labels: { severity: critical }
        annotations:
          summary: "Mistral authentication failing — API key may be revoked"
```

### Step 4: Grafana Dashboard Panels

Key panels to create:

| Panel | Query | Type |
|-------|-------|------|
| Request Rate | `rate(mistral_requests_total[5m])` | Time series |
| P50/P95/P99 Latency | `histogram_quantile(0.95, rate(..._bucket[5m]))` | Time series |
| Token Velocity | `rate(mistral_tokens_total{direction="output"}[5m])` | Time series |
| Hourly Cost | `increase(mistral_cost_usd_total[1h])` | Stat |
| Error Rate | `rate(mistral_errors_total[5m])` by status_code | Time series |
| Model Distribution | `sum by (model) (rate(mistral_requests_total[5m]))` | Pie chart |

### Step 5: Structured Log Format

```typescript
interface MistralLogEntry {
  ts: string;
  level: 'info' | 'warn' | 'error';
  model: string;
  endpoint: string;
  durationMs: number;
  inputTokens?: number;
  outputTokens?: number;
  costUsd?: number;
  status: string;
  statusCode?: number;
  requestId?: string;
}

function logMistralRequest(entry: MistralLogEntry): void {
  // Ship to SIEM, CloudWatch, or log aggregator
  // NEVER log message content — PII risk
  console.log(JSON.stringify(entry));
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing token counts | Streaming not aggregated | Sum tokens from stream chunks |
| Cost drift from bill | Pricing table outdated | Update PRICING map when rates change |
| Alert storm on 429s | Rate limit burst | Tune alert threshold, add request queue |
| High cardinality | Per-request labels | Never label by request ID or user ID |

## Resources
- [OpenLIT Mistral Monitoring](https://docs.mistral.ai/cookbooks/third_party-openlit-cookbook_mistral_opentelemetry/)
- [Prometheus Client](https://github.com/siimon/prom-client)
- [Grafana Dashboards](https://grafana.com/dashboards/)

## Output
- Instrumented client wrapper with timing and cost tracking
- Prometheus metrics (requests, duration, tokens, cost, errors)
- Alerting rules for error rate, latency, rate limits, cost, auth
- Grafana dashboard panel specifications
- Structured logging format for SIEM integration
