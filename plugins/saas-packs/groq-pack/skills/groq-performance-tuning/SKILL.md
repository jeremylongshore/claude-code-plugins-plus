---
name: groq-performance-tuning
description: 'Optimize Groq API performance with model selection, caching, streaming,
  and parallel requests.

  Use when experiencing slow responses, implementing caching strategies,

  or optimizing request throughput for Groq integrations.

  Trigger with phrases like "groq performance", "optimize groq",

  "groq latency", "groq caching", "groq slow", "groq speed".

  '
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- performance
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Performance Tuning

## Overview

Maximize Groq's LPU inference speed advantage. Groq already delivers extreme throughput (280-560 tok/s) and low latency (<200ms TTFT), but client-side optimization -- model selection, prompt size, streaming, caching, and parallelism -- determines whether your application fully exploits that speed.

This skill walks through six tuning levers at a high level; the complete, copy-pasteable code for each lives in [references/implementation.md](references/implementation.md), and end-to-end worked scenarios live in [references/examples.md](references/examples.md).

## Prerequisites

- **Groq API key** — set `GROQ_API_KEY` in the environment. The `groq-sdk` client (`new Groq()`) reads it automatically; never hardcode the key.
- **Node.js 18+** with the `groq-sdk` package installed (`npm install groq-sdk`).
- Optional packages for the caching and parallelism steps: `lru-cache` and `p-queue` (`npm install lru-cache p-queue`).
- A baseline latency measurement of your current integration so you can confirm the tuning actually helps.

## Groq Speed Benchmarks

| Model | TTFT | Throughput | Context |
|-------|------|-----------|---------|
| `llama-3.1-8b-instant` | ~50ms | ~560 tok/s | 128K |
| `llama-3.3-70b-versatile` | ~150ms | ~280 tok/s | 128K |
| `llama-3.3-70b-specdec` | ~100ms | ~400 tok/s | 128K |
| `meta-llama/llama-4-scout-17b-16e-instruct` | ~80ms | ~460 tok/s | 128K |

TTFT = Time to First Token. Actual values depend on prompt size and server load.

## Instructions

Apply these six levers in order. Each is a small, independent change — start with the ones that match your bottleneck (model choice and caching give the biggest wins on most workloads). The full code for every step is in [references/implementation.md](references/implementation.md).

1. **Choose the right model for speed.** Map each call site to a speed tier: `llama-3.1-8b-instant` for latency-critical paths, `llama-3.3-70b-versatile` for quality-sensitive paths, `llama-3.3-70b-specdec` for 70b quality at higher throughput. Set `temperature: 0` so responses are deterministic (and cacheable).
2. **Minimize token count.** Trim verbose system prompts to their essence and set `max_tokens` to the expected output size, not a safe-looking ceiling. Fewer tokens means faster responses and less TPM-quota pressure.
3. **Stream for perceived performance.** For any output the user watches arrive, stream chunks and surface live TTFT / tokens-per-second metrics. Streaming hides TTFT even when total wall-clock is unchanged.
4. **Cache deterministic responses.** Hash `{messages, model}` and serve repeat `temperature: 0` requests from an LRU cache with a short TTL — turning a repeated call into a ~0ms hit.
5. **Parallelize under a rate-limit-aware queue.** Fan out bulk work with `p-queue`, capping concurrency and per-minute volume so you saturate throughput without tripping 429s.
6. **Benchmark before you commit.** Measure the candidate models against your real prompt shape and pick the fastest that clears your quality bar.

The essential skeleton — a tiered client every other step builds on:

```typescript
import Groq from "groq-sdk";

const groq = new Groq();  // reads GROQ_API_KEY from the environment

const SPEED_MAP = {
  instant: "llama-3.1-8b-instant",      // <100ms TTFT — latency-critical
  balanced: "llama-3.3-70b-versatile",  // <200ms TTFT — quality-sensitive
  fast70b: "llama-3.3-70b-specdec",     // 70b quality, faster throughput
} as const;

async function tieredCompletion(prompt: string, tier: keyof typeof SPEED_MAP = "instant") {
  return groq.chat.completions.create({
    model: SPEED_MAP[tier],
    messages: [{ role: "user", content: prompt }],
    temperature: 0,   // deterministic = cacheable
    max_tokens: 256,  // request only what you need
  });
}
```

See [references/implementation.md](references/implementation.md) for the streaming, caching, parallel-queue, and benchmarking functions in full.

## Output

Applying these levers to a Groq integration produces:

- **A tiered model map** (`SPEED_MAP`) so each call site uses the fastest model that meets its quality bar.
- **A streaming helper** that returns `{ content, ttftMs, totalMs, tokPerSec }` for live latency instrumentation.
- **A deterministic prompt cache** (LRU + SHA-256 key) that collapses repeated requests to ~0ms.
- **A rate-limit-aware parallel executor** that maximizes throughput without hitting 429s.
- **A benchmark report** printing average latency and tokens/sec per model, e.g.:

```text
llama-3.1-8b-instant     |  61ms avg | 548 tok/s avg
llama-3.3-70b-versatile  | 148ms avg | 279 tok/s avg
llama-3.3-70b-specdec    | 103ms avg | 401 tok/s avg
```

## Performance Decision Matrix

| Scenario | Model | max_tokens | stream | cache |
|----------|-------|-----------|--------|-------|
| Classification | 8b-instant | 5 | No | Yes |
| Chat response | 70b-versatile | 1024 | Yes | No |
| Data extraction | 8b-instant | 200 | No | Yes |
| Code generation | 70b-versatile | 2048 | Yes | No |
| Bulk processing | 8b-instant | 256 | No | Yes |

## Examples

Common scenarios mapped to the levers above. Full code for each is in [references/examples.md](references/examples.md).

- **Latency-critical classification** — `8b-instant` + one-word prompt + `max_tokens: 5` + cache. First call ~50ms TTFT; identical repeats return from cache at ~0ms.
- **Interactive chat** — `70b-versatile` streamed with `streamWithMetrics`, printing tokens as they arrive plus a `[TTFT | tok/s]` footer.
- **Bulk processing (500 records)** — `parallelCompletions` wraps each call in a rate-limit-aware `p-queue` and reuses the cache for duplicate rows.
- **Empirical model choice** — run `benchmarkModels` against your real prompt, then hardcode the fastest tier that clears your quality bar.

```typescript
// Latency-critical classification, cached
const label = await cachedCompletion(
  [
    { role: "system", content: "Classify as positive/negative/neutral. One word only." },
    { role: "user", content: "This product exceeded every expectation." },
  ],
  "llama-3.1-8b-instant"
);
// => "positive"
```

See [references/examples.md](references/examples.md) for the streaming, bulk, and benchmarking walkthroughs.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High TTFT | Using 70b for simple tasks | Switch to `llama-3.1-8b-instant` |
| Rate limit (429) | Over RPM or TPM | Use queue with interval limiting |
| Stream disconnect | Network timeout | Implement reconnection with partial content |
| Token overflow | max_tokens too high | Set to expected output size |
| Cache miss rate high | Unique prompts | Normalize prompts, use template patterns |

## Resources

- [Full implementation walkthrough](references/implementation.md) — copy-pasteable code for all six steps.
- [Worked examples](references/examples.md) — end-to-end scenarios mapped to the tuning levers.
- [Groq Models & Speed](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [lru-cache on npm](https://www.npmjs.com/package/lru-cache)
- For cost optimization, see the `groq-cost-tuning` skill.
