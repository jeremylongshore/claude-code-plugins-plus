---
name: shopify-migration-deep-dive
description: |
  Migrate e-commerce data to Shopify using bulk operations, product imports,
  and the strangler fig pattern for gradual platform migration.
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

`productSet` is idempotent — it creates or updates based on `handle`. Perfect for migrations.

```typescript
const PRODUCT_SET = `
  mutation productSet($input: ProductSetInput!) {
    productSet(input: $input) {
      product {
        id
        title
        handle
        variants(first: 50) {
          edges {
            node { id sku price inventoryQuantity }
          }
        }
      }
      userErrors { field message code }
    }
  }
`;

// Migrate products in batches
async function migrateProducts(sourceProducts: SourceProduct[]): Promise<MigrationResult> {
  const results: MigrationResult = { success: 0, errors: [] };

  for (const product of sourceProducts) {
    try {
      const response = await client.request(PRODUCT_SET, {
        variables: {
          input: {
            title: product.name,
            handle: product.slug, // unique identifier for upsert
            descriptionHtml: product.description,
            vendor: product.brand,
            productType: product.category,
            tags: product.tags,
            status: "DRAFT", // Keep as draft until verified
            variants: product.variants.map((v) => ({
              price: String(v.price),
              sku: v.sku,
              barcode: v.barcode,
              optionValues: v.options.map((opt) => ({
                optionName: opt.name,
                name: opt.value,
              })),
            })),
            metafields: product.metadata?.map((m) => ({
              namespace: "migration",
              key: m.key,
              value: m.value,
              type: "single_line_text_field",
            })),
          },
        },
      });

      if (response.data.productSet.userErrors.length > 0) {
        results.errors.push({
          product: product.name,
          errors: response.data.productSet.userErrors,
        });
      } else {
        results.success++;
      }
    } catch (error) {
      results.errors.push({ product: product.name, errors: [{ message: (error as Error).message }] });
    }

    // Respect rate limits — pause between batches
    await new Promise((r) => setTimeout(r, 200));
  }

  return results;
}
```

### Step 3: Bulk Operations for Large Imports

For importing thousands of products, use Shopify's staged uploads + bulk mutation:

```typescript
// Step 1: Create a staged upload target
const STAGED_UPLOAD = `
  mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
    stagedUploadsCreate(input: $input) {
      stagedTargets {
        url
        resourceUrl
        parameters { name value }
      }
      userErrors { field message }
    }
  }
`;

const uploadTarget = await client.request(STAGED_UPLOAD, {
  variables: {
    input: [{
      resource: "BULK_MUTATION_VARIABLES",
      filename: "products.jsonl",
      mimeType: "text/jsonl",
      httpMethod: "POST",
    }],
  },
});

// Step 2: Upload JSONL file to the staged target
// Each line is the variables for one mutation call
const jsonlContent = products.map((p) =>
  JSON.stringify({ input: { title: p.name, handle: p.slug } })
).join("\n");

// Upload to the staged target URL...

// Step 3: Run bulk mutation
const BULK_MUTATION = `
  mutation bulkOperationRunMutation($mutation: String!, $stagedUploadPath: String!) {
    bulkOperationRunMutation(mutation: $mutation, stagedUploadPath: $stagedUploadPath) {
      bulkOperation { id status }
      userErrors { field message }
    }
  }
`;
```

### Step 4: Set Inventory Levels

```typescript
// After products are created, set inventory quantities
const SET_INVENTORY = `
  mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
    inventorySetQuantities(input: $input) {
      inventoryAdjustmentGroup {
        reason
        changes {
          name
          delta
          quantityAfterChange
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(SET_INVENTORY, {
  variables: {
    input: {
      reason: "correction",
      name: "available",
      quantities: [
        {
          inventoryItemId: "gid://shopify/InventoryItem/12345",
          locationId: "gid://shopify/Location/67890",
          quantity: 100,
        },
      ],
    },
  },
});
```

### Step 5: URL Redirects (SEO Preservation)

```typescript
// Preserve old URLs by creating redirects
const CREATE_REDIRECT = `
  mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
    urlRedirectCreate(urlRedirect: $urlRedirect) {
      urlRedirect { id path target }
      userErrors { field message }
    }
  }
`;

// Map old URLs to new Shopify URLs
for (const redirect of urlMappings) {
  await client.request(CREATE_REDIRECT, {
    variables: {
      urlRedirect: {
        path: redirect.oldPath,     // "/old-product-page"
        target: redirect.newPath,   // "/products/new-handle"
      },
    },
  });
}
```

### Step 6: Post-Migration Validation

```typescript
async function validateMigration(expectedCounts: Record<string, number>): Promise<void> {
  const checks = [
    {
      name: "Products",
      query: "{ productsCount { count } }",
      path: "productsCount.count",
      expected: expectedCounts.products,
    },
    {
      name: "Customers",
      query: "{ customersCount { count } }",
      path: "customersCount.count",
      expected: expectedCounts.customers,
    },
  ];

  for (const check of checks) {
    const response = await client.request(check.query);
    const actual = check.path.split(".").reduce((obj: any, k) => obj[k], response.data);
    const status = actual >= check.expected ? "PASS" : "FAIL";
    console.log(`${status}: ${check.name} — expected ${check.expected}, got ${actual}`);
  }
}
```

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
  "https://$STORE/admin/api/2024-10/graphql.json" \
  | jq '.data.productsCount.count'
```

## Resources

- [productSet Mutation (Upsert)](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productSet)
- [Bulk Operations Mutations](https://shopify.dev/docs/api/usage/bulk-operations/imports)
- [Inventory Management](https://shopify.dev/docs/apps/build/orders-fulfillment/inventory-management-apps)
- [URL Redirects](https://shopify.dev/docs/api/admin-graphql/latest/mutations/urlRedirectCreate)

## Next Steps

For advanced troubleshooting, see `shopify-advanced-troubleshooting`.
