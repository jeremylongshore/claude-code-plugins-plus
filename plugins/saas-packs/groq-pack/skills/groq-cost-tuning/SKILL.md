---
name: groq-cost-tuning
description: |
  Optimize Groq costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Groq billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "groq cost", "groq billing",
  "reduce groq costs", "groq pricing", "groq expensive", "groq budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Groq Cost Tuning

## Overview
Optimize Groq inference costs by selecting the right model for each use case and managing token volume. Groq's pricing is extremely competitive (Llama 3.1 8B at ~$0.05/M tokens, Llama 3.3 70B at ~$0.59/M tokens, Mixtral at ~$0.24/M tokens), but high throughput (500+ tokens/sec) makes it easy to burn through large volumes quickly. The main cost lever is routing requests to the smallest model that produces acceptable quality -- the 8B model is 12x cheaper than the 70B model.

## Prerequisites
- Groq Cloud account with billing dashboard access
- Understanding of which use cases need which model quality
- Application-level request routing capability

## Instructions

### Step 1: Implement Smart Model Routing
```typescript
// Route requests to cheapest model that meets quality requirements
const MODEL_ROUTING: Record<string, { model: string; costPer1MTokens: number }> = {
  'classification':  { model: 'llama-3.1-8b-instant',    costPer1MTokens: 0.05 },
  'summarization':   { model: 'llama-3.1-8b-instant',    costPer1MTokens: 0.05 },
  'code-review':     { model: 'llama-3.3-70b-versatile',  costPer1MTokens: 0.59 },
  'creative-writing':{ model: 'llama-3.3-70b-versatile',  costPer1MTokens: 0.59 },
  'extraction':      { model: 'llama-3.1-8b-instant',    costPer1MTokens: 0.05 },
  'chat':            { model: 'llama-3.3-70b-versatile',  costPer1MTokens: 0.59 },
};

function selectModel(useCase: string): string {
  return MODEL_ROUTING[useCase]?.model || 'llama-3.1-8b-instant'; // Default cheap
}
// Classification on 8B: $0.05/M tokens vs 70B: $0.59/M = 12x savings
```

### Step 2: Minimize Token Usage per Request
```typescript
// Reduce prompt tokens -- Groq charges for both input and output
const OPTIMIZATION_TIPS = {
  systemPrompt: 'Keep system prompts under 200 tokens. Be concise.',
  maxTokens: 'Set max_tokens to expected output size, not maximum.',
  context: 'Only include relevant context, not entire documents.',
  fewShot: 'Use 1-2 examples instead of 5-6 for few-shot learning.',
};

// Example: reduce a 2000-token prompt to 500 tokens
const optimizedRequest = {
  model: 'llama-3.1-8b-instant',
  messages: [
    { role: 'system', content: 'Classify: positive/negative/neutral' }, // 6 tokens vs 200
    { role: 'user', content: text }, // Only the text, no verbose instructions
  ],
  max_tokens: 5, // Only need one word
};
```

### Step 3: Cache Identical Requests
```typescript
import { createHash } from 'crypto';

const responseCache = new Map<string, { result: any; ts: number }>();

async function cachedCompletion(messages: any[], model: string) {
  const key = createHash('md5').update(JSON.stringify({ messages, model })).digest('hex');
  const cached = responseCache.get(key);
  if (cached && Date.now() - cached.ts < 3600_000) return cached.result;

  const result = await groq.chat.completions.create({ model, messages });
  responseCache.set(key, { result, ts: Date.now() });
  return result;
}
```

### Step 4: Use Batching for Bulk Processing
```typescript
// Process items in batches with the fast 8B model
// Groq's speed makes batch processing very efficient
async function batchClassify(items: string[]): Promise<string[]> {
  // Batch 10 items per request instead of 1 per request
  const batchPrompt = items.map((item, i) => `${i}: ${item}`).join('\n');
  const result = await groq.chat.completions.create({
    model: 'llama-3.1-8b-instant',
    messages: [{ role: 'user', content: `Classify each as pos/neg/neutral:\n${batchPrompt}` }],
    max_tokens: items.length * 10,
  });
  // 1 API call instead of 10 = ~90% reduction in overhead
  return parseClassifications(result.choices[0].message.content);
}
```

### Step 5: Set Spending Limits
In Groq Console > Organization > Billing:
- Set monthly spending cap
- Enable alerts at 50% and 80% of budget
- Configure auto-pause when limit is reached

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Costs higher than expected | Using 70B for simple tasks | Route classification/extraction to 8B model |
| Rate limit causing retries | RPM cap hit | Spread requests across multiple keys |
| Spending cap paused API | Budget exhausted | Increase cap or reduce request volume |
| Cache hit rate low | Unique prompts every time | Normalize prompts before caching |

## Examples
```bash
# Cost comparison: same task on different models
echo "100K requests with 500 tokens each:"
echo "  8B model: \$$(echo '100000 * 500 / 1000000 * 0.05' | bc) USD"
echo "  70B model: \$$(echo '100000 * 500 / 1000000 * 0.59' | bc) USD"
echo "  Savings: 12x by using 8B for simple tasks"
```
