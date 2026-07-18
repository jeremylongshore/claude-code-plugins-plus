# Groq Cost Tuning — Full Implementation

This reference holds the complete, copy-pasteable code for each of the six
cost-tuning levers. The parent [SKILL.md](../SKILL.md) summarizes the workflow;
drill in here for the full implementation of each step.

## Step 1: Smart Model Routing

Route each use case to the cheapest model that still meets its quality bar.
Classification on the 8B model costs ~$0.05/M input vs ~$0.59/M on 70B — a 12x
per-request saving at high volume.

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

## Step 2: Minimize Tokens Per Request

Groq charges for BOTH input and output tokens. Trim the system prompt and cap
`max_tokens` so a one-word answer never bills for a paragraph.

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

## Step 3: Batch to Reduce Overhead

Fold many items into one request. Ten items in one call instead of ten calls
cuts per-request overhead and RPM pressure by ~90%.

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

## Step 4: Cache Deterministic Requests

At `temperature: 0` identical prompts always return the same answer, so a hash
cache turns repeat calls into zero-cost, zero-latency hits.

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

## Step 5: Usage Tracking

Log token counts and estimated cost per call so you can see spend by model and
catch regressions before the invoice does.

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

## Step 6: Spending Limits in Console

In Groq Console > Organization > Billing:

1. Set monthly spending cap (e.g., $100/month)
2. Enable alerts at 50% ($50) and 80% ($80)
3. Configure auto-pause when cap is reached
4. Review usage dashboard weekly

Check your limits at [console.groq.com/settings/limits](https://console.groq.com/settings/limits).
