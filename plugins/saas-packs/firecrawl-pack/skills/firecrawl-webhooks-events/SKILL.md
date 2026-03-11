---
name: firecrawl-webhooks-events
description: |
  Implement FireCrawl webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling FireCrawl event notifications securely.
  Trigger with phrases like "firecrawl webhook", "firecrawl events",
  "firecrawl webhook signature", "handle firecrawl events", "firecrawl notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Webhooks & Events

## Overview
Handle Firecrawl webhooks for async crawl and scrape job notifications. Firecrawl supports native webhooks on crawl jobs via `api.firecrawl.dev` -- when a crawl completes, partially completes, or fails, Firecrawl POSTs results to your configured webhook URL. This enables building pipelines that react to scraped content automatically.

## Prerequisites
- Firecrawl API key stored in `FIRECRAWL_API_KEY` environment variable
- HTTPS endpoint accessible from the internet for webhook delivery
- Understanding of Firecrawl crawl vs scrape vs map endpoints
- Queue system for processing large crawl results

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `crawl.completed` | Full crawl finishes | Array of page results, metadata |
| `crawl.page` | Individual page scraped | Single page markdown/HTML content |
| `crawl.failed` | Crawl job errors | Error message, partial results |
| `crawl.started` | Crawl begins | Job ID, configuration |
| `batch_scrape.completed` | Batch scrape finishes | Array of scraped pages |

## Instructions

### Step 1: Start a Crawl with Webhook
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

const crawlResult = await firecrawl.asyncCrawlUrl("https://docs.example.com", {
  limit: 100,
  scrapeOptions: {
    formats: ["markdown", "html"],
  },
  webhook: "https://api.yourapp.com/webhooks/firecrawl",
});

console.log(`Crawl started: ${crawlResult.id}`);
```

### Step 2: Handle Webhook Events
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/firecrawl", async (req, res) => {
  const { type, id, data } = req.body;

  res.status(200).json({ received: true });

  switch (type) {
    case "crawl.completed":
      await handleCrawlComplete(id, data);
      break;
    case "crawl.page":
      await handlePageScraped(id, data);
      break;
    case "crawl.failed":
      await handleCrawlFailed(id, data);
      break;
  }
});

async function handleCrawlComplete(jobId: string, data: any) {
  const { pages, totalPages } = data;
  console.log(`Crawl ${jobId} complete: ${totalPages} pages scraped`);

  for (const page of pages) {
    await indexPage({
      url: page.metadata?.sourceURL,
      title: page.metadata?.title,
      markdown: page.markdown,
      scrapedAt: new Date(),
    });
  }
}
```

### Step 3: Process Individual Pages
```typescript
async function handlePageScraped(jobId: string, data: any) {
  const { markdown, metadata } = data;

  // Extract structured data from scraped page
  await documentStore.upsert({
    url: metadata.sourceURL,
    title: metadata.title,
    content: markdown,
    links: metadata.links || [],
    statusCode: metadata.statusCode,
  });
}

async function handleCrawlFailed(jobId: string, data: any) {
  console.error(`Crawl ${jobId} failed: ${data.error}`);

  await alerting.send({
    severity: "high",
    message: `Firecrawl job ${jobId} failed`,
    error: data.error,
    partialResults: data.partialResults?.length || 0,
  });
}
```

### Step 4: Poll as Fallback
```typescript
async function pollCrawlStatus(jobId: string) {
  const status = await firecrawl.checkCrawlStatus(jobId);

  if (status.status === "completed") {
    await handleCrawlComplete(jobId, { pages: status.data });
  } else if (status.status === "scraping") {
    console.log(`Progress: ${status.completed}/${status.total} pages`);
    setTimeout(() => pollCrawlStatus(jobId), 5000);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | URL unreachable | Verify endpoint is publicly accessible |
| Partial results | Page limit reached | Increase `limit` or filter with `includePaths` |
| Rate limited | Too many concurrent crawls | Queue crawl jobs, respect rate limits |
| Timeout on large sites | Crawl takes too long | Use `maxDepth` and `includePaths` filters |

## Examples

### Build Search Index from Crawl
```typescript
async function buildSearchIndex(pages: any[]) {
  const documents = pages.map(page => ({
    id: page.metadata.sourceURL,
    content: page.markdown,
    title: page.metadata.title,
    url: page.metadata.sourceURL,
  }));

  await searchEngine.indexBatch(documents);
  console.log(`Indexed ${documents.length} pages`);
}
```

## Resources
- [Firecrawl API Documentation](https://docs.firecrawl.dev)
- [Firecrawl Webhook Guide](https://docs.firecrawl.dev/features/crawl#webhook)
- [Firecrawl JS SDK](https://github.com/mendableai/firecrawl-js)

## Next Steps
For deployment setup, see `firecrawl-deploy-integration`.
