---
name: intercom-rate-limits
description: 'Handle Intercom API rate limits with backoff, queuing, and header monitoring.

  Use when handling 429 errors, implementing retry logic,

  or optimizing API request throughput for Intercom.

  Trigger with phrases like "intercom rate limit", "intercom throttling",

  "intercom 429", "intercom retry", "intercom backoff", "intercom request limit".

  '
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Rate Limits

## Overview

Intercom enforces rate limits per app and per workspace. Handle 429 errors
gracefully with exponential backoff, queue-based throttling, and proactive
header monitoring. This skill gives you five composable defenses — a retry
wrapper, a live monitor, a request queue, request batching, and metrics — so a
high-volume integration stays under the ceiling instead of spraying 429s.

The full, copy-paste TypeScript for all five lives in
[references/implementation.md](references/implementation.md); this page carries
the limits, the header contract, and a lean skeleton so you can wire it up from
here and drill in for depth.

## Rate Limit Tiers

| Scope | Limit | Notes |
|-------|-------|-------|
| Private app | 10,000 req/min | Per app |
| Public app (OAuth) | 10,000 req/min | Per app |
| Workspace total | 25,000 req/min | Across all apps |
| Search endpoints | 1,000 req/min | `/contacts/search`, `/conversations/search` |
| Scroll endpoints | 100 req/min | Bulk data export |

## Rate Limit Headers

Every response includes these headers — read them to throttle proactively:

```
X-RateLimit-Limit: <max requests per window>
X-RateLimit-Remaining: <remaining requests>
X-RateLimit-Reset: <unix timestamp when window resets>
```

## Prerequisites

- An Intercom access token in `INTERCOM_ACCESS_TOKEN` (Developer Hub > Your App
  > Authentication) — all requests below send it as `Authorization: Bearer`.
- The official SDK: `npm install intercom-client`.
- For queue-based throttling: `npm install p-queue`.
- **Read** an existing client wrapper before editing so you extend it rather
  than duplicate it.

## Instructions

Apply the defenses in order — each builds on the previous one. Use **Write** to
create a new `intercom-rate-limit.ts` module, or **Edit** to fold these into an
existing client wrapper.

1. **Wrap every call in header-aware retry.** On `429`, wait until
   `X-RateLimit-Reset`; on `5xx`, exponential backoff with jitter. Skeleton:

   ```typescript
   async function withRateLimitRetry<T>(op: () => Promise<T>): Promise<T> {
     // On 429: delay = (X-RateLimit-Reset * 1000) - Date.now() + 1000
     // On 5xx: delay = baseDelay * 2^attempt + jitter, capped at maxDelayMs
   }
   ```

2. **Add a proactive monitor.** Feed response headers into a monitor and call
   `waitIfNeeded()` before firing when usage crosses ~90%, so you slow down
   *before* a 429.
3. **Throttle with a queue.** Route requests through a `p-queue` capped at
   ~150 req/s to keep bursts under the per-app ceiling.
4. **Batch to cut request count.** Replace N individual lookups with OR-batched
   `contacts.search` queries.
5. **Emit metrics.** Log `remaining`, `usage_percent`, and `ms_until_reset` so
   you can alert before saturation.

Full implementation for every step:
[references/implementation.md](references/implementation.md).

## Output

Wiring these in yields three concrete artifacts in your integration:

- **A resilient client wrapper** — every call routed through
  `withRateLimitRetry` + `queuedRequest`, so transient 429/5xx are absorbed
  automatically instead of surfacing as failures.
- **Proactive throttling** — the monitor pauses outbound traffic before the
  window is exhausted, converting hard 429s into short, controlled waits.
- **Observability** — structured `intercom.rate_limit` metrics (remaining,
  usage percent, ms-until-reset) ready for dashboards and alerts.

## Error Handling

| Scenario | Strategy | Implementation |
|----------|----------|----------------|
| 429 with reset header | Wait until reset | Parse `X-RateLimit-Reset` |
| 429 without headers | Exponential backoff | 1s, 2s, 4s, 8s, 16s |
| Approaching limit (>90%) | Proactive throttle | Check remaining before request |
| Bulk operations | Queue-based | `p-queue` with `intervalCap` |
| Multiple apps hitting workspace limit | Coordinate | Shared rate limit monitor |

## Examples

**Absorb a burst of contact lookups.** Fan out hundreds of `contacts.find`
calls without tripping the limit by routing each through the queue + retry
wrapper:

```typescript
const contacts = await Promise.all(
  userIds.map(id =>
    queuedRequest(() => client.contacts.find({ contactId: id }))
  )
);
```

**Precise wait on a 429.** When a response carries `X-RateLimit-Reset`, wait
exactly until that epoch (plus a 1s buffer) instead of guessing a backoff — see
Step 1 in [references/implementation.md](references/implementation.md).

**Batch email lookups.** Replace 100 single-contact requests with 10 OR-batched
searches — full `findContactsByEmails` helper in
[references/implementation.md](references/implementation.md).

## Resources

- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Pagination](https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/pagination)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [Full implementation](references/implementation.md) — the five defenses in copy-paste TypeScript

## Next Steps

Rate limiting is one layer of a hardened Intercom integration. Once retries and
throttling are in place, pair them with `intercom-common-errors` for full
status-code triage, and `intercom-security-basics` for token scoping and
webhook-signature verification.
