---
name: bamboohr-rate-limits
description: |
  Implement BambooHR rate limiting, backoff, and request optimization.
  Use when handling 429/503 rate limit errors, implementing retry logic,
  or optimizing API request throughput for BambooHR.
  Trigger with phrases like "bamboohr rate limit", "bamboohr throttling",
  "bamboohr 429", "bamboohr 503", "bamboohr retry", "bamboohr backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, rate-limiting]
compatible-with: claude-code
---

# BambooHR Rate Limits

## Overview

BambooHR does not publish exact rate limits, but the API returns `503 Service Unavailable` with a `Retry-After` header when you exceed them. This skill covers detection, backoff, request optimization, and queue-based throttling.

## Prerequisites

- BambooHR API client configured
- Understanding of async/await patterns

## Instructions

### Step 1: Understand BambooHR Rate Limiting Behavior

BambooHR rate limiting details:

| Signal | Value | Description |
|--------|-------|-------------|
| HTTP Status | `503` | Primary rate limit signal |
| `Retry-After` header | seconds (e.g., `30`) | How long to wait before retrying |
| `X-BambooHR-Error-Message` | varies | May contain rate limit detail |
| HTTP Status `429` | rare | Some endpoints return 429 for employee count limits |

**Key insight:** BambooHR uses `503` (not `429`) for rate limiting. Failed authentication attempts also count toward rate limits, so ensure your API key is valid before making many requests.

### Step 2: Implement Retry-After Aware Backoff

```typescript
import { BambooHRApiError } from './client';

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY: RetryConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 60_000,
};

async function withBambooHRRetry<T>(
  operation: () => Promise<T>,
  config = DEFAULT_RETRY,
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === config.maxRetries) throw err;
      if (!(err instanceof BambooHRApiError)) throw err;
      if (!err.retryable) throw err; // Only retry 429, 503, 500, 502

      // Honor BambooHR's Retry-After header
      let delay: number;
      if (err.meta.retryAfter) {
        delay = parseInt(err.meta.retryAfter, 10) * 1000;
      } else {
        // Exponential backoff with jitter
        const exponential = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * config.baseDelayMs;
        delay = Math.min(exponential + jitter, config.maxDelayMs);
      }

      console.warn(
        `BambooHR rate limited (attempt ${attempt + 1}/${config.maxRetries}). ` +
        `Waiting ${(delay / 1000).toFixed(1)}s...`
      );
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}
```

### Step 3: Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

// BambooHR unofficial guidance: stay under ~10 requests/second
const bamboohrQueue = new PQueue({
  concurrency: 3,         // Max 3 concurrent requests
  interval: 1000,         // Per 1-second window
  intervalCap: 8,         // Max 8 requests per second
});

async function rateLimitedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return bamboohrQueue.add(() => withBambooHRRetry(operation));
}

// Usage — all requests go through the queue
const employees = await rateLimitedRequest(() => client.getDirectory());
const report = await rateLimitedRequest(() => client.customReport(['firstName', 'lastName']));

// Bulk operations automatically throttled
const employeeDetails = await Promise.all(
  employeeIds.map(id =>
    rateLimitedRequest(() => client.getEmployee(id, ['firstName', 'lastName', 'jobTitle']))
  ),
);
```

### Step 4: Reduce Request Volume

**Use custom reports instead of individual GETs:**

```typescript
// BAD: N+1 requests (one per employee)
const employees = await client.getDirectory();
for (const emp of employees.employees) {
  const detail = await client.getEmployee(emp.id, ['salary', 'department']);
  // 500 employees = 501 requests
}

// GOOD: 1 request using custom report
const report = await client.customReport([
  'firstName', 'lastName', 'department', 'jobTitle', 'hireDate',
]);
// 1 request, all employee data
```

**Use incremental sync:**

```typescript
// BAD: Full directory pull every time
const allEmployees = await client.getDirectory();

// GOOD: Only changed employees since last sync
const changed = await client.request<any>(
  'GET', `/employees/changed/?since=${lastSyncTimestamp}`,
);
// Only fetch details for employees that actually changed
```

**Use table changed endpoint:**

```typescript
// GET /employees/changed/tables/{tableName}?since=...
const changedJobs = await client.request<any>(
  'GET', `/employees/changed/tables/jobInfo?since=${lastSyncTimestamp}`,
);
```

### Step 5: Monitor Rate Limit Usage

```typescript
class BambooHRRateLimitMonitor {
  private requestLog: { timestamp: number; status: number }[] = [];
  private rateLimitHits = 0;

  recordRequest(status: number) {
    this.requestLog.push({ timestamp: Date.now(), status });

    // Only keep last 5 minutes
    const cutoff = Date.now() - 5 * 60 * 1000;
    this.requestLog = this.requestLog.filter(r => r.timestamp > cutoff);

    if (status === 503 || status === 429) {
      this.rateLimitHits++;
    }
  }

  getStats() {
    const recent = this.requestLog;
    return {
      requestsLast5Min: recent.length,
      requestsPerSecond: (recent.length / 300).toFixed(2),
      rateLimitHits: this.rateLimitHits,
      errorRate: recent.filter(r => r.status >= 400).length / Math.max(recent.length, 1),
    };
  }

  shouldBackOff(): boolean {
    const stats = this.getStats();
    return stats.errorRate > 0.1 || parseFloat(stats.requestsPerSecond) > 8;
  }
}
```

## Output

- Retry logic honoring `Retry-After` header
- Queue-based throttling preventing rate limit hits
- Request volume reduction via custom reports and incremental sync
- Rate limit monitoring with stats

## Error Handling

| Signal | Detection | Action |
|--------|-----------|--------|
| `503` + `Retry-After: N` | Check response status + header | Wait N seconds, then retry |
| `503` without `Retry-After` | Status only | Exponential backoff from 1s |
| `429` (employee limit) | Status code | Contact BambooHR to increase limit |
| Many consecutive 503s | Monitor hit count | Pause all requests for 60s |

## Enterprise Considerations

- **Multi-tenant rate limits**: Each company domain has independent rate limits
- **Batch jobs**: Run large syncs during off-peak hours (nights/weekends)
- **Contact BambooHR**: For enterprise-volume needs, request rate limit increases through support
- **Webhook alternatives**: Use webhooks for real-time changes instead of polling (see `bamboohr-webhooks-events`)

## Resources

- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `bamboohr-security-basics`.
