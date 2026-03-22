---
name: firecrawl-rate-limits
description: |
  Implement Firecrawl rate limiting, backoff, and request queuing patterns.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Firecrawl.
  Trigger with phrases like "firecrawl rate limit", "firecrawl throttling",
  "firecrawl 429", "firecrawl retry", "firecrawl backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api]

---
# Firecrawl Rate Limits

## Overview
Firecrawl enforces rate limits per API key measured in requests per minute and concurrent connections. When exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header. This skill covers backoff strategies, request queuing, and proactive throttling.

## Rate Limit Tiers

| Plan | Scrape RPM | Crawl Concurrency | Credits/Month |
|------|-----------|-------------------|---------------|
| Free | 10 | 2 | 500 |
| Hobby | 20 | 3 | 3,000 |
| Standard | 50 | 5 | 50,000 |
| Growth | 100 | 10 | 500,000 |
| Scale | 500+ | 50+ | Custom |

Concurrent crawl jobs count against concurrency limits. If the queue is full, new jobs are rejected with 429.

## Instructions

### Step 1: Exponential Backoff with Jitter
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

async function withBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      const status = error.statusCode || error.status;
      // Only retry on 429 (rate limit) and 5xx (server error)
      if (status && status !== 429 && status < 500) throw error;

      // Exponential delay with random jitter to prevent thundering herd
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * 500;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.warn(`Rate limited (${status}). Retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const result = await withBackoff(() =>
  firecrawl.scrapeUrl("https://example.com", { formats: ["markdown"] })
);
```

### Step 2: Queue-Based Rate Limiting with p-queue
```typescript
import PQueue from "p-queue";

// Limit to 5 concurrent requests, max 10 per second
const scrapeQueue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

async function queuedScrape(url: string) {
  return scrapeQueue.add(() =>
    withBackoff(() =>
      firecrawl.scrapeUrl(url, { formats: ["markdown"] })
    )
  );
}

// Scrape many URLs respecting rate limits
const urls = ["https://a.com", "https://b.com", "https://c.com"];
const results = await Promise.all(urls.map(url => queuedScrape(url)));
console.log(`Queue: ${scrapeQueue.pending} pending, ${scrapeQueue.size} queued`);
```

### Step 3: Proactive Throttling (Pre-emptive)
```typescript
class RateLimitTracker {
  private requestTimes: number[] = [];
  private windowMs: number;
  private maxRequests: number;

  constructor(maxRequests = 50, windowMs = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  async waitIfNeeded(): Promise<void> {
    const now = Date.now();
    this.requestTimes = this.requestTimes.filter(t => now - t < this.windowMs);

    if (this.requestTimes.length >= this.maxRequests) {
      const oldestInWindow = this.requestTimes[0];
      const waitMs = this.windowMs - (now - oldestInWindow) + 100;
      console.log(`Proactive throttle: waiting ${waitMs}ms to stay under ${this.maxRequests} RPM`);
      await new Promise(r => setTimeout(r, waitMs));
    }

    this.requestTimes.push(Date.now());
  }
}

const throttle = new RateLimitTracker(50, 60000); // 50 requests per minute

async function throttledScrape(url: string) {
  await throttle.waitIfNeeded();
  return firecrawl.scrapeUrl(url, { formats: ["markdown"] });
}
```

### Step 4: Batch Scrape for Efficiency
```typescript
// batchScrapeUrls is more efficient than individual scrapes
// It handles internal rate limiting and is cheaper on credits
const urls = [
  "https://example.com/page1",
  "https://example.com/page2",
  "https://example.com/page3",
];

// Single API call instead of 3 separate scrapes
const batchResult = await firecrawl.batchScrapeUrls(urls, {
  formats: ["markdown"],
});

console.log(`Batch scraped ${batchResult.data?.length} pages`);
```

## Error Handling
| Header | Description | Action |
|--------|-------------|--------|
| `Retry-After` | Seconds to wait | Honor this exact value |
| `X-RateLimit-Limit` | Max requests per window | Use for proactive throttling |
| `X-RateLimit-Remaining` | Remaining in window | Slow down when < 5 |
| `X-RateLimit-Reset` | Reset timestamp | Wait until this time |

## Examples

### Monitor Rate Limit Usage
```typescript
class RateLimitMonitor {
  private remaining = Infinity;
  private resetAt = new Date();

  update(status: number, headers: Record<string, string>) {
    if (headers["x-ratelimit-remaining"]) {
      this.remaining = parseInt(headers["x-ratelimit-remaining"]);
    }
    if (headers["x-ratelimit-reset"]) {
      this.resetAt = new Date(parseInt(headers["x-ratelimit-reset"]) * 1000);
    }
    if (this.remaining < 5) {
      console.warn(`Low rate limit: ${this.remaining} remaining, resets at ${this.resetAt.toISOString()}`);
    }
  }
}
```

## Resources
- [Firecrawl Rate Limits](https://docs.firecrawl.dev/rate-limits)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `firecrawl-security-basics`.
