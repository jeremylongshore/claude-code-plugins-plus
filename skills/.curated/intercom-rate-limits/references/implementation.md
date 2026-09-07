# Intercom Rate Limit Implementation

The full, copy-paste implementation of the five rate-limit defenses referenced
from the skill: header-aware retry, a proactive monitor, queue-based
throttling, batching, and metrics. Each block is standalone TypeScript against
the official `intercom-client` SDK.

## Step 1: Exponential Backoff with Header Awareness

Retry `429` and `5xx` responses. On a `429`, prefer the `X-RateLimit-Reset`
header for a precise wait; otherwise fall back to exponential backoff. Server
errors get exponential backoff with jitter.

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

async function withRateLimitRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (!(err instanceof IntercomError)) throw err;
      if (err.statusCode !== 429 && (err.statusCode ?? 0) < 500) throw err;
      if (attempt === config.maxRetries) throw err;

      let delayMs: number;

      if (err.statusCode === 429) {
        // Use X-RateLimit-Reset header for precise wait time
        const resetTimestamp = err.headers?.["x-ratelimit-reset"];
        if (resetTimestamp) {
          delayMs = Math.max(
            (parseInt(resetTimestamp) * 1000) - Date.now() + 1000,
            1000
          );
        } else {
          delayMs = config.baseDelayMs * Math.pow(2, attempt);
        }
      } else {
        // Server errors: exponential backoff with jitter
        delayMs = config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
      }

      delayMs = Math.min(delayMs, config.maxDelayMs);
      console.warn(`[Intercom] ${err.statusCode} - Retry ${attempt + 1}/${config.maxRetries} in ${delayMs}ms`);
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
  throw new Error("Unreachable");
}
```

## Step 2: Proactive Rate Limit Monitor

Track the live rate-limit window from response headers so you can slow down
*before* hitting a `429`. `10000` is the default per-app request ceiling used
until real headers arrive.

```typescript
class IntercomRateLimitMonitor {
  private remaining = 10000;
  private limit = 10000;
  private resetAt = 0;

  updateFromHeaders(headers: Record<string, string>): void {
    if (headers["x-ratelimit-remaining"]) {
      this.remaining = parseInt(headers["x-ratelimit-remaining"]);
    }
    if (headers["x-ratelimit-limit"]) {
      this.limit = parseInt(headers["x-ratelimit-limit"]);
    }
    if (headers["x-ratelimit-reset"]) {
      this.resetAt = parseInt(headers["x-ratelimit-reset"]) * 1000;
    }
  }

  get usagePercent(): number {
    return ((this.limit - this.remaining) / this.limit) * 100;
  }

  shouldThrottle(threshold = 90): boolean {
    return this.usagePercent > threshold && Date.now() < this.resetAt;
  }

  msUntilReset(): number {
    return Math.max(0, this.resetAt - Date.now());
  }

  async waitIfNeeded(threshold = 90): Promise<void> {
    if (this.shouldThrottle(threshold)) {
      const waitMs = this.msUntilReset() + 1000;
      console.warn(`[Intercom] ${this.usagePercent.toFixed(0)}% rate used, waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
    }
  }
}
```

## Step 3: Queue-Based Request Throttling

Cap outbound request rate with `p-queue` so bursts never exceed the window.
`150` req/s stays well under the 10,000 req/min per-app ceiling.

```typescript
import PQueue from "p-queue";

// Limit to 150 requests/second (well under 10,000/min)
const intercomQueue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 150,
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return intercomQueue.add(() => withRateLimitRetry(operation));
}

// Usage - all requests automatically throttled
const contacts = await Promise.all(
  userIds.map(id =>
    queuedRequest(() => client.contacts.find({ contactId: id }))
  )
);
```

## Step 4: Batch Operations to Reduce Request Count

Replace N individual lookups with OR-batched search queries. Fewer requests
means less pressure on the window.

```typescript
// Instead of N individual contact lookups, use search
async function findContactsByEmails(
  client: IntercomClient,
  emails: string[]
): Promise<Map<string, any>> {
  const results = new Map();

  // Search supports up to 50 results per page
  // Use OR queries to batch lookups
  for (let i = 0; i < emails.length; i += 10) {
    const batch = emails.slice(i, i + 10);
    const searchResult = await queuedRequest(() =>
      client.contacts.search({
        query: {
          operator: "OR",
          value: batch.map(email => ({
            field: "email",
            operator: "=",
            value: email,
          })),
        },
      })
    );

    for (const contact of searchResult.data) {
      results.set(contact.email, contact);
    }
  }

  return results;
}
```

## Step 5: Rate Limit Dashboard Metrics

Emit structured usage metrics so you can alert before saturation.

```typescript
// Track rate limit usage for monitoring
function logRateLimitMetrics(monitor: IntercomRateLimitMonitor): void {
  console.log(JSON.stringify({
    metric: "intercom.rate_limit",
    remaining: monitor["remaining"],
    usage_percent: monitor.usagePercent,
    ms_until_reset: monitor.msUntilReset(),
    timestamp: new Date().toISOString(),
  }));
}
```
