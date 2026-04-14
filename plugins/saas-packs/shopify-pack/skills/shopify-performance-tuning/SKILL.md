---
name: shopify-performance-tuning
description: |
  Optimize Shopify API performance with GraphQL query cost reduction, bulk operations,
  caching strategies, and Storefront API for high-traffic storefronts.
  Use when queries are slow or hitting THROTTLED errors, exporting large datasets,
  or optimizing API throughput for a high-traffic storefront.
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

### Step 1: Analyze and Reduce Query Cost

Use the debug header to inspect `requestedQueryCost` vs `actualQueryCost`. Reduce cost by selecting only needed fields and lowering `first:` page sizes (250 to 50 can cut cost by 5x).

See [Query Cost Optimization](references/query-cost-optimization.md) for debug commands and before/after examples.

### Step 2: Use Bulk Operations for Large Exports

Bulk operations bypass rate limits and are designed for exporting large datasets. Start a mutation, poll for completion, then download JSONL results.

See [Bulk Operations](references/bulk-operations.md) for the complete mutation/poll/download flow and performance comparison table.

### Step 3: Cache Frequently Accessed Data

LRU cache layer with webhook-driven invalidation. Cache product data for 5 minutes, then clear on `products/update` webhook events.

See [Response Caching](references/response-caching.md) for the complete implementation.

### Step 4: Use Storefront API for Public Queries

The Storefront API has separate rate limits and is designed for high-traffic public storefronts. Uses `LATEST_API_VERSION` from `@shopify/shopify-api`.

See [Storefront API Usage](references/storefront-api-usage.md) for the complete implementation.

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

### Reducing Query Cost on a Product Sync

A product sync job hits THROTTLED errors. Analyze the cost breakdown, reduce `first:` page sizes, and remove unused fields.

See [Query Cost Optimization](references/query-cost-optimization.md) for debug commands and before/after examples.

### Exporting Orders with Bulk Operations

Export 50,000 orders with line items using a bulk operation that bypasses rate limits and returns JSONL results.

See [Bulk Operations](references/bulk-operations.md) for the complete mutation, polling, and download flow.

### Caching Product Data with Webhook Invalidation

Add an LRU cache layer for product queries that auto-invalidates when `products/update` webhook events fire.

See [Response Caching](references/response-caching.md) for the complete caching implementation.

## Resources

- [GraphQL Rate Limits](https://shopify.dev/docs/api/usage/rate-limits#graphql-admin-api-rate-limits)
- [Bulk Operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)
- [Storefront API](https://shopify.dev/docs/api/storefront)
- [Query Cost Debug Header](https://shopify.dev/docs/api/usage/rate-limits#query-cost)
