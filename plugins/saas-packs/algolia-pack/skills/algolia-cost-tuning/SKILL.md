---
name: algolia-cost-tuning
description: |
  Optimize Algolia costs: understand search request vs record pricing,
  reduce operations with batching and caching, monitor usage via Analytics API.
  Trigger: "algolia cost", "algolia billing", "reduce algolia costs",
  "algolia pricing", "algolia expensive", "algolia budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Cost Tuning

## Overview

Algolia pricing is based on **search requests** and **records**. A search request is one API call (which may contain multiple queries via `search({ requests: [...] })`). Records are counted across all indices including replicas.

## Pricing Structure (2025)

| Plan | Records Included | Search Requests | Additional Cost |
|------|------------------|-----------------|-----------------|
| Build (Free) | 1M records | 10K requests/mo | N/A |
| Grow | 100K free, then $0.40/1K | 10K free, then $0.50/1K | Pay as you go |
| Grow Plus | 100K free, then $0.40/1K | 10K free, then $1.75/1K | + AI features |
| Premium | Custom | Custom | Volume discounts |

### What Counts as Records

- Every object in every index = 1 record
- Standard replicas duplicate records (multiply your count)
- Virtual replicas share records (no extra cost)
- Synonyms and rules do NOT count as records

### What Counts as Search Requests

- `searchSingleIndex()` = 1 request
- `search({ requests: [q1, q2, q3] })` = 1 request (multi-query)
- `browse()` = 1 request per page
- `saveObjects()` = NOT a search request (indexing operations are free)

## Instructions

### Step 1: Audit Current Usage

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Check total records across all indices
const { items } = await client.listIndices();
let totalRecords = 0;
let replicaRecords = 0;

items.forEach(idx => {
  const records = idx.entries || 0;
  console.log(`${idx.name}: ${records.toLocaleString()} records, ${(idx.dataSize || 0 / 1024).toFixed(0)}KB`);
  if (idx.name.includes('_replica') || idx.primary) {
    replicaRecords += records;
  }
  totalRecords += records;
});

console.log(`\nTotal: ${totalRecords.toLocaleString()} records (${replicaRecords.toLocaleString()} in replicas)`);
```

### Step 2: Replace Standard Replicas with Virtual Replicas

```typescript
// Standard replicas: duplicate all records (doubles cost)
// Virtual replicas: share records with primary (no extra cost)

// BEFORE: 3 standard replicas = 4x record count
await client.setSettings({
  indexName: 'products',
  indexSettings: {
    replicas: [
      // 'products_price_asc',      // Standard: costs records
      // 'products_price_desc',     // Standard: costs records
      'virtual(products_price_asc)',  // Virtual: FREE
      'virtual(products_price_desc)', // Virtual: FREE
    ],
  },
});

// Virtual replica limitation: can only customize ranking and customRanking
// If you need different searchableAttributes or attributesForFaceting, use standard
```

### Step 3: Use Multi-Query to Reduce Request Count

```typescript
// BAD: 3 separate requests = 3 search operations billed
const results1 = await client.searchSingleIndex({ indexName: 'products', searchParams: { query: 'laptop' } });
const results2 = await client.searchSingleIndex({ indexName: 'articles', searchParams: { query: 'laptop' } });
const results3 = await client.searchSingleIndex({ indexName: 'faq', searchParams: { query: 'laptop' } });

// GOOD: 1 multi-query request = 1 search operation billed
const { results } = await client.search({
  requests: [
    { indexName: 'products', query: 'laptop', hitsPerPage: 5 },
    { indexName: 'articles', query: 'laptop', hitsPerPage: 3 },
    { indexName: 'faq', query: 'laptop', hitsPerPage: 3 },
  ],
});
```

### Step 4: Cache Frequent Searches

```typescript
import { LRUCache } from 'lru-cache';

// Cache popular searches — Algolia's own CDN caches are limited
const searchCache = new LRUCache<string, any>({
  max: 1000,
  ttl: 5 * 60 * 1000, // 5 minutes for product search
});

async function cachedSearch(query: string, filters?: string) {
  const key = JSON.stringify({ query, filters });
  const cached = searchCache.get(key);
  if (cached) {
    console.log('Cache hit — saved 1 search request');
    return cached;
  }
  const result = await client.searchSingleIndex({
    indexName: 'products',
    searchParams: { query, filters },
  });
  searchCache.set(key, result);
  return result;
}
```

### Step 5: Delete Unused Indices

```typescript
// Audit and clean up test/development indices
const { items } = await client.listIndices();
const devIndices = items.filter(i =>
  i.name.startsWith('test_') ||
  i.name.startsWith('dev_') ||
  i.name.startsWith('ci_')
);

for (const idx of devIndices) {
  console.log(`Deleting unused index: ${idx.name} (${idx.entries} records)`);
  await client.deleteIndex({ indexName: idx.name });
}
```

### Step 6: Monitor Usage with Analytics API

```typescript
// Track search volume trends
const { count: searchCount } = await client.getSearchesCount({
  index: 'products',
  startDate: '2025-01-01',
  endDate: '2025-01-31',
});
console.log(`Search requests this month: ${searchCount.toLocaleString()}`);

// Identify no-result queries (wasted searches users will retry)
const { searches } = await client.getSearchesNoResults({
  index: 'products',
  startDate: '2025-01-01',
  endDate: '2025-01-31',
});
console.log('Top no-result searches (fix these to reduce retries):');
searches.slice(0, 10).forEach(s => console.log(`  "${s.search}" — ${s.count} times`));
```

## Cost Reduction Summary

| Strategy | Savings | Effort |
|----------|---------|--------|
| Virtual replicas | 50-75% record cost | Low |
| Multi-query search | 60-80% fewer requests | Low |
| Client-side caching | 30-50% fewer requests | Low |
| Delete unused indices | Variable | Low |
| Fix no-result queries (synonyms) | 10-20% fewer retries | Medium |
| Reduce record size | Indirect (faster = cheaper) | Medium |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bill spike | Uncached bot traffic | Add rate limiting, cache layer |
| Record count higher than expected | Standard replicas | Switch to virtual replicas |
| Search requests over budget | No caching | Add LRU cache in API layer |
| Analytics API returns empty | Wrong date range or region | Check `region` parameter matches your app |

## Resources

- [Algolia Pricing](https://www.algolia.com/pricing/)
- [How Algolia Counts Records](https://support.algolia.com/hc/en-us/articles/17245378392977)
- [Virtual Replicas](https://www.algolia.com/doc/guides/managing-results/refine-results/sorting/how-to/sort-an-index-by-date/)
- [Analytics API](https://www.algolia.com/doc/libraries/javascript/v5/methods/analytics/)

## Next Steps

For architecture patterns, see `algolia-reference-architecture`.
