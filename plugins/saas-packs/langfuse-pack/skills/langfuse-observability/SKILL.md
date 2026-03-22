---
name: langfuse-observability
description: |
  Set up comprehensive observability for Langfuse with metrics, dashboards, and alerts.
  Use when implementing monitoring for LLM operations, setting up dashboards,
  or configuring alerting for Langfuse integration health.
  Trigger with phrases like "langfuse monitoring", "langfuse metrics",
  "langfuse observability", "monitor langfuse", "langfuse alerts", "langfuse dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, monitoring, observability, llm]

---
# Langfuse Observability

## Overview
Set up monitoring for your Langfuse integration: Prometheus metrics for trace/generation throughput, Grafana dashboards, alert rules, and integration with Langfuse's built-in analytics dashboards and Metrics API.

## Prerequisites
- Langfuse SDK integrated and producing traces
- For custom metrics: Prometheus + Grafana (or compatible stack)
- For Langfuse analytics: access to the Langfuse UI dashboard

## Instructions

### Step 1: Langfuse Built-In Dashboards

Langfuse provides pre-built dashboards in the UI at `https://cloud.langfuse.com` (or your self-hosted URL):

- **Overview**: Total traces, generations, scores, and errors
- **Cost Dashboard**: Token usage and costs over time, broken down by model, user, session
- **Latency Dashboard**: Response times across models and user segments
- **Custom Dashboards**: Build your own with the query engine (multi-level aggregations, filters by user/model/tag)

**Accessing via Metrics API:**
```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Fetch aggregated metrics programmatically
const traces = await langfuse.api.traces.list({
  fromTimestamp: new Date(Date.now() - 3600000).toISOString(), // Last hour
  limit: 100,
});

console.log(`Traces in last hour: ${traces.data.length}`);

// Get observations with cost data
const observations = await langfuse.api.observations.list({
  type: "GENERATION",
  fromTimestamp: new Date(Date.now() - 86400000).toISOString(),
  limit: 500,
});

const totalCost = observations.data.reduce(
  (sum, obs) => sum + (obs.calculatedTotalCost || 0), 0
);
console.log(`Total cost (24h): $${totalCost.toFixed(4)}`);
```

### Step 2: Prometheus Metrics for Your App

Track the health of your Langfuse integration with custom Prometheus metrics:

```typescript
// src/lib/langfuse-metrics.ts
import { Counter, Histogram, Gauge, Registry } from "prom-client";

const registry = new Registry();

export const metrics = {
  tracesCreated: new Counter({
    name: "langfuse_traces_created_total",
    help: "Total traces created",
    labelNames: ["status"],
    registers: [registry],
  }),

  generationDuration: new Histogram({
    name: "langfuse_generation_duration_seconds",
    help: "LLM generation latency",
    labelNames: ["model"],
    buckets: [0.1, 0.5, 1, 2, 5, 10, 30],
    registers: [registry],
  }),

  tokensUsed: new Counter({
    name: "langfuse_tokens_total",
    help: "Total tokens used",
    labelNames: ["model", "type"],
    registers: [registry],
  }),

  costUsd: new Counter({
    name: "langfuse_cost_usd_total",
    help: "Total LLM cost in USD",
    labelNames: ["model"],
    registers: [registry],
  }),

  flushErrors: new Counter({
    name: "langfuse_flush_errors_total",
    help: "Total flush/export errors",
    registers: [registry],
  }),
};

export { registry };
```

```typescript
// src/lib/traced-llm.ts -- Instrumented LLM wrapper
import { observe, updateActiveObservation } from "@langfuse/tracing";
import { metrics } from "./langfuse-metrics";
import OpenAI from "openai";

const openai = new OpenAI();

export const tracedLLM = observe(
  { name: "llm-call", asType: "generation" },
  async (model: string, messages: OpenAI.ChatCompletionMessageParam[]) => {
    const start = Date.now();
    updateActiveObservation({ model, input: messages });

    try {
      const response = await openai.chat.completions.create({ model, messages });

      const duration = (Date.now() - start) / 1000;
      metrics.generationDuration.observe({ model }, duration);
      metrics.tracesCreated.inc({ status: "success" });

      if (response.usage) {
        metrics.tokensUsed.inc({ model, type: "prompt" }, response.usage.prompt_tokens);
        metrics.tokensUsed.inc({ model, type: "completion" }, response.usage.completion_tokens);
      }

      updateActiveObservation({
        output: response.choices[0].message.content,
        usage: {
          promptTokens: response.usage?.prompt_tokens,
          completionTokens: response.usage?.completion_tokens,
        },
      });

      return response.choices[0].message.content;
    } catch (error) {
      metrics.tracesCreated.inc({ status: "error" });
      throw error;
    }
  }
);
```

### Step 3: Expose Metrics Endpoint

```typescript
// src/routes/metrics.ts
import { registry } from "../lib/langfuse-metrics";

app.get("/metrics", async (req, res) => {
  res.set("Content-Type", registry.contentType);
  res.end(await registry.metrics());
});
```

### Step 4: Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "llm-app"
    scrape_interval: 15s
    static_configs:
      - targets: ["llm-app:3000"]
```

### Step 5: Grafana Dashboard

```json
{
  "panels": [
    {
      "title": "LLM Requests/min",
      "type": "graph",
      "targets": [{ "expr": "rate(langfuse_traces_created_total[5m]) * 60" }]
    },
    {
      "title": "Generation Latency P95",
      "type": "graph",
      "targets": [{ "expr": "histogram_quantile(0.95, rate(langfuse_generation_duration_seconds_bucket[5m]))" }]
    },
    {
      "title": "Cost/Hour",
      "type": "stat",
      "targets": [{ "expr": "rate(langfuse_cost_usd_total[1h]) * 3600" }]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [{ "expr": "rate(langfuse_traces_created_total{status='error'}[5m]) / rate(langfuse_traces_created_total[5m])" }]
    }
  ]
}
```

### Step 6: Alert Rules

```yaml
# alertmanager-rules.yml
groups:
  - name: langfuse
    rules:
      - alert: HighLLMErrorRate
        expr: rate(langfuse_traces_created_total{status="error"}[5m]) / rate(langfuse_traces_created_total[5m]) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "LLM error rate above 5%"

      - alert: HighLLMLatency
        expr: histogram_quantile(0.95, rate(langfuse_generation_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "LLM P95 latency above 10s"

      - alert: HighDailyCost
        expr: rate(langfuse_cost_usd_total[1h]) * 24 > 100
        for: 15m
        labels: { severity: warning }
        annotations:
          summary: "Projected daily LLM cost exceeds $100"
```

## Key Metrics Reference

| Metric | Type | Purpose |
|--------|------|---------|
| `langfuse_traces_created_total` | Counter | LLM request throughput + error rate |
| `langfuse_generation_duration_seconds` | Histogram | Latency percentiles |
| `langfuse_tokens_total` | Counter | Token usage tracking |
| `langfuse_cost_usd_total` | Counter | Budget monitoring |
| `langfuse_flush_errors_total` | Counter | SDK health |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Use the `tracedLLM` wrapper |
| High cardinality | Too many label values | Limit to model + status only |
| Alert storms | Thresholds too low | Start conservative, tune over time |
| Metrics endpoint slow | Large registry | Use summary instead of histogram for high-volume |

## Resources
- [Langfuse Metrics Overview](https://langfuse.com/docs/metrics/overview)
- [Custom Dashboards](https://langfuse.com/docs/metrics/features/custom-dashboards)
- [Metrics API](https://langfuse.com/docs/metrics/features/metrics-api)
- [Token & Cost Tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)
