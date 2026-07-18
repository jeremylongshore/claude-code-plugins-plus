---
name: elevenlabs-rate-limits
description: |
  Implement ElevenLabs rate limiting, concurrency queuing, and backoff patterns.
  Use when handling 429 errors, implementing retry logic, or managing concurrent
  TTS request throughput for an ElevenLabs integration.
  Trigger with "elevenlabs rate limit", "elevenlabs throttling", "elevenlabs 429",
  "elevenlabs retry", "elevenlabs backoff", "elevenlabs concurrent requests".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- rate-limits
- reliability
compatibility: Designed for Claude Code
---
# ElevenLabs Rate Limits

## Overview

Handle ElevenLabs rate limits with plan-aware concurrency queuing, exponential backoff, and quota monitoring. ElevenLabs uses two rate limit mechanisms: concurrent request limits (per plan) and system-level throttling. The key insight is that a 429 means two different things depending on its `detail.status` — and each demands the opposite response.

## Prerequisites

- ElevenLabs SDK installed (`@elevenlabs/elevenlabs-js`)
- Understanding of your subscription plan's limits
- `p-queue` package (recommended): `npm install p-queue`

## Instructions

### Step 1: Understand the Two 429 Error Types

ElevenLabs returns HTTP 429 for two different reasons. Read the `detail.status` field to tell them apart — the correct strategy is opposite for each.

| 429 Variant | Response Body | Cause | Strategy |
|-------------|--------------|-------|----------|
| `too_many_concurrent_requests` | `{"detail":{"status":"too_many_concurrent_requests"}}` | Exceeded plan concurrency | Queue requests, don't backoff |
| `system_busy` | `{"detail":{"status":"system_busy"}}` | Server overload | Exponential backoff |

### Step 2: Know Your Plan Concurrency Limits

Concurrency is capped per plan. Size your queue to this number — never higher.

| Plan | Max Concurrent Requests | Characters/Month |
|------|------------------------|-------------------|
| Free | 2 | 10,000 |
| Starter | 3 | 30,000 |
| Creator | 5 | 100,000 |
| Pro | 10 | 500,000 |
| Scale | 15 | 2,000,000 |
| Business | 15 | Custom |

### Step 3: Assemble the Four Building Blocks

Write four small modules and compose them. The full, copy-ready source for each is in [references/implementation.md](references/implementation.md) — the skeleton below shows how they fit together.

1. **Request queue** (`rate-limiter.ts`) — a `p-queue` sized to your plan's concurrency limit. This is the response to `too_many_concurrent_requests`: queue, do not back off.
2. **Backoff wrapper** (`backoff.ts`) — exponential backoff with jitter for `system_busy` and 5xx; immediate short retry for concurrency; hard-fail on 401/400/404.
3. **Quota monitor** (`quota-monitor.ts`) — polls `user.subscription` character usage, warns at a threshold, and blocks a request that would overrun remaining quota.
4. **Resilient client** (`resilient-client.ts`) — composes all three so one `generateSpeech()` call guards quota, queues, and backs off automatically:

```typescript
// src/elevenlabs/resilient-client.ts (skeleton — full source in references/implementation.md)
export function createResilientClient(plan = "pro") {
  const client = new ElevenLabsClient({ maxRetries: 0 }); // we handle retries
  const queue = createRequestQueue(plan);                 // Step 3.1
  const quota = new QuotaMonitor(client);                 // Step 3.3

  return {
    async generateSpeech(voiceId, text, modelId = "eleven_multilingual_v2") {
      await quota.guardRequest(text.length);              // Step 3.3
      return queue.add(() =>                              // Step 3.1
        withBackoff(() =>                                 // Step 3.2
          client.textToSpeech.convert(voiceId, { text, model_id: modelId })
        )
      );
    },
  };
}
```

### Step 4: Mind Model Cost When Managing Quota

Quota is spent in credits-per-character, which varies by model. Use Flash/Turbo models during development to conserve quota.

| Model | Credits per Character | 10,000 Chars Cost |
|-------|-----------------------|-------------------|
| `eleven_v3` | 1.0 | 10,000 credits |
| `eleven_multilingual_v2` | 1.0 | 10,000 credits |
| `eleven_flash_v2_5` | 0.5 | 5,000 credits |
| `eleven_turbo_v2_5` | 0.5 | 5,000 credits |

## Output

Applying this skill produces four TypeScript modules under `src/elevenlabs/` and a rate-limited request path:

- `rate-limiter.ts` — exports `createRequestQueue(plan)` returning a plan-sized `PQueue`.
- `backoff.ts` — exports `withBackoff(operation, config)` returning the operation's result or throwing after `maxRetries`.
- `quota-monitor.ts` — exports a `QuotaMonitor` class with `check()` → `{ used, limit, remaining, pctUsed, warning }` and `guardRequest(textLength)`.
- `resilient-client.ts` — exports `createResilientClient(plan)` whose `generateSpeech()` returns TTS audio, plus `getQueueStats()` and `checkQuota()`.

At runtime: concurrent requests stay at or below the plan cap, `system_busy` responses are retried with backoff, and requests that would overrun quota fail fast with a clear error instead of a wasted API call.

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| Concurrent limit hit | 429 + `too_many_concurrent_requests` | Queue; retry after ~50ms per queued request |
| System busy | 429 + `system_busy` | Exponential backoff (1s, 2s, 4s, 8s...) |
| Quota exhausted | 401 + `quota_exceeded` | Stop requests; alert; wait for reset |
| Server error | 500-599 | Exponential backoff; max 5 retries |

## Examples

Concise starting point — batch generation with just the queue:

```typescript
import { createRequestQueue } from "./elevenlabs/rate-limiter";

const queue = createRequestQueue("pro"); // 10 concurrent
const clips = await Promise.all(
  texts.map(text =>
    queue.add(() => client.textToSpeech.convert(voiceId, { text, model_id: "eleven_flash_v2_5" }))
  )
); // 20 requests, at most 10 in flight
```

For the full resilient-client example, per-429-variant branching at the call site, and the batch pattern in context, see [references/examples.md](references/examples.md).

## Resources

- [ElevenLabs Rate Limits Help](https://help.elevenlabs.io/hc/en-us/articles/19571824571921)
- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [references/implementation.md](references/implementation.md) — full source for all four building blocks
- [references/examples.md](references/examples.md) — worked end-to-end usage examples

## Next Steps

For security configuration, see `elevenlabs-security-basics`.
