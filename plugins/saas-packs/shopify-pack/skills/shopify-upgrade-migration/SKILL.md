---
name: shopify-upgrade-migration
description: |
  Upgrade Shopify API versions and migrate from REST to GraphQL with breaking change detection.
  Use when upgrading API versions, migrating from deprecated REST endpoints,
  or handling Shopify's quarterly API release cycle.
  Trigger with phrases like "upgrade shopify", "shopify API version",
  "shopify breaking changes", "migrate REST to GraphQL", "shopify deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Upgrade & Migration

## Overview

Guide for upgrading Shopify API versions (quarterly releases) and migrating from the legacy REST Admin API to the GraphQL Admin API. REST was deprecated as a legacy API on October 1, 2024.

## Prerequisites

- Current Shopify API version identified
- Git for version control
- Test suite available
- Access to Shopify release notes

## Instructions

### Step 1: Check Current Version and Available Versions

```bash
# Check what API version you're using in code
grep -r "apiVersion" src/ --include="*.ts" --include="*.js"
grep -r "api_version" . --include="*.toml"

# Check what versions the store supports
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" \
  | jq '.supported_versions[] | {handle, display_name, supported, latest}'
```

Shopify releases quarterly: `2024-01`, `2024-04`, `2024-07`, `2024-10`. Versions are supported for ~12 months after release.

### Step 2: Review Breaking Changes

Key breaking changes by version:

| Version | Breaking Change | Migration |
|---------|----------------|-----------|
| 2024-10 | `ProductInput` split into `ProductCreateInput` + `ProductUpdateInput` | Update mutations to use separate types |
| 2024-10 | REST declared legacy | Migrate to GraphQL Admin API |
| 2024-07 | `InventoryItem.unitCost` removed | Use `InventoryItem.unitCost` on `InventoryLevel` |
| 2024-04 | Cart warnings replace inventory userErrors (Storefront) | Update cart error handling |
| 2025-01 | New public apps must use GraphQL only | No REST for new public apps |

### Step 3: Migrate REST to GraphQL

```typescript
// BEFORE: REST Admin API
const restClient = new shopify.clients.Rest({ session });
const { body } = await restClient.get({
  path: "products",
  query: { limit: 50, status: "active" },
});
const products = body.products;

// AFTER: GraphQL Admin API
const graphqlClient = new shopify.clients.Graphql({ session });
const response = await graphqlClient.request(`{
  products(first: 50, query: "status:active") {
    edges {
      node {
        id
        title
        status
        variants(first: 10) {
          edges { node { id price sku } }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}`);
const products = response.data.products.edges.map((e: any) => e.node);
```

Common REST-to-GraphQL mappings:

| REST Endpoint | GraphQL Query/Mutation |
|--------------|----------------------|
| `GET /products.json` | `query { products(first: N) { edges { node { ... } } } }` |
| `POST /products.json` | `mutation { productCreate(product: $input) { ... } }` |
| `PUT /products/{id}.json` | `mutation { productUpdate(product: $input) { ... } }` |
| `GET /orders.json` | `query { orders(first: N) { edges { node { ... } } } }` |
| `GET /customers/{id}.json` | `query { customer(id: $id) { ... } }` |
| `POST /webhooks.json` | `mutation { webhookSubscriptionCreate(...) { ... } }` |

### Step 4: Update API Version in Config

```typescript
// src/shopify.ts — update the version
const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: "2024-10", // <-- update this
  // ...
});
```

```toml
# shopify.app.toml
[webhooks]
api_version = "2024-10"  # Update here too
```

### Step 5: Handle the ProductInput Split (2024-10)

```typescript
// BEFORE (pre-2024-10): single ProductInput for create AND update
const OLD_CREATE = `
  mutation($input: ProductInput!) {
    productCreate(input: $input) { ... }
  }
`;

// AFTER (2024-10+): separate types
const NEW_CREATE = `
  mutation($input: ProductCreateInput!) {
    productCreate(product: $input) {
      product { id title }
      userErrors { field message }
    }
  }
`;

const NEW_UPDATE = `
  mutation($input: ProductUpdateInput!) {
    productUpdate(product: $input) {
      product { id title }
      userErrors { field message }
    }
  }
`;
```

## Output

- API version updated across all config files
- REST endpoints migrated to GraphQL equivalents
- Breaking changes addressed
- Test suite passing on new version

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `API version unsupported` | Version too old | Check supported versions endpoint |
| `Field not found in type` | Field renamed/removed in new version | Check release notes for migration |
| `ProductInput is not defined` | Using old type on 2024-10+ | Use `ProductCreateInput` / `ProductUpdateInput` |
| `REST API 410 Gone` | Endpoint removed | Migrate to GraphQL equivalent |

## Examples

### API Version Upgrade Script

```bash
#!/bin/bash
OLD_VERSION="2024-04"
NEW_VERSION="2024-10"

echo "Upgrading Shopify API from $OLD_VERSION to $NEW_VERSION"

# Find all files referencing old version
echo "Files to update:"
grep -rn "$OLD_VERSION" . --include="*.ts" --include="*.js" --include="*.toml" --include="*.json"

# Replace (review diff before committing)
find . -type f \( -name "*.ts" -o -name "*.js" -o -name "*.toml" \) \
  -exec sed -i "s/$OLD_VERSION/$NEW_VERSION/g" {} +

echo "Updated. Run tests: npm test"
```

### Deprecation Monitor

```typescript
// Log deprecation warnings from Shopify response headers
function checkDeprecationHeaders(headers: Headers): void {
  const sunset = headers.get("x-shopify-api-deprecated-reason");
  if (sunset) {
    console.warn(`[SHOPIFY DEPRECATION] ${sunset}`);
    // Alert your team
  }
}
```

## Resources

- [Shopify API Release Notes](https://shopify.dev/docs/api/release-notes)
- [2024-10 Release Notes](https://shopify.dev/docs/api/release-notes/2024-10)
- [Migrate REST to GraphQL](https://shopify.dev/docs/apps/build/graphql/migrate/learn-how)
- [API Versioning Guide](https://shopify.dev/docs/api/usage/versioning)

## Next Steps

For CI integration during upgrades, see `shopify-ci-integration`.
