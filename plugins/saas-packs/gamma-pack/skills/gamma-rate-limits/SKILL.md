---
name: gamma-rate-limits
description: |
  Understand and manage Gamma API rate limits effectively.
  Use when hitting rate limits, optimizing API usage,
  or implementing request queuing systems.
  Trigger with phrases like "gamma rate limit", "gamma quota",
  "gamma 429", "gamma throttle", "gamma request limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Rate Limits

## Overview
Understand Gamma API rate limits and implement effective strategies for high-volume usage.

## Prerequisites
- Active Gamma API integration
- Understanding of HTTP headers
- Basic queuing concepts

## Rate Limit Tiers

| Plan | Requests/min | Presentations/day | Exports/hour |
|------|-------------|-------------------|--------------|
| Free | 10 | 5 | 10 |
| Pro | 60 | 50 | 100 |
| Team | 200 | 200 | 500 |
| Enterprise | Custom | Custom | Custom |

## Instructions

### Step 1: Check Rate Limit Headers
```typescript
const response = await gamma.presentations.list();

// Rate limit headers
const headers = response.headers;
console.log('Limit:', headers['x-ratelimit-limit']);
console.log('Remaining:', headers['x-ratelimit-remaining']);
console.log('Reset:', new Date(headers['x-ratelimit-reset'] * 1000));  # 1000: 1 second in ms
```

### Step 2: Implement Exponential Backoff
```typescript
async function withBackoff<T>(
  fn: () => Promise<T>,
  options = { maxRetries: 5, baseDelay: 1000 }  # 1000: 1 second in ms
): Promise<T> {
  for (let attempt = 0; attempt < options.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err.status !== 429 || attempt === options.maxRetries - 1) {  # HTTP 429 Too Many Requests
        throw err;
      }

      const delay = err.retryAfter
        ? err.retryAfter * 1000  # 1 second in ms
        : options.baseDelay * Math.pow(2, attempt);

      console.log(`Rate limited. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Max retries exceeded');
}

// Usage
const result = await withBackoff(() =>
  gamma.presentations.create({ title: 'My Deck', prompt: 'AI overview' })
);
```

### Step 3: Request Queue
```typescript
class RateLimitedQueue {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;
  private requestsPerMinute: number;
  private interval: number;

  constructor(requestsPerMinute = 60) {
    this.requestsPerMinute = requestsPerMinute;
    this.interval = 60000 / requestsPerMinute;  # 60000: 1 minute in ms
  }

  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          resolve(await fn());
        } catch (err) {
          reject(err);
        }
      });
      this.process();
    });
  }

  private async process() {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0) {
      const fn = this.queue.shift()!;
      await fn();
      await new Promise(r => setTimeout(r, this.interval));
    }

    this.processing = false;
  }
}

// Usage
const queue = new RateLimitedQueue(30); // 30 req/min

const results = await Promise.all([
  queue.add(() => gamma.presentations.create({ ... })),
  queue.add(() => gamma.presentations.create({ ... })),
  queue.add(() => gamma.presentations.create({ ... })),
]);
```

### Step 4: Monitor Usage
```typescript
async function getRateLimitStatus() {
  const status = await gamma.rateLimit.status();

  return {
    limit: status.limit,
    remaining: status.remaining,
    percentUsed: ((status.limit - status.remaining) / status.limit * 100).toFixed(1),
    resetAt: new Date(status.reset * 1000),  # 1000: 1 second in ms
    resetIn: Math.ceil((status.reset * 1000 - Date.now()) / 1000),  # 1 second in ms
  };
}

// Usage
const status = await getRateLimitStatus();
console.log(`Used ${status.percentUsed}% of rate limit`);
console.log(`Resets in ${status.resetIn} seconds`);
```

## Output
- Rate limit aware API calls
- Automatic retry with backoff
- Request queuing system
- Usage monitoring dashboard

## Error Handling
| Scenario | Strategy | Implementation |
|----------|----------|----------------|
| Occasional 429 | Exponential backoff | `withBackoff()` wrapper |
| Consistent 429 | Request queue | `RateLimitedQueue` class |
| Near limit | Preemptive throttle | Check remaining before call |
| Burst traffic | Token bucket | Implement token bucket algorithm |

## Resources
- [Gamma Rate Limits](https://gamma.app/docs/rate-limits)
- [Rate Limit Best Practices](https://gamma.app/docs/best-practices)

## Next Steps
Proceed to `gamma-security-basics` for security best practices.

## Examples

**Basic usage**: Apply gamma rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma rate limits for production environments with multiple constraints and team-specific requirements.