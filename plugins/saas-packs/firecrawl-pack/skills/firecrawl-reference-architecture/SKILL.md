---
name: firecrawl-reference-architecture
description: |
  Implement Firecrawl reference architecture with scrape/crawl/map/extract pipelines.
  Use when designing new Firecrawl integrations, reviewing project structure,
  or building content ingestion pipelines for AI/RAG applications.
  Trigger with phrases like "firecrawl architecture", "firecrawl project structure",
  "firecrawl pipeline", "firecrawl RAG", "firecrawl knowledge base".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, firecrawl-reference]

---
# Firecrawl Reference Architecture

## Overview
Production architecture for web scraping and content ingestion with Firecrawl. Covers three tiers: on-demand scraping, scheduled crawl pipelines, and real-time RAG ingestion. Uses all four Firecrawl endpoints: scrape, crawl, map, and extract.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Firecrawl Pipeline                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌───────────┐   │
│  │ scrapeUrl│  │ crawlUrl │  │mapUrl│  │ extract   │   │
│  │ (1 page) │  │ (N pages)│  │(URLs)│  │ (LLM+JSON)│   │
│  └────┬─────┘  └────┬─────┘  └──┬───┘  └─────┬─────┘   │
│       │              │            │            │          │
│       ▼              ▼            ▼            ▼          │
│  ┌───────────────────────────────────────────────────┐   │
│  │            Content Processing Layer                │   │
│  │  Clean MD │ Validate │ Deduplicate │ Chunk        │   │
│  └─────────────────────┬─────────────────────────────┘   │
│                         │                                 │
│  ┌─────────────────────┴─────────────────────────────┐   │
│  │              Storage & Output                      │   │
│  │  Files │ Database │ Vector Store │ Search Index    │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Firecrawl Service Layer
```typescript
// src/firecrawl/service.ts
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Single page scrape
export async function scrapePage(url: string) {
  return firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
    waitFor: 2000,
  });
}

// Site-wide crawl with safety limits
export async function crawlSite(baseUrl: string, opts?: {
  maxPages?: number;
  paths?: string[];
  excludePaths?: string[];
}) {
  return firecrawl.crawlUrl(baseUrl, {
    limit: opts?.maxPages || 50,
    maxDepth: 3,
    includePaths: opts?.paths,
    excludePaths: opts?.excludePaths || ["/blog/*", "/news/*"],
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });
}

// Fast URL discovery
export async function discoverUrls(baseUrl: string) {
  const map = await firecrawl.mapUrl(baseUrl);
  return map.links || [];
}

// Structured data extraction
export async function extractData(url: string, schema: object) {
  return firecrawl.scrapeUrl(url, {
    formats: ["extract"],
    extract: { schema },
  });
}
```

### Step 2: Content Processing Pipeline
```typescript
// src/pipeline/processor.ts
import { createHash } from "crypto";

interface ProcessedPage {
  url: string;
  title: string;
  markdown: string;
  contentHash: string;
  wordCount: number;
  chunks: string[];
}

export function processPage(page: any): ProcessedPage | null {
  const markdown = cleanMarkdown(page.markdown || "");
  if (markdown.length < 100) return null; // skip thin content

  return {
    url: page.metadata?.sourceURL || "",
    title: page.metadata?.title || "",
    markdown,
    contentHash: createHash("sha256").update(markdown).digest("hex"),
    wordCount: markdown.split(/\s+/).length,
    chunks: chunkMarkdown(markdown, 1000),
  };
}

function cleanMarkdown(md: string): string {
  return md
    .replace(/\n{3,}/g, "\n\n")
    .replace(/\[.*?\]\(javascript:.*?\)/g, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .trim();
}

function chunkMarkdown(md: string, maxWords: number): string[] {
  const sections = md.split(/\n##\s/);
  const chunks: string[] = [];
  let current = "";

  for (const section of sections) {
    if (current.split(/\s+/).length + section.split(/\s+/).length > maxWords) {
      if (current) chunks.push(current.trim());
      current = section;
    } else {
      current += "\n## " + section;
    }
  }
  if (current) chunks.push(current.trim());
  return chunks;
}
```

### Step 3: Map + Selective Scrape Pipeline
```typescript
// src/pipeline/intelligent-scrape.ts
export async function intelligentScrape(siteUrl: string, opts: {
  pathFilter: string;
  maxPages: number;
}) {
  // 1. Map site structure (1 credit)
  const allUrls = await discoverUrls(siteUrl);
  const relevant = allUrls.filter(url => url.includes(opts.pathFilter));

  console.log(`Map: ${allUrls.length} total, ${relevant.length} match "${opts.pathFilter}"`);

  // 2. Batch scrape relevant URLs (N credits)
  const targets = relevant.slice(0, opts.maxPages);
  const result = await firecrawl.batchScrapeUrls(targets, {
    formats: ["markdown"],
    onlyMainContent: true,
  });

  // 3. Process and deduplicate
  const seen = new Set<string>();
  const processed = (result.data || [])
    .map(processPage)
    .filter((p): p is ProcessedPage => {
      if (!p || seen.has(p.contentHash)) return false;
      seen.add(p.contentHash);
      return true;
    });

  return { total: allUrls.length, scraped: targets.length, processed: processed.length, pages: processed };
}
```

### Step 4: Async Crawl with Storage
```typescript
// src/pipeline/crawl-pipeline.ts
import { writeFileSync, mkdirSync } from "fs";

export async function crawlAndStore(baseUrl: string, outputDir: string) {
  mkdirSync(outputDir, { recursive: true });

  const crawl = await firecrawl.crawlUrl(baseUrl, {
    limit: 100,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });

  const manifest = (crawl.data || [])
    .map(processPage)
    .filter((p): p is ProcessedPage => p !== null)
    .map(page => {
      const slug = new URL(page.url).pathname
        .replace(/\//g, "_").replace(/^_|_$/g, "") || "index";
      writeFileSync(`${outputDir}/${slug}.md`, page.markdown);
      return { url: page.url, file: `${slug}.md`, words: page.wordCount, chunks: page.chunks.length };
    });

  writeFileSync(`${outputDir}/manifest.json`, JSON.stringify(manifest, null, 2));
  return manifest;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Timeout on scrape | JS-heavy page | Increase `waitFor` or use `actions` |
| Empty markdown | Content behind paywall | Try different URL or authenticated scrape |
| Crawl incomplete | Hit page limit | Increase `limit` or use `includePaths` |
| Duplicate content | URL aliases or redirects | Hash content for deduplication |
| Map returns few URLs | Site has no sitemap | Use `crawlUrl` for thorough discovery |

## Examples

### Documentation Scraper
```typescript
const docs = await intelligentScrape("https://docs.firecrawl.dev", {
  pathFilter: "/features/",
  maxPages: 20,
});
console.log(`Scraped ${docs.processed} unique pages from ${docs.total} discovered`);
```

### RAG Knowledge Base Builder
```typescript
const pages = await crawlAndStore("https://docs.example.com", "./knowledge-base");
// Feed chunks to vector store for RAG
for (const page of pages) {
  // Each page has pre-chunked content ready for embedding
}
```

## Resources
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)
- [Scrape Endpoint](https://docs.firecrawl.dev/features/scrape)
- [Crawl Endpoint](https://docs.firecrawl.dev/features/crawl)
- [Map Endpoint](https://docs.firecrawl.dev/features/map)

## Next Steps
For multi-environment setup, see `firecrawl-multi-env-setup`.
