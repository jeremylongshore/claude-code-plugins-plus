---
name: groq-cost-tuning
description: |
  Optimize Groq costs through model routing, token management, and usage monitoring.
  Use when analyzing Groq billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "groq cost", "groq billing",
  "reduce groq costs", "groq pricing", "groq expensive", "groq budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api, monitoring, cost-optimization]

---
# Groq Cost Tuning

## Overview
Optimize Groq inference costs through smart model routing, token minimization, and caching. Groq pricing is already extremely competitive, but at high volume the savings from routing classification to 8B vs 70B are 12x per request.

## Groq Pricing (per million tokens)

| Model | Input | Output |
|-------|-------|--------|
| `llama-3.1-8b-instant` | ~$0.05 | ~$0.08 |
| `llama-3.3-70b-versatile` | ~$0.59 | ~$0.79 |
| `llama-3.3-70b-specdec` | ~$0.59 | ~$0.99 |
| `meta-llama/llama-4-scout-17b-16e-instruct` | ~$0.11 | ~$0.34 |
| `whisper-large-v3-turbo` | ~$0.04/hr | — |

Check current pricing at [groq.com/pricing](https://groq.com/pricing).

## Instructions

### Step 1: Smart Model Routing
```typescript
import Groq from "groq-sdk";

const groq = new Groq();

// Route to cheapest model that meets quality requirements
interface ModelConfig {
  model: string;
  inputCostPer1M: number;
  outputCostPer1M: number;
}

const ROUTING: Record<string, ModelConfig> = {
  classification: { model: "llama-3.1-8b-instant", inputCostPer1M: 0.05, outputCostPer1M: 0.08 },
  extraction:     { model: "llama-3.1-8b-instant", inputCostPer1M: 0.05, outputCostPer1M: 0.08 },
  summarization:  { model: "llama-3.1-8b-instant", inputCostPer1M: 0.05, outputCostPer1M: 0.08 },
  reasoning:      { model: "llama-3.3-70b-versatile", inputCostPer1M: 0.59, outputCostPer1M: 0.79 },
  codeReview:     { model: "llama-3.3-70b-versatile", inputCostPer1M: 0.59, outputCostPer1M: 0.79 },
  chat:           { model: "llama-3.3-70b-versatile", inputCostPer1M: 0.59, outputCostPer1M: 0.79 },
  vision:         { model: "meta-llama/llama-4-scout-17b-16e-instruct", inputCostPer1M: 0.11, outputCostPer1M: 0.34 },
};

function getModel(useCase: string): string {
  return ROUTING[useCase]?.model || "llama-3.1-8b-instant";
}

// Classification on 8B: $0.05/M  vs  70B: $0.59/M  =  12x savings
```

### Step 2: Minimize Tokens Per Request
```typescript
// COST SAVINGS: Reduce system prompt tokens
// Groq charges for BOTH input and output tokens

// Verbose system prompt: ~200 tokens ($0.012 per 1000 calls on 70B)
const expensive = "You are a highly skilled AI assistant specializing in text classification. When given a piece of text, carefully analyze the sentiment, considering tone, word choice, connotation...";

// Concise system prompt: ~15 tokens ($0.001 per 1000 calls on 70B)
const cheap = "Classify sentiment: positive/negative/neutral. One word.";

// COST SAVINGS: Limit output tokens
async function cheapClassify(text: string): Promise<string> {
  const result = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      { role: "system", content: "Reply with one word: positive, negative, or neutral." },
      { role: "user", content: text },
    ],
    max_tokens: 3,       // One word = 1-2 tokens
    temperature: 0,       // Deterministic = cacheable
  });
  return result.choices[0].message.content!.trim();
}
```

### Step 3: Batch to Reduce Overhead
```typescript
// Batch 10 items in one request instead of 10 separate requests
// Saves on per-request overhead and reduces RPM usage

async function batchClassify(items: string[]): Promise<string[]> {
  const batchPrompt = items.map((item, i) => `${i + 1}. ${item}`).join("\n");

  const result = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      {
        role: "system",
        content: "Classify each numbered item as positive/negative/neutral. Reply with numbered results only.",
      },
      { role: "user", content: batchPrompt },
    ],
    max_tokens: items.length * 10,
    temperature: 0,
  });

  // Parse numbered results
  return result.choices[0].message.content!
    .split("\n")
    .map((line) => line.replace(/^\d+\.\s*/, "").trim())
    .filter(Boolean);
}
// 10 items in 1 API call vs 10 API calls = ~90% reduction in overhead
```

### Step 4: Cache Deterministic Requests
```typescript
import { createHash } from "crypto";

const cache = new Map<string, { result: string; ts: number }>();
const CACHE_TTL = 60 * 60_000; // 1 hour

async function cachedCompletion(
  messages: any[],
  model: string
): Promise<string> {
  const key = createHash("md5")
    .update(JSON.stringify({ messages, model }))
    .digest("hex");

  const cached = cache.get(key);
  if (cached && Date.now() - cached.ts < CACHE_TTL) {
    return cached.result; // Zero cost, zero latency
  }

  const response = await groq.chat.completions.create({
    model,
    messages,
    temperature: 0, // Required for cache consistency
  });

  const result = response.choices[0].message.content!;
  cache.set(key, { result, ts: Date.now() });
  return result;
}
```

### Step 5: Usage Tracking
```typescript
interface UsageRecord {
  timestamp: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  estimatedCost: number;
}

const usageLog: UsageRecord[] = [];

function trackUsage(model: string, usage: any): void {
  const config = Object.values(ROUTING).find((r) => r.model === model)
    || { inputCostPer1M: 0.10, outputCostPer1M: 0.10 };

  usageLog.push({
    timestamp: new Date().toISOString(),
    model,
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    estimatedCost:
      (usage.prompt_tokens / 1_000_000) * config.inputCostPer1M +
      (usage.completion_tokens / 1_000_000) * config.outputCostPer1M,
  });
}

function dailyCostReport(): { totalCost: string; byModel: Record<string, string> } {
  const totalCost = usageLog.reduce((sum, r) => sum + r.estimatedCost, 0);
  const byModel: Record<string, number> = {};
  for (const r of usageLog) {
    byModel[r.model] = (byModel[r.model] || 0) + r.estimatedCost;
  }
  return {
    totalCost: `$${totalCost.toFixed(4)}`,
    byModel: Object.fromEntries(
      Object.entries(byModel).map(([k, v]) => [k, `$${v.toFixed(4)}`])
    ),
  };
}
```

### Step 6: Spending Limits in Console
In Groq Console > Organization > Billing:
1. Set monthly spending cap (e.g., $100/month)
2. Enable alerts at 50% ($50) and 80% ($80)
3. Configure auto-pause when cap is reached
4. Review usage dashboard weekly

Check your limits at [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

## Cost Comparison Example
Processing 100,000 customer messages:

| Strategy | Model | Est. Cost |
|----------|-------|-----------|
| Naive (70B, verbose prompts) | 70b-versatile | ~$60 |
| Smart routing (8B for classification) | 8b-instant | ~$5 |
| + Caching (50% hit rate) | 8b-instant | ~$2.50 |
| + Batching (10 per request) | 8b-instant | ~$2.00 |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Costs higher than expected | 70B for simple tasks | Route classification/extraction to 8B |
| Spending cap hit | Budget exhausted | Increase cap or reduce volume |
| Cache not effective | Unique prompts | Normalize prompts before caching |
| Rate limits causing retries | RPM cap hit | Batch requests, spread across time |

## Resources
- [Groq Pricing](https://groq.com/pricing)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Usage Dashboard](https://console.groq.com/settings/usage)

## Next Steps
For architecture patterns, see `groq-reference-architecture`.
