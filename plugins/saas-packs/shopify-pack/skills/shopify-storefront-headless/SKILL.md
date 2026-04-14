---
name: shopify-storefront-headless
description: |
  Build headless storefronts with Shopify's Storefront API and Cart API.
  Use when building custom frontends, setting up Hydrogen, querying products
  for customer-facing apps, or managing cart operations programmatically.
  Trigger with phrases like "shopify headless", "shopify storefront api",
  "shopify hydrogen", "shopify cart api", "headless commerce shopify".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Storefront & Headless Commerce

## Overview

The Storefront API is Shopify's public-facing GraphQL API for customer experiences. Unlike the Admin API (server-side, privileged), it uses a public access token safe for client-side code. Paired with the Cart API, it powers headless storefronts, mobile apps, and custom buying experiences.

## Prerequisites

- Shopify store with a Storefront API access token (Headless channel or custom app)
- For Hydrogen: Node.js 18+ and Shopify CLI 3.x+
- Storefront API scopes: `unauthenticated_read_products`, `unauthenticated_read_collections`

## Instructions

### Step 1: Storefront API Client Setup

```typescript
import { createStorefrontApiClient } from "@shopify/storefront-api-client";

const client = createStorefrontApiClient({
  storeDomain: "my-store.myshopify.com",
  apiVersion: LATEST_API_VERSION,
  publicAccessToken: "your-storefront-public-token", // Safe in browser
});
```

### Step 2: Cart Operations

```typescript
const { data } = await client.request(CART_CREATE, {
  variables: {
    input: {
      lines: [{ merchandiseId: "gid://shopify/ProductVariant/123", quantity: 2 }],
      buyerIdentity: { email: "customer@example.com", countryCode: "US" },
    },
  },
});
// Redirect to data.cartCreate.cart.checkoutUrl to complete purchase
```

Full cart mutations (`cartLinesAdd`, `cartLinesUpdate`, `cartLinesRemove`, `cartDiscountCodesUpdate`) in [cart-api.md](references/cart-api.md).

### Step 3: Query Products (Storefront Schema)

```typescript
// Storefront API schema differs from Admin API — field names are NOT the same
const { data } = await client.request(`
  query { products(first: 10) { edges { node {
    id title handle availableForSale
    priceRange { minVariantPrice { amount currencyCode } }
    variants(first: 5) { edges { node {
      id title availableForSale
      price { amount currencyCode }  // MoneyV2 object, not a string
      selectedOptions { name value }
    }}}
  }}}}
`);
```

### Step 4: Storefront vs Admin API Decision Guide

| Concern | Storefront API | Admin API |
|---------|---------------|-----------|
| Token type | Public (safe in browser) | Private (server-only) |
| Rate limiting | Request-based | Query cost-based (1000 pts/sec) |
| Cart/Checkout | Full cart + checkout URL | No cart operations |
| Product data | Customer-facing fields only | Full data + inventory |
| Mutations | Cart, customer, checkout | Full CRUD on all resources |

Detailed comparison in [storefront-vs-admin.md](references/storefront-vs-admin.md). Hydrogen framework setup in [hydrogen-patterns.md](references/hydrogen-patterns.md).

## Output

- Storefront API client configured with public access token
- Cart created with line items and checkout URL
- Product catalog queryable from client-side code
- Clear separation of Storefront (public) vs Admin (privileged) API usage

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_STOREFRONT_ACCESS_TOKEN` | Token missing, expired, or wrong store | Regenerate in Shopify admin under Headless channel |
| `THROTTLED` | Exceeded request rate limit | Retry with backoff; cache product data |
| `PRODUCT_NOT_AVAILABLE` | Product not published to Headless channel | Publish product to the Headless sales channel |
| `CART_DOES_NOT_EXIST` | Cart ID expired (10-day inactivity) | Create a new cart; don't persist IDs long-term |

## Examples

### Building a Custom Cart Experience

Create a cart, add line items, apply discount codes, and redirect to Shopify's hosted checkout using the Storefront Cart API.

See [Cart API](references/cart-api.md) for the complete cart lifecycle mutations and response shapes.

### Scaffolding a Hydrogen Storefront

Set up a new Hydrogen project with Remix loaders, Storefront client configuration, and server-side product queries.

See [Hydrogen Patterns](references/hydrogen-patterns.md) for the framework setup and loader patterns.

### Choosing Between Storefront and Admin APIs

Decide which API to use based on token type, rate limiting model, available mutations, and data access scope.

See [Storefront vs Admin](references/storefront-vs-admin.md) for the detailed comparison.

## Resources

- [Storefront API Reference](https://shopify.dev/docs/api/storefront)
- [Cart API Guide](https://shopify.dev/docs/storefronts/headless/building-with-the-storefront-api/cart)
- [Hydrogen Framework](https://shopify.dev/docs/storefronts/hydrogen)
- [Storefront API Authentication](https://shopify.dev/docs/api/storefront#authentication)
