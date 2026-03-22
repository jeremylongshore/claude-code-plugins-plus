---
name: exa-performance-tuning
description: |
  Optimize Exa API performance with search type selection, caching, and parallelization.
  Use when experiencing slow responses, implementing caching strategies,
  or optimizing request throughput for Exa integrations.
  Trigger with phrases like "exa performance", "optimize exa",
  "exa latency", "exa caching", "exa slow", "exa fast".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, performance, optimization]

---
# Exa Performance Tuning

## Overview
Optimize Exa search API response times for production workloads. Key levers: search type selection (instant < fast < auto < neural < deep), result count reduction, content scope control, result caching, and parallel query execution.

## Latency by Search Type

| Type | Typical Latency | Use Case |
|------|----------------|----------|
| `instant` | < 150ms | Real-time autocomplete, typeahead |
| `fast` | p50 < 425ms | Speed-critical user-facing search |
| `auto` | 300-1500ms | General purpose (default) |
| `neural` | 500-2000ms | Best semantic quality |
| `deep` | 2-5s | Maximum coverage, light deep search |
| `deep-reasoning` | 5-15s | Complex research questions |

## Instructions

### Step 1: Match Search Type to Latency Budget
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

function selectSearchType(latencyBudgetMs: number) {
  if (latencyBudgetMs < 200) return "instant";
  if (latencyBudgetMs < 500) return "fast";
  if (latencyBudgetMs < 1500) return "auto";
  if (latencyBudgetMs < 3000) return "neural";
  return "deep";
}

async function optimizedSearch(query: string, latencyBudgetMs: number) {
  const type = selectSearchType(latencyBudgetMs);
  const numResults = latencyBudgetMs < 500 ? 3 : latencyBudgetMs < 2000 ? 5 : 10;

  return exa.search(query, { type, numResults });
}
```

### Step 2: Minimize Content Retrieval
```typescript
// Each content option adds latency. Only request what you need.

// Fastest: metadata only (no content retrieval)
const metadataOnly = await exa.search("query", { numResults: 5 });

// Medium: highlights only (much smaller than full text)
const highlightsOnly = await exa.searchAndContents("query", {
  numResults: 5,
  highlights: { maxCharacters: 300 },
  // No text or summary — saves content retrieval time
});

// Slower: full text (use maxCharacters to limit)
const withText = await exa.searchAndContents("query", {
  numResults: 3,  // fewer results = faster
  text: { maxCharacters: 1000 },  // limit content size
});
```

### Step 3: Cache Search Results
```typescript
import { LRUCache } from "lru-cache";

const searchCache = new LRUCache<string, any>({
  max: 5000,
  ttl: 2 * 3600 * 1000, // 2-hour TTL
});

async function cachedSearch(query: string, opts: any) {
  const key = `${query}:${opts.type || "auto"}:${opts.numResults || 10}`;
  const cached = searchCache.get(key);
  if (cached) return cached; // Cache hit: 0ms vs 500-2000ms

  const results = await exa.search(query, opts);
  searchCache.set(key, results);
  return results;
}
```

### Step 4: Parallelize Independent Searches
```typescript
// Run independent queries concurrently instead of sequentially
async function parallelSearch(queries: string[]) {
  const searches = queries.map(q =>
    cachedSearch(q, { type: "auto", numResults: 3 })
  );
  return Promise.all(searches);
  // 3 parallel searches: ~600ms total (limited by slowest)
  // 3 sequential searches: ~1800ms total
}
```

### Step 5: Two-Phase Search Pattern
```typescript
// Phase 1: Fast search for URLs only
// Phase 2: Selective content retrieval for top results only
async function twoPhaseSearch(query: string) {
  // Phase 1: metadata only (fast)
  const results = await exa.search(query, { type: "auto", numResults: 10 });

  // Phase 2: get content only for top 3 results
  const topUrls = results.results.slice(0, 3).map(r => r.url);
  const contents = await exa.getContents(topUrls, {
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500, query },
  });

  return contents;
  // Saves content retrieval time for 7 results you won't use
}
```

### Step 6: Query Normalization for Cache Hits
```typescript
function normalizeQuery(query: string): string {
  return query
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ")       // collapse whitespace
    .replace(/[?.!,;:]+$/, ""); // strip trailing punctuation
}

async function normalizedSearch(query: string, opts: any) {
  return cachedSearch(normalizeQuery(query), opts);
}
// Increases cache hit rate by 20-40% for user-generated queries
```

## Performance Comparison

| Strategy | Latency Savings | Implementation |
|----------|----------------|----------------|
| `instant` type | 5-10x faster than neural | One-line change |
| Reduce numResults (10 -> 3) | ~200-500ms saved | One-line change |
| Highlights instead of text | ~100-300ms saved | Replace `text` with `highlights` |
| LRU cache | 100% for cache hits | ~20 lines |
| Parallel queries | 2-3x throughput | `Promise.all` wrapper |
| Two-phase search | ~30-50% for large result sets | ~15 lines |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Search taking 3s+ | Neural search on complex query | Switch to `fast` or `auto` type |
| Timeout on content | Large pages, slow sources | Set `maxCharacters` limit |
| Cache miss rate high | Unique queries each time | Normalize queries before caching |
| Rate limit (429) | Too many concurrent searches | Add request queue with concurrency limit |

## Resources
- [Exa Search Types](https://docs.exa.ai/reference/search)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)

## Next Steps
For cost optimization, see `exa-cost-tuning`. For reliability, see `exa-reliability-patterns`.
