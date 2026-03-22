---
name: algolia-reference-architecture
description: |
  Implement Algolia reference architecture: index design, multi-index strategy,
  data pipeline, search service layer, and frontend/backend separation.
  Trigger: "algolia architecture", "algolia best practices", "algolia project structure",
  "how to organize algolia", "algolia index design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Reference Architecture

## Overview

Production-ready architecture for Algolia-powered search. Covers index design, data pipeline from source to Algolia, service layer patterns, and frontend integration.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend                                 │
│  InstantSearch.js / React InstantSearch                       │
│  Uses: liteClient (search-only key)                          │
│  Sends: search-insights events (clicks, conversions)          │
└───────────────────────┬──────────────────────────────────────┘
                        │ Search + Events
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                   Algolia Cloud                               │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────┐             │
│  │ Search   │  │ Analytics    │  │ Recommend   │             │
│  │ Engine   │  │ + Insights   │  │ (ML-based)  │             │
│  └─────────┘  └──────────────┘  └─────────────┘             │
└───────────────────────▲──────────────────────────────────────┘
                        │ Indexing (admin key)
                        │
┌──────────────────────────────────────────────────────────────┐
│                    Backend Service                            │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐      │
│  │ Search     │  │ Indexing     │  │ Settings        │      │
│  │ Service    │  │ Pipeline     │  │ Manager         │      │
│  └────────────┘  └──────┬───────┘  └─────────────────┘      │
│                         │                                     │
│  ┌──────────────────────▼────────────────────────────┐       │
│  │              Source Database                        │       │
│  │  PostgreSQL / MongoDB / CMS / External API          │       │
│  └────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── algolia/
│   ├── client.ts           # Singleton client (see algolia-sdk-patterns)
│   ├── indices.ts          # Index name constants + environment prefixing
│   ├── settings/
│   │   ├── products.ts     # Products index settings
│   │   ├── articles.ts     # Articles index settings
│   │   └── apply.ts        # Script to apply all settings
│   └── transforms/
│       ├── product.ts      # DB record → Algolia record transformer
│       └── article.ts      # DB record → Algolia record transformer
├── services/
│   ├── search.ts           # Search service (wraps Algolia client)
│   └── indexing.ts         # Indexing pipeline (DB → transform → Algolia)
├── api/
│   ├── search.ts           # Search endpoint (returns Algolia results)
│   └── reindex.ts          # Admin endpoint to trigger reindex
└── jobs/
    └── sync-algolia.ts     # Cron job for periodic full sync
```

## Index Design Patterns

### Pattern 1: One Index Per Entity Type

```typescript
// src/algolia/indices.ts
const ENV = process.env.NODE_ENV === 'production' ? '' : `${process.env.NODE_ENV}_`;

export const INDICES = {
  products:  `${ENV}products`,
  articles:  `${ENV}articles`,
  faq:       `${ENV}faq`,
  users:     `${ENV}users`,     // Internal search only (never expose to frontend)
} as const;

export type IndexName = typeof INDICES[keyof typeof INDICES];
```

### Pattern 2: Record Transformer (Source → Algolia)

```typescript
// src/algolia/transforms/product.ts
import type { Product } from '../db/types';

interface AlgoliaProduct {
  objectID: string;
  name: string;
  description: string;
  category: string;
  brand: string;
  price: number;
  rating: number;
  review_count: number;
  in_stock: boolean;
  image_url: string;
  _tags: string[];        // Algolia convention: filterable tags
}

export function transformProduct(product: Product): AlgoliaProduct {
  return {
    objectID: product.id,
    name: product.name,
    description: product.description?.substring(0, 5000) || '',  // Truncate
    category: product.category.name,
    brand: product.brand.name,
    price: product.price / 100,                  // Cents → dollars
    rating: product.avgRating,
    review_count: product.reviewCount,
    in_stock: product.inventory > 0,
    image_url: product.images[0]?.url || '',
    _tags: [
      product.category.slug,
      ...(product.isFeatured ? ['featured'] : []),
      ...(product.isNew ? ['new-arrival'] : []),
    ],
  };
}
```

### Pattern 3: Settings as Code

```typescript
// src/algolia/settings/products.ts
import type { IndexSettings } from 'algoliasearch';

export const productSettings: IndexSettings = {
  searchableAttributes: [
    'name',
    'brand',
    'category',
    'unordered(description)',
  ],
  attributesForFaceting: [
    'searchable(brand)',
    'category',
    'filterOnly(price)',
    'filterOnly(in_stock)',
    '_tags',
  ],
  customRanking: ['desc(review_count)', 'desc(rating)'],
  attributesToRetrieve: ['name', 'brand', 'price', 'image_url', 'category', 'rating'],
  attributesToHighlight: ['name', 'description'],
  attributesToSnippet: ['description:30'],
  unretrievableAttributes: ['_tags'],
  distinct: 1,
  attributeForDistinct: 'product_group_id',
  replicas: [
    'virtual(products_price_asc)',
    'virtual(products_price_desc)',
    'virtual(products_newest)',
  ],
};

// src/algolia/settings/apply.ts
import { getClient } from '../client';
import { INDICES } from '../indices';
import { productSettings } from './products';

async function applyAllSettings() {
  const client = getClient();
  await client.setSettings({ indexName: INDICES.products, indexSettings: productSettings });
  console.log('All Algolia settings applied');
}
```

### Pattern 4: Search Service Layer

```typescript
// src/services/search.ts
import { getClient } from '../algolia/client';
import { INDICES } from '../algolia/indices';
import { ApiError } from 'algoliasearch';

export class SearchService {
  private client = getClient();

  async searchProducts(params: {
    query: string;
    filters?: string;
    facetFilters?: string[][];
    page?: number;
    hitsPerPage?: number;
  }) {
    try {
      return await this.client.searchSingleIndex({
        indexName: INDICES.products,
        searchParams: {
          query: params.query,
          filters: params.filters,
          facetFilters: params.facetFilters,
          page: params.page ?? 0,
          hitsPerPage: params.hitsPerPage ?? 20,
          facets: ['category', 'brand'],
          clickAnalytics: true,
        },
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return { hits: [], nbHits: 0, nbPages: 0, page: 0 };
      }
      throw error;
    }
  }

  async federatedSearch(query: string) {
    const { results } = await this.client.search({
      requests: [
        { indexName: INDICES.products, query, hitsPerPage: 5 },
        { indexName: INDICES.articles, query, hitsPerPage: 3 },
        { indexName: INDICES.faq, query, hitsPerPage: 3 },
      ],
    });
    return results;
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependency | Service imports client imports service | Use lazy initialization |
| Config drift | Dashboard edits not in code | Apply settings from code in CI |
| Transform errors | DB schema change | Add validation in transformer |
| Index name typo | Hardcoded strings | Use `INDICES` constants |

## Resources

- [Algolia Architecture Guide](https://www.algolia.com/doc/guides/getting-started/how-algolia-works/)
- [Index Design Best Practices](https://www.algolia.com/doc/guides/sending-and-managing-data/prepare-your-data/)
- [Multi-Index Search](https://www.algolia.com/doc/guides/building-search-ui/ui-and-ux-patterns/multi-index-search/js/)

## Next Steps

For multi-environment setup, see `algolia-multi-env-setup`.
