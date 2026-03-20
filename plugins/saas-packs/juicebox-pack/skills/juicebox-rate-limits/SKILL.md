---
name: juicebox-rate-limits
description: |
  Implement Juicebox rate limiting and backoff.
  Use when handling API quotas, implementing retry logic,
  or optimizing request throughput.
  Trigger with phrases like "juicebox rate limit", "juicebox quota",
  "juicebox throttling", "juicebox backoff".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Rate Limits

## Overview

Implement production-grade rate limiting for Juicebox API integrations. Covers parsing rate limit headers from every response, a token bucket rate limiter that respects server-reported limits, exponential backoff with jitter for 429 recovery, a priority request queue for bulk sourcing operations, and real-time quota tracking across search and enrichment endpoints.

## Prerequisites

- Juicebox API credentials configured (`JUICEBOX_USERNAME`, `JUICEBOX_API_TOKEN`)
- Node.js 18+ (uses native `fetch` and `Headers`)
- Understanding of Juicebox's rate limit tiers (varies by plan)
- `curl` available for inspecting rate limit headers

## Instructions

### Step 1: Parse Rate Limit Headers

Every Juicebox API response includes three rate limit headers. Parse them on every response to maintain a live view of your remaining quota.

```typescript
// lib/rate-limit-headers.ts
export interface RateLimitState {
  limit: number;         // Max requests allowed per window
  remaining: number;     // Requests left in current window
  resetAt: Date;         // When the window resets (UTC)
  retryAfter: number;    // Seconds to wait (only present on 429)
}

export function parseRateLimitHeaders(headers: Headers): RateLimitState {
  return {
    limit: parseInt(headers.get("X-RateLimit-Limit") ?? "100", 10),
    remaining: parseInt(headers.get("X-RateLimit-Remaining") ?? "100", 10),
    resetAt: new Date(
      parseInt(headers.get("X-RateLimit-Reset") ?? String(Date.now() / 1000), 10) * 1000
    ),
    retryAfter: parseInt(headers.get("Retry-After") ?? "0", 10),
  };
}

export function shouldThrottle(state: RateLimitState): boolean {
  // Proactively throttle when below 10% remaining
  return state.remaining < state.limit * 0.1;
}

export function msUntilReset(state: RateLimitState): number {
  return Math.max(0, state.resetAt.getTime() - Date.now());
}
```

Verify headers against the live API:

```bash
# Inspect rate limit headers on a real request
curl -s -D - \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=engineer&limit=1" \
  | grep -iE "x-ratelimit|retry-after"
```

### Step 2: Build a Token Bucket Rate Limiter

The token bucket algorithm smooths out burst traffic and respects the server's reported limit. When a response arrives, update the bucket with the server's `X-RateLimit-Remaining` value to stay synchronized.

```typescript
// lib/token-bucket.ts
export class TokenBucketRateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly refillRate: number; // tokens per millisecond

  constructor(
    private readonly maxTokens: number,
    windowMs: number = 60_000 // default: 1 minute window
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
    this.refillRate = maxTokens / windowMs;
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  async acquire(): Promise<void> {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }

    // Wait until one token is available
    const waitMs = (1 - this.tokens) / this.refillRate;
    await new Promise((resolve) => setTimeout(resolve, Math.ceil(waitMs)));
    this.tokens -= 1;
  }

  // Sync with server-reported state after each response
  syncWithServer(state: RateLimitState): void {
    this.tokens = state.remaining;
    this.lastRefill = Date.now();
  }

  get availableTokens(): number {
    this.refill();
    return Math.floor(this.tokens);
  }
}
```

### Step 3: Add Exponential Backoff with Jitter

When a 429 does arrive, use exponential backoff with full jitter to avoid thundering herd problems when multiple clients retry simultaneously.

```typescript
// lib/backoff.ts
export interface BackoffOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitter: boolean;
}

const DEFAULT_BACKOFF: BackoffOptions = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 60_000,
  jitter: true,
};

export async function withExponentialBackoff<T>(
  fn: () => Promise<Response>,
  options: Partial<BackoffOptions> = {}
): Promise<Response> {
  const opts = { ...DEFAULT_BACKOFF, ...options };

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    const response = await fn();

    if (response.ok) return response;

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get("Retry-After") ?? "0", 10);

      // Use server's Retry-After if provided, otherwise calculate backoff
      let delayMs: number;
      if (retryAfter > 0) {
        delayMs = retryAfter * 1000;
      } else {
        delayMs = Math.min(
          opts.baseDelayMs * Math.pow(2, attempt),
          opts.maxDelayMs
        );
      }

      // Add jitter: random value between 0 and delayMs
      if (opts.jitter) {
        delayMs = Math.floor(Math.random() * delayMs);
      }

      console.warn(
        `[Juicebox] 429 rate limited. Attempt ${attempt + 1}/${opts.maxRetries}. ` +
        `Waiting ${delayMs}ms before retry.`
      );

      if (attempt < opts.maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        continue;
      }
    }

    // Non-429 error or exhausted retries
    if (attempt === opts.maxRetries) {
      throw new Error(
        `Juicebox API request failed after ${opts.maxRetries} retries. ` +
        `Last status: ${response.status}`
      );
    }
  }

  throw new Error("Unreachable");
}
```

