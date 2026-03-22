---
name: firecrawl-data-handling
description: |
  Process, validate, and store Firecrawl scraped content with deduplication and chunking.
  Use when handling scraped markdown, implementing content pipelines, building RAG knowledge
  bases, or processing crawl results for downstream consumption.
  Trigger with phrases like "firecrawl data", "firecrawl content processing",
  "firecrawl markdown cleaning", "firecrawl storage", "firecrawl RAG pipeline".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, compliance]

---
# Firecrawl Data Handling

## Overview
Process scraped web content from Firecrawl pipelines. Covers markdown cleaning, structured data extraction with Zod validation, content deduplication, chunking for LLM/RAG, and storage patterns for crawled content.

## Instructions

### Step 1: Content Cleaning
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Scrape with clean output settings
async function scrapeClean(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,   // strips nav, footer, sidebar
    excludeTags: ["script", "style", "nav", "footer", "iframe"],
    waitFor: 2000,
  });

  return {
    url: result.metadata?.sourceURL || url,
    title: result.metadata?.title || "",
    markdown: cleanMarkdown(result.markdown || ""),
    scrapedAt: new Date().toISOString(),
  };
}

function cleanMarkdown(md: string): string {
  return md
    .replace(/\n{3,}/g, "\n\n")                    // collapse multiple newlines
    .replace(/\[.*?\]\(javascript:.*?\)/g, "")      // remove JS links
    .replace(/!\[.*?\]\(data:.*?\)/g, "")           // remove inline data URIs
    .replace(/<!--[\s\S]*?-->/g, "")                // remove HTML comments
    .replace(/<script[\s\S]*?<\/script>/gi, "")     // remove script tags
    .trim();
}
```

### Step 2: Structured Extraction with Validation
```typescript
import { z } from "zod";

const ArticleSchema = z.object({
  title: z.string().min(1),
  author: z.string().optional(),
  publishedDate: z.string().optional(),
  content: z.string().min(50),
  wordCount: z.number(),
});

async function extractArticle(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ["extract"],
    extract: {
      schema: {
        type: "object",
        properties: {
          title: { type: "string" },
          author: { type: "string" },
          publishedDate: { type: "string" },
          content: { type: "string" },
        },
        required: ["title", "content"],
      },
    },
  });

  if (!result.extract) throw new Error(`Extraction failed for ${url}`);

  return ArticleSchema.parse({
    ...result.extract,
    wordCount: (result.extract.content || "").split(/\s+/).length,
  });
}
```

### Step 3: Content Deduplication
```typescript
import { createHash } from "crypto";

function contentHash(text: string): string {
  return createHash("sha256")
    .update(text.trim().toLowerCase())
    .digest("hex");
}

function deduplicatePages(pages: Array<{ url: string; markdown: string }>) {
  const seen = new Map<string, string>(); // hash -> first URL
  const unique: typeof pages = [];
  const duplicates: Array<{ url: string; duplicateOf: string }> = [];

  for (const page of pages) {
    const hash = contentHash(page.markdown);
    if (seen.has(hash)) {
      duplicates.push({ url: page.url, duplicateOf: seen.get(hash)! });
    } else {
      seen.set(hash, page.url);
      unique.push(page);
    }
  }

  console.log(`Dedup: ${pages.length} input, ${unique.length} unique, ${duplicates.length} duplicates`);
  return { unique, duplicates };
}
```

### Step 4: Chunk for LLM / RAG
```typescript
interface ContentChunk {
  url: string;
  title: string;
  chunkIndex: number;
  content: string;
  wordCount: number;
}

function chunkForRAG(
  url: string,
  title: string,
  markdown: string,
  maxWords = 800
): ContentChunk[] {
  // Split by headings to preserve semantic boundaries
  const sections = markdown.split(/\n(?=#{1,3}\s)/);
  const chunks: ContentChunk[] = [];
  let current = "";
  let index = 0;

  for (const section of sections) {
    const combined = current ? `${current}\n\n${section}` : section;
    if (combined.split(/\s+/).length > maxWords && current) {
      chunks.push({
        url, title, chunkIndex: index++,
        content: current.trim(),
        wordCount: current.split(/\s+/).length,
      });
      current = section;
    } else {
      current = combined;
    }
  }

  if (current.trim()) {
    chunks.push({
      url, title, chunkIndex: index,
      content: current.trim(),
      wordCount: current.split(/\s+/).length,
    });
  }

  return chunks;
}
```

### Step 5: Crawl and Store Pipeline
```typescript
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

async function crawlAndStore(baseUrl: string, outputDir: string, opts?: {
  maxPages?: number;
  paths?: string[];
}) {
  mkdirSync(outputDir, { recursive: true });

  const crawlResult = await firecrawl.crawlUrl(baseUrl, {
    limit: opts?.maxPages || 50,
    includePaths: opts?.paths,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });

  const pages = (crawlResult.data || []).map(page => ({
    url: page.metadata?.sourceURL || baseUrl,
    markdown: cleanMarkdown(page.markdown || ""),
  }));

  // Deduplicate
  const { unique } = deduplicatePages(pages);

  // Write files + manifest
  const manifest = unique.map(page => {
    const slug = new URL(page.url).pathname
      .replace(/\//g, "_").replace(/^_|_$/g, "") || "index";
    const filename = `${slug}.md`;
    writeFileSync(join(outputDir, filename), page.markdown);
    return { url: page.url, file: filename, size: page.markdown.length };
  });

  writeFileSync(join(outputDir, "manifest.json"), JSON.stringify(manifest, null, 2));
  return manifest;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty content | JS not rendered | Increase `waitFor`, use `onlyMainContent` |
| Garbage in markdown | Bad HTML cleanup | Add `excludeTags` for problematic elements |
| Duplicate pages | URL aliases or redirects | Content-hash deduplication |
| Oversized chunks | Long single sections | Add word limit to chunking logic |
| Extract returns null | Page too complex for LLM | Simplify schema, use shorter prompt |

## Examples

### Documentation Scraper with RAG Output
```typescript
const docs = await crawlAndStore("https://docs.example.com", "./scraped-docs", {
  maxPages: 50,
  paths: ["/docs/*", "/api/*"],
});

// Generate RAG-ready chunks
for (const doc of docs) {
  const content = readFileSync(`./scraped-docs/${doc.file}`, "utf-8");
  const chunks = chunkForRAG(doc.url, doc.file, content);
  console.log(`${doc.url}: ${chunks.length} chunks`);
  // Feed chunks to vector store (Pinecone, Weaviate, pgvector, etc.)
}
```

## Resources
- [Firecrawl Scrape Options](https://docs.firecrawl.dev/features/scrape)
- [Firecrawl Extract](https://docs.firecrawl.dev/features/llm-extract)
- [Zod Validation](https://zod.dev/)

## Next Steps
For access control, see `firecrawl-enterprise-rbac`.
