---
name: apify-performance-tuning
description: |
  Optimize Apify Actor performance: crawl speed, memory usage, concurrency, and proxy rotation.
  Use when Actors are slow, consuming too much memory, or being blocked by target sites.
  Trigger: "apify performance", "optimize apify actor", "apify slow",
  "crawlee concurrency", "apify memory tuning", "scraper performance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Performance Tuning

## Overview

Optimize Apify Actors for speed, cost, and reliability. Covers Crawlee concurrency settings, memory profiling, proxy rotation strategies, request batching, and crawler selection for different workloads.

## Prerequisites

- Existing Actor with measurable baseline performance
- Understanding of `apify-sdk-patterns`
- Access to Actor run stats in Apify Console

## Performance Baseline

Measure before optimizing. Key metrics from run stats:

```typescript
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const run = await client.run('RUN_ID').get();

console.log({
  totalDurationSecs: run.stats?.runTimeSecs,
  pagesPerMinute: (run.stats?.requestsFinished ?? 0) / ((run.stats?.runTimeSecs ?? 1) / 60),
  failedRequests: run.stats?.requestsFailed,
  retryRequests: run.stats?.requestsRetries,
  memoryAvgMb: run.stats?.memAvgBytes ? run.stats.memAvgBytes / 1e6 : null,
  memoryMaxMb: run.stats?.memMaxBytes ? run.stats.memMaxBytes / 1e6 : null,
  computeUnits: run.usage?.ACTOR_COMPUTE_UNITS,
  costUsd: run.usageTotalUsd,
});
```

## Instructions

### Step 1: Choose the Right Crawler

| Crawler | Speed | JS Rendering | Memory | Use When |
|---------|-------|-------------|--------|----------|
| `CheerioCrawler` | Very fast | No | Low (~50MB) | Static HTML, SSR pages |
| `PlaywrightCrawler` | Moderate | Yes | High (~200MB/page) | SPAs, dynamic content |
| `PuppeteerCrawler` | Moderate | Yes | High (~200MB/page) | Chromium-specific needs |
| `HttpCrawler` | Fastest | No | Minimal | APIs, JSON endpoints |

```typescript
// Switch from Playwright to Cheerio for 5-10x speed improvement
// (if pages don't require JavaScript rendering)
import { CheerioCrawler } from 'crawlee';

const crawler = new CheerioCrawler({
  // Cheerio parses HTML without launching a browser
  requestHandler: async ({ $, request }) => {
    const title = $('title').text();
    await Actor.pushData({ url: request.url, title });
  },
});
```

### Step 2: Tune Concurrency

```typescript
const crawler = new CheerioCrawler({
  // --- Concurrency controls ---
  minConcurrency: 1,        // Start with 1 parallel request
  maxConcurrency: 50,       // Scale up to 50 (CheerioCrawler can handle more)

  // For PlaywrightCrawler, use lower values (each page = ~200MB)
  // maxConcurrency: 5,

  // Auto-scaling pool adjusts between min and max based on system load
  autoscaledPoolOptions: {
    desiredConcurrency: 10,
    scaleUpStepRatio: 0.05,   // Increase concurrency 5% at a time
    scaleDownStepRatio: 0.05,
    maybeRunIntervalSecs: 5,
  },

  // Rate limiting (protect target site)
  maxRequestsPerMinute: 300,  // Hard cap
});
```

### Step 3: Optimize Memory

```typescript
// CheerioCrawler memory optimization
const crawler = new CheerioCrawler({
  // Don't keep full HTML in memory
  requestHandlerTimeoutSecs: 30,

  // Process and discard — don't accumulate
  requestHandler: async ({ $, request }) => {
    // Extract only what you need
    const data = {
      url: request.url,
      title: $('title').text().trim(),
      price: parseFloat($('.price').text().replace(/[^0-9.]/g, '')),
    };

    // Push immediately (don't collect in array)
    await Actor.pushData(data);
  },
});

// PlaywrightCrawler memory optimization
const playwrightCrawler = new PlaywrightCrawler({
  maxConcurrency: 3,  // Key: fewer concurrent browsers

  launchContext: {
    launchOptions: {
      headless: true,
      args: [
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-extensions',
      ],
    },
  },

  preNavigationHooks: [
    async ({ page }) => {
      // Block heavy resources to save memory and bandwidth
      await page.route('**/*.{png,jpg,jpeg,gif,svg,webp,ico}', route => route.abort());
      await page.route('**/*.{css,woff,woff2,ttf}', route => route.abort());
      await page.route('**/analytics*', route => route.abort());
      await page.route('**/tracking*', route => route.abort());
    },
  ],

  postNavigationHooks: [
    async ({ page }) => {
      // Close unnecessary page resources
      await page.evaluate(() => {
        window.stop();  // Stop loading remaining resources
      });
    },
  ],
});
```

