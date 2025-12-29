---
name: vercel-rate-limits
description: |
  Implement Vercel rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Vercel.
  Trigger with phrases like "vercel rate limit", "vercel throttling",
  "vercel 429", "vercel retry", "vercel backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Rate Limits

## Overview
Handle Vercel rate limits gracefully with exponential backoff and idempotency.

## Prerequisites
- Vercel SDK installed
- Understanding of async/await patterns
- Access to rate limit headers

## Instructions

### Step 1: Understand Rate Limit Tiers

| Tier | Requests/min | Requests/day | Burst |
|------|-------------|--------------|-------|
| Hobby | 100 | 100,000 | 10 |
| Pro | 1,000 | 1,000,000 | 50 |
| Enterprise | 10,000 | Unlimited | 200 |

### Step 2: Implement Exponential Backoff

```typescript
async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;
      const delay = Math.min(config.baseDelayMs * Math.pow(2, attempt), config.maxDelayMs);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 3: Add Idempotency Keys

```typescript
import { v4 as uuidv4 } from 'uuid';

async function idempotentRequest<T>(
  client: VercelClient,
  params: Record<string, any>
): Promise<T> {
  return client.request({
    ...params,
    headers: { 'Idempotency-Key': uuidv4(), ...params.headers },
  });
}
```

## Output
- Reliable API calls with automatic retry
- Idempotent requests preventing duplicates
- Rate limit headers properly handled

## Error Handling
| Header | Description | Action |
|--------|-------------|--------|
| X-RateLimit-Limit | Max requests | Monitor usage |
| X-RateLimit-Remaining | Remaining requests | Throttle if low |
| X-RateLimit-Reset | Reset timestamp | Wait until reset |
| Retry-After | Seconds to wait | Honor this value |

## Examples

### Queue-Based Rate Limiting
```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation);
}
```

### Monitor Rate Limit Usage
```typescript
class RateLimitMonitor {
  private remaining: number = 60;

  updateFromHeaders(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
  }

  shouldThrottle(): boolean {
    return this.remaining < 5;
  }
}
```

## Resources
- [Vercel Rate Limits](https://vercel.com/docs/rate-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `vercel-security-basics`.