---
name: supabase-rate-limits
description: |
  Supabase rate limiting, backoff, and idempotency patterns.
  Trigger phrases: "supabase rate limit", "supabase throttling",
  "supabase 429", "supabase retry", "supabase backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Rate Limits

## Overview
Handle Supabase rate limits gracefully with exponential backoff and idempotency.

## Rate Limit Tiers

| Tier | Requests/min | Requests/day | Burst |
|------|-------------|--------------|-------|
| Free | 500 | 50,000 | 10 |
| Pro | 5,000 | 1,000,000 | 50 |
| Enterprise | Unlimited | Unlimited | 200 |

## Response Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
Retry-After: 30
```

## Exponential Backoff Implementation

```typescript
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config: RetryConfig = {
    maxRetries: 5,
    baseDelayMs: 1000,
    maxDelayMs: 32000,
    jitterMs: 500,
  }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      // Only retry on rate limit (429) or server errors (5xx)
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Calculate delay with exponential backoff + jitter
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.log(`Rate limited. Retry ${attempt + 1}/${config.maxRetries} in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Idempotency Pattern

```typescript
import { v4 as uuidv4 } from 'uuid';

async function idempotentRequest<T>(
  client: SupabaseClient,
  operation: string,
  params: Record<string, any>,
  idempotencyKey?: string
): Promise<T> {
  const key = idempotencyKey || `${operation}-${uuidv4()}`;

  return client.request({
    ...params,
    headers: {
      'Idempotency-Key': key,
      ...params.headers,
    },
  });
}
```

## Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

// Create queue with rate limit
const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

// Add operations to queue
async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation);
}
```

## Monitoring Rate Limit Usage

```typescript
class RateLimitMonitor {
  private remaining: number = 60;
  private resetAt: Date = new Date();

  updateFromHeaders(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
    const reset = headers.get('X-RateLimit-Reset');
    if (reset) this.resetAt = new Date(parseInt(reset) * 1000);
  }

  shouldThrottle(): boolean {
    return this.remaining < 5 && new Date() < this.resetAt;
  }
}
```

## Next Steps
For security configuration, see `supabase-security-basics`.