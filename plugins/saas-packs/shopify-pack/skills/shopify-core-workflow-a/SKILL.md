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

```typescript
// As of 2024-10, productCreate uses ProductCreateInput (not the old ProductInput)
const CREATE_PRODUCT = `
  mutation productCreate($input: ProductCreateInput!) {
    productCreate(product: $input) {
      product {
        id
        title
        handle
        status
        variants(first: 10) {
          edges {
            node {
              id
              title
              price
              sku
              inventoryQuantity
            }
          }
        }
      }
      userErrors {
        field
        message
        code
      }
    }
  }
`;

const response = await client.request(CREATE_PRODUCT, {
  variables: {
    input: {
      title: "Premium Cotton T-Shirt",
      descriptionHtml: "<p>Soft 100% organic cotton tee.</p>",
      vendor: "My Brand",
      productType: "Apparel",
      tags: ["cotton", "organic", "summer"],
      status: "DRAFT", // ACTIVE, DRAFT, or ARCHIVED
      productOptions: [
        {
          name: "Size",
          values: [{ name: "S" }, { name: "M" }, { name: "L" }, { name: "XL" }],
        },
        {
          name: "Color",
          values: [{ name: "Black" }, { name: "White" }, { name: "Navy" }],
        },
      ],
    },
  },
});

// ALWAYS check userErrors — Shopify returns 200 even on validation failures
if (response.data.productCreate.userErrors.length > 0) {
  console.error("Validation errors:", response.data.productCreate.userErrors);
  // Example: [{ field: ["title"], message: "Title can't be blank", code: "BLANK" }]
}
```

### Step 2: Update a Product

```typescript
// 2024-10+: productUpdate uses ProductUpdateInput (separate from create)
const UPDATE_PRODUCT = `
  mutation productUpdate($input: ProductUpdateInput!) {
    productUpdate(product: $input) {
      product {
        id
        title
        status
        updatedAt
      }
      userErrors {
        field
        message
      }
    }
  }
`;

await client.request(UPDATE_PRODUCT, {
  variables: {
    input: {
      id: "gid://shopify/Product/1234567890",
      title: "Updated Product Title",
      status: "ACTIVE",
      metafields: [
        {
          namespace: "custom",
          key: "care_instructions",
          value: "Machine wash cold",
          type: "single_line_text_field",
        },
      ],
    },
  },
});
```

### Step 3: Query Products with Filtering

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

### Step 4: Manage Variants and Pricing

```typescript
// Create variants in bulk
const BULK_CREATE_VARIANTS = `
  mutation productVariantsBulkCreate(
    $productId: ID!,
    $variants: [ProductVariantsBulkInput!]!
  ) {
    productVariantsBulkCreate(productId: $productId, variants: $variants) {
      productVariants {
        id
        title
        price
        sku
        barcode
        inventoryQuantity
        selectedOptions { name value }
      }
      userErrors {
        field
        message
        code
      }
    }
  }
`;

await client.request(BULK_CREATE_VARIANTS, {
  variables: {
    productId: "gid://shopify/Product/1234567890",
    variants: [
      {
        price: "29.99",
        sku: "TSH-BLK-S",
        barcode: "1234567890123",
        optionValues: [
          { optionName: "Color", name: "Black" },
          { optionName: "Size", name: "S" },
        ],
        inventoryQuantities: [
          {
            availableQuantity: 100,
            locationId: "gid://shopify/Location/1234",
          },
        ],
      },
    ],
  },
});
```

### Step 5: Manage Collections

```typescript
// Create a smart (automated) collection
const CREATE_SMART_COLLECTION = `
  mutation collectionCreate($input: CollectionInput!) {
    collectionCreate(input: $input) {
      collection {
        id
        title
        handle
        productsCount
        ruleSet {
          appliedDisjunctively
          rules { column relation condition }
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(CREATE_SMART_COLLECTION, {
  variables: {
    input: {
      title: "Summer Sale",
      descriptionHtml: "<p>All items on summer sale</p>",
      ruleSet: {
        appliedDisjunctively: false, // AND logic
        rules: [
          { column: "TAG", relation: "EQUALS", condition: "sale" },
          { column: "PRODUCT_TYPE", relation: "EQUALS", condition: "Apparel" },
        ],
      },
    },
  },
});
```

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
| `Product not found` | Wrong GID format | Must be `gid://shopify/Product/{numeric_id}` |

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

## Next Steps

For order management workflow, see `shopify-core-workflow-b`.
