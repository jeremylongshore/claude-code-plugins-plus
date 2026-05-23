---
name: hubspot-rate-limit-survival
description: |
  Survive HubSpot API rate limits at production scale. Covers daily 500K portal quota,
  per-10s burst limits, batch API efficiency (100x), token bucket pattern, queue-based
  worker architecture, and Retry-After header parsing. Use when a sync job burns the
  daily quota before 8am, when a parallelized batch job retry-storms on 429s, when
  single-record reads waste 99% of available throughput, or when instrumenting a
  rate-limit dashboard for an Ops Hub Enterprise portal. Trigger with "hubspot rate
  limit", "hubspot quota", "hubspot 429", "hubspot batch API", "hubspot token bucket",
  "hubspot throttle", "hubspot daily limit exhausted", "hubspot Ops Hub rate limit".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - rate-limits
  - performance
  - data-engineering
---

# HubSpot Rate Limit Survival

## Overview

Rate-limit your HubSpot integration so it survives production volume without burning the portal's daily quota before lunch. This skill covers the six failure modes that take down integrations at scale and gives you the code to prevent each one.

**Key invariant:** HubSpot rate limits are portal-scoped, not app-scoped. Every private app and OAuth app in the same portal shares the same daily and per-10s buckets. There is no per-app isolation.

The six production failures this skill prevents:

1. **Daily quota burnout** — a naive sync of 5M contacts at 100 records/call requires 50,000 API calls. A misconfigured parallel worker pool exhausts the 500K/day quota in under 90 minutes, leaving the portal dark for 22 hours.
2. **Burst limit ignorance** — parallelizing 20 concurrent requests saturates the 100 req/10s window instantly. The 429 retry storm then burns the daily budget too. The burst limit and daily quota are two independent counters.
3. **Ignoring batch APIs** — `GET /contacts/{id}` costs 1 quota unit and returns 1 record. `POST /contacts/batch/read` with 100 IDs costs 1 unit and returns 100 records. Single-record reads waste 99% of available throughput.
4. **Retry-After ignored** — a 429 includes `Retry-After: N`. Backing off by 1s when N=30 produces 29 consecutive failures. Backing off by 30s when N=1 adds unnecessary latency. Always parse and honor the header exactly.
5. **Daily limit vs per-10s confusion** — these are two independent systems. Burning the burst window does not decrement the daily counter. Exhausting the daily counter does not care about the per-10s rate. Conflating them breaks rate-limit logic.
6. **Operations Hub Enterprise gating** — the 100 req/s sustained rate is gated on Ops Hub Enterprise. A Starter account assuming that throughput gets 429s at 10x the expected rate with no clear signal that the limit tier is wrong.

## Prerequisites

- Node.js 18+ or Python 3.10+
- HubSpot private app token or OAuth access token
- `@hubspot/api-client` (npm) or `hubspot` (pip) for SDK-based integrations
- For queue-based architecture: Redis 6+ with `bullmq` (npm) or `celery`+`redis-py` (Python)
- Portal Settings → Integrations → Private Apps to confirm the plan tier

**Auth:** Every API call requires `Authorization: Bearer {token}`. For token acquisition and caching, see `hubspot-auth` skill. This skill assumes a valid token is already available.

## Instructions

Build in this order. Steps 1–3 are mandatory. Steps 4–6 apply when volume exceeds ~50,000 calls/day or when multiple apps share the portal.

### Step 1: Read rate-limit headers on every response

Every HubSpot response carries both bucket states. Never fly blind.

```typescript
interface RateLimitState {
  dailyLimit: number;
  dailyRemaining: number;
  windowMs: number;
  windowMax: number;
  windowRemaining: number;
}

let rl: RateLimitState = {
  dailyLimit: 500_000, dailyRemaining: 500_000,
  windowMs: 10_000, windowMax: 100, windowRemaining: 100,
};

function updateRateLimitState(headers: Headers): void {
  if (headers.get("X-HubSpot-RateLimit-Daily"))
    rl.dailyLimit = parseInt(headers.get("X-HubSpot-RateLimit-Daily")!, 10);
  if (headers.get("X-HubSpot-RateLimit-Daily-Remaining"))
    rl.dailyRemaining = parseInt(headers.get("X-HubSpot-RateLimit-Daily-Remaining")!, 10);
  if (headers.get("X-HubSpot-RateLimit-Max"))
    rl.windowMax = parseInt(headers.get("X-HubSpot-RateLimit-Max")!, 10);
  if (headers.get("X-HubSpot-RateLimit-Remaining"))
    rl.windowRemaining = parseInt(headers.get("X-HubSpot-RateLimit-Remaining")!, 10);

  const pctUsed = 1 - rl.dailyRemaining / rl.dailyLimit;
  console.log(JSON.stringify({
    event: "hubspot_rate_limit_state",
    daily_remaining: rl.dailyRemaining,
    daily_pct_used: parseFloat(pctUsed.toFixed(4)),
    window_remaining: rl.windowRemaining,
  }));
}
```

