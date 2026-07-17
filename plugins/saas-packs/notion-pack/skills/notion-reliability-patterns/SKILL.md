---
name: notion-reliability-patterns
description: 'Graceful degradation when Notion is down: offline cache, retry with
  exponential backoff, circuit breaker, health checks, and fallback content.
  Use when building fault-tolerant Notion integrations for production, or when a
  Notion outage is breaking your app. Trigger with phrases like "notion reliability",
  "notion circuit breaker", "notion offline fallback", "notion health check",
  "notion graceful degradation".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Reliability Patterns

## Overview

Production reliability patterns for Notion integrations: retry with exponential backoff, a circuit breaker to prevent cascade failures, and graceful degradation (offline cache, health checks, fallback content) so users see stale data instead of errors when the API is unreachable. All patterns use `Client` from `@notionhq/client` and handle Notion-specific error codes.

The three layers compose in order — retry sits inside the circuit breaker, which sits inside the cache/fallback layer. Read the skeletons below to follow the workflow, then open [references/implementation.md](references/implementation.md) for the complete copy-paste code.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- `lru-cache` for in-memory caching (`npm install lru-cache`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set
- Understanding of circuit breaker and retry patterns

## Authentication

All patterns authenticate with a Notion internal integration token read from the `NOTION_TOKEN` environment variable — `new Client({ auth: process.env.NOTION_TOKEN })` (TS) or `Client(auth=os.environ["NOTION_TOKEN"])` (Python). Never hardcode the token; the health check calls `notion.users.me()` to confirm the token is valid and the API reachable.

## Instructions

Build the three layers in order. Each skeleton shows the shape; the full implementation lives in [references/implementation.md](references/implementation.md).

### Step 1: Retry with Exponential Backoff

Classify errors as transient (429, 500, 502, 503, timeouts, network) vs permanent (400/401/404), retry only the transient ones with exponential backoff + jitter, and honor the `Retry-After` header on rate limits.

```typescript
async function retryWithBackoff<T>(fn: () => Promise<T>, opts = {}): Promise<T> {
  // maxRetries=4, baseDelayMs=1000. Loop; on transient error wait
  // baseDelayMs * 2^attempt (+ jitter), else rethrow. See implementation.md.
}
```

Full code (TypeScript + Python, including `isTransientError` and rate-limit handling): [references/implementation.md](references/implementation.md) Step 1.

### Step 2: Circuit Breaker to Prevent Cascade Failures

During a sustained outage, stop hammering the API and fail fast. The breaker moves `closed → open` after N consecutive transient failures, waits a reset timeout, then tests recovery in `half-open` before returning to `closed`.

```typescript
class NotionCircuitBreaker {
  // failureThreshold=5, resetTimeoutMs=30_000, halfOpenSuccesses=2
  async execute<T>(fn: () => Promise<T>): Promise<T> { /* ...see implementation.md */ }
  getState() { /* { state, failures, lastFailure } for health checks */ }
}
```

Full class + `CircuitOpenError`: [references/implementation.md](references/implementation.md) Step 2.

### Step 3: Graceful Degradation — Cache, Health Checks, Fallback

Wrap calls so a success refreshes an LRU cache and a failure serves the last-good cached value; expose a health check and static fallback content for the cache-cold case.

```typescript
async function resilientQuery<T>(cacheKey, fn, fallbackContext?) {
  // circuit.execute(() => retryWithBackoff(fn)) → cache on success,
  // serve cache on failure, static fallback if cache is empty.
}
```

Full code — `queryWithFallback`, `notionHealthCheck`, `getFallbackContent`, `resilientQuery`, and the Python equivalents: [references/implementation.md](references/implementation.md) Step 3.

## Output

- Retry with exponential backoff handling 429, 500, 502, 503 errors
- Circuit breaker preventing cascade failures (5 failures = circuit opens)
- Offline cache serving stale data when API is unavailable
- Health check endpoint returning healthy/degraded/down status
- Fallback content for zero-downtime user experience
- Combined resilient query pattern composing all layers

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Circuit stays open | Threshold too low for occasional errors | Increase `failureThreshold` to 10 |
| Stale cached data | Long TTL during extended outage | Add freshness indicator in UI, reduce TTL |
| `CircuitOpenError` in logs | API is down, circuit protecting | Expected behavior, check status.notion.com |
| Retries not helping | Error is permanent (400/401/404) | `isTransientError` filters these out |
| Health check shows degraded | Notion API latency > 2s | Normal during peak load, monitor trend |
| Memory growing | Large cache | Set `max` on LRU cache, reduce TTL |

## Examples

Operational wiring — a pollable health endpoint and Prometheus alert rules — lives in [references/examples.md](references/examples.md):

- **System Health Dashboard** — expose `notionHealthCheck()` as `GET /api/health/notion`, returning 200 for healthy/degraded and 503 for down.
- **Monitoring Alert Rules** — Prometheus alerts that page when the circuit opens (`notion_circuit_state == 2`) or when >50% of requests are served from cache.

## Resources

- [Notion Status Page](https://status.notion.com)
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [Full implementation](references/implementation.md) · [Examples](references/examples.md)

## Next Steps

For governance and policy enforcement, see `notion-policy-guardrails`.
For scaling beyond single-token limits, see `notion-load-scale`.
