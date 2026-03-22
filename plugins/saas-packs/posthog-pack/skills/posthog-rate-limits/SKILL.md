---
name: posthog-rate-limits
description: |
  Handle PostHog API rate limits with exponential backoff, request queuing,
  and understanding PostHog's actual limit tiers (240/min analytics, 600/min flags).
  Trigger: "posthog rate limit", "posthog throttling", "posthog 429",
  "posthog retry", "posthog backoff", "posthog too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api]
---

# PostHog Rate Limits

## Overview

PostHog rate limits apply to private API endpoints authenticated with a personal API key (`phx_...`). Public capture endpoints (`/capture/`, `/batch/`, `/decide/`) are **not** rate limited. Understanding which endpoints have limits is critical to avoiding 429 errors.

## Prerequisites

- PostHog personal API key (`phx_...`) for admin endpoints
- Understanding of which endpoints you call and how often
- `posthog-node` or direct API usage

## PostHog Rate Limit Tiers

| Endpoint Category | Rate Limit | Examples |
|-------------------|-----------|----------|
| Event capture (`/capture/`, `/batch/`) | **No limit** | `posthog.capture()`, batch ingestion |
| Feature flag decide (`/decide/`) | **No limit** | Client-side flag evaluation |
| Analytics API (insights, persons, recordings) | **240/min, 1200/hour** | Trend queries, person lookup |
| HogQL query API (`/api/projects/:id/query/`) | **1200/hour** | Custom SQL queries |
| Feature flag local evaluation polling | **600/min** | Server SDK flag definition fetch |
| All other private endpoints | **240/min, 1200/hour** | Feature flag CRUD, cohorts, annotations |

## Instructions

### Step 1: Implement Exponential Backoff with Retry-After

```typescript
async function postHogApiCall<T>(
  url: string,
  options: RequestInit,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
        ...options.headers,
      },
    });

    if (response.ok) {
      return response.json();
    }

    if (response.status === 429) {
      // Honor the Retry-After header from PostHog
      const retryAfter = parseInt(response.headers.get('Retry-After') || '0');
      const backoffMs = retryAfter > 0
        ? retryAfter * 1000
        : Math.min(1000 * Math.pow(2, attempt) + Math.random() * 500, 32000);

      console.warn(`PostHog 429: retrying in ${Math.round(backoffMs)}ms (attempt ${attempt + 1}/${maxRetries})`);
      await new Promise(r => setTimeout(r, backoffMs));
      continue;
    }

    // Don't retry client errors (except 429)
    if (response.status >= 400 && response.status < 500) {
      const body = await response.text();
      throw new Error(`PostHog API ${response.status}: ${body}`);
    }

    // Retry server errors (500+)
    if (attempt < maxRetries) {
      const delay = 1000 * Math.pow(2, attempt);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    throw new Error(`PostHog API failed after ${maxRetries} retries: ${response.status}`);
  }

  throw new Error('Unreachable');
}
```

### Step 2: Request Queue for Burst Protection

```typescript
import PQueue from 'p-queue';

// Enforce 240 requests/minute = 4 requests/second
const posthogQueue = new PQueue({
  concurrency: 2,       // Max parallel requests
  interval: 1000,       // Per second
  intervalCap: 4,       // Max 4 requests per second
});

async function queuedPostHogCall<T>(
  url: string,
  options: RequestInit
): Promise<T> {
  return posthogQueue.add(() => postHogApiCall<T>(url, options));
}

// Usage: all calls are automatically throttled
const insights = await queuedPostHogCall(
  `https://app.posthog.com/api/projects/${PROJECT_ID}/insights/trend/`,
  { method: 'GET' }
);
```

### Step 3: Cache Frequently Accessed Data

```typescript
// Cache insight results to reduce API calls
class PostHogCache {
  private cache = new Map<string, { data: any; expiry: number }>();

  async get<T>(key: string, fetcher: () => Promise<T>, ttlMs = 300000): Promise<T> {
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiry) {
      return cached.data as T;
    }

    const data = await fetcher();
    this.cache.set(key, { data, expiry: Date.now() + ttlMs });
    return data;
  }

  invalidate(key: string) {
    this.cache.delete(key);
  }
}

const phCache = new PostHogCache();

// Cache trend data for 5 minutes
const trends = await phCache.get('weekly-pageviews', () =>
  queuedPostHogCall(`https://app.posthog.com/api/projects/${PROJECT_ID}/insights/trend/?events=[{"id":"$pageview"}]&date_from=-7d`, { method: 'GET' })
);
```

### Step 4: Monitor Rate Limit Headers

```typescript
class RateLimitMonitor {
  private remaining = Infinity;
  private resetAt = 0;

  update(headers: Headers) {
    const remaining = headers.get('X-RateLimit-Remaining');
    const reset = headers.get('X-RateLimit-Reset');

    if (remaining) this.remaining = parseInt(remaining);
    if (reset) this.resetAt = parseInt(reset) * 1000;
  }

  shouldThrottle(): boolean {
    return this.remaining < 10 && Date.now() < this.resetAt;
  }

  waitTime(): number {
    return Math.max(0, this.resetAt - Date.now());
  }

  log() {
    console.log(`PostHog rate limit: ${this.remaining} remaining, resets in ${Math.round(this.waitTime() / 1000)}s`);
  }
}

const rateLimits = new RateLimitMonitor();

// After each API call, update the monitor
const response = await fetch(url, options);
rateLimits.update(response.headers);
if (rateLimits.shouldThrottle()) {
  console.warn(`Approaching PostHog rate limit — waiting ${rateLimits.waitTime()}ms`);
  await new Promise(r => setTimeout(r, rateLimits.waitTime()));
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| HTTP 429 on insights | >240 req/min on analytics | Queue requests, cache results |
| 429 on flag polling | >600 req/min local eval fetch | Increase `featureFlagsPollingInterval` |
| 429 on HogQL | >1200 req/hour | Cache query results, reduce frequency |
| Thundering herd on retry | All clients retry simultaneously | Add random jitter to backoff |

## Key Points

- **Capture endpoints are NOT rate limited** — `posthog.capture()` calls will never 429
- **Only private API calls are limited** — endpoints requiring `Authorization: Bearer phx_...`
- **Cache aggressively** — insight data rarely needs real-time refresh
- **Honor Retry-After** — PostHog tells you exactly how long to wait

## Output

- Exponential backoff with Retry-After header support
- Request queue enforcing 4 req/sec
- In-memory cache for API responses
- Rate limit header monitoring

## Resources

- [PostHog API Overview (rate limits)](https://posthog.com/docs/api)
- [PostHog Feature Flag Local Evaluation](https://posthog.com/docs/feature-flags/local-evaluation)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `posthog-security-basics`.