### Step 2: Token bucket (neutralizes burst limit ignorance)

A token bucket is the correct primitive for the per-10s burst limit. Callers block until a slot is available instead of firing and failing.

```typescript
class TokenBucket {
  private tokens: number;
  private lastRefillAt: number;

  constructor(
    private readonly capacity: number,
    private readonly refillRatePerMs: number,
  ) {
    this.tokens = capacity;
    this.lastRefillAt = Date.now();
  }

  consume(count = 1): number {  // returns ms to wait; 0 = immediate
    const now = Date.now();
    this.tokens = Math.min(
      this.capacity,
      this.tokens + (now - this.lastRefillAt) * this.refillRatePerMs,
    );
    this.lastRefillAt = now;
    if (this.tokens >= count) { this.tokens -= count; return 0; }
    return Math.ceil((count - this.tokens) / this.refillRatePerMs);
  }
}

// Private app, standard plan: 100 req/10s = 0.01 req/ms
// Ops Hub Enterprise: 100 req/s = 0.1 req/ms
const BUCKETS = {
  starter:            new TokenBucket(100,  10 / 10_000),
  professional:       new TokenBucket(150,  15 / 10_000),
  ops_hub_enterprise: new TokenBucket(1000, 100 / 10_000),
};

type PlanTier = keyof typeof BUCKETS;
let activeBucket: TokenBucket = BUCKETS.starter;

export function configurePlanTier(tier: PlanTier): void {
  activeBucket = BUCKETS[tier];
}

export async function acquireToken(): Promise<void> {
  const waitMs = activeBucket.consume();
  if (waitMs > 0) await new Promise((r) => setTimeout(r, waitMs));
}
```

### Step 3: Retry-After parser and hubspotFetch (neutralizes ignored 429s)

Honor the exact backoff value HubSpot specifies. Full implementation with mock-server test harness in [`implementation-guide.md`](references/implementation-guide.md).

```typescript
function parseRetryAfterMs(headers: Headers): number | null {
  const raw = headers.get("Retry-After");
  if (!raw) return null;
  const s = parseInt(raw, 10);
  return isNaN(s) ? null : s * 1_000;
}

export async function hubspotFetch(
  path: string,
  init: RequestInit = {},
  maxAttempts = 5,
): Promise<Response> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    await acquireToken();
    const res = await fetch(`https://api.hubapi.com${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${process.env.HUBSPOT_ACCESS_TOKEN!}`,
        "Content-Type": "application/json",
        ...init.headers,
      },
    });
    updateRateLimitState(res.headers);
    if (res.ok) return res;

    const retryable = res.status === 429 || (res.status >= 500 && res.status < 600);
    if (!retryable || attempt === maxAttempts) throw new Error(`HubSpot ${res.status}: ${path}`);

    const delayMs = parseRetryAfterMs(res.headers)
      ?? Math.random() * Math.min(60_000, 500 * 2 ** attempt);
    await new Promise((r) => setTimeout(r, delayMs));
  }
  throw new Error("unreachable");
}
```

### Step 4: Batch API wrapper (neutralizes single-record waste)

Auto-chunk any array of IDs into groups of 100. Each chunk costs 1 quota unit.

```typescript
const BATCH_SIZE = 100; // HubSpot hard limit

function chunk<T>(arr: T[], size = BATCH_SIZE): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) chunks.push(arr.slice(i, i + size));
  return chunks;
}

export async function batchRead(
  objectType: "contacts" | "companies" | "deals" | "tickets",
  ids: string[],
  properties: string[],
): Promise<{ results: unknown[]; errors: unknown[] }> {
  const results: unknown[] = [];
  const errors: unknown[] = [];
  for (const batch of chunk(ids)) {
    const res = await hubspotFetch(`/crm/v3/objects/${objectType}/batch/read`, {
      method: "POST",
      body: JSON.stringify({ inputs: batch.map((id) => ({ id })), properties }),
    });
    const body = await res.json() as { results: unknown[]; errors?: unknown[] };
    results.push(...body.results);
    if (body.errors) errors.push(...body.errors);
  }
  return { results, errors };
}
```

### Step 5: Daily quota shutoff valve (neutralizes quota burnout)

Halt lower-priority work before the portal goes dark.

```typescript
type Priority = "critical" | "high" | "normal" | "low";

const SHUTOFF: Record<Priority, number> = {
  critical: 0.99, high: 0.95, normal: 0.90, low: 0.80,
};

