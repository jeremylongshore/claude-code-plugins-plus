---
name: salesloft-rate-limits
description: |
  Handle SalesLoft cost-based rate limiting with backoff and request budgeting.
  Use when hitting 429 errors, optimizing API throughput,
  or implementing pagination-aware rate limit strategies.
  Trigger: "salesloft rate limit", "salesloft 429", "salesloft throttling".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Rate Limits

## Overview

SalesLoft uses cost-based rate limiting at 600 cost per minute. Each request costs 1 point by default, but deep pagination multiplies the cost. Rate limit state is returned in response headers.

## Rate Limit Model

### Cost per Request

| Page Range | Cost per Request | Example: 1000 records at 100/page |
|------------|-----------------|-----------------------------------|
| 1-100 | 1 point | Pages 1-10: 10 points |
| 101-150 | 3 points | N/A for this example |
| 151-250 | 8 points | N/A |
| 251-500 | 10 points | N/A |
| 501+ | 30 points | N/A |

**Budget: 600 points/minute.** A simple 10-page pagination costs 10 points. But paginating to page 500 costs 10 + 150 + 800 + 2500 = 3460 points (nearly 6 minutes of budget).

### Response Headers

```
X-RateLimit-Limit-Per-Minute: 600
X-RateLimit-Remaining-Per-Minute: 487
Retry-After: 42          # Only present on 429 responses
X-Request-Id: abc-123    # For support tickets
```

## Instructions

### Step 1: Rate-Limit-Aware Client

```typescript
import axios, { AxiosInstance } from 'axios';

class SalesloftRateLimiter {
  private remaining = 600;
  private resetAt = Date.now();

  constructor(private client: AxiosInstance) {
    client.interceptors.response.use(
      (res) => {
        this.remaining = parseInt(res.headers['x-ratelimit-remaining-per-minute'] || '600');
        return res;
      },
      async (err) => {
        if (err.response?.status === 429) {
          const wait = parseInt(err.response.headers['retry-after'] || '60');
          console.warn(`Rate limited. Waiting ${wait}s (X-Request-Id: ${err.response.headers['x-request-id']})`);
          await this.sleep(wait * 1000);
          return this.client.request(err.config);
        }
        throw err;
      }
    );
  }

  async throttledRequest<T>(fn: () => Promise<T>): Promise<T> {
    if (this.remaining < 10) {
      const waitMs = Math.max(0, this.resetAt - Date.now());
      if (waitMs > 0) await this.sleep(waitMs);
    }
    return fn();
  }

  private sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }
}
```

### Step 2: Pagination Cost Calculator

```typescript
function paginationCost(totalRecords: number, perPage: number = 100): number {
  const totalPages = Math.ceil(totalRecords / perPage);
  let cost = 0;
  for (let p = 1; p <= totalPages; p++) {
    if (p <= 100) cost += 1;
    else if (p <= 150) cost += 3;
    else if (p <= 250) cost += 8;
    else if (p <= 500) cost += 10;
    else cost += 30;
  }
  return cost;
}

// Budget check before large exports
const totalPeople = 25000; // from metadata.paging.total_count
const cost = paginationCost(totalPeople);
const minutes = Math.ceil(cost / 600);
console.log(`Export will cost ${cost} points (~${minutes} minutes at rate limit)`);
```

### Step 3: Queue-Based Throttling for Bulk Operations

```typescript
import PQueue from 'p-queue';

// Max 5 concurrent, 10 per second (600/min = 10/sec)
const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 10 });

async function bulkCreatePeople(people: any[]) {
  const results = await Promise.allSettled(
    people.map(person =>
      queue.add(() => api.post('/people.json', person))
    )
  );
  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  console.log(`Created ${succeeded}/${people.length} people`);
}
```

## Error Handling

| Scenario | Cost Impact | Strategy |
|----------|-------------|----------|
| Simple list (page 1-10) | 10 points | No throttle needed |
| Full export (250 pages) | 910 points | ~2 min, add delays |
| Bulk create (500 records) | 500 points | Queue with intervalCap |
| Deep pagination (page 500) | 3460 points | Cache or use webhooks instead |

## Resources

- [SalesLoft Rate Limits](https://developers.salesloft.com/docs/platform/api-basics/rate-limits/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `salesloft-security-basics`.
