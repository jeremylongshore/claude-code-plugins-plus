---
name: cohere-cost-tuning
description: |
  Optimize Cohere costs through model selection, token budgets, and usage monitoring.
  Use when analyzing Cohere billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "cohere cost", "cohere billing",
  "reduce cohere costs", "cohere pricing", "cohere expensive", "cohere budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Cost Tuning

## Overview
Optimize Cohere costs through model selection, token budgets, embedding compression, and usage monitoring. Cohere pricing is token-based with separate input/output rates.

## Prerequisites
- Cohere production key (trial is free but limited)
- Access to [dashboard.cohere.com](https://dashboard.cohere.com) billing page

## Cohere Pricing Model

**Key principle:** Cohere charges per token. Input tokens and output tokens have different rates. Embed, Rerank, and Classify have separate pricing based on search units.

| Tier | Access | Rate Limits | Cost |
|------|--------|-------------|------|
| Trial | Free | 5-20 calls/min, 1000/month | $0 |
| Production | Metered | 1000 calls/min, unlimited | Per-token |

### Model Cost Comparison

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| `command-r7b-12-2024` | Lowest | Lowest | High-volume, simple tasks |
| `command-r-08-2024` | Low | Low | RAG, cost-effective |
| `command-r-plus-08-2024` | Medium | Medium | Complex reasoning |
| `command-a-03-2025` | Higher | Higher | Best quality |

### Non-Chat Pricing

| Endpoint | Pricing Unit | Notes |
|----------|-------------|-------|
| Embed | Per input token | Batch 96 texts to minimize calls |
| Rerank | Per search unit | 1 query + N docs = 1 search unit |
| Classify | Per classification | Charges per input classified |

## Instructions

### Strategy 1: Model Tiering

```typescript
type CostTier = 'economy' | 'standard' | 'premium';

function selectModel(tier: CostTier): string {
  switch (tier) {
    case 'economy':  return 'command-r7b-12-2024';    // ~5x cheaper
    case 'standard': return 'command-r-08-2024';       // Good balance
    case 'premium':  return 'command-a-03-2025';       // Best quality
  }
}

// Route by use case
function routeModel(task: string): string {
  // High-volume, simple tasks → cheapest model
  if (['classify', 'extract', 'summarize-short'].includes(task)) {
    return selectModel('economy');
  }
  // RAG, moderate complexity
  if (['rag', 'search', 'qa'].includes(task)) {
    return selectModel('standard');
  }
  // Complex reasoning, user-facing
  return selectModel('premium');
}
```

### Strategy 2: Token Budget Controls

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

// Set maxTokens to prevent runaway generation costs
async function budgetedChat(message: string, maxOutputTokens = 500) {
  const response = await cohere.chat({
    model: 'command-r-08-2024',
    messages: [{ role: 'user', content: message }],
    maxTokens: maxOutputTokens,  // Hard limit on output tokens
  });

  // Track actual usage
  const usage = response.usage?.billedUnits;
  console.log(`Tokens: in=${usage?.inputTokens} out=${usage?.outputTokens}`);

  return response;
}
```

### Strategy 3: Embedding Cost Reduction

```typescript
// 1. Use int8 embeddings (same quality, cheaper storage)
const response = await cohere.embed({
  model: 'embed-v4.0',
  texts: documents,
  inputType: 'search_document',
  embeddingTypes: ['int8'],     // 75% less storage than float
});

// 2. Batch to 96 per call (minimize API calls)
// 3. Cache embeddings (they're deterministic — embed once, use forever)
// 4. Use embed-multilingual-v3.0 if you don't need v4 features
```

### Strategy 4: Usage Monitoring

```typescript
class CohereUsageTracker {
  private usage: Record<string, { inputTokens: number; outputTokens: number; calls: number }> = {};
  private dailyBudget: number;

  constructor(dailyBudgetUSD: number) {
    this.dailyBudget = dailyBudgetUSD;
  }

  track(endpoint: string, billedUnits: { inputTokens?: number; outputTokens?: number }) {
    if (!this.usage[endpoint]) {
      this.usage[endpoint] = { inputTokens: 0, outputTokens: 0, calls: 0 };
    }
    this.usage[endpoint].inputTokens += billedUnits.inputTokens ?? 0;
    this.usage[endpoint].outputTokens += billedUnits.outputTokens ?? 0;
    this.usage[endpoint].calls++;
  }

  getReport(): string {
    return Object.entries(this.usage)
      .map(([ep, u]) =>
        `${ep}: ${u.calls} calls, ${u.inputTokens} in, ${u.outputTokens} out`
      )
      .join('\n');
  }

  estimateDailyCost(): number {
    // Rough estimate — check cohere.com/pricing for exact rates
    const chatIn = (this.usage['chat']?.inputTokens ?? 0) / 1_000_000;
    const chatOut = (this.usage['chat']?.outputTokens ?? 0) / 1_000_000;
    const embedIn = (this.usage['embed']?.inputTokens ?? 0) / 1_000_000;
    // Multiply by per-million-token rates from pricing page
    return (chatIn * 0.5) + (chatOut * 1.5) + (embedIn * 0.1); // example rates
  }
}

// Wrap all API calls
const tracker = new CohereUsageTracker(10); // $10/day budget

async function trackedChat(params: any) {
  const response = await cohere.chat(params);
  tracker.track('chat', response.usage?.billedUnits ?? {});

  if (tracker.estimateDailyCost() > tracker['dailyBudget'] * 0.8) {
    console.warn('WARNING: Approaching daily Cohere budget limit');
  }

  return response;
}
```

### Strategy 5: Rerank Before RAG (Skip Embed for Small Corpora)

```typescript
// If you have < 1000 documents, skip embedding entirely
// Rerank is cheaper than Embed + vector search for small collections

async function cheapRAG(query: string, corpus: string[]) {
  // 1 search unit instead of N embed calls
  const ranked = await cohere.rerank({
    model: 'rerank-v3.5',
    query,
    documents: corpus,
    topN: 3,
  });

  const docs = ranked.results.map((r, i) => ({
    id: `doc-${i}`,
    data: { text: corpus[r.index] },
  }));

  // Use cheaper model for generation
  return cohere.chat({
    model: 'command-r-08-2024', // Not command-a (cheaper)
    messages: [{ role: 'user', content: query }],
    documents: docs,
    maxTokens: 300,
  });
}
```

## Cost Optimization Checklist

- [ ] Use `command-r7b` for simple tasks, `command-a` only for complex ones
- [ ] Set `maxTokens` on all chat calls
- [ ] Batch embed calls (96 texts per request)
- [ ] Cache embeddings (deterministic — compute once)
- [ ] Use `int8` embeddings for storage
- [ ] Monitor `usage.billedUnits` in every response
- [ ] Set daily budget alerts
- [ ] Use `rerank` instead of `embed` for small corpora (< 1000 docs)

## Output
- Model tiering by cost/quality
- Token budget controls preventing runaway costs
- Usage tracking with daily budget alerts
- Cost-effective RAG with rerank pre-filtering

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bill spike | No maxTokens | Set maxTokens on all chat calls |
| High embed costs | Individual texts | Batch to 96 per call |
| Budget exceeded | No monitoring | Track billedUnits per response |
| Over-provisioned model | Using premium everywhere | Tier models by task complexity |

## Resources
- [Cohere Pricing](https://cohere.com/pricing)
- [Cohere Billing Dashboard](https://dashboard.cohere.com/billing)
- [Cohere Token Counting](https://docs.cohere.com/docs/tokens-and-tokenizers)

## Next Steps
For architecture patterns, see `cohere-reference-architecture`.
