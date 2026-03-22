---
name: exa-data-handling
description: |
  Implement Exa search result processing, content extraction, caching, and RAG context management.
  Use when handling search results, implementing caching, building citation pipelines,
  or managing content payloads for LLM context windows.
  Trigger with phrases like "exa data", "exa results processing",
  "exa cache", "exa RAG context", "exa content extraction".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, data, rag, caching]

---
# Exa Data Handling

## Overview
Manage search result data from Exa's neural search API. Covers content extraction scope control (text vs highlights vs summary), result caching with TTL, citation deduplication, token budget management for LLM context windows, and structured summary extraction.

## Prerequisites
- `exa-js` SDK installed and configured
- Optional: `lru-cache` for in-memory caching, `ioredis` for Redis
- Understanding of Exa content options (text, highlights, summary)

## Instructions

### Step 1: Control Content Extraction Scope
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Tier 1: Metadata only (cheapest, fastest)
async function searchMetadataOnly(query: string) {
  return exa.search(query, {
    type: "auto",
    numResults: 10,
    // No content options — returns URLs, titles, scores only
  });
}

// Tier 2: Highlights only (balanced cost/value)
async function searchWithHighlights(query: string) {
  return exa.searchAndContents(query, {
    numResults: 10,
    highlights: {
      maxCharacters: 500,
      query: query,  // focus highlights on the original query
    },
  });
}

// Tier 3: Full text with character limit
async function searchWithText(query: string, maxChars = 2000) {
  return exa.searchAndContents(query, {
    numResults: 5,
    text: { maxCharacters: maxChars },
    highlights: { maxCharacters: 300 },
  });
}

// Tier 4: Structured summary (LLM-generated per result)
async function searchWithSummary(query: string) {
  return exa.searchAndContents(query, {
    numResults: 5,
    summary: { query: query },
    // summary returns a concise LLM-generated summary per result
  });
}
```

### Step 2: Result Caching with TTL
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const searchCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 60, // 1 hour default
});

function cacheKey(query: string, options: any): string {
  return createHash("sha256")
    .update(JSON.stringify({ query, ...options }))
    .digest("hex");
}

async function cachedSearch(query: string, options: any = {}, ttlMs?: number) {
  const key = cacheKey(query, options);
  const cached = searchCache.get(key);
  if (cached) return cached;

  const results = await exa.searchAndContents(query, options);
  searchCache.set(key, results, { ttl: ttlMs });
  return results;
}
```

### Step 3: Token Budget Management for RAG
```typescript
interface ProcessedResult {
  url: string;
  title: string;
  score: number;
  snippet: string;
  tokenEstimate: number;
}

function processForRAG(results: any[], maxSnippetLength = 500): ProcessedResult[] {
  return results.map(r => {
    const snippet = (r.text || r.highlights?.join(" ") || r.summary || "")
      .slice(0, maxSnippetLength);
    return {
      url: r.url,
      title: r.title || "Untitled",
      score: r.score,
      snippet,
      tokenEstimate: Math.ceil(snippet.length / 4),
    };
  });
}

function fitToTokenBudget(results: ProcessedResult[], maxTokens: number) {
  const sorted = [...results].sort((a, b) => b.score - a.score);
  const selected: ProcessedResult[] = [];
  let tokenCount = 0;

  for (const result of sorted) {
    if (tokenCount + result.tokenEstimate > maxTokens) break;
    selected.push(result);
    tokenCount += result.tokenEstimate;
  }

  return { selected, tokenCount, dropped: sorted.length - selected.length };
}

// Usage: fit search results into a 4K token context window
const results = await exa.searchAndContents("query", {
  numResults: 15,
  text: { maxCharacters: 1500 },
});
const processed = processForRAG(results.results);
const { selected, tokenCount } = fitToTokenBudget(processed, 4000);
```

### Step 4: Citation Deduplication
```typescript
function deduplicateResults(results: any[]): any[] {
  const seen = new Map<string, any>();

  for (const result of results) {
    const domain = new URL(result.url).hostname;
    const key = `${domain}:${result.title}`;
    if (!seen.has(key) || result.score > seen.get(key).score) {
      seen.set(key, result);
    }
  }

  return Array.from(seen.values());
}
```

### Step 5: Structured Summary Extraction
```typescript
// Use summary.schema for structured data extraction
const results = await exa.searchAndContents(
  "YC-backed AI startups Series A 2025",
  {
    numResults: 10,
    category: "company",
    summary: {
      query: "company name, funding amount, what they do",
      // schema can define JSON structure for the summary output
    },
  }
);

// Each result.summary contains a structured summary
for (const r of results.results) {
  console.log(`${r.title}: ${r.summary}`);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Large response payload | Full text for many URLs | Use highlights or limit `maxCharacters` |
| Cache stale for news | Default TTL too long | Use 5-minute TTL for time-sensitive queries |
| Duplicate sources | Same article syndicated | Deduplicate by domain + title |
| Token budget exceeded | Too much context for LLM | Use `fitToTokenBudget` to trim by score |
| Missing `.text` field | Content not requested | Use `searchAndContents` not `search` |

## Examples

### RAG-Optimized Search Pipeline
```typescript
async function ragSearch(query: string, tokenBudget = 4000) {
  const results = await cachedSearch(query, {
    numResults: 15,
    type: "neural",
    text: { maxCharacters: 1500 },
    highlights: { maxCharacters: 300, query },
  });

  const deduped = deduplicateResults(results.results);
  const processed = processForRAG(deduped);
  const { selected, tokenCount } = fitToTokenBudget(processed, tokenBudget);

  return {
    context: selected.map((r, i) =>
      `[${i + 1}] ${r.title} (${r.url})\n${r.snippet}`
    ).join("\n\n---\n\n"),
    sources: selected.map(r => ({ title: r.title, url: r.url })),
    tokenCount,
  };
}
```

## Resources
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)
- [Exa Search Reference](https://docs.exa.ai/reference/search)

## Next Steps
For rate limit handling, see `exa-rate-limits`. For cost optimization, see `exa-cost-tuning`.
