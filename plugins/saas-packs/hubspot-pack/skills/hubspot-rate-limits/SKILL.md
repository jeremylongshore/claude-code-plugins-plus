---
name: hubspot-rate-limits
description: |
  Implement HubSpot rate limiting, backoff, and request queuing patterns.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API throughput against HubSpot rate limits.
  Trigger with phrases like "hubspot rate limit", "hubspot throttling",
  "hubspot 429", "hubspot retry", "hubspot backoff", "hubspot quota".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Rate Limits

## Overview

Handle HubSpot API rate limits with proper backoff strategies. HubSpot enforces per-second and daily limits shared across all apps in a portal.

## Prerequisites

- `@hubspot/api-client` installed
- Understanding of HubSpot's shared rate limit model

## Instructions

### Step 1: Understand HubSpot Rate Limit Tiers

| Plan | Per-Second Limit | Daily Limit | Burst |
|------|-----------------|-------------|-------|
| Free/Starter | 10 requests/sec | 250,000/day | -- |
| Professional | 10 requests/sec | 500,000/day | -- |
| Enterprise | 10 requests/sec | 500,000/day | -- |
| API Add-on | 10 requests/sec | 1,000,000/day | -- |

**Critical:** Limits are per HubSpot portal (account), not per app. All private apps and OAuth apps in the same portal share the same limit bucket.

### Step 2: Use SDK Built-in Retries

```typescript
import * as hubspot from '@hubspot/api-client';

// The SDK has built-in retry for 429 responses
const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3, // retries 429 and 5xx automatically
});
```

### Step 3: Custom Backoff with Retry-After Header

```typescript
async function withHubSpotBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      const status = error?.code || error?.statusCode || error?.response?.status;

      // Only retry on 429 and 5xx
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Honor Retry-After header from HubSpot
      let delay: number;
      const retryAfter = error?.response?.headers?.['retry-after'];
      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        // Exponential backoff with jitter
        const exponential = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * 500;
        delay = Math.min(exponential + jitter, config.maxDelayMs);
      }

      console.warn(`HubSpot rate limited (attempt ${attempt + 1}/${config.maxRetries}). ` +
        `Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Request Queue for Throughput Control

```typescript
import PQueue from 'p-queue';

// Queue that respects HubSpot's 10 req/sec limit
const hubspotQueue = new PQueue({
  concurrency: 5,        // max parallel requests
  interval: 1000,        // per second
  intervalCap: 10,       // max 10 per interval (HubSpot limit)
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return hubspotQueue.add(operation) as Promise<T>;
}

// Usage -- all calls automatically throttled
const results = await Promise.all(
  contactIds.map(id =>
    queuedRequest(() =>
      client.crm.contacts.basicApi.getById(id, ['email', 'firstname'])
    )
  )
);
```

### Step 5: Batch Operations to Reduce Call Volume

```typescript
// Instead of 100 individual GET calls (100 API calls):
// BAD
for (const id of contactIds) {
  await client.crm.contacts.basicApi.getById(id, ['email']);
}

// Use batch read (1 API call for up to 100 records):
// GOOD - POST /crm/v3/objects/contacts/batch/read
const batchResult = await client.crm.contacts.batchApi.read({
  inputs: contactIds.map(id => ({ id })),
  properties: ['email', 'firstname', 'lastname'],
  propertiesWithHistory: [],
});

console.log(`Fetched ${batchResult.results.length} contacts in 1 API call`);
```

### Step 6: Monitor Rate Limit Headers

```typescript
class HubSpotRateLimitMonitor {
  private dailyRemaining = 500000;
  private secondlyRemaining = 10;

  updateFromResponse(headers: Record<string, string>): void {
    if (headers['x-hubspot-ratelimit-daily-remaining']) {
      this.dailyRemaining = parseInt(headers['x-hubspot-ratelimit-daily-remaining']);
    }
    if (headers['x-hubspot-ratelimit-secondly-remaining']) {
      this.secondlyRemaining = parseInt(headers['x-hubspot-ratelimit-secondly-remaining']);
    }
  }

  shouldThrottle(): boolean {
    return this.secondlyRemaining < 2 || this.dailyRemaining < 1000;
  }

  getStatus(): { daily: number; secondly: number; warning: boolean } {
    return {
      daily: this.dailyRemaining,
      secondly: this.secondlyRemaining,
      warning: this.shouldThrottle(),
    };
  }
}
```

## Output

- SDK built-in retry handles basic 429s
- Custom backoff honors `Retry-After` header
- Request queue enforces 10 req/sec limit
- Batch operations reduce API call volume by 100x
- Rate limit monitoring prevents threshold breaches

## Error Handling

| Header | Description | Action |
|--------|-------------|--------|
| `X-HubSpot-RateLimit-Daily` | Daily quota | Monitor usage |
| `X-HubSpot-RateLimit-Daily-Remaining` | Remaining today | Alert if < 10% |
| `X-HubSpot-RateLimit-Secondly` | Per-second limit | Always 10 |
| `X-HubSpot-RateLimit-Secondly-Remaining` | Remaining this second | Throttle if < 2 |
| `Retry-After` | Seconds to wait | Always honor this |

## Examples

### Quick Rate Limit Check

```bash
# Check current rate limit state
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i ratelimit

# Output:
# X-HubSpot-RateLimit-Daily: 500000
# X-HubSpot-RateLimit-Daily-Remaining: 499800
# X-HubSpot-RateLimit-Secondly: 10
# X-HubSpot-RateLimit-Secondly-Remaining: 9
```

## Resources

- [HubSpot API Usage Guidelines](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [Error Handling Guide](https://developers.hubspot.com/docs/api-reference/error-handling)
- [p-queue npm](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `hubspot-security-basics`.
