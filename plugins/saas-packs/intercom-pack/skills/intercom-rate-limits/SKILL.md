---
name: intercom-rate-limits
description: |
  Handle Intercom API rate limits with backoff, queuing, and header monitoring.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Intercom.
  Trigger with phrases like "intercom rate limit", "intercom throttling",
  "intercom 429", "intercom retry", "intercom backoff", "intercom request limit".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Rate Limits

## Overview

Intercom enforces rate limits per app and per workspace. Handle 429 errors gracefully with exponential backoff, queue-based throttling, and proactive header monitoring.

## Rate Limit Tiers

| Scope | Limit | Notes |
|-------|-------|-------|
| Private app | 10,000 req/min | Per app |
| Public app (OAuth) | 10,000 req/min | Per app |
| Workspace total | 25,000 req/min | Across all apps |
| Search endpoints | 1,000 req/min | `/contacts/search`, `/conversations/search` |
| Scroll endpoints | 100 req/min | Bulk data export |

## Rate Limit Headers

Every response includes these headers:

```
X-RateLimit-Limit: 10000        # Max requests per window
X-RateLimit-Remaining: 9847     # Remaining requests
X-RateLimit-Reset: 1711100060   # Unix timestamp when window resets
```

## Instructions

### Step 1: Exponential Backoff with Header Awareness

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

### Step 2: Proactive Rate Limit Monitor

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

### Step 3: Queue-Based Request Throttling

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

### Step 4: Batch Operations to Reduce Request Count

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

### Step 5: Rate Limit Dashboard Metrics

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

## Error Handling

| Scenario | Strategy | Implementation |
|----------|----------|----------------|
| 429 with reset header | Wait until reset | Parse `X-RateLimit-Reset` |
| 429 without headers | Exponential backoff | 1s, 2s, 4s, 8s, 16s |
| Approaching limit (>90%) | Proactive throttle | Check remaining before request |
| Bulk operations | Queue-based | `p-queue` with `intervalCap` |
| Multiple apps hitting workspace limit | Coordinate | Shared rate limit monitor |

## Resources

- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Pagination](https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/pagination)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `intercom-security-basics`.
