---
name: shopify-rate-limits
description: |
  Handle Shopify API rate limits for both REST (leaky bucket) and GraphQL (calculated query cost).
  Use when hitting 429 errors, implementing retry logic, or optimizing API request throughput.
  Trigger with phrases like "shopify rate limit", "shopify throttling",
  "shopify 429", "shopify THROTTLED", "shopify query cost", "shopify backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Rate Limits

## Overview

Shopify uses two distinct rate limiting systems: leaky bucket for REST and calculated query cost for GraphQL. This skill covers both with real header values and response shapes.

## Prerequisites

- Understanding of Shopify's REST and GraphQL Admin APIs
- Familiarity with the `@shopify/shopify-api` library

## Instructions

### Step 1: Understand the Two Rate Limit Systems

**REST Admin API** — Leaky Bucket:

| Plan | Bucket Size | Leak Rate |
|------|------------|-----------|
| Standard | 40 requests | 2/second |
| Shopify Plus | 80 requests | 4/second |

The `X-Shopify-Shop-Api-Call-Limit` header shows your bucket state:

```
X-Shopify-Shop-Api-Call-Limit: 32/40
```

Means: 32 of 40 slots used. When full, you get HTTP 429 with `Retry-After` header.

**GraphQL Admin API** — Calculated Query Cost:

| Plan | Max Available | Restore Rate |
|------|--------------|-------------|
| Standard | 1,000 points | 50 points/second |
| Shopify Plus | 2,000 points | 100 points/second |

Every GraphQL response includes cost info in `extensions`:

```json
{
  "extensions": {
    "cost": {
      "requestedQueryCost": 252,
      "actualQueryCost": 12,
      "throttleStatus": {
        "maximumAvailable": 1000.0,
        "currentlyAvailable": 988.0,
        "restoreRate": 50.0
      }
    }
  }
}
```

Key insight: `requestedQueryCost` is the *worst case* estimate. `actualQueryCost` is the real cost (often much lower). When `currentlyAvailable` drops to 0, you get `THROTTLED`.

### Step 2: Implement GraphQL Cost-Aware Throttling

```typescript
interface ShopifyThrottleStatus {
  maximumAvailable: number;
  currentlyAvailable: number;
  restoreRate: number;
}

class ShopifyRateLimiter {
  private available: number;
  private restoreRate: number;
  private lastUpdate: number;

  constructor(maxAvailable = 1000, restoreRate = 50) {
    this.available = maxAvailable;
    this.restoreRate = restoreRate;
    this.lastUpdate = Date.now();
  }

  updateFromResponse(throttleStatus: ShopifyThrottleStatus): void {
    this.available = throttleStatus.currentlyAvailable;
    this.restoreRate = throttleStatus.restoreRate;
    this.lastUpdate = Date.now();
  }

  async waitIfNeeded(estimatedCost: number): Promise<void> {
    // Estimate current available based on restore rate
    const elapsed = (Date.now() - this.lastUpdate) / 1000;
    const estimated = Math.min(
      this.available + elapsed * this.restoreRate,
      1000
    );

    if (estimated < estimatedCost) {
      const waitSeconds = (estimatedCost - estimated) / this.restoreRate;
      console.log(`Rate limit: waiting ${waitSeconds.toFixed(1)}s for ${estimatedCost} points`);
      await new Promise((r) => setTimeout(r, waitSeconds * 1000));
    }
  }
}

// Usage
const limiter = new ShopifyRateLimiter();

async function rateLimitedQuery(client: any, query: string, variables?: any) {
  await limiter.waitIfNeeded(100); // estimate cost

  const response = await client.request(query, { variables });

  // Update limiter from actual response
  if (response.extensions?.cost?.throttleStatus) {
    limiter.updateFromResponse(response.extensions.cost.throttleStatus);
  }

  return response;
}
```

### Step 3: Implement Retry with Backoff for 429s

```typescript
async function withShopifyRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const isThrottled =
        error.response?.code === 429 ||
        error.body?.errors?.[0]?.extensions?.code === "THROTTLED";

      if (!isThrottled || attempt === maxRetries) throw error;

      // Use Retry-After header if available (REST), otherwise calculate
      const retryAfter = error.response?.headers?.["retry-after"];
      const delay = retryAfter
        ? parseFloat(retryAfter) * 1000
        : Math.min(1000 * Math.pow(2, attempt) + Math.random() * 500, 30000);

      console.warn(
        `Shopify throttled (attempt ${attempt + 1}/${maxRetries}). ` +
        `Retrying in ${(delay / 1000).toFixed(1)}s`
      );

      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 4: Reduce Query Cost

```typescript
// EXPENSIVE query — requests all fields, high cost
const EXPENSIVE = `{
  products(first: 250) {
    edges {
      node {
        id title description
        variants(first: 100) {
          edges {
            node {
              id title price sku inventoryQuantity
              metafields(first: 10) {
                edges { node { key value } }
              }
            }
          }
        }
        images(first: 20) {
          edges { node { url altText } }
        }
      }
    }
  }
}`;
// requestedQueryCost: ~5,502 (may THROTTLE immediately)

// OPTIMIZED query — only needed fields, lower page sizes
const OPTIMIZED = `{
  products(first: 50) {
    edges {
      node {
        id
        title
        variants(first: 10) {
          edges {
            node { id price sku }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}`;
// requestedQueryCost: ~112 (safe, leaves room for other queries)
```

### Step 5: Debug Query Cost

```bash
# Add this header to see cost breakdown per field
curl -X POST "https://store.myshopify.com/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{"query": "{ products(first: 10) { edges { node { id title } } } }"}' \
  | jq '.extensions.cost'
```

## Output

- Rate limit-aware client that prevents 429 errors
- Retry logic with proper backoff for both REST and GraphQL
- Optimized queries with lower calculated cost
- Debug headers for cost analysis

## Error Handling

| Scenario | REST Indicator | GraphQL Indicator |
|----------|---------------|-------------------|
| Approaching limit | `X-Shopify-Shop-Api-Call-Limit: 38/40` | `currentlyAvailable < 100` |
| At limit | HTTP 429 + `Retry-After: 2.0` | `errors[0].extensions.code: "THROTTLED"` |
| Recovering | Wait for `Retry-After` seconds | Wait for `restoreRate` to refill |

## Examples

### Queue-Based Bulk Operations

```typescript
import PQueue from "p-queue";

// For bulk operations, use Shopify's bulk query API instead
const BULK_QUERY = `
  mutation bulkOperationRunQuery($query: String!) {
    bulkOperationRunQuery(query: $query) {
      bulkOperation {
        id
        status
        url
      }
      userErrors { field message }
    }
  }
`;

// Bulk queries bypass rate limits for large data exports
await client.request(BULK_QUERY, {
  variables: {
    query: `{
      products {
        edges {
          node {
            id
            title
            variants { edges { node { id sku price } } }
          }
        }
      }
    }`,
  },
});
```

## Resources

- [Shopify API Rate Limits](https://shopify.dev/docs/api/usage/rate-limits)
- [REST Rate Limits](https://shopify.dev/docs/api/admin-rest/usage/rate-limits)
- [GraphQL Rate Limits](https://shopify.dev/docs/api/usage/rate-limits#graphql-admin-api-rate-limits)
- [Bulk Operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)

## Next Steps

For security configuration, see `shopify-security-basics`.
