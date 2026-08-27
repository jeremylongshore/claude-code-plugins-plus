---
name: apify-rate-limits
description: 'Handle Apify API rate limits with proper backoff and request queuing.
  Use when hitting 429 errors, optimizing API request throughput, or implementing
  rate-aware client wrappers. Trigger with "apify rate limit", "apify throttling",
  "apify 429", "apify retry", "apify backoff", "too many requests apify".'
allowed-tools: Read, Write, Edit
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Rate Limits

## Overview

The Apify API enforces rate limits per resource. The `apify-client` library
auto-retries 429s (up to 8 times with exponential backoff), so most workloads never
notice a limit. You reach for this skill when bulk operations, custom API calls, or
large fan-outs push past what the built-in retry can absorb — you then batch, queue,
stagger, and monitor to stay under the ceiling.

Full runnable code for every step is in
[implementation.md](references/implementation.md); combined scenarios are in
[examples.md](references/examples.md).

### Apify rate limit rules

| Scope | Limit | Notes |
|-------|-------|-------|
| Per resource (default) | 60 req/sec | Applies to each Actor, dataset, KV store independently |
| Dataset push | 60 req/sec per dataset | Batch items to reduce call count |
| Actor runs | 60 req/sec per Actor | Start runs in sequence or with delays |
| Platform-wide | Higher limit | Aggregate across all resources |

**"Per resource" means:** calls to dataset A and dataset B each get 60 req/sec
independently. Every response carries `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, and `X-RateLimit-Reset` (epoch seconds) headers.

## Prerequisites

- An Apify account with API access and `APIFY_TOKEN` set in the environment.
- The `apify-client` package installed (`npm install apify-client`).
- For custom queuing: `p-queue` (`npm install p-queue`); `crawlee` for `sleep` and
  crawler-level concurrency.

## Instructions

The workflow is five steps. Each is summarized here with its core lever; the full
runnable code for every step is in
[implementation.md](references/implementation.md).

1. **Understand built-in retries** — `apify-client` already retries 429/500+ with
   exponential backoff. Tune `maxRetries` / `minDelayBetweenRetriesMillis` only when
   the defaults are wrong for your endpoint:

   ```typescript
   import { ApifyClient } from 'apify-client';
   const client = new ApifyClient({
     token: process.env.APIFY_TOKEN,
     maxRetries: 5,                      // Default: 8
     minDelayBetweenRetriesMillis: 500,  // Default: 500
   });
   ```

2. **Batch operations** (biggest lever) — collapse per-item loops into one batched
   call (up to 9 MB), chunking only for very large datasets:

   ```typescript
   await client.dataset(dsId).pushItems(items);   // 1 call, not N
   ```

3. **Queue custom calls** — gate raw API calls through `p-queue`
   (`concurrency` + `intervalCap`) so fan-out reads never exceed 60 req/sec. See
   [implementation.md](references/implementation.md) § Step 3.

4. **Stagger Actor starts** — insert a ~200 ms delay between `start()` calls so the
   runs endpoint never 429s, then `waitForFinish()` in parallel. See
   [implementation.md](references/implementation.md) § Step 4.

5. **Monitor headers** — feed `X-RateLimit-*` into a small monitor that warns before
   the wall and pauses exactly until reset. See
   [implementation.md](references/implementation.md) § Step 5.

Target-website throttling is a separate ceiling from the platform API — cap it with
Crawlee's `maxConcurrency` / `maxRequestsPerMinute`
([implementation.md](references/implementation.md) § Crawlee-level concurrency).

## Output

Applying this skill produces a rate-aware Apify integration:

- A configured `ApifyClient` with an explicit retry envelope.
- Batched/chunked dataset writes that cut API-call count by orders of magnitude.
- A `p-queue`-gated call path that holds requests under 60 req/sec per resource.
- Staggered Actor starts and, optionally, a header-driven monitor that pauses before
  exhaustion — the net effect being zero (or transparently retried) 429s under load.

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| API 429 | `apify-client` auto-retries | Usually transparent; increase delays if persistent |
| Target site 429 | `statusCode === 429` in handler | Reduce `maxConcurrency`, add proxy rotation |
| Burst of starts | Starting 100+ runs at once | Stagger with 200ms delays |
| Large data push | Single 50MB dataset push | Chunk into 9MB batches |

## Examples

Worked end-to-end scenarios live in [examples.md](references/examples.md):

- **Bulk dataset push without 429s** — 50,000 rows in ~50 calls via chunked batching.
- **Fan-out reads through a queue** — 500 Actor reads held under 50 req/sec.
- **Launch 100 runs safely** — staggered starts, then parallel wait-for-finish.
- **Pause on header-driven exhaustion** — sleep exactly until the limit resets.

## Resources

- [Apify API Rate Limits](https://docs.apify.com/api/v2)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Crawlee Auto-scaling](https://crawlee.dev/js/docs/guides/configuration)

For security configuration, see `apify-security-basics`.
