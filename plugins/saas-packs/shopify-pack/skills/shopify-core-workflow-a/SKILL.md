---
name: shopify-core-workflow-a
description: |
  Manage Shopify products, variants, and collections using the GraphQL Admin API.
  Use when creating, updating, or querying products, managing inventory,
  or building product catalog integrations.
  Trigger with phrases like "shopify products", "create shopify product",
  "shopify variants", "shopify collections", "shopify inventory".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Products & Catalog Management

## Overview

Primary workflow for Shopify: manage products, variants, collections, and inventory using the GraphQL Admin API. Covers CRUD operations with real API mutations and response shapes.

## Prerequisites

- Completed `shopify-install-auth` setup
- Access scopes: `read_products`, `write_products`, `read_inventory`, `write_inventory`
- API version 2024-10 or later (ProductInput was split in this version)

## Instructions

### Step 1: Create a Product

Use `productCreate` with `ProductCreateInput` (as of 2024-10, this replaced the old unified `ProductInput`). Always check `userErrors` -- Shopify returns 200 even on validation failures.

See [Product Create Mutation](references/product-create-mutation.md) for the complete mutation, variables, and error handling.

### Step 2: Update a Product

Use `productUpdate` with `ProductUpdateInput` (separate from create as of 2024-10). Supports metafield updates inline.

See [Product Update Mutation](references/product-update-mutation.md) for the complete mutation and variables.

### Step 3: Query Products with Filtering

Search products using Shopify's query syntax (`status:active`, `product_type:Apparel AND vendor:'My Brand'`, `tag:sale`, etc.) with cursor-based pagination.

See [Search Products Query](references/search-products-query.md) for the complete query with pagination and query syntax examples.

### Step 4: Manage Variants and Pricing

Create variants in bulk with `productVariantsBulkCreate`, including pricing, SKU, barcode, option values, and inventory quantities per location.

See [Bulk Create Variants](references/bulk-create-variants.md) for the complete mutation and variables.

### Step 5: Manage Collections

Create smart (automated) collections with rule-based product matching using tag, product type, and other column filters.

See [Smart Collection Create](references/smart-collection-create.md) for the complete mutation and variables.

## Output

- Product created with variants and options
- Products queryable with search filters
- Variant pricing and inventory configured
- Smart collections auto-organizing products

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `userErrors: [{code: "TAKEN", field: ["handle"]}]` | Duplicate product handle | Use a unique handle or let Shopify auto-generate |
| `userErrors: [{code: "BLANK", field: ["title"]}]` | Empty required field | Provide non-empty title |
| `userErrors: [{code: "INVALID"}]` | Invalid metafield type | Check `type` matches Shopify's metafield types |
| `Access denied` on `productCreate` | Missing `write_products` scope | Request scope in app config |
| `Product not found` | Wrong GID format | Must be `gid://shopify/Product/1234567890` (numeric ID) |

## Examples

### ProductSet Mutation (Upsert)

```typescript
// productSet creates OR updates — idempotent by handle
const PRODUCT_SET = `
  mutation productSet($input: ProductSetInput!) {
    productSet(input: $input) {
      product { id title }
      userErrors { field message code }
    }
  }
`;

await client.request(PRODUCT_SET, {
  variables: {
    input: {
      title: "Organic Coffee Beans",
      handle: "organic-coffee-beans", // unique identifier
      productType: "Coffee",
      vendor: "Bean Co",
    },
  },
});
```

## Resources

- [productCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productCreate)
- [productSet Mutation (Upsert)](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productSet)
- [Product Object](https://shopify.dev/docs/api/admin-graphql/latest/objects/Product)
- [2024-10 ProductInput Split](https://shopify.dev/docs/api/release-notes/2024-10)
