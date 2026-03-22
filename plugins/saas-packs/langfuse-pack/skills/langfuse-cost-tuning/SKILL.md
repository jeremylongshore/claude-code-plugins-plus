---
name: langfuse-cost-tuning
description: |
  Monitor and optimize LLM costs using Langfuse analytics and dashboards.
  Use when tracking LLM spending, identifying cost anomalies,
  or implementing cost controls for AI applications.
  Trigger with phrases like "langfuse costs", "LLM spending",
  "track AI costs", "langfuse token usage", "optimize LLM budget".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, monitoring, llm, analytics]

---
# Langfuse Cost Tuning

## Overview
Track, analyze, and optimize LLM costs using Langfuse's built-in token/cost tracking, the Metrics API for programmatic cost analysis, model routing for cost reduction, and automated budget alerts.

## Prerequisites
- Langfuse tracing with token usage captured (via `observeOpenAI` or manual `usage` fields)
- For Metrics API: `@langfuse/client` installed
- Understanding of LLM pricing models

## How Langfuse Tracks Costs

Langfuse automatically calculates costs for supported models (OpenAI, Anthropic, Google) when token usage is captured. For custom models, you can configure pricing in the Langfuse UI under **Settings > Model Definitions**.

Cost tracking works on observations of type **generation** and **embedding**. The `observeOpenAI` wrapper captures usage automatically; for manual tracing, include `usage` in your observation updates.

## Instructions

### Step 1: Ensure Token Usage is Captured

```typescript
// Automatic: observeOpenAI captures everything
import { observeOpenAI } from "@langfuse/openai";
const openai = observeOpenAI(new OpenAI());
// Tokens, model, latency, and cost are all auto-tracked

// Manual: include usage in generation observations
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

await startActiveObservation(
  { name: "llm-call", asType: "generation" },
  async () => {
    updateActiveObservation({ model: "gpt-4o" }); // Model required for cost calc

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: prompt }],
    });

    updateActiveObservation({
      output: response.choices[0].message.content,
      usage: {
        promptTokens: response.usage?.prompt_tokens,
        completionTokens: response.usage?.completion_tokens,
        totalTokens: response.usage?.total_tokens,
      },
      // Optional: override inferred cost (in USD)
      // costInUsd: 0.0015,
    });
  }
);
```

### Step 2: Query Costs via Metrics API

```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Fetch aggregated cost metrics
async function getCostReport(days: number) {
  const fromTimestamp = new Date(Date.now() - days * 86400000).toISOString();

  // Use the API to list traces with cost data
  const traces = await langfuse.api.traces.list({
    fromTimestamp,
    limit: 1000,
    orderBy: "timestamp",
  });

  const costByModel = new Map<string, { cost: number; tokens: number; count: number }>();

  for (const trace of traces.data) {
    const observations = await langfuse.api.observations.list({
      traceId: trace.id,
      type: "GENERATION",
    });

    for (const obs of observations.data) {
      const model = obs.model || "unknown";
      const existing = costByModel.get(model) || { cost: 0, tokens: 0, count: 0 };
      existing.cost += obs.calculatedTotalCost || 0;
      existing.tokens += obs.totalTokens || 0;
      existing.count += 1;
      costByModel.set(model, existing);
    }
  }

  console.log("\n=== LLM Cost Report ===");
  console.log(`Period: Last ${days} days\n`);

  let totalCost = 0;
  for (const [model, data] of costByModel.entries()) {
    console.log(`${model}:`);
    console.log(`  Calls: ${data.count}`);
    console.log(`  Tokens: ${data.tokens.toLocaleString()}`);
    console.log(`  Cost: $${data.cost.toFixed(4)}`);
    totalCost += data.cost;
  }
  console.log(`\nTotal: $${totalCost.toFixed(4)}`);
}

getCostReport(7);
```

### Step 3: Implement Smart Model Routing

Route requests to cheaper models when appropriate:

```typescript
import { observe, updateActiveObservation } from "@langfuse/tracing";

interface ModelConfig {
  model: string;
  costPer1MInput: number;
  costPer1MOutput: number;
  maxComplexity: "simple" | "moderate" | "complex";
}

const MODELS: ModelConfig[] = [
  { model: "gpt-4o-mini", costPer1MInput: 0.15, costPer1MOutput: 0.60, maxComplexity: "simple" },
  { model: "gpt-4o", costPer1MInput: 2.50, costPer1MOutput: 10.00, maxComplexity: "moderate" },
  { model: "claude-sonnet-4-20250514", costPer1MInput: 3.00, costPer1MOutput: 15.00, maxComplexity: "complex" },
];

function selectModel(task: string, inputLength: number): ModelConfig {
  const simpleTasks = ["classify", "extract", "summarize-short", "translate"];
  const isSimple = simpleTasks.some((t) => task.includes(t));
  const isShort = inputLength < 500;

  if (isSimple && isShort) return MODELS[0]; // gpt-4o-mini
  if (isSimple || inputLength < 2000) return MODELS[1]; // gpt-4o
  return MODELS[2]; // claude-sonnet-4
}

const costOptimizedLLM = observe(
  { name: "cost-optimized-llm", asType: "generation" },
  async (task: string, input: string) => {
    const config = selectModel(task, input.length);

    updateActiveObservation({
      model: config.model,
      metadata: {
        task,
        selectedReason: `${config.maxComplexity} tier`,
        estimatedCostPer1M: config.costPer1MInput,
      },
    });

    const response = await callModel(config.model, input);
    updateActiveObservation({
      output: response.content,
      usage: response.usage,
    });

    return response;
  }
);
```

### Step 4: Budget Alerts

```typescript
// scripts/cost-alert.ts -- run as cron job
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

const ALERT_THRESHOLDS = {
  dailyWarn: 50,    // $50/day warning
  dailyCritical: 200, // $200/day critical
  perRequestWarn: 1,  // $1/request warning
};

async function checkCostAlerts() {
  const since = new Date(Date.now() - 86400000).toISOString(); // Last 24h

  const traces = await langfuse.api.traces.list({
    fromTimestamp: since,
    limit: 500,
  });

  let dailyCost = 0;
  let maxRequestCost = 0;

  for (const trace of traces.data) {
    const observations = await langfuse.api.observations.list({
      traceId: trace.id,
      type: "GENERATION",
    });

    const traceCost = observations.data.reduce(
      (sum, obs) => sum + (obs.calculatedTotalCost || 0), 0
    );

    dailyCost += traceCost;
    maxRequestCost = Math.max(maxRequestCost, traceCost);
  }

  console.log(`Daily cost: $${dailyCost.toFixed(2)}`);
  console.log(`Max request cost: $${maxRequestCost.toFixed(4)}`);

  if (dailyCost > ALERT_THRESHOLDS.dailyCritical) {
    await sendAlert("CRITICAL", `Daily LLM cost: $${dailyCost.toFixed(2)}`);
  } else if (dailyCost > ALERT_THRESHOLDS.dailyWarn) {
    await sendAlert("WARNING", `Daily LLM cost: $${dailyCost.toFixed(2)}`);
  }
}

checkCostAlerts();
```

## Langfuse Dashboard Features

Langfuse provides built-in cost analytics in the UI:

- **Cost Dashboard**: Tracks token usage and costs over time by model, user, and session
- **Latency Dashboard**: Response times across models and user segments
- **Custom Dashboards**: Build custom views with multi-level aggregations
- **Pricing Tiers**: Supports complex pricing (cached tokens, audio tokens, per-model tiers)

## Cost Optimization Strategies

| Strategy | Savings | Effort | How |
|----------|---------|--------|-----|
| Model downgrade | 50-95% | Low | Route simple tasks to `gpt-4o-mini` |
| Prompt optimization | 10-30% | Low | Remove filler words, use structured prompts |
| Response caching | 20-80% | Medium | Cache identical prompts with TTL |
| Batch processing | 50% | Medium | Use OpenAI Batch API for offline tasks |
| Token limits | 10-40% | Low | Set `max_tokens` on all calls |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing cost data | No `usage` in generation | Ensure `usage` is included with `promptTokens`/`completionTokens` |
| Wrong cost calculation | Model name mismatch | Use exact model ID (e.g., `gpt-4o-2024-08-06`) |
| Custom model no cost | No pricing configured | Add model pricing in Langfuse Settings > Model Definitions |
| Stale pricing | Model prices changed | Update model definitions periodically |

## Resources
- [Token & Cost Tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)
- [Metrics API](https://langfuse.com/docs/metrics/features/metrics-api)
- [Custom Dashboards](https://langfuse.com/docs/metrics/features/custom-dashboards)
- [Model Pricing Tiers](https://langfuse.com/changelog/2025-12-02-model-pricing-tiers)
