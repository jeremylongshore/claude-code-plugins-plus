---
name: brightdata-rate-limits
description: |
  Implement Bright Data rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Bright Data.
  Trigger with phrases like "brightdata rate limit", "brightdata throttling",
  "brightdata 429", "brightdata retry", "brightdata backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Rate Limits

## Overview

Handle Bright Data rate limits and concurrent request limits. Unlike traditional API rate limits, Bright Data limits are per-zone and based on concurrent connections and requests per second. The Web Scraper API trigger endpoint is limited to 20 requests/min and 60 requests/hour.

## Prerequisites

- Bright Data zone configured
- Understanding of async/await patterns
- p-queue or similar concurrency library

## Instructions

### Step 1: Understand Bright Data Rate Limits

| Product | Concurrent Limit | Per-Minute | Notes |
|---------|-----------------|------------|-------|
| Residential Proxy | Based on plan | No hard cap | Charged per GB |
| Web Unlocker | Based on plan | No hard cap | Charged per request |
| Scraping Browser | Based on plan sessions | No hard cap | Charged per session |
| SERP API | Based on plan | No hard cap | Charged per search |
| Web Scraper API (trigger) | N/A | 20/min, 60/hr | Async collections |
| Datasets API | N/A | 20/min | Snapshot requests |

### Step 2: Implement Concurrent Request Limiter

```typescript
// src/brightdata/limiter.ts
import PQueue from 'p-queue';

// Match concurrency to your Bright Data plan limits
const scrapeQueue = new PQueue({
  concurrency: 10,       // Max concurrent proxy requests
  interval: 1000,        // Per second
  intervalCap: 20,       // Max 20 requests per second
  timeout: 120000,       // Kill after 2 min
  throwOnTimeout: true,
});

export async function queuedScrape(url: string): Promise<string> {
  return scrapeQueue.add(async () => {
    const client = getBrightDataClient();
    const response = await client.get(url);
    return response.data;
  });
}

// Monitor queue health
scrapeQueue.on('active', () => {
  console.log(`Queue: ${scrapeQueue.size} waiting, ${scrapeQueue.pending} active`);
});
```

### Step 3: Exponential Backoff for Proxy Errors

```typescript
// src/brightdata/backoff.ts
export async function scrapeWithBackoff(
  url: string,
  config = { maxRetries: 5, baseDelay: 2000, maxDelay: 60000 }
): Promise<string> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const client = getBrightDataClient();
      const response = await client.get(url);
      return response.data;
    } catch (error: any) {
      const status = error.response?.status;
      const luminatiError = error.response?.headers?.['x-luminati-error'];

      // Only retry on transient errors
      const retryable = [502, 503, 429].includes(status)
        || error.code === 'ETIMEDOUT'
        || luminatiError === 'ip_banned';

      if (attempt === config.maxRetries || !retryable) throw error;

      const delay = Math.min(
        config.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        config.maxDelay
      );
      console.log(`[${luminatiError || status}] Retry ${attempt + 1} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Web Scraper API Rate Limiter

```typescript
// src/brightdata/trigger-limiter.ts — 20/min, 60/hr for trigger endpoint
const triggerQueue = new PQueue({
  concurrency: 1,
  interval: 60000,       // Per minute
  intervalCap: 20,       // 20 triggers per minute
});

let hourlyCount = 0;
setInterval(() => { hourlyCount = 0; }, 3600000); // Reset hourly

export async function rateLimitedTrigger(
  datasetId: string,
  urls: string[]
): Promise<any> {
  if (hourlyCount >= 55) { // Leave buffer
    throw new Error('Approaching hourly trigger limit (60/hr). Wait before triggering.');
  }

  return triggerQueue.add(async () => {
    hourlyCount++;
    const response = await fetch(
      `https://api.brightdata.com/datasets/v3/trigger?dataset_id=${datasetId}&format=json`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.BRIGHTDATA_API_TOKEN}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(urls.map(url => ({ url }))),
      }
    );
    return response.json();
  });
}
```

### Step 5: Batch URLs to Minimize Triggers

```typescript
// Instead of triggering per-URL, batch into single triggers
async function batchTrigger(urls: string[], batchSize = 100) {
  const batches = [];
  for (let i = 0; i < urls.length; i += batchSize) {
    batches.push(urls.slice(i, i + batchSize));
  }

  console.log(`Triggering ${urls.length} URLs in ${batches.length} batches`);

  for (const batch of batches) {
    await rateLimitedTrigger('gd_dataset_id', batch);
  }
}
```

## Output

- Concurrent request limiter matching plan limits
- Exponential backoff handling X-Luminati error headers
- Web Scraper API trigger rate limiter (20/min, 60/hr)
- URL batching to minimize trigger count

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| HTTP 429 | Concurrent limit exceeded | Queue requests with p-queue |
| HTTP 502 + `ip_banned` | IP blocked by target | Retry (auto-rotates IP) |
| HTTP 502 + `target_site_blocked` | Anti-bot blocked | Switch to Scraping Browser |
| `ETIMEDOUT` | Connection timeout | Retry with longer timeout |
| Hourly trigger limit | 60 triggers/hr exceeded | Batch URLs into fewer triggers |

## Resources

- [Bright Data Proxy Limits](https://docs.brightdata.com/general/account/proxy-infrastructure)
- [Web Scraper API Limits](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/trigger-a-collection)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `brightdata-security-basics`.
