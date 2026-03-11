---
name: exa-performance-tuning
description: |
  Optimize Exa API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Exa integrations.
  Trigger with phrases like "exa performance", "optimize exa",
  "exa latency", "exa caching", "exa slow", "exa batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Performance Tuning

## Overview
Optimize Exa AI search API response times and throughput for production RAG pipelines and search integrations. Exa search latency varies by type: keyword search (200-500ms), neural search (500-2000ms), and auto mode (300-1500ms). The biggest performance levers are: using keyword search for structured queries (3-4x faster than neural), caching results for repeated queries, limiting `numResults` to what's actually needed, and parallelizing independent searches.

## Prerequisites
- Exa API integration (`exa-js` SDK or REST API)
- Cache infrastructure (Redis or in-memory LRU)
- Understanding of search patterns in your application

## Instructions

### Step 1: Choose Search Type by Latency Requirement
```typescript
import Exa from 'exa-js';

// Match search type to latency budget
function optimizedSearch(exa: Exa, query: string, latencyBudgetMs: number) {
  if (latencyBudgetMs < 500) {
    // Fast path: keyword search for structured/exact queries
    return exa.search(query, { type: 'keyword', numResults: 3 });
  } else if (latencyBudgetMs < 1500) {
    // Balanced: auto mode picks best approach
    return exa.search(query, { type: 'auto', numResults: 5 });
  } else {
    // Quality: neural search for semantic understanding
    return exa.search(query, { type: 'neural', numResults: 10 });
  }
}
```

### Step 2: Cache Search Results
```typescript
import { LRUCache } from 'lru-cache';

const searchCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 2 * 3600_000, // 2-hour TTL for most searches
});

async function cachedSearch(exa: Exa, query: string, options: any) {
  const key = `${query}:${options.type}:${options.numResults}`;
  const cached = searchCache.get(key);
  if (cached) return cached; // Cache hit: 0ms vs 500-2000ms

  const results = await exa.search(query, options);
  searchCache.set(key, results);
  return results;
}
```

### Step 3: Minimize Result Count
```typescript
// Each additional result adds latency (content retrieval)
const RESULT_CONFIGS: Record<string, number> = {
  'rag-context':     3,   // Only need top 3 for RAG
  'autocomplete':    5,   // Quick suggestions
  'deep-research':  10,   // Comprehensive coverage
};

// Don't default to numResults: 10 when 3 suffices
// Reducing from 10 to 3 results saves ~200-500ms per search
```

### Step 4: Parallelize Independent Searches
```typescript
// When RAG needs multiple search contexts, run them in parallel
async function parallelContextSearch(exa: Exa, queries: string[]) {
  const searches = queries.map(q =>
    cachedSearch(exa, q, { type: 'auto', numResults: 3 })
  );
  return Promise.all(searches);
  // 3 parallel searches: ~600ms total
  // 3 sequential searches: ~1800ms total
}
```

### Step 5: Use Content Retrieval Selectively
```typescript
// The /get-contents endpoint is separate from search
// Only fetch full content for results you'll actually use
async function searchThenFetch(exa: Exa, query: string) {
  // Step 1: Fast search for URLs only
  const results = await exa.search(query, { type: 'auto', numResults: 5 });

  // Step 2: Only fetch content for top 2 results
  const topUrls = results.results.slice(0, 2).map(r => r.url);
  const contents = await exa.getContents(topUrls, { text: { maxCharacters: 2000 } });

  return contents;
}
// Saves content retrieval time for 3 results you won't use
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Search taking 3s+ | Neural search on complex query | Switch to keyword or auto mode |
| Timeout on content retrieval | Large pages, slow source servers | Set `maxCharacters` limit on content |
| Cache miss rate high | Unique queries every time | Normalize queries before caching |
| Rate limit (429) | Too many concurrent searches | Add request queue with concurrency limit |

## Examples
```bash
# Benchmark: keyword vs neural latency on same query
echo "Keyword:"
time curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "GraphQL best practices 2024", "type": "keyword", "numResults": 3}' -o /dev/null

echo "Neural:"
time curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "GraphQL best practices 2024", "type": "neural", "numResults": 3}' -o /dev/null
```

```typescript
// Optimized RAG pipeline search
const context = await parallelContextSearch(exa, [
  `${topic} technical overview`,
  `${topic} implementation examples`,
]);
// Total latency: max(search1, search2) + cache overhead ~= 600ms
```
