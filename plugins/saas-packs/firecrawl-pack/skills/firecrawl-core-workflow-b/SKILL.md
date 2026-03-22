---
name: firecrawl-core-workflow-b
description: |
  Execute Firecrawl secondary workflow: LLM extraction, batch scraping, and site mapping.
  Use when extracting structured data from pages, batch scraping known URLs,
  or discovering site structure with the map endpoint.
  Trigger with phrases like "firecrawl extract", "firecrawl batch scrape",
  "firecrawl map site", "firecrawl structured data", "firecrawl JSON extract".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, workflow]

---
# Firecrawl Core Workflow B — Extract, Batch & Map

## Overview
Secondary workflow complementing the scrape/crawl workflow. Covers LLM-powered structured data extraction with JSON schemas, batch scraping multiple known URLs, and rapid site map discovery. Use this when you need typed data rather than raw markdown.

## Prerequisites
- `@mendable/firecrawl-js` installed
- `FIRECRAWL_API_KEY` environment variable set
- Understanding of JSON Schema (for extract)

## Instructions

### Step 1: LLM Extract — Structured Data from Pages
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Extract structured data using an LLM + JSON schema
const result = await firecrawl.scrapeUrl("https://firecrawl.dev/pricing", {
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
              credits_per_month: { type: "number" },
              features: { type: "array", items: { type: "string" } },
            },
            required: ["name", "price"],
          },
        },
      },
    },
  },
});

console.log("Extracted plans:", JSON.stringify(result.extract, null, 2));
```

### Step 2: Extract with Prompt (No Schema)
```typescript
// Use natural language prompt instead of rigid schema
const result = await firecrawl.scrapeUrl("https://news.ycombinator.com", {
  formats: ["extract"],
  extract: {
    prompt: "Extract the top 5 stories with their title, URL, points, and comment count",
  },
});

console.log(result.extract);
```

### Step 3: Batch Scrape Known URLs
```typescript
// Scrape multiple specific URLs at once — more efficient than individual calls
const batchResult = await firecrawl.batchScrapeUrls(
  [
    "https://docs.firecrawl.dev/features/scrape",
    "https://docs.firecrawl.dev/features/crawl",
    "https://docs.firecrawl.dev/features/extract",
    "https://docs.firecrawl.dev/features/map",
  ],
  {
    formats: ["markdown"],
    onlyMainContent: true,
  }
);

for (const page of batchResult.data || []) {
  console.log(`${page.metadata?.title}: ${page.markdown?.length} chars`);
}
```

### Step 4: Async Batch Scrape (Large Sets)
```typescript
// Start async batch scrape for many URLs — returns job ID
const job = await firecrawl.asyncBatchScrapeUrls(
  urls,  // array of 100+ URLs
  { formats: ["markdown"] }
);

// Poll for completion
let status = await firecrawl.checkBatchScrapeStatus(job.id);
while (status.status !== "completed") {
  await new Promise(r => setTimeout(r, 5000));
  status = await firecrawl.checkBatchScrapeStatus(job.id);
}

console.log(`Batch complete: ${status.data?.length} pages`);
```

### Step 5: Map — Rapid URL Discovery
```typescript
// Discover all URLs on a site in ~2-3 seconds
// Uses sitemap.xml + SERP + cached crawl data
const mapResult = await firecrawl.mapUrl("https://docs.firecrawl.dev");

const urls = mapResult.links || [];
console.log(`Discovered ${urls.length} URLs`);

// Categorize by section
const sections = {
  docs: urls.filter(u => u.includes("/docs/")),
  api: urls.filter(u => u.includes("/api-reference/")),
  features: urls.filter(u => u.includes("/features/")),
  other: urls.filter(u => !u.includes("/docs/") && !u.includes("/api-reference/")),
};

Object.entries(sections).forEach(([name, list]) => {
  console.log(`  ${name}: ${list.length} URLs`);
});
```

### Step 6: Map + Selective Scrape Pipeline
```typescript
// 1. Map to discover URLs, 2. Filter, 3. Batch scrape relevant ones
async function intelligentScrape(siteUrl: string, pathFilter: string) {
  const map = await firecrawl.mapUrl(siteUrl);
  const relevant = (map.links || []).filter(url => url.includes(pathFilter));

  console.log(`Map found ${map.links?.length} URLs, ${relevant.length} match filter`);

  if (relevant.length === 0) return [];
  if (relevant.length <= 10) {
    return firecrawl.batchScrapeUrls(relevant, { formats: ["markdown"] });
  }

  // For large sets, use async batch
  const job = await firecrawl.asyncBatchScrapeUrls(relevant.slice(0, 100), {
    formats: ["markdown"],
  });
  // ...poll for completion
  return job;
}

await intelligentScrape("https://docs.firecrawl.dev", "/features/");
```

## Output
- Typed JSON objects extracted from web pages
- Batch scrape results for multiple URLs
- Complete site URL map for discovery
- Filtered scrape pipeline combining map + batch

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty `extract` | Page content too complex for LLM | Simplify schema, shorten prompt |
| Inconsistent extraction | Prompt too long | Keep prompts short and focused |
| Batch scrape timeout | Too many URLs | Use async batch with polling |
| Map returns few URLs | Site has no sitemap.xml | Use `crawlUrl` for thorough discovery |
| `402 Payment Required` | Credits exhausted | Reduce batch size, check balance |

## Examples

### Extract Products from E-Commerce
```typescript
const products = await firecrawl.scrapeUrl("https://store.example.com/products", {
  formats: ["extract"],
  extract: {
    schema: {
      type: "object",
      properties: {
        products: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              price: { type: "number" },
              availability: { type: "string" },
            },
            required: ["name", "price"],
          },
        },
      },
    },
  },
});
```

## Resources
- [Extract (JSON Mode)](https://docs.firecrawl.dev/features/llm-extract)
- [Batch Scrape](https://docs.firecrawl.dev/features/batch-scrape)
- [Map Endpoint](https://docs.firecrawl.dev/features/map)
- [Extract v2 Blog](https://www.firecrawl.dev/blog/launch-week-iii-day-3-extract-v2)

## Next Steps
For common errors, see `firecrawl-common-errors`.
