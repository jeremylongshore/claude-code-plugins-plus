---
name: brightdata-performance-tuning
description: |
  Optimize Bright Data API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Bright Data integrations.
  Trigger with phrases like "brightdata performance", "optimize brightdata",
  "brightdata latency", "brightdata caching", "brightdata slow", "brightdata batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Performance Tuning

## Overview

Optimize Bright Data scraping performance through connection pooling, response caching, concurrent request tuning, and smart product selection. Web Unlocker latency is typically 5-30s due to CAPTCHA solving; Scraping Browser sessions are 10-60s.

## Prerequisites

- Bright Data zone configured
- Understanding of async patterns
- Redis or file cache available (optional)

## Latency Benchmarks

| Product | P50 | P95 | P99 | Notes |
|---------|-----|-----|-----|-------|
| Web Unlocker (simple) | 3s | 8s | 15s | No CAPTCHA |
| Web Unlocker (CAPTCHA) | 10s | 25s | 45s | With CAPTCHA solving |
| Scraping Browser | 8s | 20s | 40s | Full browser render |
| SERP API (sync) | 2s | 5s | 10s | Search results |
| Residential Proxy | 1s | 3s | 8s | Raw proxy, no unblocking |

## Instructions

### Step 1: Choose the Right Product

```typescript
// Product selection matrix
function selectProduct(target: { js: boolean; captcha: boolean; structured: boolean }) {
  if (target.structured) return 'serp_api';       // Pre-parsed JSON
  if (!target.js && !target.captcha) return 'residential'; // Fastest
  if (target.js) return 'scraping_browser';         // Browser rendering
  return 'web_unlocker';                            // Best default
}
```

### Step 2: Connection Pooling with Keep-Alive

```typescript
import { Agent } from 'https';
import axios from 'axios';

// Reuse TCP connections to brd.superproxy.io
const httpsAgent = new Agent({
  keepAlive: true,
  maxSockets: 25,        // Match your concurrency limit
  maxFreeSockets: 5,
  timeout: 120000,
  rejectUnauthorized: false,
});

const client = axios.create({
  proxy: { host: 'brd.superproxy.io', port: 33335, auth: { username: proxyUser, password: proxyPass } },
  httpsAgent,
  timeout: 60000,
});
```

### Step 3: Response Caching Layer

```typescript
// src/brightdata/cache.ts — avoid re-scraping identical URLs
import { createHash } from 'crypto';
import { LRUCache } from 'lru-cache';

const memoryCache = new LRUCache<string, string>({
  max: 500,             // Max cached pages
  maxSize: 100_000_000, // 100MB total
  sizeCalculation: (v) => Buffer.byteLength(v),
  ttl: 3600000,         // 1 hour
});

export async function cachedScrape(
  url: string,
  scraper: (url: string) => Promise<string>,
  ttlMs?: number
): Promise<string> {
  const key = createHash('sha256').update(url).digest('hex');
  const cached = memoryCache.get(key);
  if (cached) {
    console.log(`Cache HIT: ${url}`);
    return cached;
  }

  const html = await scraper(url);
  memoryCache.set(key, html, { ttl: ttlMs });
  console.log(`Cache MISS: ${url} (${Buffer.byteLength(html)} bytes)`);
  return html;
}
```

### Step 4: Concurrent Scraping with Backpressure

```typescript
import PQueue from 'p-queue';

// Tune concurrency based on your plan and target site
const scrapeQueue = new PQueue({
  concurrency: 10,      // Concurrent proxy connections
  interval: 1000,       // Per second window
  intervalCap: 15,      // Max new requests per second
});

async function scrapeMany(urls: string[]): Promise<Map<string, string>> {
  const results = new Map<string, string>();

  await Promise.allSettled(
    urls.map(url =>
      scrapeQueue.add(async () => {
        const html = await cachedScrape(url, (u) => client.get(u).then(r => r.data));
        results.set(url, html);
      })
    )
  );

  console.log(`Scraped ${results.size}/${urls.length} successfully`);
  return results;
}
```

### Step 5: Use Async API for Bulk Jobs

For 100+ URLs, use the Web Scraper API instead of individual proxy requests:

```typescript
// Bulk collection — one API call, Bright Data handles parallelism
async function bulkScrape(urls: string[]) {
  const response = await fetch(
    `https://api.brightdata.com/datasets/v3/trigger?dataset_id=${DATASET_ID}&format=json`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.BRIGHTDATA_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(urls.map(url => ({ url }))),
    }
  );
  return response.json(); // Returns snapshot_id for status polling
}
// 1000 URLs via one trigger vs 1000 individual proxy requests
```

### Step 6: Performance Monitoring

```typescript
class ScrapeMetrics {
  private timings: number[] = [];
  private errors = 0;
  private cacheHits = 0;

  record(durationMs: number) { this.timings.push(durationMs); }
  recordError() { this.errors++; }
  recordCacheHit() { this.cacheHits++; }

  report() {
    const sorted = [...this.timings].sort((a, b) => a - b);
    return {
      count: sorted.length,
      errors: this.errors,
      cacheHits: this.cacheHits,
      p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
      p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
    };
  }
}
```

## Output

- Right product selection per use case
- Connection pooling reducing TCP overhead
- Response cache avoiding duplicate scrapes
- Concurrent scraping with backpressure control
- Bulk API for large-scale jobs

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Slow scrapes | CAPTCHA solving overhead | Expected for Web Unlocker; use cache |
| Connection exhausted | Too many concurrent | Reduce p-queue concurrency |
| Memory pressure | Large cached pages | Set maxSize on LRU cache |
| Timeout storms | All requests hitting slow site | Add circuit breaker |

## Resources

- [Bright Data Products](https://brightdata.com/products)
- [Web Scraper API](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/overview)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `brightdata-cost-tuning`.
