Product search query with Shopify query syntax, pagination, and price/image data.

```typescript
// Search products with Shopify's query syntax
const SEARCH_PRODUCTS = `
  query products($query: String!, $first: Int!, $after: String) {
    products(first: $first, after: $after, query: $query) {
      edges {
        node {
          id
          title
          handle
          status
          productType
          vendor
          totalInventory
          priceRangeV2 {
            minVariantPrice { amount currencyCode }
            maxVariantPrice { amount currencyCode }
          }
          images(first: 1) {
            edges {
              node { url altText }
            }
          }
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

// Shopify query syntax examples:
// "status:active"
// "product_type:Apparel AND vendor:'My Brand'"
// "inventory_total:>0"
// "created_at:>2024-01-01"
// "tag:sale"
const data = await client.request(SEARCH_PRODUCTS, {
  variables: {
    query: "status:active AND product_type:Apparel",
    first: 25,
  },
});
```
