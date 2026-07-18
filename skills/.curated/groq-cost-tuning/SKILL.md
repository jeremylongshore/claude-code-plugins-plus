---
name: groq-cost-tuning
description: 'Optimize Groq costs through model routing, token management, and usage
  monitoring.

  Use when analyzing Groq billing, reducing API costs,

  or implementing usage monitoring and budget alerts.

  Trigger with phrases like "groq cost", "groq billing",

  "reduce groq costs", "groq pricing", "groq expensive", "groq budget".

  '
allowed-tools: Read, Grep
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- monitoring
- cost-optimization
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Cost Tuning

## Overview

Optimize Groq inference costs through smart model routing, token minimization, and caching. Groq pricing is already extremely competitive, but at high volume the savings from routing classification to 8B vs 70B are 12x per request.

## Prerequisites

- A Groq account with an API key exported as the `GROQ_API_KEY` environment variable — the `groq-sdk` client reads it automatically (`new Groq()`).
- Node.js with the `groq-sdk` package installed (`npm install groq-sdk`).
- Access to the [Groq Console](https://console.groq.com) to set spending caps and read the usage dashboard.

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

Apply these six levers in order. Each compounds on the last — routing alone is
the biggest win (~12x), and caching plus batching halve the remainder. The lean
skeleton below shows the routing core; the full code for every step lives in
[references/implementation.md](references/implementation.md).

1. **Smart model routing** — map each use case to the cheapest model that meets its quality bar (classification/extraction/summarization → `llama-3.1-8b-instant`; reasoning/code review/chat → `llama-3.3-70b-versatile`; vision → `llama-4-scout`).
2. **Minimize tokens per request** — trim verbose system prompts and cap `max_tokens` so a one-word answer never bills for a paragraph.
3. **Batch to reduce overhead** — fold many items into one request; 10-in-1 cuts per-request overhead and RPM pressure ~90%.
4. **Cache deterministic requests** — at `temperature: 0`, hash identical prompts into a cache for zero-cost, zero-latency repeat hits.
5. **Usage tracking** — log token counts and estimated cost per call to catch spend regressions before the invoice.
6. **Spending limits in console** — set a monthly cap, alerts at 50%/80%, and auto-pause in Groq Console > Billing.

```typescript
import Groq from "groq-sdk";
const groq = new Groq(); // reads GROQ_API_KEY

const ROUTING = {
  classification: "llama-3.1-8b-instant",   // ~$0.05/M
  reasoning:      "llama-3.3-70b-versatile", // ~$0.59/M
};
const getModel = (useCase: string) =>
  ROUTING[useCase] || "llama-3.1-8b-instant";
// Classification on 8B vs 70B = 12x savings
```

See [references/implementation.md](references/implementation.md) for the complete
routing table, token-minimization, batching, caching, usage-tracking, and
console-limit code.

## Output

Applying the workflow produces:

- A **routing map** (`getModel(useCase)`) that resolves every call to the cheapest fit model.
- A **usage log** of `UsageRecord` rows (timestamp, model, prompt/completion tokens, estimated cost) accumulated per call.
- A **daily cost report** from `dailyCostReport()` returning `{ totalCost, byModel }`, e.g. `{ totalCost: "$2.0000", byModel: { "llama-3.1-8b-instant": "$2.0000" } }`.
- **Console spending controls**: a monthly cap, 50%/80% alerts, and auto-pause.

## Examples

Batch three items in a single call using the `batchClassify` helper from
[references/implementation.md](references/implementation.md):

```typescript
const labels = await batchClassify([
  "Loved it, five stars",
  "Broke on day one",
  "It was fine, nothing special",
]);
// -> ["positive", "negative", "neutral"]  (1 API call instead of 3)
```

For the full 100,000-message cost walkthrough and a stacked routing +
caching + tracking pipeline, see
[references/examples.md](references/examples.md).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Costs higher than expected | 70B for simple tasks | Route classification/extraction to 8B |
| Spending cap hit | Budget exhausted | Increase cap or reduce volume |
| Cache not effective | Unique prompts | Normalize prompts before caching |
| Rate limits causing retries | RPM cap hit | Batch requests, spread across time |

## Resources

- [references/implementation.md](references/implementation.md) — full code for all six cost-tuning levers.
- [references/examples.md](references/examples.md) — worked cost walkthroughs and a stacked pipeline.
- [Groq Pricing](https://groq.com/pricing)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Usage Dashboard](https://console.groq.com/settings/usage)
- For architecture patterns, see the `groq-reference-architecture` skill.
