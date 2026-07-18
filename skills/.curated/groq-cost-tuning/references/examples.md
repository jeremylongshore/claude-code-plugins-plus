# Groq Cost Tuning — Worked Examples

Concrete, end-to-end scenarios that combine the levers from
[implementation.md](implementation.md). Each shows the cost impact of stacking
the optimizations.

## Example 1: 100,000 customer messages

Processing 100,000 customer messages through sentiment classification. Each row
adds one more lever on top of the previous.

| Strategy | Model | Est. Cost |
|----------|-------|-----------|
| Naive (70B, verbose prompts) | 70b-versatile | ~$60 |
| Smart routing (8B for classification) | 8b-instant | ~$5 |
| + Caching (50% hit rate) | 8b-instant | ~$2.50 |
| + Batching (10 per request) | 8b-instant | ~$2.00 |

The move from the naive baseline to full optimization is a ~30x reduction —
almost entirely from routing classification to the 8B model (Step 1), then
halved again by caching repeat prompts (Step 4).

## Example 2: Stacking the levers in code

A single pipeline that routes by use case, caps output tokens, caches
deterministic calls, and tracks spend. All functions are defined in
[implementation.md](implementation.md):

```typescript
// 1. Route: classification -> 8B (getModel from Step 1)
const model = getModel("classification");

// 2. Minimize: one-word answer, capped output (cheapClassify from Step 2)
const sentiment = await cheapClassify("The delivery was fast and the product is great!");

// 3. Cache: identical prompts return zero-cost hits (cachedCompletion from Step 4)
const answer = await cachedCompletion(
  [{ role: "system", content: "Reply with one word." },
   { role: "user", content: "The delivery was fast!" }],
  model
);

// 4. Track: record token usage + estimated cost (trackUsage from Step 5)
trackUsage(model, { prompt_tokens: 18, completion_tokens: 1 });

// 5. Report: end-of-day rollup by model (dailyCostReport from Step 5)
console.log(dailyCostReport());
// -> { totalCost: "$0.0000", byModel: { "llama-3.1-8b-instant": "$0.0000" } }
```

## Example 3: Batch high-volume classification

When you have many items in hand at once, batch them (Step 3) instead of one
call each:

```typescript
const labels = await batchClassify([
  "Loved it, five stars",
  "Broke on day one",
  "It was fine, nothing special",
]);
// -> ["positive", "negative", "neutral"]
// 3 items in 1 API call instead of 3 calls = ~90% less per-request overhead
```
