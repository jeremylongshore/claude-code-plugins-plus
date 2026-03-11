# Apollo Rate Limits - Implementation Guide

> Full implementation details and code examples for the `apollo-rate-limits` skill.

# Apollo Rate Limits

## Overview
Implement robust rate limiting and backoff strategies for Apollo.io API to maximize throughput while avoiding 429 errors.

## Apollo Rate Limits

| Endpoint Category | Rate Limit | Window | Burst Limit |
|-------------------|------------|--------|-------------|
| People Search | 100/min | 1 minute | 10/sec |
| Person Enrichment | 100/min | 1 minute | 10/sec |
| Organization Enrichment | 100/min | 1 minute | 10/sec |
| Sequences/Campaigns | 50/min | 1 minute | 5/sec |
| Bulk Operations | 10/min | 1 minute | 2/sec |
| General API | 100/min | 1 minute | 10/sec |

## Rate Limit Headers

```bash
# Check current rate limit status
curl -I -X POST "https://api.apollo.io/v1/people/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "'$APOLLO_API_KEY'", "per_page": 1}'

# Response headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1640000000
# Retry-After: 60  (only when rate limited)
```

## Implementation: Rate Limiter Class

```typescript
// src/lib/apollo/rate-limiter.ts
interface RateLimiterConfig {
  maxRequests: number;
  windowMs: number;
  minSpacingMs: number;
}

class RateLimiter {
  private queue: Array<{
    resolve: (value: void) => void;
    reject: (error: Error) => void;
  }> = [];
  private requestTimestamps: number[] = [];
  private lastRequestTime = 0;
  private processing = false;

  constructor(private config: RateLimiterConfig) {}

  async acquire(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.queue.push({ resolve, reject });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    while (this.queue.length > 0) {
      // Clean old timestamps outside window
      const now = Date.now();
      this.requestTimestamps = this.requestTimestamps.filter(
        (ts) => now - ts < this.config.windowMs
      );

      // Check if we're at capacity
      if (this.requestTimestamps.length >= this.config.maxRequests) {
        const oldestTs = this.requestTimestamps[0];
        const waitTime = this.config.windowMs - (now - oldestTs) + 100;
        await this.wait(waitTime);
        continue;
      }

      // Enforce minimum spacing
      const timeSinceLastRequest = now - this.lastRequestTime;
      if (timeSinceLastRequest < this.config.minSpacingMs) {
        await this.wait(this.config.minSpacingMs - timeSinceLastRequest);
      }

      // Process next request
      const item = this.queue.shift()!;
      this.requestTimestamps.push(Date.now());
      this.lastRequestTime = Date.now();
      item.resolve();
    }

    this.processing = false;
  }

  private wait(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Create rate limiter for Apollo
export const apolloRateLimiter = new RateLimiter({
  maxRequests: 90, // Leave buffer below 100
  windowMs: 60000,
  minSpacingMs: 100, // 100ms between requests
});
```

## Implementation: Exponential Backoff

```typescript
// src/lib/apollo/backoff.ts
interface BackoffConfig {
  initialDelayMs: number;
  maxDelayMs: number;
  maxRetries: number;
  multiplier: number;
  jitter: boolean;
}

const defaultConfig: BackoffConfig = {
  initialDelayMs: 1000,
  maxDelayMs: 60000,
  maxRetries: 5,
  multiplier: 2,
  jitter: true,
};

export async function withBackoff<T>(
  fn: () => Promise<T>,
  config: Partial<BackoffConfig> = {}
): Promise<T> {
  const cfg = { ...defaultConfig, ...config };
  let lastError: Error;
  let delay = cfg.initialDelayMs;

  for (let attempt = 0; attempt <= cfg.maxRetries; attempt++) {
    try {
      await apolloRateLimiter.acquire();
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Check if retryable
      const status = error.response?.status;
      if (status === 401 || status === 403 || status === 422) {
        throw error; // Don't retry auth/validation errors
      }

      if (attempt === cfg.maxRetries) {
        break;
      }

      // Get delay from Retry-After header or calculate
      const retryAfter = error.response?.headers?.['retry-after'];
      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      }

      // Add jitter to prevent thundering herd
      const jitter = cfg.jitter ? Math.random() * 1000 : 0;
      const actualDelay = Math.min(delay + jitter, cfg.maxDelayMs);

      console.log(`Retry ${attempt + 1}/${cfg.maxRetries} after ${actualDelay}ms`);
      await new Promise((r) => setTimeout(r, actualDelay));

      delay *= cfg.multiplier;
    }
  }

  throw lastError!;
}
```