export function assertDailyQuotaAvailable(priority: Priority): void {
  const pctConsumed = 1 - rl.dailyRemaining / rl.dailyLimit;
  if (pctConsumed >= SHUTOFF[priority]) {
    throw new Error(
      `Daily quota shutoff: ${(pctConsumed * 100).toFixed(1)}% consumed — ` +
      `${priority} priority requests halted`,
    );
  }
}
```

### Step 6: Plan-tier auto-detection at startup

Read `X-HubSpot-RateLimit-Max` from the first response instead of hard-coding the tier.

```typescript
export async function detectAndConfigurePlanTier(): Promise<PlanTier> {
  const res = await fetch(
    "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
    { headers: { Authorization: `Bearer ${process.env.HUBSPOT_ACCESS_TOKEN!}` } },
  );
  const max = parseInt(res.headers.get("X-HubSpot-RateLimit-Max") ?? "100", 10);
  const tier: PlanTier =
    max >= 1000 ? "ops_hub_enterprise" :
    max >= 150  ? "professional"       :
                  "starter";
  configurePlanTier(tier);
  console.log(`HubSpot plan tier: ${tier} (window max: ${max})`);
  return tier;
}
```

## Error Handling

| HTTP Status | Error Code | Root Cause | Action |
|---|---|---|---|
| `429` | `RATE_LIMIT` / `policyName: SECONDLY` | Per-10s burst window exhausted | Read `Retry-After`; wait exactly that many seconds |
| `429` | `RATE_LIMIT` / `policyName: DAILY` | 500K/day quota exhausted | Stop all non-critical calls; resume after midnight UTC |
| `400` | `BATCH_SIZE_EXCEEDED` | More than 100 IDs in batch payload | Chunk inputs to max 100; `batchRead` wrapper handles this |
| `400` | `INVALID_BATCH_REQUEST` | Malformed batch payload | Verify `inputs` is `[{id: string}]`; `properties` is an array |
| `403` | `MISSING_SCOPES` | Token lacks scope for the object type | Add required scope in HubSpot Settings → Private Apps |
| `403` | `PORTAL_NOT_ALLOWED` | Ops Hub Enterprise feature on lower-tier plan | Reduce throughput target; verify plan tier via `X-HubSpot-RateLimit-Max` |
| `5xx` | `INTERNAL_ERROR` | HubSpot transient error | Retry with exponential backoff; typically resolves within 60s |

**Diagnose daily vs burst 429:**

```bash
curl -sv "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" 2>&1 \
  | grep -E "< (X-HubSpot|Retry-After|HTTP)"
# Retry-After 1-30s + Daily-Remaining > 0 → burst window
# Daily-Remaining = 0 → daily quota
```

## Examples

### Baseline rate-limit health check

```bash
curl -sI "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "X-HubSpot-RateLimit\|Retry-After"
```

### Batch read 500 contacts (5 quota units instead of 500)

```bash
curl -s "https://api.hubapi.com/crm/v3/objects/contacts/batch/read" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs":[{"id":"1"},{"id":"2"},{"id":"3"}],"properties":["email","firstname"]}' \
  | jq '{count: (.results | length), errors: (.errors | length)}'
```

### Python quota monitor (cron-safe, 1 quota unit per run)

```python
import os, json, requests

def check_quota() -> dict:
    r = requests.get(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {os.environ['HUBSPOT_ACCESS_TOKEN']}"},
        params={"limit": 1},
    )
    daily = int(r.headers.get("X-HubSpot-RateLimit-Daily", 500_000))
    rem   = int(r.headers.get("X-HubSpot-RateLimit-Daily-Remaining", daily))
    pct   = 1 - rem / daily
    return {"daily_remaining": rem, "pct_consumed": round(pct, 4),
            "shutoff_active": pct >= 0.90,
            "window_remaining": int(r.headers.get("X-HubSpot-RateLimit-Remaining", 0))}

print(json.dumps(check_quota(), indent=2))
```

## Output

- Token bucket module calibrated to portal plan tier; callers block rather than fire-and-fail
- `hubspotFetch` wrapper parsing `Retry-After` on every 429 and backing off by the server-specified duration
- Batch read wrapper auto-chunking any array into groups of 100, reducing quota consumption up to 100x
- Structured log events for every rate-limit state update, suitable for Datadog / Prometheus / CloudWatch
- Priority-tiered shutoff valve halting background jobs at 80% and critical jobs at 99%
- Plan-tier auto-detection from response headers so the correct burst limit is applied without hard-coding

## Resources

- [HubSpot API Usage and Rate Limits](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [CRM Batch APIs Reference](https://developers.hubspot.com/docs/api/crm/contacts)
- [HubSpot API Error Handling](https://developers.hubspot.com/docs/api-reference/error-handling)
- [Operations Hub Overview](https://www.hubspot.com/products/operations)
- [HubSpot Status Page](https://status.hubspot.com)
- [`API_REFERENCE.md`](references/API_REFERENCE.md) — all rate-limit headers, limit tiers by plan, batch endpoint signatures, 429 response shapes
- [`implementation-guide.md`](references/implementation-guide.md) — Python token bucket, Bull/Redis queue worker, daily quota dashboard metrics, Retry-After parser, batch chunker, mock-server test harness
