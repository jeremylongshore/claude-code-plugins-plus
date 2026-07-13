# Storefront API for Public Queries

The Storefront API has separate rate limits and is designed for high-traffic public storefronts. Safe for client-side use.

```typescript
import { LATEST_API_VERSION } from "@shopify/shopify-api";

// Storefront API — safe for client-side, higher rate limits
const storefrontClient = new shopify.clients.Storefront({
  session,
  apiVersion: LATEST_API_VERSION,
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
