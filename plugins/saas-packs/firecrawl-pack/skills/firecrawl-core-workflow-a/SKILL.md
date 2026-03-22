---
name: firecrawl-core-workflow-a
description: |
  Execute Firecrawl primary workflow: scrape and crawl websites into LLM-ready markdown.
  Use when scraping single pages, crawling entire sites, or building content
  ingestion pipelines with Firecrawl's scrapeUrl and crawlUrl methods.
  Trigger with phrases like "firecrawl scrape", "firecrawl crawl site",
  "scrape page to markdown", "crawl documentation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, workflow]

---
# Firecrawl Core Workflow A — Scrape & Crawl

## Overview
Primary workflow for Firecrawl: convert websites into clean LLM-ready markdown. Covers single-page scraping with `scrapeUrl`, multi-page crawling with `crawlUrl`, async crawl jobs with polling, and content processing pipelines.

## Prerequisites
- `@mendable/firecrawl-js` installed
- `FIRECRAWL_API_KEY` environment variable set
- Target URL(s) identified

## Instructions

### Step 1: Single-Page Scrape
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Scrape a single page to clean markdown
const result = await firecrawl.scrapeUrl("https://docs.example.com/api", {
  formats: ["markdown"],
  onlyMainContent: true,  // strips nav, footer, sidebars
  waitFor: 2000,           // wait 2s for JS to render
});

if (result.success) {
  console.log("Title:", result.metadata?.title);
  console.log("Source:", result.metadata?.sourceURL);
  console.log("Markdown:", result.markdown?.substring(0, 200));
}
```

### Step 2: Multi-Page Synchronous Crawl
```typescript
// Crawl a site — Firecrawl follows links, renders JS, returns all pages
const crawlResult = await firecrawl.crawlUrl("https://docs.example.com", {
  limit: 50,                   // max pages to crawl
  maxDepth: 3,                 // link depth from start URL
  includePaths: ["/docs/*", "/api/*"],   // only these paths
  excludePaths: ["/blog/*", "/changelog/*"],
  allowBackwardLinks: false,   // only crawl child paths
  scrapeOptions: {
    formats: ["markdown"],
    onlyMainContent: true,
  },
});

console.log(`Crawled ${crawlResult.data?.length} pages`);
for (const page of crawlResult.data || []) {
  console.log(`  ${page.metadata?.sourceURL}: ${page.markdown?.length} chars`);
}
```

### Step 3: Async Crawl for Large Sites
```typescript
// Start an async crawl job — returns immediately with job ID
const job = await firecrawl.asyncCrawlUrl("https://docs.example.com", {
  limit: 500,
  scrapeOptions: { formats: ["markdown"] },
});

console.log(`Crawl started: ${job.id}`);

// Poll for completion with backoff
let pollInterval = 2000;
let status = await firecrawl.checkCrawlStatus(job.id);

while (status.status === "scraping") {
  console.log(`Progress: ${status.completed}/${status.total} pages`);
  await new Promise(r => setTimeout(r, pollInterval));
  pollInterval = Math.min(pollInterval * 1.5, 30000);
  status = await firecrawl.checkCrawlStatus(job.id);
}

if (status.status === "completed") {
  console.log(`Done: ${status.data?.length} pages scraped`);
} else {
  console.error("Crawl failed:", status.error);
}
```

### Step 4: Process and Store Results
```typescript
import { writeFileSync, mkdirSync } from "fs";

function processResults(pages: any[], outputDir: string) {
  mkdirSync(outputDir, { recursive: true });

  const manifest = pages.map((page, i) => {
    const url = page.metadata?.sourceURL || `page-${i}`;
    const slug = new URL(url).pathname
      .replace(/\//g, "_")
      .replace(/^_|_$/g, "") || "index";
    const filename = `${slug}.md`;

    // Clean markdown: collapse whitespace, remove JS links
    const content = (page.markdown || "")
      .replace(/\n{3,}/g, "\n\n")
      .replace(/\[.*?\]\(javascript:.*?\)/g, "")
      .trim();

    writeFileSync(`${outputDir}/${filename}`, content);

    return { url, filename, chars: content.length };
  });

  writeFileSync(`${outputDir}/manifest.json`, JSON.stringify(manifest, null, 2));
  return manifest;
}
```

## Output
- Clean markdown files per crawled page
- `manifest.json` with URL-to-file mapping
- Crawl summary with page count and failures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty `markdown` | JS content not rendered | Increase `waitFor` to 5000ms |
| `429 Too Many Requests` | Rate limit hit | Back off, reduce concurrency |
| Crawl returns few pages | URL filters too strict | Widen `includePaths` patterns |
| `402 Payment Required` | Credits exhausted | Check balance, reduce `limit` |
| Partial crawl results | Site blocks bot on some pages | Use `scrapeUrl` for failed URLs individually |

## Examples

### Scrape with Multiple Formats
```typescript
const result = await firecrawl.scrapeUrl("https://example.com", {
  formats: ["markdown", "html", "links"],
  onlyMainContent: true,
});

console.log("Markdown:", result.markdown?.length);
console.log("HTML:", result.html?.length);
console.log("Links:", result.links?.length);
```

### Crawl with Webhook (No Polling)
```typescript
const job = await firecrawl.asyncCrawlUrl("https://docs.example.com", {
  limit: 100,
  scrapeOptions: { formats: ["markdown"] },
  webhook: {
    url: "https://api.yourapp.com/webhooks/firecrawl",
    events: ["completed", "page"],
  },
});
console.log(`Crawl ${job.id} started — webhook will fire on completion`);
```

## Resources
- [Scrape Endpoint](https://docs.firecrawl.dev/features/scrape)
- [Crawl Endpoint](https://docs.firecrawl.dev/features/crawl)
- [Advanced Scraping Guide](https://docs.firecrawl.dev/advanced-scraping-guide)

## Next Steps
For structured data extraction, see `firecrawl-core-workflow-b`.
