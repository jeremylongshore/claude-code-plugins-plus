---
name: shopify-hello-world
description: |
  Create a minimal working Shopify app that queries products via GraphQL Admin API.
  Use when starting a new Shopify integration, testing your setup,
  or learning basic Shopify API patterns.
  Trigger with phrases like "shopify hello world", "shopify example",
  "shopify quick start", "simple shopify app", "first shopify API call".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Hello World

## Overview

Minimal working example: query your store's products using the Shopify GraphQL Admin API. Uses `@shopify/shopify-api` with a custom app access token for zero-friction setup.

## Prerequisites

- Completed `shopify-install-auth` setup
- A Shopify development store
- An Admin API access token (`shpat_xxx`) from Settings > Apps > Develop apps

## Instructions

### Step 1: Create Project

```bash
mkdir shopify-hello-world && cd shopify-hello-world
npm init -y
npm install @shopify/shopify-api dotenv
```

### Step 2: Configure Environment

```bash
# .env
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
```

### Step 3: Write the Hello World Script

```typescript
// hello-shopify.ts
import "@shopify/shopify-api/adapters/node";
import { shopifyApi } from "@shopify/shopify-api";
import "dotenv/config";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: "localhost",
  apiVersion: "2024-10",
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!,
});

async function main() {
  const session = shopify.session.customAppSession(
    process.env.SHOPIFY_STORE!
  );

  const client = new shopify.clients.Graphql({ session });

  // Query shop info
  const shopInfo = await client.request(`{
    shop {
      name
      currencyCode
      primaryDomain { url }
    }
  }`);
  console.log("Store:", shopInfo.data.shop.name);
  console.log("Currency:", shopInfo.data.shop.currencyCode);

  // Query first 5 products
  const products = await client.request(`{
    products(first: 5) {
      edges {
        node {
          id
          title
          status
          totalInventory
          variants(first: 3) {
            edges {
              node {
                title
                price
                sku
                inventoryQuantity
              }
            }
          }
        }
      }
    }
  }`);

  console.log("\nProducts:");
  for (const edge of products.data.products.edges) {
    const p = edge.node;
    console.log(`  - ${p.title} (${p.status}, ${p.totalInventory} in stock)`);
    for (const v of p.variants.edges) {
      console.log(`      Variant: ${v.node.title} — $${v.node.price} (SKU: ${v.node.sku})`);
    }
  }

  console.log("\nSuccess! Your Shopify connection is working.");
}

main().catch((err) => {
  console.error("Failed:", err.message);
  if (err.response) {
    console.error("Response:", JSON.stringify(err.response.body, null, 2));
  }
  process.exit(1);
});
```

### Step 4: Run It

```bash
npx tsx hello-shopify.ts
# Or compile first:
npx tsc hello-shopify.ts && node hello-shopify.js
```

## Output

Expected console output:

```
Store: My Dev Store
Currency: USD

Products:
  - Classic T-Shirt (ACTIVE, 150 in stock)
      Variant: Small — $29.99 (SKU: TSH-SM)
      Variant: Medium — $29.99 (SKU: TSH-MD)
      Variant: Large — $29.99 (SKU: TSH-LG)
  - Coffee Mug (ACTIVE, 42 in stock)
      Variant: Default Title — $14.99 (SKU: MUG-01)

Success! Your Shopify connection is working.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `HttpResponseError: 401 Unauthorized` | Invalid or revoked access token | Regenerate token in Shopify admin > Settings > Apps |
| `HttpResponseError: 403 Forbidden` | Token lacks required scopes | Enable `read_products` scope in app config |
| `HttpResponseError: 404 Not Found` | Wrong store domain or API version | Verify store URL is `*.myshopify.com` |
| `ENOTFOUND your-store.myshopify.com` | Store domain typo or DNS issue | Double-check `SHOPIFY_STORE` value |
| `GraphqlQueryError` with `userErrors` | Invalid query syntax | Check field names against API version docs |
| `MODULE_NOT_FOUND @shopify/shopify-api` | Package not installed | Run `npm install @shopify/shopify-api` |

## Examples

### Create a Product via GraphQL Mutation

```typescript
const response = await client.request(`
  mutation productCreate($input: ProductCreateInput!) {
    productCreate(product: $input) {
      product {
        id
        title
        handle
      }
      userErrors {
        field
        message
      }
    }
  }
`, {
  variables: {
    input: {
      title: "Hello World Product",
      descriptionHtml: "<p>Created via Shopify API</p>",
      vendor: "My App",
      productType: "Test",
      tags: ["api-created", "hello-world"],
    },
  },
});

if (response.data.productCreate.userErrors.length > 0) {
  console.error("Errors:", response.data.productCreate.userErrors);
} else {
  console.log("Created:", response.data.productCreate.product.title);
}
```

### REST Admin API (Legacy but Still Supported)

```typescript
const restClient = new shopify.clients.Rest({ session });

// GET /admin/api/2024-10/products.json
const { body } = await restClient.get({
  path: "products",
  query: { limit: 5, status: "active" },
});

console.log("Products:", body.products.map((p: any) => p.title));
```

## Resources

- [Shopify GraphQL Admin API Reference](https://shopify.dev/docs/api/admin-graphql/latest)
- [Getting Started with GraphQL](https://shopify.dev/docs/apps/build/graphql/basics/queries)
- [REST Admin API Reference](https://shopify.dev/docs/api/admin-rest)
- [Shopify API Versioning](https://shopify.dev/docs/api/usage/versioning)

## Next Steps

Proceed to `shopify-local-dev-loop` for development workflow setup.
