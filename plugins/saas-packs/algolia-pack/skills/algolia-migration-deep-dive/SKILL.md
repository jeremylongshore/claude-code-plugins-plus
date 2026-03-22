---
name: algolia-migration-deep-dive
description: |
  Migrate to Algolia from Elasticsearch, Typesense, or Meilisearch.
  Covers data migration, query translation, replaceAllObjects zero-downtime swap,
  and strangler fig traffic shifting.
  Trigger: "migrate to algolia", "switch to algolia", "algolia migration",
  "elasticsearch to algolia", "replace search engine", "algolia replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Migration Deep Dive

## Overview

Comprehensive guide for migrating from another search engine (Elasticsearch, Typesense, Meilisearch, or custom) to Algolia. Uses the strangler fig pattern: run old and new in parallel, gradually shift traffic, then cut over.

## Migration Planning

| From | To Algolia | Difficulty | Duration |
|------|-----------|-----------|----------|
| Elasticsearch | Medium — query syntax differs significantly | 2-4 weeks |
| Typesense | Low — similar hosted model | 1-2 weeks |
| Meilisearch | Low — similar API concepts | 1-2 weeks |
| Custom SQL LIKE | Low — major upgrade | 1-2 weeks |
| Solr | Medium — config-heavy to API-driven | 2-4 weeks |

## Instructions

### Step 1: Assess Current Implementation

```bash
# Find all search-related code
grep -rn "elasticsearch\|elastic\|typesense\|meilisearch\|\.search(" \
  --include="*.ts" --include="*.tsx" --include="*.js" src/ | wc -l

# Inventory current search features used
grep -rn "aggregations\|facets\|filters\|sort\|highlight\|suggest" \
  --include="*.ts" --include="*.tsx" src/
```

```typescript
// Document current capabilities
interface MigrationAssessment {
  currentEngine: string;
  recordCount: number;
  indexCount: number;
  features: {
    fullTextSearch: boolean;
    faceting: boolean;
    filtering: boolean;
    geoSearch: boolean;
    synonyms: boolean;
    customRanking: boolean;
    analytics: boolean;
    abTesting: boolean;
    recommendations: boolean;
  };
  integrationPoints: string[];  // Files that call the search engine
  queryPatterns: string[];       // Types of queries used
}
```

### Step 2: Create the Adapter Layer

```typescript
// src/search/adapter.ts
// Abstraction layer — both engines implement the same interface

interface SearchResult<T> {
  hits: T[];
  totalHits: number;
  totalPages: number;
  currentPage: number;
  facets?: Record<string, Record<string, number>>;
  processingTimeMs: number;
}

interface SearchAdapter {
  search<T>(params: {
    index: string;
    query: string;
    filters?: string;
    facets?: string[];
    page?: number;
    hitsPerPage?: number;
  }): Promise<SearchResult<T>>;

  index(params: { index: string; records: Record<string, any>[] }): Promise<void>;
  delete(params: { index: string; ids: string[] }): Promise<void>;
}
```

### Step 3: Implement the Algolia Adapter

```typescript
// src/search/algolia-adapter.ts
import { algoliasearch, ApiError } from 'algoliasearch';

export class AlgoliaAdapter implements SearchAdapter {
  private client;

  constructor(appId: string, apiKey: string) {
    this.client = algoliasearch(appId, apiKey);
  }

  async search<T>(params: {
    index: string;
    query: string;
    filters?: string;
    facets?: string[];
    page?: number;
    hitsPerPage?: number;
  }): Promise<SearchResult<T>> {
    const result = await this.client.searchSingleIndex<T>({
      indexName: params.index,
      searchParams: {
        query: params.query,
        filters: params.filters,
        facets: params.facets || ['*'],
        page: params.page || 0,
        hitsPerPage: params.hitsPerPage || 20,
      },
    });

    return {
      hits: result.hits,
      totalHits: result.nbHits,
      totalPages: result.nbPages,
      currentPage: result.page,
      facets: result.facets,
      processingTimeMs: result.processingTimeMS,
    };
  }

  async index(params: { index: string; records: Record<string, any>[] }) {
    const { taskID } = await this.client.saveObjects({
      indexName: params.index,
      objects: params.records.map(r => ({
        objectID: r.id || r.objectID,
        ...r,
      })),
    });
    await this.client.waitForTask({ indexName: params.index, taskID });
  }

  async delete(params: { index: string; ids: string[] }) {
    const { taskID } = await this.client.deleteObjects({
      indexName: params.index,
      objectIDs: params.ids,
    });
    await this.client.waitForTask({ indexName: params.index, taskID });
  }
}
```

### Step 4: Query Translation Guide

