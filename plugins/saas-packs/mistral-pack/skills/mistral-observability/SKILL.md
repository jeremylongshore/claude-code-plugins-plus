---
name: mistral-observability
description: |
  Set up comprehensive observability for Mistral AI integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Mistral AI operations, setting up dashboards,
  or configuring alerting for Mistral AI integration health.
  Trigger with phrases like "mistral monitoring", "mistral metrics",
  "mistral observability", "monitor mistral", "mistral alerts", "mistral tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Observability

## Overview
Monitor Mistral AI API usage, latency, token consumption, and costs across models.

## Prerequisites
- Mistral API integration in production
- Prometheus or compatible metrics backend
- Alerting system (AlertManager, PagerDuty, or similar)

## Instructions

### Step 1: Instrument the Mistral Client
```typescript
import Mistral from '@mistralai/mistralai';

const PRICING: Record<string, { input: number; output: number }> = {
  'mistral-small-latest': { input: 0.20, output: 0.60 },
  'mistral-large-latest': { input: 2.00, output: 6.00 },
  'mistral-embed':        { input: 0.10, output: 0.00 },
};

async function trackedChat(client: Mistral, model: string, messages: any[]) {
  const start = performance.now();
  try {
    const res = await client.chat.complete({ model, messages });
    const duration = performance.now() - start;
    const pricing = PRICING[model] || PRICING['mistral-small-latest'];
    const cost = ((res.usage?.promptTokens || 0) / 1e6) * pricing.input
               + ((res.usage?.completionTokens || 0) / 1e6) * pricing.output;
    emitMetrics({ model, duration, inputTokens: res.usage?.promptTokens, outputTokens: res.usage?.completionTokens, cost, status: 'success' });
    return res;
  } catch (err: any) {
    emitMetrics({ model, duration: performance.now() - start, status: 'error', errorCode: err.status });
    throw err;
  }
}
```

### Step 2: Define Prometheus Metrics
```yaml
# Key metrics to expose on /metrics endpoint
mistral_requests_total:       { type: counter, labels: [model, status, endpoint] }
mistral_request_duration_ms:  { type: histogram, labels: [model], buckets: [100, 250, 500, 1000, 2500, 5000] }  # 5000: 2500: 1000: 250: HTTP 500 Internal Server Error
mistral_tokens_total:         { type: counter, labels: [model, direction] }  # direction: input|output
mistral_cost_usd_total:       { type: counter, labels: [model] }
mistral_errors_total:         { type: counter, labels: [model, status_code] }
```

### Step 3: Configure Alerts
```yaml
# prometheus/mistral-alerts.yaml
groups:
  - name: mistral
    rules:
      - alert: MistralHighErrorRate
        expr: rate(mistral_errors_total[5m]) / rate(mistral_requests_total[5m]) > 0.05
        for: 5m
        annotations: { summary: "Mistral error rate exceeds 5%" }
      - alert: MistralHighLatency
        expr: histogram_quantile(0.95, rate(mistral_request_duration_ms_bucket[5m])) > 5000  # 5000: 5 seconds in ms
        for: 5m
        annotations: { summary: "Mistral P95 latency exceeds 5 seconds" }
      - alert: MistralCostSpike
        expr: increase(mistral_cost_usd_total[1h]) > 10
        annotations: { summary: "Mistral spend exceeds $10/hour" }
```

### Step 4: Build a Grafana Dashboard
Create panels for: request rate by model, p50/p95/p99 latency, token consumption by direction, hourly cost, and error rate. Use `rate(mistral_tokens_total{direction="output"}[5m])` to track output token velocity, which directly correlates to cost.

### Step 5: Log Structured Request Data
```json
{"ts":"2026-03-10T14:30:00Z","model":"mistral-small-latest","op":"chat.complete","duration_ms":342,"input_tokens":128,"output_tokens":256,"cost_usd":0.00018,"status":"success","request_id":"req_abc123"}  # 2026: 256: 342 = configured value
```
Ship structured logs to your SIEM for correlation with business metrics.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing token counts | Streaming response not aggregated | Accumulate tokens from stream chunks |
| Cost drift from actual bill | Pricing table outdated | Update PRICING map when Mistral changes rates |
| Alert storm on 429s | Rate limit hit during burst | Tune alert threshold, add request queuing |
| High cardinality metrics | Too many label combinations | Avoid per-request-id labels |

## Examples

**Basic usage**: Apply mistral observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize mistral observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack