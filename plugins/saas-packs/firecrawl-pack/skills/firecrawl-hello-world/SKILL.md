---
name: firecrawl-hello-world
description: |
  Create a minimal working Firecrawl example that scrapes a page to markdown.
  Use when starting a new Firecrawl integration, testing your setup,
  or learning the scrape/crawl/map/extract API surface.
  Trigger with phrases like "firecrawl hello world", "firecrawl example",
  "firecrawl quick start", "simple firecrawl code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, testing]

---
# Firecrawl Hello World

## Overview
Four minimal examples covering Firecrawl's core endpoints: **scrape** (single page), **crawl** (multi-page), **map** (URL discovery), and **extract** (LLM structured data). Each is a standalone snippet you can run immediately.

## Prerequisites
- `@mendable/firecrawl-js` installed (`npm install @mendable/firecrawl-js`)
- `FIRECRAWL_API_KEY` environment variable set

## Instructions

### Step 1: Single-Page Scrape
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Scrape one page — returns markdown, HTML, metadata, links
const result = await firecrawl.scrapeUrl("https://docs.firecrawl.dev", {
  formats: ["markdown"],
});

console.log("Title:", result.metadata?.title);
console.log("Markdown:", result.markdown?.substring(0, 500));
```

### Step 2: Multi-Page Crawl
```typescript
// Crawl a site recursively — follows links, respects robots.txt
const crawlResult = await firecrawl.crawlUrl("https://docs.firecrawl.dev", {
  limit: 10,  // max 10 pages (saves credits)
  scrapeOptions: {
    formats: ["markdown"],
  },
});

console.log(`Crawled ${crawlResult.data?.length} pages`);
for (const page of crawlResult.data || []) {
  console.log(`  ${page.metadata?.title} — ${page.metadata?.sourceURL}`);
}
```

### Step 3: Map a Site (URL Discovery)
```typescript
// Discover all URLs on a site in ~2-3 seconds (uses sitemap + SERP)
const mapResult = await firecrawl.mapUrl("https://docs.firecrawl.dev");

console.log(`Found ${mapResult.links?.length} URLs`);
mapResult.links?.slice(0, 10).forEach(url => console.log(`  ${url}`));
```

### Step 4: LLM Extract (Structured Data)
```typescript
// Extract structured data from a page using an LLM + JSON schema
const extracted = await firecrawl.scrapeUrl("https://firecrawl.dev/pricing", {
  formats: ["extract"],
  extract: {
    schema: {
      type: "object",
      properties: {
        plans: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              price: { type: "string" },
              credits: { type: "number" },
            },
          },
        },
      },
    },
  },
});

console.log("Pricing plans:", JSON.stringify(extracted.extract, null, 2));
```

## Output
- Single-page markdown scraped from a live URL
- Multi-page crawl results with titles and source URLs
- Site map with all discovered URLs
- Structured JSON extracted by LLM from page content

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module` | SDK not installed | `npm install @mendable/firecrawl-js` |
| `401 Unauthorized` | Missing or invalid API key | Check `FIRECRAWL_API_KEY` env var |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry with backoff |
| Empty `markdown` | JS-heavy page not rendered | Add `waitFor: 5000` to scrape options |
| `402 Payment Required` | Credits exhausted | Check balance at firecrawl.dev/app |

## Examples

### Python Hello World
```python
from firecrawl import FirecrawlApp

firecrawl = FirecrawlApp(api_key="fc-YOUR_API_KEY")

# Scrape
result = firecrawl.scrape_url("https://example.com", params={
    "formats": ["markdown"]
})
print(result["markdown"][:500])

# Map
urls = firecrawl.map_url("https://example.com")
print(f"Found {len(urls.get('links', []))} URLs")
```

### Batch Scrape Multiple URLs
```typescript
// Scrape many URLs at once — more efficient than individual scrapes
const batchResult = await firecrawl.batchScrapeUrls(
  [
    "https://docs.firecrawl.dev/features/scrape",
    "https://docs.firecrawl.dev/features/crawl",
    "https://docs.firecrawl.dev/features/extract",
  ],
  { formats: ["markdown"] }
);

for (const page of batchResult.data || []) {
  console.log(`${page.metadata?.title}: ${page.markdown?.length} chars`);
}
```

## Resources
- [Firecrawl Quickstart](https://docs.firecrawl.dev/introduction)
- [Scrape Endpoint](https://docs.firecrawl.dev/features/scrape)
- [Crawl Endpoint](https://docs.firecrawl.dev/features/crawl)
- [Map Endpoint](https://docs.firecrawl.dev/features/map)
- [Extract (JSON Mode)](https://docs.firecrawl.dev/features/llm-extract)

## Next Steps
Proceed to `firecrawl-local-dev-loop` for development workflow setup.
