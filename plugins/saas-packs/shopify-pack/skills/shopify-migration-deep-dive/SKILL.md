---
name: shopify-migration-deep-dive
description: |
  Migrate e-commerce data to Shopify using bulk operations, product imports,
  and the strangler fig pattern for gradual platform migration.
  Use when replatforming to Shopify, importing product catalogs, or migrating customer and order data from another e-commerce system.
  Trigger with phrases like "migrate to shopify", "shopify data migration",
  "import products shopify", "shopify replatform", "move to shopify".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Migration Deep Dive

## Overview

Migrate product catalogs, customers, and orders to Shopify using the GraphQL Admin API bulk mutations, CSV imports, and incremental migration patterns.

## Prerequisites

- Source platform data exported (CSV, JSON, or API access)
- Shopify store with appropriate access scopes
- Scopes needed: `write_products`, `write_customers`, `write_orders`, `write_inventory`

## Instructions

### Step 1: Assess Migration Scope

| Data Type | Shopify Import Method | Complexity |
|-----------|----------------------|------------|
| Products + variants | `productSet` mutation (upsert) | Low |
| Product images | `productCreateMedia` mutation | Low |
| Customers | Customer CSV import or `customerCreate` | Medium |
| Historical orders | `draftOrderCreate` + `draftOrderComplete` | High |
| Inventory levels | `inventorySetQuantities` mutation | Medium |
| Collections | `collectionCreate` mutation | Low |
| Redirects (URLs) | `urlRedirectCreate` mutation | Low |
| Metafields | Included in product/customer mutations | Medium |

### Step 2: Bulk Product Import with productSet

`productSet` is idempotent — it creates or updates based on `handle`, making it perfect for migrations. Handles variants, metafields, and all product attributes in a single mutation.

See [Product Set Migration](references/product-set-migration.md) for the complete migration function.

### Step 3: Bulk Operations for Large Imports

For importing thousands of products, use Shopify's staged uploads combined with bulk mutation to avoid rate limit issues.

See [Bulk Operations Import](references/bulk-operations-import.md) for the staged upload and bulk mutation workflow.

### Step 4: Set Inventory Levels & URL Redirects

After products are created, set inventory quantities at each location and create URL redirects to preserve SEO from the old platform.

See [Inventory and Redirects](references/inventory-and-redirects.md) for both mutation implementations.

### Step 5: Post-Migration Validation

Automated validation that compares expected source counts against actual Shopify counts for products, customers, and other data types.

See [Post-Migration Validation](references/post-migration-validation.md) for the validation script.

## Output

- Products migrated with variants, images, and metafields
- Inventory levels set at correct locations
- URL redirects preserving SEO
- Migration validated against source counts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TAKEN` on product handle | Duplicate handle | Append suffix or use `productSet` for upsert |
| Rate limited during import | Too many sequential calls | Use bulk operations or add delays |
| Image upload fails | URL not publicly accessible | Use staged uploads for private images |
| Inventory not updating | Wrong `inventoryItemId` | Query variant's `inventoryItem.id` first |

## Examples

### Quick Migration Status

```bash
# Count products in source vs Shopify
echo "Shopify product count:"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ productsCount { count } }"}' \
  "https://$STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/graphql.json" \
  | jq '.data.productsCount.count'
```

## Resources

- [productSet Mutation (Upsert)](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productSet)
- [Bulk Operations Mutations](https://shopify.dev/docs/api/usage/bulk-operations/imports)
- [Inventory Management](https://shopify.dev/docs/apps/build/orders-fulfillment/inventory-management-apps)
- [URL Redirects](https://shopify.dev/docs/api/admin-graphql/latest/mutations/urlRedirectCreate)
