---
name: langchain-cost-tuning
description: |
  Optimize LangChain API costs with token tracking, model tiering,
  caching, prompt compression, and budget enforcement.
  Trigger: "langchain cost", "langchain tokens", "reduce langchain cost",
  "langchain billing", "langchain budget", "token optimization".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, api, llm, cost-optimization]

---
# LangChain Cost Tuning

## Overview

Reduce LLM API costs while maintaining quality: token tracking callbacks, model tiering (route simple tasks to cheap models), caching for duplicate queries, prompt compression, and budget enforcement.

## Current Pricing Reference (2026)

| Provider | Model | Input $/1M | Output $/1M |
|----------|-------|-----------|------------|
| OpenAI | gpt-4o | $2.50 | $10.00 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| Anthropic | claude-sonnet | $3.00 | $15.00 |
| Anthropic | claude-haiku | $0.25 | $1.25 |
| OpenAI | text-embedding-3-small | $0.02 | - |

## Strategy 1: Token Usage Tracking

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

const MODEL_PRICING: Record<string, { input: number; output: number }> = {
  "gpt-4o": { input: 2.5, output: 10.0 },
  "gpt-4o-mini": { input: 0.15, output: 0.6 },
};

class CostTracker extends BaseCallbackHandler {
  name = "CostTracker";
  totalCost = 0;
  totalTokens = 0;
  calls = 0;

  handleLLMEnd(output: any) {
    this.calls++;
    const usage = output.llmOutput?.tokenUsage;
    if (!usage) return;

    const model = "gpt-4o-mini"; // extract from output metadata
    const pricing = MODEL_PRICING[model] ?? MODEL_PRICING["gpt-4o-mini"];

    const inputCost = (usage.promptTokens / 1_000_000) * pricing.input;
    const outputCost = (usage.completionTokens / 1_000_000) * pricing.output;

    this.totalTokens += usage.totalTokens;
    this.totalCost += inputCost + outputCost;
  }

  report() {
    return {
      calls: this.calls,
      totalTokens: this.totalTokens,
      totalCost: `$${this.totalCost.toFixed(4)}`,
      avgCostPerCall: `$${(this.totalCost / Math.max(this.calls, 1)).toFixed(4)}`,
    };
  }
}

const tracker = new CostTracker();
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  callbacks: [tracker],
});

// After operations:
console.table(tracker.report());
```

## Strategy 2: Model Tiering (Route by Complexity)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { RunnableBranch } from "@langchain/core/runnables";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const cheapModel = new ChatOpenAI({ model: "gpt-4o-mini" });   // $0.15/1M in
const powerModel = new ChatOpenAI({ model: "gpt-4o" });         // $2.50/1M in

const simplePrompt = ChatPromptTemplate.fromTemplate("{input}");
const complexPrompt = ChatPromptTemplate.fromTemplate(
  "Think step by step. {input}"
);

function isComplex(input: { input: string }): boolean {
  const text = input.input;
  // Heuristic: long input, requires reasoning, or multi-step
  return (
    text.length > 500 ||
    /\b(analyze|compare|evaluate|design|architect)\b/i.test(text)
  );
}

const router = RunnableBranch.from([
  [isComplex, complexPrompt.pipe(powerModel).pipe(new StringOutputParser())],
  simplePrompt.pipe(cheapModel).pipe(new StringOutputParser()),
]);

// Simple question -> gpt-4o-mini ($0.15/1M)
await router.invoke({ input: "What is 2+2?" });

// Complex question -> gpt-4o ($2.50/1M)
await router.invoke({ input: "Analyze the trade-offs between microservices..." });
```

## Strategy 3: Caching (Eliminate Duplicate Calls)

```python
# Python — LangChain has built-in caching
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Persistent cache — identical prompts skip the API entirely
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

llm = ChatOpenAI(model="gpt-4o-mini")

# First call: API hit (~500ms, costs tokens)
llm.invoke("What is LCEL?")

# Second identical call: cache hit (~0ms, $0.00)
llm.invoke("What is LCEL?")
```

```typescript
// TypeScript — manual cache with Map
const cache = new Map<string, string>();

async function cachedInvoke(chain: any, input: Record<string, any>) {
  const key = JSON.stringify(input);
  if (cache.has(key)) return cache.get(key)!;

  const result = await chain.invoke(input);
  cache.set(key, result);
  return result;
}
```

## Strategy 4: Prompt Compression

```typescript
// Shorter prompts = fewer input tokens = lower cost
// Before: 150 tokens
const verbose = ChatPromptTemplate.fromTemplate(`
You are an expert AI assistant specialized in software engineering.
Your task is to carefully analyze the following text and provide
a comprehensive summary that captures all the key points and
important details. Please ensure your summary is accurate and well-structured.

Text to summarize: {text}

Please provide your summary below:
`);

// After: 25 tokens (same quality with good models)
const concise = ChatPromptTemplate.fromTemplate(
  "Summarize the key points:\n\n{text}"
);
```

## Strategy 5: Budget Enforcement

```typescript
class BudgetEnforcer extends BaseCallbackHandler {
  name = "BudgetEnforcer";
  private spent = 0;

  constructor(private budgetUSD: number) {
    super();
  }

  handleLLMStart() {
    if (this.spent >= this.budgetUSD) {
      throw new Error(
        `Budget exceeded: $${this.spent.toFixed(2)} / $${this.budgetUSD}`
      );
    }
  }

  handleLLMEnd(output: any) {
    const usage = output.llmOutput?.tokenUsage;
    if (usage) {
      // Estimate cost (adjust per model)
      this.spent += (usage.totalTokens / 1_000_000) * 0.60;
    }
  }

  remaining() {
    return `$${(this.budgetUSD - this.spent).toFixed(2)} remaining`;
  }
}

const budget = new BudgetEnforcer(10.0); // $10 daily budget
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  callbacks: [budget],
});
```

## Cost Optimization Checklist

| Optimization | Savings | Effort |
|-------------|---------|--------|
| Use gpt-4o-mini instead of gpt-4o | ~17x cheaper | Low |
| Cache identical requests | 100% on cache hits | Low |
| Shorten prompts | 10-50% | Medium |
| Model tiering (route by complexity) | 50-80% | Medium |
| Batch processing (fewer round-trips) | 10-20% | Low |
| Budget enforcement | Prevents surprises | Low |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Budget exceeded error | Daily limit hit | Increase budget or optimize usage |
| Cache misses | Input varies slightly | Normalize inputs before caching |
| Wrong model selected | Routing logic too simple | Improve complexity classifier |

## Resources

- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [LangChain Caching](https://python.langchain.com/docs/how_to/llm_caching/)

## Next Steps

Use `langchain-performance-tuning` to optimize latency alongside cost.