### Step 4: Memory Allocation Strategy

Actor memory affects both performance and cost:

```
CU = (Memory in GB) x (Duration in hours)
CU cost = $0.25 - $0.30 per CU (plan-dependent)
```

| Actor Type | Recommended Memory | Reasoning |
|-----------|-------------------|-----------|
| CheerioCrawler (simple) | 256-512 MB | HTML parsing is lightweight |
| CheerioCrawler (complex) | 512-1024 MB | Large pages, many concurrent |
| PlaywrightCrawler | 2048-4096 MB | Each browser page ~200MB |
| Data processing | 1024-2048 MB | In-memory transforms |

```typescript
// Start low, let the platform auto-scale if needed
const run = await client.actor('user/actor').call(input, {
  memory: 512,    // Start here for Cheerio
  timeout: 3600,  // 1 hour max
});
```

### Step 5: Proxy Rotation for Speed and Reliability

```typescript
import { Actor } from 'apify';

// Datacenter proxy (fast, cheap, may be blocked)
const dcProxy = await Actor.createProxyConfiguration({
  groups: ['BUYPROXIES94952'],
});

// Residential proxy (slower, expensive, higher success rate)
const resProxy = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
  countryCode: 'US',
});

// Smart rotation: try datacenter first, fall back to residential
const crawler = new CheerioCrawler({
  proxyConfiguration: dcProxy,  // Start with fast proxy

  async failedRequestHandler({ request }, error) {
    if (error.message.includes('403') || error.message.includes('blocked')) {
      // Re-enqueue with residential proxy
      request.userData.useResidential = true;
      await crawler.requestQueue.addRequest(request, { forefront: true });
    }
  },

  async requestHandler({ request, session, ...ctx }) {
    if (request.userData.useResidential) {
      // Switch proxy for this request
      session?.retire();  // Force new IP
    }
    // ... extraction logic
  },
});
```

### Step 6: Request-Level Optimizations

```typescript
const crawler = new CheerioCrawler({
  // Retry configuration
  maxRequestRetries: 3,           // Default: 3
  requestHandlerTimeoutSecs: 30,  // Kill slow pages

  // Navigation settings (CheerioCrawler-specific)
  additionalMimeTypes: ['application/json'],  // Accept JSON responses
  suggestResponseEncoding: 'utf-8',

  // Session pool (IP rotation and ban detection)
  useSessionPool: true,
  sessionPoolOptions: {
    maxPoolSize: 100,                    // Sessions in pool
    sessionOptions: {
      maxUsageCount: 50,                 // Requests per session
      maxErrorScore: 3,                  // Errors before retiring session
    },
  },

  // Pre-navigation hooks for request modification
  preNavigationHooks: [
    async ({ request }) => {
      // Add headers that help avoid blocks
      request.headers = {
        ...request.headers,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml',
      };
    },
  ],
});
```

## Performance Monitoring in Actors

```typescript
import { Actor } from 'apify';
import { log } from 'crawlee';

// Log performance metrics during the crawl
let processedCount = 0;
const startTime = Date.now();

const crawler = new CheerioCrawler({
  requestHandler: async ({ request, $ }) => {
    processedCount++;

    if (processedCount % 100 === 0) {
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = processedCount / (elapsed / 60);
      log.info(`Progress: ${processedCount} pages | ${rate.toFixed(1)} pages/min`);
    }

    await Actor.pushData({
      url: request.url,
      title: $('title').text().trim(),
    });
  },
});
```

## Performance Comparison

| Optimization | Before | After | Impact |
|-------------|--------|-------|--------|
| Cheerio instead of Playwright | 3 pages/min | 30 pages/min | 10x speed |
| Block images/CSS | 5 pages/min | 12 pages/min | 2.4x speed |
| Increase concurrency | 5 pages/min | 25 pages/min | 5x speed |
| Reduce memory 4GB to 512MB | $0.04/run | $0.005/run | 8x cost savings |
| Batch dataset pushes | 1000 API calls | 1 API call | Eliminates rate limits |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Out of memory crash | Too many concurrent browsers | Reduce `maxConcurrency` |
| Slow crawl speed | Low concurrency | Increase `maxConcurrency` |
| High failure rate | Anti-bot blocking | Add proxy, reduce concurrency |
| Expensive runs | Over-provisioned memory | Profile and reduce allocation |
| Stalled crawl | Request handler timeout | Set `requestHandlerTimeoutSecs` |

## Resources

- [Crawlee Performance Guide](https://crawlee.dev/js/docs/guides/configuration)
- [Actor Memory & Performance](https://docs.apify.com/platform/actors/running/usage-and-resources)
- [Proxy Management](https://docs.apify.com/sdk/js/docs/guides/proxy-management)

## Next Steps

For cost optimization, see `apify-cost-tuning`.