## Implementation: Request Queue

```typescript
// src/lib/apollo/request-queue.ts
import PQueue from 'p-queue';

// Concurrency-limited queue
export const apolloQueue = new PQueue({
  concurrency: 5, // Max 5 concurrent requests
  interval: 1000, // Per second
  intervalCap: 10, // Max 10 per interval
});

// Usage
async function batchSearchPeople(domains: string[]): Promise<Person[]> {
  const results = await Promise.all(
    domains.map((domain) =>
      apolloQueue.add(() =>
        withBackoff(() => apollo.searchPeople({ q_organization_domains: [domain] }))
      )
    )
  );

  return results.flat().map((r) => r?.people || []).flat();
}
```

## Usage Patterns

### Pattern 1: Simple Rate-Limited Request
```typescript
import { withBackoff } from './backoff';

const people = await withBackoff(() =>
  apollo.searchPeople({
    q_organization_domains: ['stripe.com'],
    per_page: 100,
  })
);
```

### Pattern 2: Batch Processing with Queue
```typescript
import { apolloQueue } from './request-queue';

async function enrichCompanies(domains: string[]) {
  const results = [];

  for (const domain of domains) {
    const result = await apolloQueue.add(
      () => withBackoff(() => apollo.enrichOrganization(domain)),
      { priority: 1 } // Lower priority
    );
    results.push(result);
  }

  return results;
}
```

### Pattern 3: Priority Queue for Interactive vs Background
```typescript
// High priority for user-facing requests
async function interactiveSearch(query: string) {
  return apolloQueue.add(
    () => withBackoff(() => apollo.searchPeople({ q_keywords: query })),
    { priority: 0 } // Highest priority
  );
}

// Low priority for background sync
async function backgroundSync(contacts: string[]) {
  return Promise.all(
    contacts.map((id) =>
      apolloQueue.add(
        () => withBackoff(() => apollo.getContact(id)),
        { priority: 10 } // Low priority
      )
    )
  );
}
```

## Monitoring Rate Limit Usage

```typescript
// src/lib/apollo/rate-monitor.ts
class RateLimitMonitor {
  private requests: Array<{ timestamp: number; remaining: number }> = [];

  recordRequest(remaining: number) {
    this.requests.push({
      timestamp: Date.now(),
      remaining,
    });

    // Keep only last 5 minutes
    const cutoff = Date.now() - 5 * 60 * 1000;
    this.requests = this.requests.filter((r) => r.timestamp > cutoff);
  }

  getStats() {
    const lastMinute = this.requests.filter(
      (r) => r.timestamp > Date.now() - 60000
    );

    return {
      requestsLastMinute: lastMinute.length,
      currentRemaining: lastMinute[lastMinute.length - 1]?.remaining ?? 100,
      utilizationPercent: (lastMinute.length / 100) * 100,
      isNearLimit: lastMinute.length > 80,
    };
  }
}

export const rateLimitMonitor = new RateLimitMonitor();
```

## Output
- Rate limiter class with token bucket algorithm
- Exponential backoff with jitter
- Request queue with concurrency control
- Priority-based request scheduling
- Rate limit monitoring and alerts

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 response | Use Retry-After header |
| Burst limit hit | Add minimum spacing |
| Sustained limit | Queue with concurrency |
| Network timeout | Exponential backoff |

## Resources
- [Apollo Rate Limits](https://apolloio.github.io/apollo-api-docs/#rate-limits)
- [p-queue Library](https://github.com/sindresorhus/p-queue)
- [Exponential Backoff](https://cloud.google.com/storage/docs/exponential-backoff)

## Next Steps
Proceed to `apollo-security-basics` for API security best practices.
