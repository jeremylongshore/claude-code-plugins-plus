# Query Cost Optimization

Before-and-after examples of GraphQL query cost reduction through field selection and page size tuning.

### Debug Query Cost

```bash
# Debug query cost with special header
curl -X POST "https://$STORE/admin/api/2025-04/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{"query": "{ products(first: 50) { edges { node { id title variants(first: 20) { edges { node { id price } } } } } } }"}' \
  | jq '.extensions.cost'
```

Use a recent stable version (e.g., 2025-04) in the API URL. Response shows cost breakdown:

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

### Before vs After

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

**Key rule:** `requestedQueryCost` is calculated as `first * nested_fields`. Reducing `first:` from 250 to 50 can cut cost by 5x.