```typescript
// Elasticsearch → Algolia query translation

// ES: { "query": { "match": { "title": "laptop" } } }
// Algolia:
await client.searchSingleIndex({ indexName: 'products', searchParams: { query: 'laptop' } });

// ES: { "query": { "bool": { "filter": [{ "term": { "category": "electronics" } }] } } }
// Algolia:
await client.searchSingleIndex({
  indexName: 'products',
  searchParams: { query: '', filters: 'category:electronics' },
});

// ES: { "query": { "range": { "price": { "gte": 50, "lte": 200 } } } }
// Algolia:
await client.searchSingleIndex({
  indexName: 'products',
  searchParams: { query: '', numericFilters: ['price >= 50', 'price <= 200'] },
});

// ES: { "aggs": { "categories": { "terms": { "field": "category" } } } }
// Algolia:
await client.searchSingleIndex({
  indexName: 'products',
  searchParams: { query: '', facets: ['category'] },
});
// facets in response: { category: { electronics: 42, clothing: 18 } }

// ES: { "sort": [{ "price": "asc" }] }
// Algolia: Use a replica index with price sort ranking
await client.searchSingleIndex({ indexName: 'products_price_asc', searchParams: { query: '' } });

// ES: { "highlight": { "fields": { "title": {} } } }
// Algolia: Built-in, use _highlightResult in response
```

### Step 5: Data Migration

```typescript
// Full data migration with transform
async function migrateData(sourceAdapter: SearchAdapter, targetIndex: string) {
  const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

  // Use replaceAllObjects for atomic zero-downtime swap
  // Internally: creates temp index → indexes all records → moves temp → deletes old
  console.log(`Starting migration to ${targetIndex}...`);

  const allRecords: Record<string, any>[] = [];
  let page = 0;
  let hasMore = true;

  // Export from source
  while (hasMore) {
    const result = await sourceAdapter.search({
      index: 'products',
      query: '',
      page,
      hitsPerPage: 1000,
    });
    allRecords.push(...result.hits.map(transformRecord));
    hasMore = page < result.totalPages - 1;
    page++;
    console.log(`Exported ${allRecords.length} records...`);
  }

  // Import to Algolia atomically
  const { taskID } = await client.replaceAllObjects({
    indexName: targetIndex,
    objects: allRecords,
    batchSize: 1000,
  });
  await client.waitForTask({ indexName: targetIndex, taskID });

  console.log(`Migration complete: ${allRecords.length} records in ${targetIndex}`);
}

function transformRecord(record: any): Record<string, any> {
  return {
    objectID: record.id || record._id,
    ...record,
    // Remove Elasticsearch-specific fields
    _id: undefined,
    _source: undefined,
    _score: undefined,
  };
}
```

### Step 6: Traffic Shifting (Strangler Fig)

```typescript
// Gradually shift traffic from old engine to Algolia
function getSearchAdapter(): SearchAdapter {
  const algoliaPercent = parseInt(process.env.ALGOLIA_TRAFFIC_PERCENT || '0');

  if (Math.random() * 100 < algoliaPercent) {
    return new AlgoliaAdapter(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);
  }

  return new ElasticsearchAdapter(process.env.ES_URL!);
}

// Deployment steps:
// Week 1: ALGOLIA_TRAFFIC_PERCENT=10   (canary)
// Week 2: ALGOLIA_TRAFFIC_PERCENT=50   (half traffic)
// Week 3: ALGOLIA_TRAFFIC_PERCENT=100  (full cutover)
// Week 4: Remove old adapter code
```

### Step 7: Validation

```typescript
// Compare results between old and new engines
async function validateMigration(queries: string[]) {
  const old = new ElasticsearchAdapter(process.env.ES_URL!);
  const algolia = new AlgoliaAdapter(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

  for (const query of queries) {
    const oldResult = await old.search({ index: 'products', query });
    const algoliaResult = await algolia.search({ index: 'products', query });

    const oldIds = new Set(oldResult.hits.map((h: any) => h.objectID || h.id));
    const algoliaIds = new Set(algoliaResult.hits.map((h: any) => h.objectID));

    const overlap = [...algoliaIds].filter(id => oldIds.has(id)).length;
    const overlapPct = (overlap / Math.max(oldIds.size, 1) * 100).toFixed(0);

    console.log(`"${query}": old=${oldResult.totalHits}, algolia=${algoliaResult.totalHits}, overlap=${overlapPct}%`);
  }
}
```

## Rollback Plan

```bash
# Instant rollback: set traffic to 0%
export ALGOLIA_TRAFFIC_PERCENT=0
# Restart services to pick up new env var

# Or if fully cut over: old engine is still running, swap adapter
# Keep old engine data in sync for at least 2 weeks after cutover
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Result mismatch | Different ranking algorithms | Tune `customRanking` and `searchableAttributes` |
| Missing records | Transform dropped fields | Add logging to transform, validate counts |
| Higher latency | Cold Algolia index | Search a few times to warm cache, then benchmark |
| Filter syntax errors | Elasticsearch query DSL ≠ Algolia filters | Use translation guide above |

## Resources

- [Algolia Migration Guide](https://www.algolia.com/doc/guides/sending-and-managing-data/send-and-update-your-data/)
- [replaceAllObjects](https://www.algolia.com/doc/api-reference/api-methods/replace-all-objects/)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Elasticsearch to Algolia](https://www.algolia.com/for/elasticsearch-alternative/)

## Next Steps

Migration complete. See `algolia-prod-checklist` for go-live preparation.
