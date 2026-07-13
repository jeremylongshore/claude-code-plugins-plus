# Storefront API Access

The Storefront API uses a different token (generated in admin) and has its own rate limits separate from the Admin API.

```typescript
// Storefront API uses a different token — generated in admin
const storefrontClient = new shopify.clients.Storefront({
  session,
  apiVersion: LATEST_API_VERSION,
});

const products = await storefrontClient.request(`{
  products(first: 10) {
    edges {
      node {
        id
        title
        handle
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
        }
      }
    }
  }
}`);
```
