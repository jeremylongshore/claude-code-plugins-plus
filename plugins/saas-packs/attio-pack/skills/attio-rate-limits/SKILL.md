---
name: attio-rate-limits
description: |
  Handle Attio API rate limits with exponential backoff, queue-based
  throttling, and Retry-After header parsing.
  Trigger: "attio rate limit", "attio 429", "attio throttling",
  "attio retry", "attio backoff", "attio too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Rate Limits

## Overview

Attio uses a **sliding window algorithm** with a **10-second window**. Rate limit scores are summed across all apps and access tokens hitting the API. When exceeded, you get HTTP 429 with a `Retry-After` header containing a date (usually the next second). Attio may temporarily reduce limits during incidents.

## Rate Limit Response

```
HTTP/1.1 429 Too Many Requests
Retry-After: Sat, 22 Mar 2025 14:30:01 GMT
Content-Type: application/json

{
  "status_code": 429,
  "type": "rate_limit_error",
  "code": "rate_limit_exceeded",
  "message": "Rate limit exceeded, please try again later"
}
```

**Key fact:** The `Retry-After` header is a date string (not seconds). Parse it as a Date to calculate wait time.

## Instructions

### Step 1: Parse Retry-After Header

```typescript
function parseRetryAfter(headers: Headers): number {
  const retryAfter = headers.get("Retry-After");
  if (!retryAfter) return 1000; // Default 1s

  // Attio sends a date string
  const retryDate = new Date(retryAfter);
  const waitMs = retryDate.getTime() - Date.now();
  return Math.max(waitMs, 100); // Minimum 100ms
}
```

### Step 2: Exponential Backoff with Retry-After Awareness

```typescript
import { AttioApiError } from "./client";

interface RetryConfig {
  maxRetries: number;
  baseMs: number;
  maxMs: number;
}

async function withRateLimitRetry<T>(
  operation: () => Promise<{ data: T; headers?: Headers }>,
  config: RetryConfig = { maxRetries: 5, baseMs: 1000, maxMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const result = await operation();
      return result.data;
    } catch (err) {
      if (attempt === config.maxRetries) throw err;

      if (err instanceof AttioApiError) {
        if (!err.retryable) throw err; // Only retry 429 and 5xx

        // Use Retry-After if available, otherwise exponential backoff
        const backoff = config.baseMs * Math.pow(2, attempt);
        const jitter = Math.random() * 500;
        const delay = Math.min(backoff + jitter, config.maxMs);

        console.warn(
          `Attio ${err.statusCode} on attempt ${attempt + 1}/${config.maxRetries}. ` +
          `Retrying in ${delay.toFixed(0)}ms...`
        );
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw err;
      }
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Queue-Based Throttling

Prevent 429s proactively by limiting concurrency and request rate:

```typescript
import PQueue from "p-queue";

// Attio: sliding 10-second window. Stay well under the limit.
const attioQueue = new PQueue({
  concurrency: 5,           // Max parallel requests
  interval: 1000,           // 1 second interval
  intervalCap: 8,           // Max 8 requests per second
});

async function throttledAttioCall<T>(
  operation: () => Promise<T>
): Promise<T> {
  return attioQueue.add(operation) as Promise<T>;
}

// Usage
const results = await Promise.all(
  recordIds.map((id) =>
    throttledAttioCall(() =>
      client.get(`/objects/people/records/${id}`)
    )
  )
);
```

### Step 4: Rate Limit Monitor

```typescript
class AttioRateLimitMonitor {
  private windowStart = Date.now();
  private requestCount = 0;

  recordRequest(responseHeaders?: Headers): void {
    const now = Date.now();
    // Reset counter every 10 seconds (Attio's sliding window)
    if (now - this.windowStart > 10000) {
      this.windowStart = now;
      this.requestCount = 0;
    }
    this.requestCount++;
  }

  shouldThrottle(threshold = 0.8): boolean {
    // Conservative: throttle at 80% of observed capacity
    return this.requestCount > 50 * threshold; // Adjust 50 based on your limit
  }

  getStats(): { requestsInWindow: number; windowAgeMs: number } {
    return {
      requestsInWindow: this.requestCount,
      windowAgeMs: Date.now() - this.windowStart,
    };
  }
}
```

### Step 5: Batch Operations to Reduce Request Count

```typescript
// Instead of N individual GET calls, use the query endpoint (1 POST)
// BAD: N requests
for (const email of emails) {
  await client.post("/objects/people/records/query", {
    filter: { email_addresses: email },
    limit: 1,
  });
}

// GOOD: 1 request with $in filter
const results = await client.post("/objects/people/records/query", {
  filter: {
    email_addresses: {
      email_address: { $in: emails },
    },
  },
  limit: emails.length,
});
```

### Step 6: Circuit Breaker for Sustained Rate Limiting

```typescript
class AttioCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  private readonly threshold = 5;       // Open after 5 consecutive 429s
  private readonly resetMs = 30000;     // Try again after 30s

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetMs) {
        this.state = "half-open";
      } else {
        throw new Error("Circuit open: Attio rate limited. Retry after 30s.");
      }
    }

    try {
      const result = await operation();
      this.failures = 0;
      this.state = "closed";
      return result;
    } catch (err) {
      if (err instanceof AttioApiError && err.statusCode === 429) {
        this.failures++;
        this.lastFailure = Date.now();
        if (this.failures >= this.threshold) {
          this.state = "open";
        }
      }
      throw err;
    }
  }
}
```

## Error Handling

| Symptom | Cause | Solution |
|---------|-------|----------|
| Burst of 429s on startup | No throttling | Add `PQueue` with `intervalCap` |
| 429s during bulk import | Too many parallel requests | Reduce concurrency, batch with query |
| Intermittent 429s | Multiple apps sharing limit | Coordinate rate across apps |
| 429s after long silence | Attio reduced limit during incident | Check `status.attio.com`, honor `Retry-After` |

## Resources

- [Attio Rate Limiting Guide](https://docs.attio.com/rest-api/guides/rate-limiting)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Attio Status Page](https://status.attio.com)

## Next Steps

For security best practices, see `attio-security-basics`.
