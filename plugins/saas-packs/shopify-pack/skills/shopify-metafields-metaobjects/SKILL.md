---
name: shopify-metafields-metaobjects
description: |
  Model custom data with Shopify metafields and metaobjects via the GraphQL Admin API.
  Use when adding custom fields to products/orders, creating custom content types,
  or building structured data models beyond Shopify's default schema.
  Trigger with phrases like "shopify metafields", "shopify metaobjects",
  "custom data shopify", "shopify custom fields", "metafield definition".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Metafields & Metaobjects

## Overview

Metafields attach key-value custom data to existing resources (products, variants, orders, customers). Metaobjects define entirely new content types with custom schemas. Together they replace the need for external databases for most custom data needs.

## Prerequisites

- Completed `shopify-install-auth` setup
- Access scopes: `read_metaobjects`, `write_metaobjects`, `read_metaobject_definitions`, `write_metaobject_definitions`
- Metafield scopes per resource: `read_products`/`write_products` for product metafields, etc.

## Instructions

### Step 1: Define a Metafield on Products

Use `metafieldDefinitionCreate` with `namespace`, `key`, `type`, and `ownerType`:

```typescript
await client.request(METAFIELD_DEFINITION_CREATE, {
  variables: {
    definition: {
      namespace: "custom",
      key: "care_instructions",
      name: "Care Instructions",
      type: "multi_line_text_field",  // See references/metafield-types.md
      ownerType: "PRODUCT",
      pin: true, // Show in admin UI
    },
  },
});
// Always check userErrors — Shopify returns 200 even on validation failures
```

### Step 2: Set Values in Batch with metafieldsSet

```typescript
await client.request(METAFIELDS_SET, {
  variables: {
    metafields: [
      {
        ownerId: "gid://shopify/Product/123456",
        namespace: "custom",
        key: "care_instructions",
        value: "Machine wash cold.\nTumble dry low.",
        type: "multi_line_text_field",
      },
      // Up to 25 metafields per call
    ],
  },
});
```

### Step 3: Create a Metaobject Definition

Define a custom content type (e.g., "Designer" with typed fields):

```typescript
await client.request(METAOBJECT_DEFINITION_CREATE, {
  variables: {
    definition: {
      type: "$app:designer",
      displayNameKey: "name",
      fieldDefinitions: [
        { key: "name", name: "Name", type: "single_line_text_field" },
        { key: "bio", name: "Bio", type: "multi_line_text_field" },
        { key: "photo", name: "Photo", type: "file_reference" },
      ],
      access: { storefront: "PUBLIC_READ" },
    },
  },
});
```

### Step 4: Create Metaobject Instances

```typescript
await client.request(METAOBJECT_CREATE, {
  variables: {
    metaobject: {
      type: "$app:designer",
      handle: "jane-doe",
      fields: [
        { key: "name", value: "Jane Doe" },
        { key: "bio", value: "Award-winning textile designer." },
      ],
    },
  },
});
```

See [metafield-types.md](references/metafield-types.md) for all types, [toml-config.md](references/toml-config.md) for app config, and [bulk-metafield-ops.md](references/bulk-metafield-ops.md) for bulk operations.

## Output

- Metafield definitions registered on target resource types
- Metafield values set on individual resources (batch supported, max 25 per call)
- Custom metaobject types with typed field schemas
- Metaobject instances queryable via Storefront and Admin APIs

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `TAKEN` | Namespace + key already exists on this owner type | Use `metafieldDefinitionUpdate` or choose a different key |
| `INVALID_TYPE` | Type string not in Shopify's registry | Check [metafield-types.md](references/metafield-types.md) |
| `INVALID_VALUE` | Value doesn't match declared type | Cast value to correct format before setting |
| `TOO_LONG` | Value exceeds type limit (512KB for text types) | Truncate or switch to `multi_line_text_field` |

## Examples

### Adding Care Instructions to All Products

Define a "care_instructions" metafield on the PRODUCT owner type, then bulk-set values across hundreds of products in batches of 25.

See [Bulk Metafield Ops](references/bulk-metafield-ops.md) for the batch set/delete operations.

### Choosing the Right Metafield Type

You need to store a color swatch, a date range, or a product reference. Pick the correct type from Shopify's type registry.

See [Metafield Types](references/metafield-types.md) for the complete type list with value format examples.

### Declaring Metafields in App Configuration

Define metafield and metaobject schemas in `shopify.app.toml` so they deploy automatically with the app instead of making API calls.

See [TOML Config](references/toml-config.md) for the app configuration syntax.

## Resources

- [Metafield Definition API](https://shopify.dev/docs/api/admin-graphql/latest/mutations/metafieldDefinitionCreate)
- [metafieldsSet Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/metafieldsSet)
- [Metaobject API Guide](https://shopify.dev/docs/apps/build/custom-data/metaobjects)
- [Metafield Types Reference](https://shopify.dev/docs/apps/build/custom-data/metafields/types)
