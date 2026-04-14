---
name: shopify-graphql-cost-optimizer
description: |
  Master Shopify's calculated query cost system to avoid throttling.
  Use when hitting THROTTLED errors, optimizing GraphQL queries,
  or deciding when to use bulk operations instead.
  Trigger with phrases like "shopify query cost", "shopify graphql cost",
  "shopify rate limit graphql", "shopify throttled", "shopify bulk operations".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify GraphQL Cost Optimizer

## Overview

Every Shopify GraphQL query has a calculated cost. The API uses a token bucket (1,000 points max, refills at 50/second for standard plans) and throttles once depleted. The key insight: `requestedQueryCost` is the worst-case estimate, while `actualQueryCost` is what you really paid. Understanding the gap between them is how you avoid throttling.

## Prerequisites

- Shopify app with GraphQL Admin API access
- `@shopify/shopify-api` package installed
- Understanding of GraphQL connections (edges/node pattern)

## Instructions

### Step 1: Read Cost Headers

Every GraphQL response includes cost data in `extensions.cost`:

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

Add the `X-GraphQL-Cost-Include-Fields: true` request header for a per-field cost breakdown.

### Step 2: Predict Query Cost

Cost rules for calculation:

- **Single object field**: 1 point (e.g., `shop { name }` = 1)
- **Connection**: `first` or `last` param multiplied by child cost, plus 2 for the connection itself
- **Nested connections**: costs multiply

```graphql
# Example: products(first: 10) { edges { node { title variants(first: 5) { edges { node { price } } } } } }
# Cost = 2 (products connection) + 10 * (1 (title) + 2 (variants connection) + 5 * 1 (price))
# = 2 + 10 * (1 + 2 + 5) = 2 + 80 = 82 requestedQueryCost
```

See [references/cost-calculation-rules.md](references/cost-calculation-rules.md) for the full calculation rules.

### Step 3: Cost Reduction Techniques

**Reduce `first` parameter** — the single biggest lever:

```graphql
# BAD: 250 * nested cost = massive
products(first: 250) { ... }

# GOOD: paginate with smaller pages
products(first: 25, after: $cursor) { ... }
```

**Select only needed fields** — every field costs 1 point per connection node:

```graphql
# BAD: 10 fields * 50 products = 500+ points
products(first: 50) { edges { node { id title description vendor tags status productType totalInventory createdAt updatedAt } } }

# GOOD: 3 fields * 50 products = ~152 points
products(first: 50) { edges { node { id title status } } }
```

**Avoid deep nesting** — flatten or split queries. See [references/query-splitting.md](references/query-splitting.md) for patterns.

### Step 4: Use Bulk Operations for Large Data Sets

When you need 250+ items, switch to `bulkOperationRunQuery`. It bypasses the cost system entirely — no `first`/`last` params, no cursors, returns all items as JSONL.

See [references/bulk-operations.md](references/bulk-operations.md) for the complete `bulkOperationRunQuery` mutation, polling, and JSONL download flow.

## Output

- Query cost visible in every response via `extensions.cost`
- Queries optimized below 200 points each
- Bulk operations configured for large data exports
- Per-field cost breakdown available for debugging

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `THROTTLED` | Bucket depleted (0 points available) | Wait for `restoreRate` to refill, then retry |
| `MAX_COST_EXCEEDED` | Single query exceeds 1,000 points | Reduce `first` params or split into multiple queries |
| `QUERY_TOO_COMPLEX` | Too many nested connections (depth > 3) | Flatten query, fetch nested data separately |
| `BULK_OPERATION_FAILED` | Bulk query syntax error or timeout | Check `errorCode` on the bulk operation object |
| `BULK_OPERATION_ALREADY_RUNNING` | Only one bulk op per app per store | Poll current operation status before starting new one |

## Examples

### Calculating Cost for a Nested Product Query

Predict the cost of a query that fetches products with variants and metafields before running it, to avoid unexpected THROTTLED errors.

See [Cost Calculation Rules](references/cost-calculation-rules.md) for the full calculation formula and worked examples.

### Splitting an Expensive Query

A single query exceeds 1,000 points due to deep nesting. Break it into multiple cheaper queries that stay well under the limit.

See [Query Splitting](references/query-splitting.md) for patterns to flatten and separate expensive queries.

### Exporting a Full Product Catalog

You need all 10,000+ products with variants. Switch from paginated queries to a bulk operation that bypasses the cost system entirely.

See [Bulk Operations](references/bulk-operations.md) for the complete mutation, polling, and JSONL download flow.

## Resources

- [GraphQL Rate Limits](https://shopify.dev/docs/api/usage/rate-limits#graphql-admin-api-rate-limits)
- [Calculated Query Cost](https://shopify.dev/docs/api/usage/rate-limits#calculated-query-cost)
- [Bulk Operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)
- [Query Cost Debugging](https://shopify.dev/docs/api/usage/rate-limits#debugging-query-cost)
