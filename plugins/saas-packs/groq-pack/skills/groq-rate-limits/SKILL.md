---
name: groq-rate-limits
description: 'Implement Groq rate limit handling with backoff, queuing, and header
  parsing.

  Use when handling rate limit errors, implementing retry logic,

  or optimizing API request throughput for Groq.

  Trigger with phrases like "groq rate limit", "groq throttling",

  "groq 429", "groq retry", "groq backoff".

  '
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Rate Limits

## Overview

Handle Groq rate limits using the `retry-after` header, exponential backoff, and request queuing. Groq enforces limits at the organization level with both RPM (requests/minute) and TPM (tokens/minute) constraints -- hitting either one triggers a `429`.

The workflow builds up in five composable layers: parse the rate-limit headers, wrap calls in retry-with-backoff, gate concurrency through a queue, monitor remaining capacity proactively, and fall back across models when one pool is exhausted. Read `SKILL.md` for the high-level flow, then drill into [the full implementation](references/implementation.md) for every code block and [the reference tables + worked examples](references/reference.md) for header definitions and composed clients.

## Prerequisites

- A Groq API key (`GROQ_API_KEY`) — get one at [console.groq.com](https://console.groq.com).
- `groq-sdk` installed: `npm install groq-sdk`.
- For queuing (Step 3): `p-queue` installed: `npm install p-queue`.
- Node.js 18+ (for native `fetch` and the SDK).
- Know your plan's limits — check [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

## Rate Limits at a Glance

Groq applies **RPM, RPD, TPM, and TPD** limits simultaneously — you must stay under every one, and either RPM or TPM can trip a `429`. Every response (even a success) carries `x-ratelimit-*` headers describing remaining capacity and reset timing; `429` responses add a `retry-after` header. Full header and constraint tables: [reference.md](references/reference.md).

## Instructions

Compose these five steps into one client wrapper (queue → monitor → retry). Each step's complete, copy-pasteable code is in [implementation.md](references/implementation.md).

### Step 1: Parse Rate Limit Headers

Read the `x-ratelimit-*` headers off every response into a typed `RateLimitInfo` so downstream logic can reason about remaining capacity. Groq reports reset times as strings like `"1.2s"` or `"120ms"` — normalize them to milliseconds.

### Step 2: Exponential Backoff with Retry-After

Wrap each API call in a retry loop. Prefer Groq's `retry-after` header when present; otherwise back off exponentially with jitter, capped at `maxDelayMs`. Retry only `429` and `5xx` — other `4xx` errors are not retryable.

### Step 3: Request Queue with Concurrency Control

Gate all requests through a `p-queue` sized to your plan's RPM (`intervalCap` over a 60s `interval`) so bursts never exceed the limit in the first place.

### Step 4: Proactive Rate Limit Monitor

Track remaining requests/tokens from response headers and pause *before* hitting zero (`shouldThrottle()` → `waitIfNeeded()`), instead of reacting to `429`s after the fact.

### Step 5: Model-Aware Rate Limit Strategy

Different models draw from different limit pools. When the preferred model is throttled, fall back to another model to keep making progress without waiting for a reset.

## Output

Applying this skill produces:

- A **`withRateLimitRetry()`** wrapper that transparently retries `429`/`5xx` with `retry-after`-aware backoff.
- A **`RateLimitMonitor`** that surfaces live status (`getStatus()` → `"Requests: N remaining | Tokens: M remaining"`) and throttles proactively.
- A **`p-queue`-backed client** that caps throughput to your RPM so 100 fan-out calls complete without tripping the limit.
- Console diagnostics on every backoff/throttle event (e.g. `Rate limited (attempt 2/5). Waiting 1.4s...`).

The observable end state: sustained request volume that stays under RPM/TPM with zero unhandled `429`s.

## Error Handling

| Scenario | Symptom | Solution |
|----------|---------|----------|
| Burst of requests | Many 429s in quick succession | Use queue with `p-queue` interval limiting (Step 3) |
| Large prompts burn TPM | 429 on tokens, not requests | Reduce `max_tokens`, compress prompts |
| Free tier too restrictive | Constant 429s | Upgrade to Developer plan at console.groq.com |
| Multiple services sharing key | Cascading 429s | Use separate API keys per service |
| `retry-after` absent on 429 | Retries hammer too fast | Fall back to exponential backoff + jitter (Step 2) |

## Examples

Start from this minimal `429` handler, then graduate to the composed client (queue + monitor + retry) in [reference.md](references/reference.md):

```typescript
try {
  await groq.chat.completions.create({ model, messages });
} catch (err) {
  if (err instanceof Groq.APIError && err.status === 429) {
    const retryAfter = parseInt(err.headers?.["retry-after"] || "0");
    console.log(`Rate limited. retry-after says wait ${retryAfter}s.`);
    // -> feed retryAfter into withRateLimitRetry (Step 2)
  }
}
```

- **Full five-step implementation** (every code block, verbatim): [implementation.md](references/implementation.md)
- **Composed client + header/limit tables + a 100-request fan-out**: [reference.md](references/reference.md)

## Resources

- [Groq Rate Limits Documentation](https://console.groq.com/docs/rate-limits)
- [Groq Pricing / Plans](https://groq.com/pricing)
- [p-queue on npm](https://www.npmjs.com/package/p-queue)
- Full implementation: [references/implementation.md](references/implementation.md)
- Reference tables & worked examples: [references/reference.md](references/reference.md)

## Next Steps

For security configuration, see the `groq-security-basics` skill in this pack, which covers API key storage, rotation, and request signing to complement the throughput handling above.
