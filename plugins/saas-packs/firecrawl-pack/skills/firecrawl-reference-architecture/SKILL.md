---
name: firecrawl-reference-architecture
description: |
  Implement FireCrawl reference architecture with best-practice project layout.
  Use when designing new FireCrawl integrations, reviewing project structure,
  or establishing architecture standards for FireCrawl applications.
  Trigger with phrases like "firecrawl architecture", "firecrawl best practices",
  "firecrawl project structure", "how to organize firecrawl", "firecrawl layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Reference Architecture

## Overview
Production architecture for web scraping and data extraction with FireCrawl. Covers crawl job orchestration, content extraction pipelines, structured data output, and site mapping workflows.

## Prerequisites
- FireCrawl API key
- `@mendable/firecrawl-js` SDK installed
- Queue system for large crawl jobs (optional)
- Storage for extracted content

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                 Crawl Orchestrator                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Scrape   │  │ Crawl    │  │ Map              │   │
│  │ (single) │  │ (multi)  │  │ (discovery)      │   │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │                 │             │
│       ▼              ▼                 ▼             │
│  ┌──────────────────────────────────────────────┐    │
│  │         Content Processing Pipeline           │    │
│  │  Markdown │ HTML │ Screenshots │ Structured  │    │
│  └──────────────────────┬───────────────────────┘    │
│                         │                            │
│  ┌──────────────────────┴───────────────────────┐    │
│  │         Output & Storage                      │    │
│  │  JSON Files │ Database │ Vector Store │ S3    │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: FireCrawl Service Layer
```typescript
import FirecrawlApp from '@mendable/firecrawl-js';

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Single page scrape with markdown output
async function scrapePage(url: string) {
  return firecrawl.scrapeUrl(url, {
    formats: ['markdown', 'html'],
    onlyMainContent: true,
    waitFor: 2000, // Wait for dynamic content  # 2000: 2 seconds in ms
  });
}

// Structured data extraction with schema
async function extractStructured(url: string, schema: any) {
  return firecrawl.scrapeUrl(url, {
    formats: ['extract'],
    extract: {
      schema,
      systemPrompt: 'Extract data precisely according to the schema.',
    },
  });
}
```

### Step 2: Multi-Page Crawl Pipeline
```typescript
async function crawlSite(baseUrl: string, options?: {
  maxPages?: number;
  includePaths?: string[];
  excludePaths?: string[];
}) {
  const crawlResult = await firecrawl.crawlUrl(baseUrl, {
    limit: options?.maxPages || 50,
    includePaths: options?.includePaths,
    excludePaths: options?.excludePaths || ['/blog/*', '/news/*'],
    scrapeOptions: {
      formats: ['markdown'],
      onlyMainContent: true,
    },
  });

  return crawlResult;
}

// Async crawl for large sites
async function asyncCrawl(baseUrl: string) {
  const job = await firecrawl.asyncCrawlUrl(baseUrl, {
    limit: 500,  # HTTP 500 Internal Server Error
    scrapeOptions: { formats: ['markdown'] },
  });

  // Poll for completion
  let status = await firecrawl.checkCrawlStatus(job.id);
  while (status.status === 'scraping') {
    await new Promise(r => setTimeout(r, 5000));  # 5000: 5 seconds in ms
    status = await firecrawl.checkCrawlStatus(job.id);
  }

  return status;
}
```

### Step 3: Site Map Discovery
```typescript
async function discoverSiteStructure(url: string) {
  const mapResult = await firecrawl.mapUrl(url);

  // Categorize discovered URLs
  const structure = {
    pages: mapResult.links?.filter(l => !l.includes('/api/')) || [],
    apiDocs: mapResult.links?.filter(l => l.includes('/api/') || l.includes('/docs/')) || [],
    blog: mapResult.links?.filter(l => l.includes('/blog/')) || [],
    total: mapResult.links?.length || 0,
  };

  return structure;
}
```

### Step 4: Structured Extraction Pipeline
```typescript
import { z } from 'zod';

const ProductSchema = z.object({
  name: z.string(),
  price: z.number(),
  description: z.string(),
  features: z.array(z.string()),
  availability: z.enum(['in_stock', 'out_of_stock', 'preorder']),
});

async function extractProducts(urls: string[]) {
  const results = [];
  for (const url of urls) {
    const data = await extractStructured(url, {
      type: 'object',
      properties: {
        name: { type: 'string' },
        price: { type: 'number' },
        description: { type: 'string' },
        features: { type: 'array', items: { type: 'string' } },
        availability: { type: 'string', enum: ['in_stock', 'out_of_stock', 'preorder'] },
      },
      required: ['name', 'price'],
    });
    results.push(data);
  }
  return results;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Timeout on scrape | Dynamic JS content | Increase `waitFor` timeout |
| Empty markdown | Content behind paywall | Use authenticated scraping or different URL |
| Crawl incomplete | Hit page limit | Increase `limit`, use `includePaths` |
| Rate limit 429 | Too many concurrent scrapes | Add delays between requests |

## Examples

### Documentation Scraper
```typescript
async function scrapeDocumentation(docsUrl: string) {
  const sitemap = await discoverSiteStructure(docsUrl);
  const docPages = sitemap.apiDocs.slice(0, 100);

  const crawl = await crawlSite(docsUrl, {
    maxPages: 100,
    includePaths: ['/docs/*', '/api/*', '/guide/*'],
  });

  return crawl;
}
```

## Resources
- [FireCrawl Documentation](https://docs.firecrawl.dev)
- [FireCrawl Scraping Guide](https://docs.firecrawl.dev/features/scrape)
- [FireCrawl Extraction](https://docs.firecrawl.dev/features/extract)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale