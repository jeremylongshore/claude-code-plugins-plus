---
name: algolia-core-workflow-a
description: |
  Implement Algolia search with filters, facets, highlighting, and pagination.
  The primary money-path workflow: search records, apply filters, display results.
  Trigger: "algolia search", "search with algolia", "algolia filters",
  "algolia facets", "algolia search implementation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Core Workflow A — Search & Filtering

## Overview

Primary Algolia workflow: full-text search with filters, faceted navigation, hit highlighting, and pagination. Uses `searchSingleIndex` (v5) with real Algolia search parameters.

## Prerequisites

- Completed `algolia-install-auth` and `algolia-hello-world` setup
- Index populated with records (see `algolia-hello-world`)
- Index settings configured with `searchableAttributes` and `attributesForFaceting`

## Instructions

### Step 1: Configure Index for Filtering

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

await client.setSettings({
  indexName: 'products',
  indexSettings: {
    // What to search (ordered = priority matters)
    searchableAttributes: ['name', 'description', 'brand', 'category'],

    // What to filter/facet on — prefix with filterOnly() if no facet counts needed
    attributesForFaceting: [
      'searchable(brand)',           // Searchable facet: users can search within brand values
      'category',                     // Regular facet: shown in facet panels
      'filterOnly(price)',           // Filter only: no counts computed, saves CPU
      'filterOnly(in_stock)',
    ],

    // Custom ranking: tie-breaker after Algolia's relevance ranking
    customRanking: ['desc(sales_count)', 'desc(rating)'],

    // What comes back in hits
    attributesToRetrieve: ['name', 'brand', 'price', 'image_url', 'category'],
    attributesToHighlight: ['name', 'description'],
    attributesToSnippet: ['description:30'],  // 30-word snippet
  },
});
```

### Step 2: Search with Filters

```typescript
// Algolia filter syntax uses SQL-like expressions
const { hits, nbHits, facets } = await client.searchSingleIndex({
  indexName: 'products',
  searchParams: {
    query: 'running shoes',

    // Numeric/boolean/string filters
    filters: 'price < 150 AND in_stock = true',

    // OR: facetFilters for UI-driven filtering (array = OR, nested = AND)
    // facetFilters: [['category:shoes', 'category:sneakers'], ['brand:Nike']],
    //   ^ shoes OR sneakers, AND brand is Nike

    // Numeric range filters
    numericFilters: ['price >= 50', 'price <= 150'],

    // Request facet counts for these attributes
    facets: ['category', 'brand'],

    // Pagination
    hitsPerPage: 20,
    page: 0,

    // Highlighting
    highlightPreTag: '<mark>',
    highlightPostTag: '</mark>',
  },
});

console.log(`${nbHits} results found`);

// Access facet counts for building filter UI
// facets = { category: { shoes: 42, sneakers: 18 }, brand: { Nike: 30, Adidas: 25 } }
for (const [facetName, values] of Object.entries(facets || {})) {
  console.log(`${facetName}:`);
  for (const [value, count] of Object.entries(values)) {
    console.log(`  ${value}: ${count}`);
  }
}
```

### Step 3: Display Highlighted Results

```typescript
hits.forEach(hit => {
  // _highlightResult contains highlighted versions of each field
  const highlighted = hit._highlightResult;
  const name = highlighted?.name?.value || hit.name;
  const snippet = hit._snippetResult?.description?.value || '';

  console.log(`${name} — $${hit.price}`);
  if (snippet) console.log(`  ${snippet}`);
});
```

### Step 4: Implement Pagination

```typescript
async function paginatedSearch(query: string, page: number = 0) {
  const { hits, nbHits, nbPages, hitsPerPage } = await client.searchSingleIndex({
    indexName: 'products',
    searchParams: {
      query,
      hitsPerPage: 20,
      page,
    },
  });

  return {
    hits,
    totalHits: nbHits,
    totalPages: nbPages,
    currentPage: page,
    hasMore: page < nbPages - 1,
  };
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid filter syntax` | Malformed `filters` string | Check filter syntax: `field:value`, `field < N`, use AND/OR/NOT |
| `Attribute not valid for filtering` | Field not in `attributesForFaceting` | Add field to `attributesForFaceting` in settings |
| `0 results` unexpectedly | Typo tolerance may be disabled | Check `typoTolerance` setting; verify data is indexed |
| Stale results after update | Didn't wait for task | Use `await client.waitForTask()` after indexing |

## Examples

### Multi-Index Search (Federated)

```typescript
const { results } = await client.search({
  requests: [
    { indexName: 'products', query: 'laptop', hitsPerPage: 5 },
    { indexName: 'articles', query: 'laptop', hitsPerPage: 3 },
  ],
});

// results[0].hits = product hits, results[1].hits = article hits
```

### Search with Optional Filters (boost, not require)

```typescript
const { hits } = await client.searchSingleIndex({
  indexName: 'products',
  searchParams: {
    query: 'shoes',
    optionalFilters: ['brand:Nike'],  // Nike products ranked higher but not required
  },
});
```

## Resources

- [Filtering Guide](https://www.algolia.com/doc/guides/managing-results/refine-results/filtering/)
- [Faceting Guide](https://www.algolia.com/doc/guides/managing-results/refine-results/faceting/)
- [Search Parameters](https://www.algolia.com/doc/api-reference/search-api-parameters/)

## Next Steps

For indexing and data sync workflows, see `algolia-core-workflow-b`.
