---
name: algolia-performance-tuning
description: |
  Optimize Algolia search performance: record size, searchable attributes,
  replica strategy, response caching, and query-time parameter tuning.
  Trigger: "algolia performance", "optimize algolia", "algolia latency",
  "algolia slow", "algolia caching", "algolia response time".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Performance Tuning

## Overview

Algolia's edge infrastructure typically delivers search in < 50ms globally. When performance degrades, the causes are usually: oversized records, too many searchable attributes, unoptimized faceting, or missing client-side caching. This skill covers server-side and client-side optimizations.

## Performance Baselines

| Metric | Good | Warning | Action Needed |
|--------|------|---------|---------------|
| Search latency (P50) | < 20ms | 20-100ms | > 100ms |
| Search latency (P95) | < 50ms | 50-200ms | > 200ms |
| Indexing time per 1K records | < 2s | 2-10s | > 10s |
| Record size (avg) | < 5KB | 5-50KB | > 50KB |

## Instructions

### Step 1: Optimize Record Size

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// BAD: Full record with unnecessary data
const badRecord = {
  objectID: '1',
  name: 'Running Shoes',
  full_html_description: '<div>...5000 chars of HTML...</div>',  // Too big
  internal_notes: 'Supplier ref: ABC-123',                       // Not searchable
  all_reviews: [/* 200 reviews */],                                // Huge array
};

// GOOD: Lean record for search
const goodRecord = {
  objectID: '1',
  name: 'Running Shoes',
  description: 'Lightweight running shoes with cushioned sole',  // Plain text, truncated
  category: 'shoes',
  brand: 'Nike',
  price: 129.99,
  rating: 4.5,
  review_count: 200,          // Count, not full reviews
  in_stock: true,
  image_url: '/images/1.jpg', // URL, not base64
};
```

### Step 2: Optimize Searchable Attributes

```typescript
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    // Order matters: first attribute = highest priority in ranking
    // Fewer searchable attributes = faster search
    searchableAttributes: [
      'name',                    // Highest priority
      'brand',
      'category',
      'unordered(description)',  // unordered = position in attribute doesn't affect ranking
    ],
    // DON'T make IDs, URLs, or numeric fields searchable

    // unretrievableAttributes: fields searchable but never returned in hits
    // Use for fields users should match against but not see
    unretrievableAttributes: ['internal_tags'],

    // attributesToRetrieve: limit what comes back (smaller response = faster)
    attributesToRetrieve: ['name', 'brand', 'price', 'image_url', 'category'],
  },
});
```

### Step 3: Optimize Faceting

```typescript
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    attributesForFaceting: [
      'category',              // Regular facet: counts computed
      'brand',                 // Regular facet
      'filterOnly(price)',     // filterOnly: no counts = faster
      'filterOnly(in_stock)',  // Use for boolean/numeric filters
      'filterOnly(created_at)',
    ],
    // filterOnly() saves CPU — use it when you don't need facet counts
    // searchable(brand) lets users search within facet values
  },
});
```

### Step 4: Client-Side Response Caching

```typescript
import { LRUCache } from 'lru-cache';

const searchCache = new LRUCache<string, any>({
  max: 500,           // Max cached queries
  ttl: 60 * 1000,     // 1 minute TTL
});

async function cachedSearch(query: string, filters?: string) {
  const cacheKey = `${query}|${filters || ''}`;
  const cached = searchCache.get(cacheKey);
  if (cached) return cached;

  const result = await client.searchSingleIndex({
    indexName: 'products',
    searchParams: { query, filters, hitsPerPage: 20 },
  });

  searchCache.set(cacheKey, result);
  return result;
}
```

### Step 5: Query-Time Optimization Parameters

```typescript
const { hits } = await client.searchSingleIndex({
  indexName: 'products',
  searchParams: {
    query: 'laptop',

    // Reduce response size
    attributesToRetrieve: ['name', 'price', 'image_url'],  // Only what UI needs
    attributesToHighlight: ['name'],                         // Fewer = faster
    attributesToSnippet: [],                                 // Skip snippets if not used
    responseFields: ['hits', 'nbHits', 'page', 'nbPages'],  // Skip unnecessary metadata

    // Limit processing
    hitsPerPage: 20,              // Don't over-fetch
    maxValuesPerFacet: 10,        // Limit facet values returned

    // Disable features you don't use
    // typoTolerance: false,      // Uncomment if exact matching is fine
    // removeStopWords: false,    // Keep stop words in query
  },
});
```

### Step 6: Replica Strategy for Sort Orders

```typescript
// Standard replicas share data but have their own ranking
// Virtual replicas share data AND ranking config (less storage cost)
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    replicas: [
      'virtual(products_price_asc)',   // Virtual: cheaper, limited customization
      'virtual(products_price_desc)',
      'products_newest',               // Standard: full ranking control
    ],
  },
});

// Virtual replica can only override: customRanking and ranking
// Standard replica can override all settings
```

## Performance Monitoring

```typescript
async function measureSearchLatency(query: string, iterations = 10) {
  const latencies: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await client.searchSingleIndex({
      indexName: 'products',
      searchParams: { query, hitsPerPage: 20 },
    });
    latencies.push(performance.now() - start);
  }

  latencies.sort((a, b) => a - b);
  console.log({
    p50: latencies[Math.floor(iterations * 0.5)].toFixed(1),
    p95: latencies[Math.floor(iterations * 0.95)].toFixed(1),
    p99: latencies[Math.floor(iterations * 0.99)].toFixed(1),
    avg: (latencies.reduce((a, b) => a + b) / iterations).toFixed(1),
  });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| P95 > 200ms | Oversized records | Trim records, use `unretrievableAttributes` |
| Facet queries slow | Too many facet values | Use `filterOnly()` or `maxValuesPerFacet` |
| Indexing slow | Large batch + complex settings | Reduce batch size, simplify `searchableAttributes` |
| Cache stampede | TTL expired, burst traffic | Use stale-while-revalidate pattern |

## Resources

- [Performance Best Practices](https://www.algolia.com/doc/guides/managing-results/optimize-search-results/)
- [Record Size Tips](https://support.algolia.com/hc/en-us/articles/4406981897617)
- [Virtual Replicas](https://www.algolia.com/doc/guides/managing-results/refine-results/sorting/how-to/sort-an-index-by-date/)

## Next Steps

For cost optimization, see `algolia-cost-tuning`.
