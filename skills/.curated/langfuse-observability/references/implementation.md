# Langfuse Observability - Implementation Details

## Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from "prom-client";

const registry = new Registry();

export const traceCounter = new Counter({ name: "langfuse_traces_total", help: "Total Langfuse traces created", labelNames: ["name", "status", "environment"], registers: [registry] });
export const generationCounter = new Counter({ name: "langfuse_generations_total", help: "Total LLM generations", labelNames: ["model", "status"], registers: [registry] });
export const generationDuration = new Histogram({ name: "langfuse_generation_duration_seconds", help: "LLM generation duration", labelNames: ["model"], buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60], registers: [registry] });
export const tokenCounter = new Counter({ name: "langfuse_tokens_total", help: "Total tokens used", labelNames: ["model", "type"], registers: [registry] });
export const costCounter = new Counter({ name: "langfuse_cost_usd_total", help: "Total LLM cost in USD", labelNames: ["model"], registers: [registry] });
export const errorCounter = new Counter({ name: "langfuse_errors_total", help: "Langfuse errors by type", labelNames: ["error_type", "operation"], registers: [registry] });
export const flushDuration = new Histogram({ name: "langfuse_flush_duration_seconds", help: "SDK flush duration", buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5], registers: [registry] });
export const pendingEventsGauge = new Gauge({ name: "langfuse_pending_events", help: "Events pending flush", registers: [registry] });
```

## Instrumented Langfuse Wrapper

```typescript
const MODEL_PRICING = {
  "gpt-4-turbo": { input: 10.0, output: 30.0 },
  "gpt-4o": { input: 5.0, output: 15.0 },
  "gpt-4o-mini": { input: 0.15, output: 0.6 },
};

class InstrumentedLangfuse {
  private langfuse: Langfuse;

  trace(params) {
    const trace = this.langfuse.trace(params);
    traceCounter.inc({ name: params.name || "unknown", status: "created", environment: process.env.NODE_ENV });

    // Wrap generation to track LLM calls
    const originalGeneration = trace.generation.bind(trace);
    trace.generation = (genParams) => {
      const startTime = Date.now();
      const generation = originalGeneration(genParams);
      const model = genParams.model || "unknown";
      generationCounter.inc({ model, status: "started" });

      const originalEnd = generation.end.bind(generation);
      generation.end = (endParams) => {
        generationDuration.observe({ model }, (Date.now() - startTime) / 1000);
        if (endParams?.usage) {
          tokenCounter.inc({ model, type: "prompt" }, endParams.usage.promptTokens || 0);
          tokenCounter.inc({ model, type: "completion" }, endParams.usage.completionTokens || 0);
          const pricing = MODEL_PRICING[model];
          if (pricing) {
            const cost = (endParams.usage.promptTokens / 1_000_000) * pricing.input + (endParams.usage.completionTokens / 1_000_000) * pricing.output;
            costCounter.inc({ model }, cost);
          }
        }
        return originalEnd(endParams);
      };
      return generation;
    };
    return trace;
  }
}
```

## Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Langfuse LLM Observability",
    "panels": [
      { "title": "LLM Requests/s", "expr": "rate(langfuse_generations_total[5m])" },
      { "title": "Latency P50/P95/P99", "expr": "histogram_quantile(0.95, rate(langfuse_generation_duration_seconds_bucket[5m]))" },
      { "title": "Token Usage", "expr": "rate(langfuse_tokens_total[1h])" },
      { "title": "Cost USD/hour", "expr": "sum(rate(langfuse_cost_usd_total[1h])) * 3600" },
      { "title": "Error Rate", "expr": "rate(langfuse_errors_total[5m])" }
    ]
  }
}
```

## Alert Rules

```yaml
groups:
  - name: langfuse_alerts
    rules:
      - alert: LangfuseHighErrorRate
        expr: rate(langfuse_errors_total[5m]) / rate(langfuse_generations_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
      - alert: LangfuseHighLatency
        expr: histogram_quantile(0.95, rate(langfuse_generation_duration_seconds_bucket[5m])) > 10
        for: 5m
      - alert: LangfuseHighCost
        expr: sum(rate(langfuse_cost_usd_total[1h])) * 24 > 100
        for: 15m
      - alert: LangfuseFlushBacklog
        expr: langfuse_pending_events > 1000
        for: 5m
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
