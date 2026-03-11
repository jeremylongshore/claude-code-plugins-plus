---
name: firecrawl-architecture-variants
description: |
  Choose and implement FireCrawl validated architecture blueprints for different scales.
  Use when designing new FireCrawl integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for FireCrawl applications.
  Trigger with phrases like "firecrawl architecture", "firecrawl blueprint",
  "how to structure firecrawl", "firecrawl project layout", "firecrawl microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Architecture Variants

## Overview
Deployment architectures for Firecrawl web scraping at different scales. Firecrawl's async crawl model, credit billing, and JavaScript rendering support different architectures from simple page scraping to enterprise content ingestion pipelines.

## Prerequisites
- Firecrawl API configured
- Clear scraping use case defined
- Infrastructure for async job processing

## Instructions

### Step 1: On-Demand Scraping (Simple)

**Best for:** Single-page scraping, < 500 pages/day, content extraction.

```
User Request -> Backend -> Firecrawl scrapeUrl -> Parse Content -> Response
```

```typescript
app.post('/extract', async (req, res) => {
  const result = await firecrawl.scrapeUrl(req.body.url, {
    formats: ['markdown'], onlyMainContent: true
  });
  res.json({ content: result.markdown, title: result.metadata.title });
});
```

### Step 2: Scheduled Crawl Pipeline (Moderate)

**Best for:** Content monitoring, 500-10K pages/day, documentation indexing.

```
Scheduler (cron) -> Crawl Queue -> Firecrawl crawlUrl -> Result Store
                                                              |
                                                              v
                                                    Content Processor -> Search Index
```

```typescript
// Scheduled crawler
cron.schedule('0 2 * * *', async () => {  // Daily at 2 AM
  const sites = await db.getCrawlTargets();
  for (const site of sites) {
    const crawl = await firecrawl.asyncCrawlUrl(site.url, {
      limit: site.maxPages, includePaths: site.paths
    });
    await db.saveCrawlJob({ siteId: site.id, jobId: crawl.id });
  }
});

// Separate worker polls for results
async function processCrawlResults() {
  const pending = await db.getPendingCrawlJobs();
  for (const job of pending) {
    const status = await firecrawl.checkCrawlStatus(job.jobId);
    if (status.status === 'completed') {
      await indexPages(status.data);
      await db.markComplete(job.id);
    }
  }
}
```

### Step 3: Real-Time Content Pipeline (Scale)

**Best for:** Enterprise, 10K+ pages/day, AI training data, knowledge base.

```
URL Sources -> Priority Queue -> Firecrawl Workers -> Content Validation
                                                            |
                                                            v
                                                     Vector DB + Search Index
                                                            |
                                                            v
                                                      RAG / AI Pipeline
```

```typescript
class ContentPipeline {
  async ingest(urls: string[], priority: 'high' | 'normal' | 'low') {
    const budget = this.creditTracker.canAfford(urls.length);
    if (!budget) throw new Error('Daily credit budget exceeded');

    const results = await firecrawl.batchScrapeUrls(urls, {
      formats: ['markdown'], onlyMainContent: true
    });

    const validated = results.filter(r => this.validateContent(r));
    await this.vectorStore.upsert(validated);
    this.creditTracker.record(urls.length);
    return { ingested: validated.length, rejected: urls.length - validated.length };
  }
}
```

## Decision Matrix

| Factor | On-Demand | Scheduled | Real-Time Pipeline |
|--------|-----------|-----------|-------------------|
| Volume | < 500/day | 500-10K/day | 10K+/day |
| Latency | Sync (2-10s) | Async (hours) | Async (minutes) |
| Use Case | Single page | Site monitoring | Knowledge base |
| Cost Control | Per-request | Per-crawl budget | Credit pipeline |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow scraping in request path | Synchronous scrapeUrl | Move to async pipeline |
| Stale content | Infrequent crawling | Increase crawl frequency |
| Credit overrun | No budget tracking | Implement credit circuit breaker |
| Duplicate content | Re-crawling same pages | Dedup by URL hash before indexing |

## Examples

### Architecture Selection
```
< 500 pages/day, user-facing: On-Demand
500-10K pages, batch processing: Scheduled Pipeline  
10K+, AI/ML ingestion: Real-Time Pipeline
```

## Resources
- [Firecrawl API Docs](https://docs.firecrawl.dev)
