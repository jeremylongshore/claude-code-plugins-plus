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

**REST Admin API** -- Leaky Bucket:

| Plan | Bucket Size | Leak Rate |
|------|------------|-----------|
| Standard | 40 requests | 2/second |
| Shopify Plus | 80 requests | 4/second |

The `X-Shopify-Shop-Api-Call-Limit` header shows your bucket state (e.g., `32/40` means 32 of 40 slots used). When full, you get HTTP 429 with `Retry-After` header.

**GraphQL Admin API** -- Calculated Query Cost:

| Plan | Max Available | Restore Rate |
|------|--------------|-------------|
| Standard | 1,000 points | 50 points/second |
| Shopify Plus | 2,000 points | 100 points/second |

Every GraphQL response includes cost info in `extensions.cost` with `requestedQueryCost` (worst-case estimate), `actualQueryCost` (real cost, often much lower), and `throttleStatus` (available points and restore rate). When `currentlyAvailable` drops to 0, you get `THROTTLED`.

### Step 2: Implement GraphQL Cost-Aware Throttling

Client-side rate limiter that tracks the query cost bucket and pre-emptively waits before sending requests that would be throttled. Updates available points from each response's `throttleStatus`.

See [Cost-Aware Rate Limiter](references/cost-aware-rate-limiter.md) for the complete `ShopifyRateLimiter` class.

### Step 3: Implement Retry with Backoff for 429s

Generic retry wrapper handling both REST 429 responses and GraphQL THROTTLED errors. Uses `Retry-After` header when available, otherwise exponential backoff with jitter (max 30s).

See [Retry with Backoff](references/retry-with-backoff.md) for the complete implementation.

### Step 4: Reduce Query Cost

Prune unused fields and lower `first:` page sizes to reduce `requestedQueryCost`. A query dropping from `first: 250` to `first: 50` with fewer nested fields can go from ~5,500 to ~112 cost.

See [Query Cost Reduction](references/query-cost-reduction.md) for before/after examples and the debug curl command.

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

For large data exports, use Shopify's bulk query API which bypasses rate limits entirely:

```typescript
import PQueue from "p-queue";

const BULK_QUERY = `
  mutation bulkOperationRunQuery($query: String!) {
    bulkOperationRunQuery(query: $query) {
      bulkOperation { id status url }
      userErrors { field message }
    }
  }
`;

await client.request(BULK_QUERY, {
  variables: {
    query: `{
      products {
        edges {
          node {
            id title
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
