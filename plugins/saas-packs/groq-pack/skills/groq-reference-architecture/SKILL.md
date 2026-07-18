---
name: groq-reference-architecture
description: 'Implement Groq reference architecture with model routing, streaming
  pipelines, and fallbacks.

  Use when designing new Groq integrations, reviewing project structure,

  or establishing architecture standards for Groq applications.

  Trigger with phrases like "groq architecture", "groq best practices",

  "groq project structure", "how to organize groq", "groq design".

  '
allowed-tools: Read, Grep
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- groq-reference
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Reference Architecture

## Overview

Production architecture for applications built on Groq's LPU inference API. It
covers four concerns that every serious Groq integration needs: routing requests
to the right model by latency/capability/cost, a middleware band (cache, metrics,
retry), a multi-provider fallback chain, and a streaming pipeline. The service
layer built here is reusable across a chat UI, an API backend, a batch processor,
or an agent.

The full layer diagram and how the pieces interact lives in
[references/architecture.md](references/architecture.md); the complete,
copy-ready TypeScript for every layer is in
[references/implementation.md](references/implementation.md).

## Prerequisites

- **Groq API key** — create one at [console.groq.com](https://console.groq.com)
  and export it as `GROQ_API_KEY`. The Groq SDK reads it from the environment;
  the client is constructed as `new Groq({ apiKey: process.env.GROQ_API_KEY })`.
  Never hardcode the key.
- **Runtime**: Node.js 18+ (for `performance.now()` and native `fetch`).
- **Packages**: `groq-sdk` and `lru-cache` (`npm install groq-sdk lru-cache`).
- **Optional backup provider**: an OpenAI-compatible key if you extend the
  fallback chain beyond Groq's own models.

## Instructions

Build the service layer in five ordered steps. Each step is one file under
`src/groq/`. The router depends on the registry; the middleware and fallback
depend on the client; the streaming pipeline stands alone. Full source for every
step (verbatim) is in [references/implementation.md](references/implementation.md).

1. **Model Registry** (`models.ts`) — declare a `ModelSpec` for each model with
   its tier, context window, speed, cost, and capabilities. Skeleton:

   ```typescript
   export const MODELS: Record<string, ModelSpec> = {
     "llama-3.1-8b-instant":     { tier: "speed",   /* fast, cheap */ },
     "llama-3.3-70b-versatile":  { tier: "quality", /* tools + JSON */ },
     "meta-llama/llama-4-scout-17b-16e-instruct": { tier: "vision" },
     "whisper-large-v3-turbo":   { tier: "audio" },
   };
   ```

2. **Model Router** (`router.ts`) — `selectModel(req)` maps requirements
   (`maxLatencyMs`, `needsVision`, `needsTools`, `costSensitive`) to the cheapest
   model that satisfies them. Callers pass requirements, never hardcoded ids.
3. **Middleware** (`middleware.ts`) — `completionWithMiddleware()` wraps each call
   with an LRU cache (deterministic requests only, `temperature === 0`), latency +
   token metrics, and a pluggable metrics sink.
4. **Fallback Chain** (`fallback.ts`) — `completionWithFallback()` tries the
   primary model, drops to a model in a different rate-limit pool on 429/5xx, then
   returns a graceful-degradation payload instead of throwing.
5. **Streaming Pipeline** (`streaming.ts`) — `streamCompletion()` is an async
   generator yielding `{ type: "token" | "done" | "error" }` for real-time SSE UIs.

When applying this to an existing repo, `Read` the current `src/` layout and
`Grep` for direct `groq.chat.completions.create` calls to find code that should
route through the middleware and fallback wrappers instead.

## Integration Patterns

| Pattern | When to Use | Groq Feature |
|---------|-------------|-------------|
| Direct completion | Simple request/response | `chat.completions.create` |
| Streaming SSE | Real-time chat UI | `stream: true` |
| Tool calling | Agent with function execution | `tools` parameter |
| JSON extraction | Structured data from text | `response_format: json_object` |
| Batch processing | High-volume document processing | Queue + rate limiting |
| Audio transcription | Voice input | `audio.transcriptions.create` |
| Vision analysis | Image understanding | Llama 4 Scout/Maverick |

## Output

Applying this skill produces a `src/groq/` service layer with six files
(`client.ts`, `models.ts`, `router.ts`, `middleware.ts`, `fallback.ts`,
`streaming.ts`) plus the service and API layers that consume it. At runtime you get:

- **Routed completions** — `selectModel()` returns a `ModelSpec`; callers never
  hardcode a model id, so cost/latency policy lives in one place.
- **Cached deterministic responses** — repeated `temperature: 0` calls return from
  the LRU cache instead of re-billing the API.
- **Resilient calls** — `completionWithFallback()` returns a valid completion shape
  even when Groq is rate-limited, never surfacing a raw 429 to the user.
- **Streamed tokens** — `streamCompletion()` yields `{ type, content }` events for
  SSE, with a terminal `done` or `error` event.
- **Metrics** — every call emits `{ model, latencyMs, tokens, cached }` to your
  metrics sink (Prometheus, Datadog, or `console.log` by default).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 on primary model | RPM/TPM exceeded | Fall back to different model |
| High latency | Wrong model tier | Route to `8b-instant` for latency-critical paths |
| Context overflow | Input > 128K tokens | Truncate or chunk input |
| Vision errors | Wrong model for images | Use Llama 4 Scout full model path |
| `GROQ_API_KEY` undefined | Env var not exported | Export the key before starting the process |

## Examples

A latency-critical chat turn routes to the speed tier and returns one completion:

```typescript
const model = selectModel({ maxLatencyMs: 80, costSensitive: true });
// → llama-3.1-8b-instant
const res = await completionWithMiddleware(groq, model.id, messages);
```

Streaming a UI consumes the async generator token-by-token:

```typescript
for await (const event of streamCompletion(groq, messages)) {
  if (event.type === "token") process.stdout.write(event.content!);
}
```

Four fully worked examples — latency-critical, quality-with-fallback, streaming,
and vision routing — are in [references/examples.md](references/examples.md).

## Resources

- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Pricing](https://groq.com/pricing)

## Next Steps

For multi-environment deployment, see the `groq-multi-env-setup` skill, which
extends this service layer with per-environment configuration and secrets handling.
