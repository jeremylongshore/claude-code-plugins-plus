---
name: firecrawl-performance-tuning
description: |
  Optimize Firecrawl scraping performance with caching, batch scraping, and format selection.
  Use when experiencing slow scrapes, optimizing credit usage per page,
  or building high-throughput scraping pipelines.
  Trigger with phrases like "firecrawl performance", "optimize firecrawl",
  "firecrawl latency", "firecrawl caching", "firecrawl slow", "firecrawl batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, performance]

---
# Firecrawl Performance Tuning

## Overview
Optimize Firecrawl API performance by choosing efficient scraping modes, caching results, using batch endpoints, and minimizing unnecessary rendering. Key levers: format selection (markdown vs HTML vs screenshot), `waitFor` tuning, `onlyMainContent`, and batch vs individual scraping.

## Latency Benchmarks

| Operation | Typical | With JS Wait | With Screenshot |
|-----------|---------|--------------|-----------------|
| scrapeUrl (markdown) | 2-5s | 5-10s | 8-15s |
| scrapeUrl (extract) | 3-8s | 8-15s | N/A |
| crawlUrl (10 pages) | 20-40s | 40-80s | N/A |
| mapUrl | 1-3s | N/A | N/A |
| batchScrapeUrls (10) | 10-20s | 20-40s | N/A |

## Instructions

### Step 1: Minimize Formats (Biggest Win)
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// SLOW: requesting everything
const slow = await firecrawl.scrapeUrl(url, {
  formats: ["markdown", "html", "links", "screenshot"],
  // screenshot + full HTML = 3-5x slower
});

// FAST: request only what you need
const fast = await firecrawl.scrapeUrl(url, {
  formats: ["markdown"],   // markdown only = fastest
  onlyMainContent: true,   // skip nav/footer/sidebar
});
```

### Step 2: Tune waitFor for JS-Heavy Pages
```typescript
// Default: no JS wait (fastest, works for static sites)
const staticResult = await firecrawl.scrapeUrl("https://docs.example.com", {
  formats: ["markdown"],
  // No waitFor needed — content is in initial HTML
});

// SPA/dynamic pages: add minimal wait
const spaResult = await firecrawl.scrapeUrl("https://app.example.com", {
  formats: ["markdown"],
  waitFor: 3000,  // 3s — enough for most SPAs
  onlyMainContent: true,
});

// Heavy interactive page: use actions instead of long wait
const heavyResult = await firecrawl.scrapeUrl("https://dashboard.example.com", {
  formats: ["markdown"],
  actions: [
    { type: "wait", selector: ".data-table" },  // wait for specific element
    { type: "scroll", direction: "down" },        // trigger lazy loading
  ],
});
```

### Step 3: Cache Scraped Content
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const scrapeCache = new LRUCache<string, any>({
  max: 500,          // max 500 cached pages
  ttl: 3600000,      // 1 hour TTL
});

async function cachedScrape(url: string) {
  const key = createHash("md5").update(url).digest("hex");
  const cached = scrapeCache.get(key);
  if (cached) {
    console.log(`Cache hit: ${url}`);
    return cached;
  }

  const result = await firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
  });

  if (result.success) {
    scrapeCache.set(key, result);
  }
  return result;
}
// Typical savings: 50-80% credit reduction for repeated scrapes
```

### Step 4: Use Batch Scrape for Multiple URLs
```typescript
// SLOW: sequential individual scrapes
const urls = ["https://a.com", "https://b.com", "https://c.com"];
for (const url of urls) {
  await firecrawl.scrapeUrl(url, { formats: ["markdown"] }); // 3 API calls
}

// FAST: single batch scrape call
const batchResult = await firecrawl.batchScrapeUrls(urls, {
  formats: ["markdown"],
  onlyMainContent: true,
});
// 1 API call, internally parallelized
```

### Step 5: Map Before Crawl (Save Credits)
```typescript
// EXPENSIVE: crawl everything, filter later
await firecrawl.crawlUrl("https://docs.example.com", { limit: 1000 });

// CHEAPER: map first (1 credit), then scrape only what you need
const map = await firecrawl.mapUrl("https://docs.example.com");
const apiDocs = (map.links || []).filter(url =>
  url.includes("/api/") || url.includes("/reference/")
);
console.log(`Map: ${map.links?.length} total, ${apiDocs.length} relevant`);

// Batch scrape only relevant URLs
const result = await firecrawl.batchScrapeUrls(apiDocs.slice(0, 50), {
  formats: ["markdown"],
});
```

### Step 6: Measure Scrape Performance
```typescript
async function timedScrape(url: string) {
  const start = Date.now();
  const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
  const duration = Date.now() - start;

  console.log({
    url,
    durationMs: duration,
    contentLength: result.markdown?.length || 0,
    success: result.success,
    charsPerSecond: Math.round((result.markdown?.length || 0) / (duration / 1000)),
  });

  return result;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Scrape > 10s | Screenshot or full HTML requested | Use `formats: ["markdown"]` only |
| Empty content | `waitFor` too short for SPA | Increase or use `actions` with selector |
| High credit burn | Scraping same URLs repeatedly | Implement URL-based caching |
| Batch timeout | Too many URLs in one batch | Split into chunks of 50 |
| Cache stale data | TTL too long | Reduce TTL or add cache invalidation |

## Examples

### Performance Comparison Script
```typescript
const url = "https://docs.firecrawl.dev";

// Compare different format configurations
for (const formats of [["markdown"], ["markdown", "html"], ["markdown", "html", "screenshot"]]) {
  const start = Date.now();
  await firecrawl.scrapeUrl(url, { formats: formats as any, onlyMainContent: true });
  console.log(`${formats.join(",")}: ${Date.now() - start}ms`);
}
```

## Resources
- [Advanced Scraping Guide](https://docs.firecrawl.dev/advanced-scraping-guide)
- [Batch Scrape](https://docs.firecrawl.dev/features/batch-scrape)
- [Map Endpoint](https://docs.firecrawl.dev/features/map)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps
For cost optimization, see `firecrawl-cost-tuning`.