### Step 4: Implement a Priority Request Queue

For bulk operations (e.g., sourcing 500 candidates), queue requests with priorities so critical lookups skip ahead of background enrichments.

```typescript
// lib/request-queue.ts
import { TokenBucketRateLimiter } from "./token-bucket";
import { parseRateLimitHeaders } from "./rate-limit-headers";
import { withExponentialBackoff } from "./backoff";

type Priority = "critical" | "normal" | "background";

interface QueuedRequest<T> {
  priority: Priority;
  execute: () => Promise<Response>;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
}

const PRIORITY_ORDER: Record<Priority, number> = {
  critical: 0,
  normal: 1,
  background: 2,
};

export class RateLimitedQueue {
  private queue: QueuedRequest<Response>[] = [];
  private processing = false;
  private readonly limiter: TokenBucketRateLimiter;

  constructor(requestsPerMinute: number) {
    this.limiter = new TokenBucketRateLimiter(requestsPerMinute);
  }

  async enqueue(
    execute: () => Promise<Response>,
    priority: Priority = "normal"
  ): Promise<Response> {
    return new Promise<Response>((resolve, reject) => {
      this.queue.push({ priority, execute, resolve, reject });
      // Sort by priority after insertion
      this.queue.sort(
        (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
      );
      this.processQueue();
    });
  }

  private async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    while (this.queue.length > 0) {
      await this.limiter.acquire();

      const item = this.queue.shift()!;
      try {
        const response = await withExponentialBackoff(item.execute);
        // Sync rate limiter with server state
        const state = parseRateLimitHeaders(response.headers);
        this.limiter.syncWithServer(state);
        item.resolve(response);
      } catch (error) {
        item.reject(error as Error);
      }
    }

    this.processing = false;
  }

  get pendingCount(): number {
    return this.queue.length;
  }
}
```

### Step 5: Track Quota Across Endpoints

Different Juicebox endpoints may have separate rate limits. Track quota per-endpoint to avoid one category of requests starving another.

```typescript
// lib/quota-tracker.ts
import { RateLimitState, parseRateLimitHeaders } from "./rate-limit-headers";

type Endpoint = "search" | "profiles" | "enrichments";

export class QuotaTracker {
  private state = new Map<Endpoint, RateLimitState>();
  private dailyCounts = new Map<Endpoint, number>();
  private resetTime: Date;

  constructor() {
    this.resetTime = this.nextMidnightUTC();
  }

  updateFromResponse(endpoint: Endpoint, headers: Headers): void {
    const state = parseRateLimitHeaders(headers);
    this.state.set(endpoint, state);
    this.incrementDaily(endpoint);
  }

  getEndpointState(endpoint: Endpoint): RateLimitState | undefined {
    return this.state.get(endpoint);
  }

  canMakeRequest(endpoint: Endpoint): boolean {
    const state = this.state.get(endpoint);
    if (!state) return true; // No data yet, allow
    return state.remaining > 0;
  }

  getDailySummary(): Record<Endpoint, number> {
    this.maybeResetDaily();
    return Object.fromEntries(this.dailyCounts) as Record<Endpoint, number>;
  }

  getFullReport(): string {
    const lines: string[] = ["=== Juicebox Quota Report ==="];
    for (const endpoint of ["search", "profiles", "enrichments"] as Endpoint[]) {
      const state = this.state.get(endpoint);
      const daily = this.dailyCounts.get(endpoint) ?? 0;
      if (state) {
        lines.push(
          `${endpoint}: ${state.remaining}/${state.limit} remaining ` +
          `(resets ${state.resetAt.toISOString()}) — ${daily} calls today`
        );
      } else {
        lines.push(`${endpoint}: no data yet — ${daily} calls today`);
      }
    }
    return lines.join("\n");
  }

  private incrementDaily(endpoint: Endpoint): void {
    this.maybeResetDaily();
    this.dailyCounts.set(endpoint, (this.dailyCounts.get(endpoint) ?? 0) + 1);
  }

  private maybeResetDaily(): void {
    if (Date.now() > this.resetTime.getTime()) {
      this.dailyCounts.clear();
      this.resetTime = this.nextMidnightUTC();
    }
  }

  private nextMidnightUTC(): Date {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() + 1);
    d.setUTCHours(0, 0, 0, 0);
    return d;
  }
}
```

