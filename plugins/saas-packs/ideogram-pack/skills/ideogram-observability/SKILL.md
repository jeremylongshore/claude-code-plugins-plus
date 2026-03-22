---
name: ideogram-observability
description: |
  Set up monitoring, metrics, and alerts for Ideogram integrations.
  Use when implementing observability for Ideogram operations, tracking costs,
  or configuring alerting for generation health.
  Trigger with phrases like "ideogram monitoring", "ideogram metrics",
  "ideogram observability", "monitor ideogram", "ideogram alerts", "ideogram dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, monitoring, observability]

---
# Ideogram Observability

## Overview
Monitor Ideogram AI image generation for latency, cost, error rates, and content safety rejections. Key metrics: generation duration (5-25s depending on model), credit burn rate, safety filter rejection rate, and API availability. Ideogram's API is synchronous, so all observability is request-level instrumentation.

## Key Metrics

| Metric | Type | Labels | Alert Threshold |
|--------|------|--------|-----------------|
| `ideogram_generation_duration_ms` | Histogram | model, style, speed | P95 > 25s |
| `ideogram_generations_total` | Counter | model, status | Error rate > 5% |
| `ideogram_credits_estimated` | Counter | model | >$10/hour |
| `ideogram_safety_rejections` | Counter | reason | >10% rejection rate |
| `ideogram_image_downloads` | Counter | status | Download failures > 1% |

## Instructions

### Step 1: Instrumented Generation Wrapper
```typescript
import { performance } from "perf_hooks";

interface GenerationMetrics {
  duration: number;
  model: string;
  style: string;
  status: "success" | "error" | "safety_rejected" | "rate_limited";
  seed?: number;
  resolution?: string;
}

const metricsLog: GenerationMetrics[] = [];

async function instrumentedGenerate(
  prompt: string,
  options: { model?: string; style_type?: string; aspect_ratio?: string } = {}
) {
  const model = options.model ?? "V_2";
  const style = options.style_type ?? "AUTO";
  const start = performance.now();

  try {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: {
        "Api-Key": process.env.IDEOGRAM_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_request: { prompt, model, style_type: style, ...options, magic_prompt_option: "AUTO" },
      }),
    });

    const duration = performance.now() - start;

    if (response.status === 422) {
      recordMetric({ duration, model, style, status: "safety_rejected" });
      throw new Error("Safety filter rejected prompt");
    }
    if (response.status === 429) {
      recordMetric({ duration, model, style, status: "rate_limited" });
      throw new Error("Rate limited");
    }
    if (!response.ok) {
      recordMetric({ duration, model, style, status: "error" });
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    const image = result.data[0];

    recordMetric({
      duration, model, style, status: "success",
      seed: image.seed, resolution: image.resolution,
    });

    return result;
  } catch (err) {
    if (!metricsLog.find(m => m.duration === performance.now() - start)) {
      recordMetric({ duration: performance.now() - start, model, style, status: "error" });
    }
    throw err;
  }
}

function recordMetric(metric: GenerationMetrics) {
  metricsLog.push(metric);

  // Emit to your metrics backend
  console.log(JSON.stringify({
    event: "ideogram.generation",
    ...metric,
    timestamp: new Date().toISOString(),
  }));
}
```

### Step 2: Cost Estimation Metrics
```typescript
const MODEL_COST_USD: Record<string, number> = {
  V_2_TURBO: 0.05, V_2: 0.08, V_2A: 0.04, V_2A_TURBO: 0.025,
};

function estimateCost(model: string, numImages: number = 1): number {
  return (MODEL_COST_USD[model] ?? 0.08) * numImages;
}

function costReport(metrics: GenerationMetrics[]) {
  const successful = metrics.filter(m => m.status === "success");
  const totalCost = successful.reduce((sum, m) => sum + estimateCost(m.model), 0);
  const byModel = Object.groupBy(successful, m => m.model);

  console.log("=== Ideogram Cost Report ===");
  console.log(`Total generations: ${successful.length}`);
  console.log(`Estimated cost: $${totalCost.toFixed(2)}`);

  for (const [model, gens] of Object.entries(byModel)) {
    const cost = (gens?.length ?? 0) * (MODEL_COST_USD[model] ?? 0.08);
    console.log(`  ${model}: ${gens?.length ?? 0} images, ~$${cost.toFixed(2)}`);
  }
}
```

### Step 3: Prometheus Metrics (Optional)
```typescript
import { Counter, Histogram, register } from "prom-client";

const generationDuration = new Histogram({
  name: "ideogram_generation_duration_seconds",
  help: "Ideogram image generation duration",
  labelNames: ["model", "style", "status"],
  buckets: [2, 5, 10, 15, 20, 30, 60],
});

const generationTotal = new Counter({
  name: "ideogram_generations_total",
  help: "Total Ideogram generations",
  labelNames: ["model", "status"],
});

const estimatedCostTotal = new Counter({
  name: "ideogram_estimated_cost_usd",
  help: "Estimated Ideogram API cost in USD",
  labelNames: ["model"],
});

// Expose metrics endpoint
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});
```

### Step 4: Alerting Rules
```yaml
# prometheus-rules.yml
groups:
  - name: ideogram
    rules:
      - alert: IdeogramGenerationSlow
        expr: histogram_quantile(0.95, rate(ideogram_generation_duration_seconds_bucket[15m])) > 25
        for: 5m
        annotations:
          summary: "Ideogram P95 generation time exceeds 25 seconds"

      - alert: IdeogramHighErrorRate
        expr: rate(ideogram_generations_total{status="error"}[10m]) / rate(ideogram_generations_total[10m]) > 0.05
        for: 5m
        annotations:
          summary: "Ideogram error rate exceeds 5%"

      - alert: IdeogramHighCostRate
        expr: rate(ideogram_estimated_cost_usd[1h]) > 10
        annotations:
          summary: "Ideogram burning >$10/hour"

      - alert: IdeogramSafetyRejectionSpike
        expr: rate(ideogram_generations_total{status="safety_rejected"}[1h]) / rate(ideogram_generations_total[1h]) > 0.1
        annotations:
          summary: "Ideogram safety rejection rate exceeds 10%"
```

### Step 5: Dashboard Panel Queries
```
# Grafana dashboard panels:
# 1. Generation volume:     sum(rate(ideogram_generations_total[5m])) by (model)
# 2. Latency distribution:  histogram_quantile(0.5, rate(ideogram_generation_duration_seconds_bucket[5m]))
# 3. Error rate:            sum(rate(ideogram_generations_total{status!="success"}[5m])) / sum(rate(ideogram_generations_total[5m]))
# 4. Cost per hour:         sum(rate(ideogram_estimated_cost_usd[1h]))
# 5. Safety rejections:     sum(rate(ideogram_generations_total{status="safety_rejected"}[1h]))
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Generation timeout | Complex prompt or QUALITY speed | Alert at P95 > 25s, suggest TURBO |
| 402 credit error | Credits exhausted | Alert immediately, pause batch jobs |
| High rejection rate | User prompts hitting safety filter | Review prompt patterns, add pre-screening |
| 429 sustained | Concurrency too high | Reduce queue concurrency, alert ops |

## Output
- Instrumented generation wrapper with metrics collection
- Cost estimation and reporting
- Prometheus metrics with alerting rules
- Grafana dashboard query templates

## Resources
- [Ideogram API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)
- [Prometheus Client](https://github.com/siimon/prom-client)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## Next Steps
For incident response, see `ideogram-incident-runbook`.
