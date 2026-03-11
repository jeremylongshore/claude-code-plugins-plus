---
name: exa-data-handling
description: |
  Implement Exa PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Exa integrations.
  Trigger with phrases like "exa data", "exa PII",
  "exa GDPR", "exa data retention", "exa privacy", "exa CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Data Handling

## Overview
Manage search result data from Exa neural search APIs. Covers content extraction filtering, result caching with TTL, citation deduplication, and handling large content payloads efficiently for RAG pipelines.

## Prerequisites
- Exa API key
- `exa-js` SDK installed
- Storage layer for cached results
- Understanding of content extraction options

## Instructions

### Step 1: Control Content Extraction Scope
```typescript
import Exa from 'exa-js';

const exa = new Exa(process.env.EXA_API_KEY!);

// Minimal extraction: metadata only (cheapest)
async function searchMetadataOnly(query: string) {
  return exa.search(query, {
    numResults: 10,
    type: 'auto',
    // No contents - just URLs, titles, scores
  });
}

// Controlled extraction: highlights only (balanced)
async function searchWithHighlights(query: string) {
  return exa.searchAndContents(query, {
    numResults: 10,
    highlights: { numSentences: 3, highlightsPerUrl: 2 },
    // No full text - reduces payload significantly
  });
}

// Full extraction: text with character limit
async function searchWithText(query: string, maxChars = 2000) {
  return exa.searchAndContents(query, {
    numResults: 5,
    text: { maxCharacters: maxChars },
    highlights: { numSentences: 3 },
  });
}
```

### Step 2: Result Caching with TTL
```typescript
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';

const searchCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 60, // 1 hour default
});

function cacheKey(query: string, options: any): string {
  return createHash('sha256')
    .update(JSON.stringify({ query, ...options }))
    .digest('hex');
}

async function cachedSearch(
  query: string,
  options: any = {},
  ttlMs?: number
) {
  const key = cacheKey(query, options);
  const cached = searchCache.get(key);
  if (cached) return cached;

  const results = await exa.searchAndContents(query, options);
  searchCache.set(key, results, { ttl: ttlMs });
  return results;
}
```

### Step 3: Content Size Management
```typescript
interface ProcessedResult {
  url: string;
  title: string;
  score: number;
  snippet: string;  // Truncated content
  contentSize: number;
}

function processResults(results: any[], maxSnippetLength = 500): ProcessedResult[] {
  return results.map(r => ({
    url: r.url,
    title: r.title || 'Untitled',
    score: r.score,
    snippet: (r.text || r.highlights?.join(' ') || '').slice(0, maxSnippetLength),
    contentSize: (r.text || '').length,
  }));
}

// Estimate token count for LLM context budgets
function estimateTokens(results: ProcessedResult[]): number {
  const totalChars = results.reduce((sum, r) => sum + r.snippet.length, 0);
  return Math.ceil(totalChars / 4); // Rough estimate: 4 chars per token
}

function fitToTokenBudget(results: ProcessedResult[], maxTokens: number) {
  const sorted = results.sort((a, b) => b.score - a.score);
  const selected: ProcessedResult[] = [];
  let tokenCount = 0;

  for (const result of sorted) {
    const resultTokens = Math.ceil(result.snippet.length / 4);
    if (tokenCount + resultTokens > maxTokens) break;
    selected.push(result);
    tokenCount += resultTokens;
  }

  return { selected, tokenCount };
}
```

### Step 4: Citation Deduplication
```typescript
function deduplicateCitations(results: any[]): any[] {
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

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Large response payload | Requesting full text for many URLs | Use highlights or limit `maxCharacters` |
| Cache stale for news | Default TTL too long | Use shorter TTL for time-sensitive queries |
| Duplicate sources | Same article from multiple domains | Deduplicate by domain + title |
| Token budget exceeded | Too much context for LLM | Use `fitToTokenBudget` to trim |

## Examples

### RAG-Optimized Search
```typescript
async function ragSearch(query: string, tokenBudget = 3000) {
  const results = await cachedSearch(query, {
    numResults: 15,
    text: { maxCharacters: 1500 },
    highlights: { numSentences: 3 },
  });

  const processed = processResults(results.results);
  const { selected } = fitToTokenBudget(processed, tokenBudget);
  return selected;
}
```

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Content Options](https://docs.exa.ai/reference/contents)
