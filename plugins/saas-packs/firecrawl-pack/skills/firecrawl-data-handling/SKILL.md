---
name: firecrawl-data-handling
description: |
  Implement FireCrawl PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for FireCrawl integrations.
  Trigger with phrases like "firecrawl data", "firecrawl PII",
  "firecrawl GDPR", "firecrawl data retention", "firecrawl privacy", "firecrawl CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# FireCrawl Data Handling

## Overview
Manage scraped web content from FireCrawl pipelines. Covers content extraction filtering, HTML sanitization, markdown cleaning, structured data validation, and storage patterns for crawled content.

## Prerequisites
- FireCrawl API key
- `@mendable/firecrawl-js` SDK
- Storage system for crawled content
- Understanding of web scraping data formats

## Instructions

### Step 1: Content Format Selection and Cleaning
```typescript
import FirecrawlApp from '@mendable/firecrawl-js';

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Scrape with controlled output formats
async function scrapeClean(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ['markdown'],       // Markdown is cleanest for LLMs
    onlyMainContent: true,       // Strip nav, footer, sidebar
    excludeTags: ['script', 'style', 'nav', 'footer', 'iframe'],
    waitFor: 2000,
  });

  return {
    markdown: cleanMarkdown(result.markdown || ''),
    metadata: result.metadata,
    url,
    scrapedAt: new Date().toISOString(),
  };
}

function cleanMarkdown(md: string): string {
  return md
    .replace(/\n{3,}/g, '\n\n')        // Collapse multiple newlines
    .replace(/\[.*?\]\(javascript:.*?\)/g, '') // Remove JS links
    .replace(/!\[.*?\]\(data:.*?\)/g, '') // Remove inline data URIs
    .replace(/<!--[\s\S]*?-->/g, '')    // Remove HTML comments
    .trim();
}
```

### Step 2: Structured Data Extraction and Validation
```typescript
import { z } from 'zod';

const ArticleSchema = z.object({
  title: z.string().min(1),
  author: z.string().optional(),
  publishedDate: z.string().optional(),
  content: z.string().min(50),
  wordCount: z.number(),
});

async function extractArticle(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ['extract'],
    extract: {
      schema: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          author: { type: 'string' },
          publishedDate: { type: 'string' },
          content: { type: 'string' },
        },
        required: ['title', 'content'],
      },
    },
  });

  const extracted = result.extract;
  if (!extracted) throw new Error('Extraction failed');

  return ArticleSchema.parse({
    ...extracted,
    wordCount: extracted.content?.split(/\s+/).length || 0,
  });
}
```

### Step 3: Batch Crawl with Storage Pipeline
```typescript
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

async function crawlAndStore(
  baseUrl: string,
  outputDir: string,
  options?: { maxPages?: number; includePaths?: string[] }
) {
  mkdirSync(outputDir, { recursive: true });

  const crawlResult = await firecrawl.crawlUrl(baseUrl, {
    limit: options?.maxPages || 50,
    includePaths: options?.includePaths,
    scrapeOptions: {
      formats: ['markdown'],
      onlyMainContent: true,
    },
  });

  const manifest: Array<{ url: string; path: string; size: number }> = [];

  for (const page of crawlResult.data || []) {
    const slug = new URL(page.metadata?.sourceURL || baseUrl)
      .pathname.replace(/\//g, '_').replace(/^_|_$/g, '') || 'index';
    const filename = `${slug}.md`;
    const filePath = join(outputDir, filename);

    const content = cleanMarkdown(page.markdown || '');
    writeFileSync(filePath, content);

    manifest.push({
      url: page.metadata?.sourceURL || baseUrl,
      path: filename,
      size: content.length,
    });
  }

  writeFileSync(join(outputDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  return manifest;
}
```

### Step 4: Content Deduplication
```typescript
import { createHash } from 'crypto';

function contentHash(text: string): string {
  return createHash('sha256').update(text.trim().toLowerCase()).digest('hex');
}

function deduplicatePages(pages: Array<{ url: string; content: string }>) {
  const seen = new Map<string, string>(); // hash -> url
  const unique: typeof pages = [];
  const duplicates: Array<{ url: string; duplicateOf: string }> = [];

  for (const page of pages) {
    const hash = contentHash(page.content);
    if (seen.has(hash)) {
      duplicates.push({ url: page.url, duplicateOf: seen.get(hash)! });
    } else {
      seen.set(hash, page.url);
      unique.push(page);
    }
  }

  return { unique, duplicates };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty content | Dynamic JS not loaded | Increase `waitFor` timeout |
| Garbage in markdown | Bad HTML cleanup | Use `onlyMainContent` and `excludeTags` |
| Duplicate pages | URL aliases or redirects | Hash content for deduplication |
| Large file sizes | Full HTML stored | Use markdown format only |

## Examples

### Documentation Scraper
```typescript
const docs = await crawlAndStore('https://docs.example.com', './scraped-docs', {
  maxPages: 100,
  includePaths: ['/docs/*', '/api/*'],
});
console.log(`Scraped ${docs.length} pages`);
```

## Resources
- [FireCrawl Documentation](https://docs.firecrawl.dev)
- [FireCrawl Scrape Options](https://docs.firecrawl.dev/features/scrape)
