---
name: shopify-performance-tuning
description: |
  Optimize Shopify API performance with GraphQL query cost reduction, bulk operations,
  caching strategies, and Storefront API for high-traffic storefronts.
  Trigger with phrases like "shopify performance", "optimize shopify",
  "shopify slow", "shopify caching", "shopify bulk operation", "shopify query cost".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Performance Tuning

## Overview

Optimize Shopify API performance through GraphQL query cost reduction, bulk operations for large data exports, response caching, and Storefront API for high-traffic public-facing queries.

## Prerequisites

- Understanding of Shopify's calculated query cost system
- Access to the `Shopify-GraphQL-Cost-Debug: 1` header for cost analysis
- Redis or in-memory cache available (optional)

## Instructions

### Step 1: Analyze Query Cost

```bash
# Debug query cost with special header
curl -X POST "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{"query": "{ products(first: 50) { edges { node { id title variants(first: 20) { edges { node { id price } } } } } } }"}' \
  | jq '.extensions.cost'
```

Response shows cost breakdown:
```json
{
  "requestedQueryCost": 152,
  "actualQueryCost": 42,
  "throttleStatus": {
    "maximumAvailable": 1000.0,
    "currentlyAvailable": 958.0,
    "restoreRate": 50.0
  }
}
```

**Key rule:** `requestedQueryCost` is calculated as `first * nested_fields`. Reducing `first:` from 250 to 50 can cut cost by 5x.

### Step 2: Reduce Query Cost

```typescript
// BEFORE: High cost — requests too many fields and items
// requestedQueryCost: ~5,502
const EXPENSIVE_QUERY = `{
  products(first: 250) {
    edges {
      node {
        id title description descriptionHtml vendor productType tags
        variants(first: 100) {
          edges {
            node {
              id title price compareAtPrice sku barcode
              inventoryQuantity weight weightUnit
              selectedOptions { name value }
              metafields(first: 10) {
                edges { node { namespace key value type } }
              }
            }
          }
        }
        images(first: 20) {
          edges { node { url altText width height } }
        }
        metafields(first: 10) {
          edges { node { namespace key value type } }
        }
      }
    }
  }
}`;

// AFTER: Optimized — only needed fields, smaller page sizes
// requestedQueryCost: ~112
const OPTIMIZED_QUERY = `{
  products(first: 50) {
    edges {
      node {
        id
        title
        status
        variants(first: 5) {
          edges {
            node { id price sku inventoryQuantity }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}`;
```

### Step 3: Use Bulk Operations for Large Exports

Bulk operations bypass rate limits and are designed for exporting large datasets:

```typescript
// Step 1: Start bulk operation
const START_BULK = `
  mutation {
    bulkOperationRunQuery(query: """
      {
        products {
          edges {
            node {
              id
              title
              handle
              variants {
                edges {
                  node {
                    id
                    sku
                    price
                    inventoryQuantity
                  }
                }
              }
            }
          }
        }
      }
    """) {
      bulkOperation {
        id
        status
      }
      userErrors { field message }
    }
  }
`;

// Step 2: Poll for completion
const CHECK_BULK = `{
  currentBulkOperation {
    id
    status       # CREATED, RUNNING, COMPLETED, FAILED
    errorCode
    objectCount
    fileSize
    url          # JSONL download URL when COMPLETED
    createdAt
  }
}`;

// Step 3: Download results (JSONL format — one JSON object per line)
// const response = await fetch(bulkOperation.url);
// Each line: {"id":"gid://shopify/Product/123","title":"Widget",...}
```

### Step 4: Cache Frequently Accessed Data

```typescript
import { LRUCache } from "lru-cache";

const shopifyCache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000, // 5 minutes
  updateAgeOnGet: true,
});

async function cachedQuery<T>(
  cacheKey: string,
  queryFn: () => Promise<T>,
  ttlMs?: number
): Promise<T> {
  const cached = shopifyCache.get(cacheKey);
  if (cached !== undefined) return cached as T;

  const result = await queryFn();
  shopifyCache.set(cacheKey, result, { ttl: ttlMs });
  return result;
}

// Usage — cache product data for 5 minutes
const product = await cachedQuery(
  `product:${productId}`,
  () => shopifyQuery(shop, PRODUCT_QUERY, { id: productId })
);

// Invalidate on webhook
app.post("/webhooks", (req, res) => {
  const topic = req.headers["x-shopify-topic"];
  if (topic === "products/update") {
    const payload = JSON.parse(req.body);
    shopifyCache.delete(`product:gid://shopify/Product/${payload.id}`);
  }
});
```

### Step 5: Use Storefront API for Public Queries

The Storefront API has separate rate limits and is designed for high-traffic public storefronts:

```typescript
// Storefront API — safe for client-side, higher rate limits
const storefrontClient = new shopify.clients.Storefront({
  session,
  apiVersion: "2024-10",
});

// Storefront API query — no admin credentials exposed
const products = await storefrontClient.request(`{
  products(first: 12, sortKey: BEST_SELLING) {
    edges {
      node {
        id
        title
        handle
        priceRange {
          minVariantPrice { amount currencyCode }
        }
        featuredImage {
          url(transform: { maxWidth: 400 })
          altText
        }
      }
    }
  }
}`);
```

## Output

- Query costs reduced through field selection and page size optimization
- Bulk operations configured for large data exports
- Response caching with webhook-driven invalidation
- Storefront API used for public-facing high-traffic queries

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `THROTTLED` on every query | `requestedQueryCost` too high | Reduce `first:` and remove unused fields |
| Bulk operation FAILED | Query syntax error | Test query in GraphiQL first |
| Stale cache data | Cache not invalidated | Add webhook handlers to clear cache |
| Storefront API 403 | Wrong token type | Use Storefront API access token, not Admin |

## Examples

### Performance Comparison

| Approach | 10K Products Export | Rate Limit Impact |
|----------|-------------------|-------------------|
| Paginated (first: 250) | 40 queries, ~60s | Uses ~6,000 points |
| Paginated (first: 50) | 200 queries, ~300s | Uses ~22,000 points |
| Bulk Operation | 1 query + poll, ~30s | Minimal impact |

## Resources

- [GraphQL Rate Limits](https://shopify.dev/docs/api/usage/rate-limits#graphql-admin-api-rate-limits)
- [Bulk Operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)
- [Storefront API](https://shopify.dev/docs/api/storefront)
- [Query Cost Debug Header](https://shopify.dev/docs/api/usage/rate-limits#query-cost)

## Next Steps

For cost optimization, see `shopify-cost-tuning`.
