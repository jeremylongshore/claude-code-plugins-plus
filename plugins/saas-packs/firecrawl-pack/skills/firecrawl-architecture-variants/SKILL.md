---
name: firecrawl-architecture-variants
description: |
  Choose and implement Firecrawl architecture patterns for different scales and use cases.
  Use when designing new Firecrawl integrations, choosing between on-demand/scheduled/pipeline
  architectures, or planning scraping infrastructure.
  Trigger with phrases like "firecrawl architecture", "firecrawl blueprint",
  "how to structure firecrawl", "firecrawl at scale", "firecrawl pipeline design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, migration, scaling, microservices]

---
# Firecrawl Architecture Variants

## Overview
Three deployment architectures for Firecrawl at different scales: on-demand scraping for simple use cases, scheduled crawl pipelines for content monitoring, and real-time ingestion pipelines for AI/RAG applications. Choose based on volume, latency requirements, and cost budget.

## Decision Matrix

| Factor | On-Demand | Scheduled Pipeline | Real-Time Pipeline |
|--------|-----------|-------------------|-------------------|
| Volume | < 500/day | 500-10K/day | 10K+/day |
| Latency | Sync (2-10s) | Async (hours) | Async (minutes) |
| Use Case | Single page lookup | Site monitoring | Knowledge base, RAG |
| Credit Control | Per-request | Per-crawl budget | Credit pipeline |
| Complexity | Low | Medium | High |

## Instructions

### Architecture 1: On-Demand Scraping
```
User Request → Backend API → firecrawl.scrapeUrl → Clean Content → Response
```

Best for: chatbots, content preview, single-page extraction.

```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Simple API endpoint
app.post("/api/scrape", async (req, res) => {
  const { url } = req.body;

  const result = await firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
    waitFor: 3000,
  });

  res.json({
    title: result.metadata?.title,
    content: result.markdown,
    url: result.metadata?.sourceURL,
  });
});

// With LLM extraction
app.post("/api/extract", async (req, res) => {
  const { url, schema } = req.body;

  const result = await firecrawl.scrapeUrl(url, {
    formats: ["extract"],
    extract: { schema },
  });

  res.json({ data: result.extract });
});
```

### Architecture 2: Scheduled Crawl Pipeline
```
Scheduler (cron) → Crawl Queue → firecrawl.asyncCrawlUrl → Result Store
                                                                  │
                                                                  ▼
                                                        Content Processor → Search Index
```

Best for: documentation monitoring, content indexing, competitive analysis.

```typescript
import cron from "node-cron";

interface CrawlTarget {
  id: string;
  url: string;
  maxPages: number;
  paths?: string[];
  schedule: string; // cron expression
}

const targets: CrawlTarget[] = [
  { id: "docs", url: "https://docs.example.com", maxPages: 100, paths: ["/docs/*"], schedule: "0 2 * * *" },
  { id: "blog", url: "https://blog.example.com", maxPages: 50, schedule: "0 4 * * 1" },
];

// Schedule crawls
for (const target of targets) {
  cron.schedule(target.schedule, async () => {
    console.log(`Starting scheduled crawl: ${target.id}`);
    const job = await firecrawl.asyncCrawlUrl(target.url, {
      limit: target.maxPages,
      includePaths: target.paths,
      scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
    });
    await db.saveCrawlJob({ targetId: target.id, jobId: job.id, startedAt: new Date() });
  });
}

// Separate worker polls for results
async function processPendingCrawls() {
  const pending = await db.getPendingCrawlJobs();
  for (const job of pending) {
    const status = await firecrawl.checkCrawlStatus(job.jobId);
    if (status.status === "completed") {
      await indexPages(job.targetId, status.data || []);
      await db.markComplete(job.id, status.data?.length || 0);
      console.log(`Crawl ${job.targetId} complete: ${status.data?.length} pages indexed`);
    }
  }
}
setInterval(processPendingCrawls, 30000);
```

### Architecture 3: Real-Time Content Pipeline
```
URL Sources → Priority Queue → Firecrawl Workers → Content Validation
                                                          │
                                                          ▼
                                                   Vector DB + Search Index
                                                          │
                                                          ▼
                                                    RAG / AI Pipeline
```

Best for: AI training data, knowledge base, enterprise content platform.

```typescript
import PQueue from "p-queue";

class ContentPipeline {
  private queue: PQueue;
  private firecrawl: FirecrawlApp;
  private creditBudget: number;
  private creditsUsed = 0;

  constructor(concurrency = 5, dailyBudget = 10000) {
    this.queue = new PQueue({ concurrency, interval: 1000, intervalCap: 10 });
    this.firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
    this.creditBudget = dailyBudget;
  }

  async ingest(urls: string[]) {
    if (this.creditsUsed + urls.length > this.creditBudget) {
      throw new Error("Daily credit budget exceeded");
    }

    // Use batch scrape for efficiency
    const result = await this.queue.add(() =>
      this.firecrawl.batchScrapeUrls(urls, {
        formats: ["markdown"],
        onlyMainContent: true,
      })
    );

    this.creditsUsed += urls.length;

    // Validate and process
    const pages = (result?.data || []).filter(page => {
      const md = page.markdown || "";
      return md.length > 100 && !/captcha|access denied/i.test(md);
    });

    // Store in vector DB
    for (const page of pages) {
      await vectorStore.upsert({
        id: page.metadata?.sourceURL,
        content: page.markdown,
        metadata: { title: page.metadata?.title, url: page.metadata?.sourceURL },
      });
    }

    return { ingested: pages.length, rejected: urls.length - pages.length };
  }

  async discover(siteUrl: string, pathFilter: string) {
    const map = await this.firecrawl.mapUrl(siteUrl);
    return (map.links || []).filter(url => url.includes(pathFilter));
  }
}

// Usage
const pipeline = new ContentPipeline(5, 10000);
const urls = await pipeline.discover("https://docs.example.com", "/api/");
const result = await pipeline.ingest(urls.slice(0, 100));
console.log(`Ingested ${result.ingested} pages into vector store`);
```

## Choosing Your Architecture

```
Need real-time, user-facing response?
├── YES → On-Demand (Architecture 1)
└── NO → How many pages/day?
    ├── < 500 → On-Demand with caching
    ├── 500-10K → Scheduled Pipeline (Architecture 2)
    └── 10K+ → Real-Time Pipeline (Architecture 3)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow on-demand response | JS-heavy target page | Add caching layer, reduce waitFor |
| Stale indexed content | Crawl schedule too infrequent | Increase frequency for critical sources |
| Credit overrun | Pipeline ingesting too aggressively | Implement daily budget with hard cap |
| Duplicate content | Re-crawling same pages | Deduplicate by content hash before indexing |

## Resources
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)
- [Batch Scrape](https://docs.firecrawl.dev/features/batch-scrape)
- [Crawl Endpoint](https://docs.firecrawl.dev/features/crawl)

## Next Steps
For common pitfalls, see `firecrawl-known-pitfalls`.
