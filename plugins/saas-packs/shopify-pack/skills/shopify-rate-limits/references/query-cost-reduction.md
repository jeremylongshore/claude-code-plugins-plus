# Query Cost Reduction Examples

Before-and-after examples showing how to reduce GraphQL query cost through field pruning and page size limits.

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

### Debug Query Cost

```bash
# Add this header to see cost breakdown per field
curl -X POST "https://store.myshopify.com/admin/api/2025-04/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{"query": "{ products(first: 10) { edges { node { id title } } } }"}' \
  | jq '.extensions.cost'
```

Use a recent stable version (e.g., 2025-04) in the API URL.
