---
name: groq-migration-deep-dive
description: |
  Use when you are moving a codebase off OpenAI, Anthropic, or another LLM
  provider onto Groq (or between Groq model generations) and want a
  zero-downtime, feature-flagged cutover with a benchmark and rollback plan.
  Trigger with phrases like "migrate to groq", "switch to groq",
  "groq migration", "openai to groq", "groq replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- migration
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Migration Deep Dive

## Current State

!`npm list groq-sdk openai @anthropic-ai/sdk 2>/dev/null | grep -E "groq|openai|anthropic" || echo 'No LLM SDKs found'`

## Overview

Migrate to Groq from OpenAI, Anthropic, or other LLM providers. Groq's
OpenAI-compatible API makes migration straightforward — the primary changes
are a different SDK import, different model IDs, and different response
metadata. The reward is 10-50x faster inference.

The safe path is a provider-abstraction layer plus feature-flagged traffic
shifting: route a small canary to Groq, benchmark quality and speed, ramp to
100%, and keep a one-flag rollback the whole way.

## Migration Complexity

| Source | Complexity | Key Changes |
|--------|-----------|-------------|
| OpenAI | Low | Import, model IDs, base URL — API shape is identical |
| Anthropic | Medium | Different API shape, message format, streaming protocol |
| Local LLMs | Medium | Remove infra, add API calls |
| Other cloud (Bedrock, Vertex) | Medium | Remove cloud SDK, add groq-sdk |

## Prerequisites

- A Groq API key (`GROQ_API_KEY`) from [console.groq.com](https://console.groq.com).
- `groq-sdk` installed: `npm install groq-sdk`.
- A feature-flag mechanism (LaunchDarkly, env var, config service) exposing a
  `groq_migration_pct` value for gradual traffic shifting.
- The existing provider's key still available (`OPENAI_API_KEY` or equivalent)
  so you can run both providers side-by-side during the cutover.
- Node `>=18` if you use the `performance.now()` benchmark helper.

## Instructions

Steps 1-2 below are the essential skeleton — the two changes every migration
needs. Steps 3-7 (the provider abstraction, traffic shifting, scanner,
benchmark, and full compatibility matrix) are moved verbatim into the
reference files linked under Examples so this file stays scannable.

### Step 1: OpenAI to Groq Migration

The minimal change: swap the SDK import, client, and model ID. The response
shape is identical, so downstream code (`result.choices[0].message.content`)
is untouched.

```typescript
// BEFORE: OpenAI
import OpenAI from "openai";
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const result = await openai.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "Hello" }],
});

// AFTER: Groq (minimal changes)
import Groq from "groq-sdk";
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const result = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",  // or "llama-3.1-8b-instant"
  messages: [{ role: "user", content: "Hello" }],
});

// Same response shape: result.choices[0].message.content
```

### Step 2: Model ID Mapping

Centralize the OpenAI/Anthropic → Groq translation so a single map drives the
whole codebase and unknown models fall back to a safe default.

```typescript
// OpenAI → Groq model equivalents
const MODEL_MAP: Record<string, string> = {
  // OpenAI → Groq (quality equivalent)
  "gpt-4o":        "llama-3.3-70b-versatile",
  "gpt-4o-mini":   "llama-3.1-8b-instant",
  "gpt-4-turbo":   "llama-3.3-70b-versatile",
  "gpt-3.5-turbo": "llama-3.1-8b-instant",

  // Anthropic → Groq (approximate)
  "claude-3-5-sonnet": "llama-3.3-70b-versatile",
  "claude-3-haiku":    "llama-3.1-8b-instant",
};

function migrateModelId(model: string): string {
  return MODEL_MAP[model] || "llama-3.3-70b-versatile";
}
```

### Steps 3-7: Zero-Downtime Rollout

Once Steps 1-2 compile, wrap both providers in a common interface and shift
traffic gradually. The full code lives in the references:

- **Step 3 — Provider abstraction layer** and **Step 4 — feature-flag traffic
  shifting**: [references/implementation.md](references/implementation.md).
- **Step 5 — automated migration scanner** (sizes the migration before you
  start) and the **rollback plan**: [references/implementation.md](references/implementation.md).
- **Step 6 — comparison benchmark** and **Step 7 — the OpenAI↔Groq
  compatibility matrix**: [references/examples.md](references/examples.md).

## Output

Running this skill's workflow produces:

- A migration assessment printout from the scanner (Step 5): OpenAI import
  count, the distinct `gpt-*` model IDs in use, any OpenAI-only features
  (embeddings/images/fine-tuning) that block a clean cutover, and the number
  of API-key references to update.
- A provider-agnostic `LLMProvider` layer with `GroqProvider` and
  `OpenAIProvider` implementations both live behind one `getProvider()` call.
- A benchmark table per prompt: Groq vs OpenAI latency in ms, token counts,
  and the measured speedup factor.
- A `groq_migration_pct` feature flag driving the canary → 100% ramp, with a
  one-flag rollback to 0%.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Quality regression | Different model strengths | Tune system prompts for Llama models |
| Missing features | Groq doesn't have embeddings/images | Keep OpenAI for those features |
| Rate limits | Different limits than OpenAI | Configure per-model rate limits |
| Cost increase | Different pricing structure | Route simple tasks to 8B model |

## Examples

- **Full provider abstraction + traffic shifting + scanner + rollback**:
  [references/implementation.md](references/implementation.md) — the complete
  Step 3-5 code plus the rollback procedure.
- **Benchmark harness + compatibility matrix**:
  [references/examples.md](references/examples.md) — the side-by-side
  quality/speed benchmark and the full OpenAI↔Groq feature table.

## Resources

- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq Models](https://console.groq.com/docs/models)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [groq-sdk npm](https://www.npmjs.com/package/groq-sdk)

## Next Steps

For ongoing SDK version upgrades between Groq model generations, see the
companion `groq-upgrade-migration` skill in this pack.