## Output

- `lib/rate-limit-headers.ts` — Header parser with proactive throttle detection
- `lib/token-bucket.ts` — Token bucket rate limiter synchronized with server state
- `lib/backoff.ts` — Exponential backoff with jitter and Retry-After support
- `lib/request-queue.ts` — Priority request queue for bulk operations
- `lib/quota-tracker.ts` — Per-endpoint quota tracking with daily summaries

## Error Handling

| Scenario | Strategy | Implementation |
|----------|----------|----------------|
| 429 with `Retry-After` header | Wait the exact duration specified by the server | `withExponentialBackoff` reads `Retry-After` first |
| 429 without `Retry-After` | Exponential backoff: 1s, 2s, 4s, 8s, 16s with jitter | `backoff.ts` with `jitter: true` |
| Approaching limit (< 10% remaining) | Proactive throttling before 429 occurs | `shouldThrottle()` in header parser |
| Daily quota exhausted | Queue requests for next UTC midnight | `QuotaTracker.canMakeRequest()` returns false |
| Multiple endpoints competing | Per-endpoint tracking prevents starvation | `QuotaTracker` maintains separate state per endpoint |

## Examples

### Rate-Limited Search with Queue

```typescript
import { RateLimitedQueue } from "./lib/request-queue";
import { QuotaTracker } from "./lib/quota-tracker";

const queue = new RateLimitedQueue(60); // 60 requests/minute
const quota = new QuotaTracker();
const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;

// Queue a critical search (skips ahead of background tasks)
const searchResponse = await queue.enqueue(
  () =>
    fetch(
      `https://api.juicebox.ai/api/v1/search?q=${encodeURIComponent("staff engineer")}&limit=50`,
      { headers: { Authorization: authHeader } }
    ),
  "critical"
);

quota.updateFromResponse("search", searchResponse.headers);
const candidates = await searchResponse.json();
console.log(`Found ${candidates.profiles.length} candidates`);

// Queue background enrichments at lower priority
for (const profile of candidates.profiles.slice(0, 10)) {
  queue.enqueue(
    () =>
      fetch(`https://api.juicebox.ai/api/v1/profiles/${profile.id}`, {
        headers: { Authorization: authHeader },
      }),
    "background"
  );
}

console.log(`${queue.pendingCount} background requests queued`);
console.log(quota.getFullReport());
```

### Inspecting Rate Limits from CLI

```bash
# Make a request and extract rate limit state
curl -s -D /tmp/jb-headers \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=test&limit=1" > /dev/null

echo "Rate limit headers:"
grep -iE "x-ratelimit|retry-after" /tmp/jb-headers

# Calculate seconds until reset
RESET=$(grep -i "x-ratelimit-reset" /tmp/jb-headers | awk '{print $2}' | tr -d '\r')
echo "Resets in $(( RESET - $(date +%s) )) seconds"
```

### Bulk Operation with Quota Safety

```typescript
import { RateLimitedQueue } from "./lib/request-queue";
import { QuotaTracker } from "./lib/quota-tracker";

const queue = new RateLimitedQueue(30); // Conservative: 30 req/min
const quota = new QuotaTracker();
const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;

const queries = [
  "senior frontend engineer React",
  "staff backend engineer Go",
  "principal ML engineer PyTorch",
  "engineering manager distributed systems",
];

for (const q of queries) {
  if (!quota.canMakeRequest("search")) {
    console.warn("Search quota exhausted. Remaining requests will queue for reset.");
  }

  const res = await queue.enqueue(
    () =>
      fetch(
        `https://api.juicebox.ai/api/v1/search?q=${encodeURIComponent(q)}&limit=25`,
        { headers: { Authorization: authHeader } }
      ),
    "normal"
  );

  quota.updateFromResponse("search", res.headers);
  const data = await res.json();
  console.log(`"${q}" → ${data.profiles.length} results`);
}

console.log("\n" + quota.getFullReport());
```

## Resources

- [Juicebox Rate Limits Documentation](https://juicebox.ai/docs/rate-limits)
- [API Quota Dashboard](https://app.juicebox.ai/usage)
- [Retry-After Header (RFC 7231)](https://tools.ietf.org/html/rfc7231#section-7.1.3)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)

## Next Steps

After implementing rate limiting, see `juicebox-cost-tuning` for caching and deduplication strategies, or `juicebox-security-basics` for securing API credentials.
