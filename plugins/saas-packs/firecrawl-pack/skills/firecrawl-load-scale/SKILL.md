---
name: firecrawl-load-scale
description: |
  Load test and scale Firecrawl scraping pipelines with concurrency control and batching.
  Use when testing scraping throughput, planning capacity for large crawl jobs,
  or optimizing concurrent scrape performance.
  Trigger with phrases like "firecrawl load test", "firecrawl scale",
  "firecrawl throughput", "firecrawl capacity", "firecrawl concurrent".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, testing, performance, scaling]

---
# Firecrawl Load & Scale

## Overview
Load test and scale Firecrawl scraping pipelines. Firecrawl's rate limits are per-plan (RPM and concurrent connections), so scaling means maximizing throughput within those limits using batch scraping, async crawls, and queue-based request management.

## Rate Limits by Plan

| Plan | Scrape RPM | Concurrent Crawls | Max Batch Size |
|------|-----------|-------------------|----------------|
| Free | 10 | 2 | 10 |
| Hobby | 20 | 3 | 50 |
| Standard | 50 | 5 | 100 |
| Growth | 100 | 10 | 100 |
| Scale | 500+ | 50+ | 100 |

## Instructions

### Step 1: Measure Baseline Throughput
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

async function measureThroughput(urls: string[], concurrency: number) {
  const start = Date.now();
  const results: Array<{ url: string; durationMs: number; success: boolean; chars: number }> = [];

  // Process in batches of `concurrency`
  for (let i = 0; i < urls.length; i += concurrency) {
    const batch = urls.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(async url => {
        const t0 = Date.now();
        try {
          const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
          return { url, durationMs: Date.now() - t0, success: true, chars: result.markdown?.length || 0 };
        } catch {
          return { url, durationMs: Date.now() - t0, success: false, chars: 0 };
        }
      })
    );
    results.push(...batchResults);
  }

  const totalMs = Date.now() - start;
  const succeeded = results.filter(r => r.success).length;

  console.log(`=== Throughput Report ===`);
  console.log(`URLs: ${urls.length}, Concurrency: ${concurrency}`);
  console.log(`Total time: ${totalMs}ms`);
  console.log(`Success: ${succeeded}/${urls.length}`);
  console.log(`Throughput: ${(urls.length / (totalMs / 1000)).toFixed(1)} pages/sec`);
  console.log(`Avg latency: ${(results.reduce((s, r) => s + r.durationMs, 0) / results.length).toFixed(0)}ms`);

  return results;
}
```

### Step 2: Use Batch Scrape for Maximum Efficiency
```typescript
// batchScrapeUrls is the most efficient way to scrape multiple known URLs
async function scaledBatchScrape(urls: string[], batchSize = 50) {
  const allResults: any[] = [];

  for (let i = 0; i < urls.length; i += batchSize) {
    const batch = urls.slice(i, i + batchSize);
    console.log(`Batch ${i / batchSize + 1}: scraping ${batch.length} URLs...`);

    const result = await firecrawl.batchScrapeUrls(batch, {
      formats: ["markdown"],
      onlyMainContent: true,
    });

    allResults.push(...(result.data || []));
    console.log(`  Done: ${result.data?.length} pages scraped`);
  }

  return allResults;
}
```

### Step 3: Queue-Based Scraping with p-queue
```typescript
import PQueue from "p-queue";

function createScrapeQueue(config: {
  concurrency: number;
  requestsPerSecond: number;
}) {
  const queue = new PQueue({
    concurrency: config.concurrency,
    interval: 1000,
    intervalCap: config.requestsPerSecond,
  });

  async function scrape(url: string) {
    return queue.add(async () => {
      const result = await firecrawl.scrapeUrl(url, {
        formats: ["markdown"],
        onlyMainContent: true,
      });
      return { url, markdown: result.markdown, title: result.metadata?.title };
    });
  }

  return { scrape, queue };
}

// Usage: respect rate limits automatically
const { scrape, queue } = createScrapeQueue({
  concurrency: 5,
  requestsPerSecond: 10,
});

const urls = ["https://a.com", "https://b.com", /* ... */];
const results = await Promise.all(urls.map(scrape));
console.log(`Queue: ${queue.pending} pending, ${queue.size} queued`);
```

### Step 4: Scale Async Crawls
```typescript
// For large-scale content ingestion, run multiple async crawls
async function parallelCrawls(targets: Array<{ url: string; limit: number }>) {
  // Start all crawls
  const jobs = await Promise.all(
    targets.map(async t => {
      const job = await firecrawl.asyncCrawlUrl(t.url, {
        limit: t.limit,
        scrapeOptions: { formats: ["markdown"] },
      });
      return { ...t, jobId: job.id };
    })
  );

  console.log(`Started ${jobs.length} crawl jobs`);

  // Poll all jobs until complete
  const results: any[] = [];
  const pending = new Set(jobs.map(j => j.jobId));

  while (pending.size > 0) {
    for (const jobId of [...pending]) {
      const status = await firecrawl.checkCrawlStatus(jobId);
      if (status.status === "completed") {
        results.push({ jobId, pages: status.data?.length });
        pending.delete(jobId);
        console.log(`Job ${jobId} complete: ${status.data?.length} pages (${pending.size} remaining)`);
      } else if (status.status === "failed") {
        pending.delete(jobId);
        console.error(`Job ${jobId} failed: ${status.error}`);
      }
    }
    if (pending.size > 0) {
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  return results;
}
```

### Step 5: Capacity Planning
```typescript
function estimateCapacity(plan: {
  rpm: number;
  concurrentCrawls: number;
  credits: number;
}) {
  const pagesPerMinute = plan.rpm;
  const pagesPerHour = pagesPerMinute * 60;
  const pagesPerDay = pagesPerHour * 24;
  const daysOfCredits = plan.credits / (pagesPerDay * 0.5); // assume 50% utilization

  console.log(`=== Capacity Estimate ===`);
  console.log(`Max throughput: ${pagesPerMinute} pages/min`);
  console.log(`Daily capacity: ${pagesPerDay.toLocaleString()} pages/day`);
  console.log(`Credit runway: ${daysOfCredits.toFixed(0)} days at 50% utilization`);
  console.log(`Concurrent crawl jobs: ${plan.concurrentCrawls}`);
}

// Standard plan
estimateCapacity({ rpm: 50, concurrentCrawls: 5, credits: 50000 });
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors under load | Exceeding RPM limit | Reduce concurrency, use p-queue |
| Batch scrape timeout | Too many URLs | Split into chunks of 50 |
| Crawl jobs queued | Hit concurrent crawl limit | Stagger start times |
| Diminishing returns | Network bottleneck | Increase plan tier, not concurrency |

## Examples

### Quick Load Test
```typescript
const testUrls = Array.from({ length: 20 }, (_, i) =>
  `https://docs.firecrawl.dev/features/${["scrape", "crawl", "map", "extract"][i % 4]}`
);
await measureThroughput(testUrls, 5);
```

## Resources
- [Firecrawl Rate Limits](https://docs.firecrawl.dev/rate-limits)
- [Batch Scrape](https://docs.firecrawl.dev/features/batch-scrape)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For reliability patterns, see `firecrawl-reliability-patterns`.
