---
name: shopify-sdk-patterns
description: |
  Apply production-ready patterns for @shopify/shopify-api including typed GraphQL clients,
  session management, and retry logic.
  Use when implementing Shopify integrations, refactoring SDK usage,
  or establishing team coding standards for Shopify.
  Trigger with phrases like "shopify SDK patterns", "shopify best practices",
  "shopify code patterns", "idiomatic shopify", "shopify client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify SDK Patterns

## Overview

Production-ready patterns for the `@shopify/shopify-api` library: singleton clients, typed GraphQL operations, session management, cursor-based pagination, codegen-typed operations, bulk operations, and webhook registry patterns.

## Prerequisites

- `@shopify/shopify-api` v9+ installed
- Familiarity with Shopify's GraphQL Admin API
- Understanding of async/await and TypeScript generics

## Instructions

### Step 1: Typed GraphQL Client Wrapper

Initialize a singleton `shopifyApi` instance with `LATEST_API_VERSION`, cache sessions per shop, and expose a typed `shopifyQuery<T>()` helper that wraps `client.request()`.

See [Typed GraphQL Client](references/typed-graphql-client.md) for the complete implementation.

### Step 2: Error Handling with Shopify Error Types

Custom `ShopifyServiceError` class that distinguishes retryable errors (429, 5xx) from permanent ones. Includes `handleShopifyError()` for error translation and `safeShopifyCall()` that returns `{data, error}` tuples instead of throwing.

See [Error Handling](references/error-handling.md) for the complete implementation.

### Step 3: Cursor-Based Pagination

Async generator `paginateShopify<T>()` for Relay-style cursor pagination. Yields batches of nodes, automatically following `pageInfo.endCursor` until `hasNextPage` is false. Memory-efficient for large datasets.

See [Cursor Pagination](references/cursor-pagination.md) for the complete implementation.

### Step 4: Multi-Tenant Client Factory

`ShopifyClientFactory` class for apps installed on multiple stores. Creates isolated `GraphqlClient` instances per merchant with session caching. Includes `removeClient()` for eviction on app uninstall.

See [Multi-Tenant Factory](references/multi-tenant-factory.md) for the complete implementation.

### Step 5: Codegen-Typed Operations

Use `@shopify/api-codegen-preset` to generate TypeScript types from your GraphQL operations. This eliminates manual type definitions and catches schema changes at build time.

```typescript
// codegen.ts — project root config
import { shopifyApiProject, ApiType } from "@shopify/api-codegen-preset";

export default {
  schema: "https://shopify.dev/admin-graphql-direct-proxy",
  documents: ["src/**/*.{ts,tsx}"],
  projects: {
    default: shopifyApiProject({
      apiType: ApiType.Admin,
      apiVersion: "2025-04", // Update quarterly
      outputDir: "./src/types",
    }),
  },
};
```

```typescript
// src/operations/products.ts — typed query with codegen output
import type { ProductsQuery } from "../types/admin.generated";

const PRODUCTS_QUERY = `#graphql
  query Products($first: Int!, $after: String) {
    products(first: $first, after: $after) {
      edges {
        node { id title status totalInventory }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
` as const;

// Return type is fully inferred from codegen
export async function getProducts(shop: string): Promise<ProductsQuery> {
  return shopifyQuery<ProductsQuery>(shop, PRODUCTS_QUERY, { first: 50 });
}
```

Run `npx graphql-codegen` after changing any GraphQL operation or upgrading API versions.

### Step 6: Bulk Operation Helpers

For datasets too large for pagination (100k+ records), use Shopify's Bulk Operations API. It runs a query server-side and produces a JSONL file you download when ready.

```typescript
// src/shopify/bulk.ts
const BULK_QUERY = `
  mutation bulkOperationRunQuery($query: String!) {
    bulkOperationRunQuery(query: $query) {
      bulkOperation { id status }
      userErrors { field message }
    }
  }
`;

const POLL_QUERY = `{
  currentBulkOperation {
    id status errorCode objectCount url
  }
}`;

export async function runBulkOperation(
  shop: string,
  query: string
): Promise<string> {
  // Start the bulk operation
  const { bulkOperationRunQuery } = await shopifyQuery(shop, BULK_QUERY, { query });
  if (bulkOperationRunQuery.userErrors?.length) {
    throw new Error(bulkOperationRunQuery.userErrors[0].message);
  }

  // Poll until complete (typically 1-10 minutes for large datasets)
  let result;
  do {
    await new Promise((r) => setTimeout(r, 5000)); // 5s interval
    result = (await shopifyQuery(shop, POLL_QUERY)).currentBulkOperation;
  } while (result.status === "RUNNING" || result.status === "CREATED");

  if (result.status !== "COMPLETED") {
    throw new Error(`Bulk operation failed: ${result.errorCode}`);
  }

  return result.url; // JSONL download URL
}

// Usage: export all products
const url = await runBulkOperation(shop, `{
  products { edges { node { id title status variants { edges { node { sku price } } } } } }
}`);
const response = await fetch(url);
const jsonl = await response.text();
const products = jsonl.trim().split("\n").map(JSON.parse);
```

### Step 7: Webhook Registry Patterns

Programmatically register webhook subscriptions using `webhookSubscriptionCreate` with typed `WebhookSubscriptionInput`. Supports both HTTP and EventBridge/PubSub endpoints.

```typescript
// src/shopify/webhooks.ts
const REGISTER_WEBHOOK = `
  mutation webhookSubscriptionCreate(
    $topic: WebhookSubscriptionTopic!,
    $webhookSubscription: WebhookSubscriptionInput!
  ) {
    webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
      webhookSubscription { id topic }
      userErrors { field message }
    }
  }
`;

interface WebhookConfig {
  topic: string;
  callbackUrl: string;
  format?: "JSON" | "XML";
}

export async function registerWebhooks(
  shop: string,
  webhooks: WebhookConfig[]
): Promise<{ registered: string[]; errors: string[] }> {
  const registered: string[] = [];
  const errors: string[] = [];

  for (const wh of webhooks) {
    const result = await shopifyQuery(shop, REGISTER_WEBHOOK, {
      topic: wh.topic,
      webhookSubscription: {
        callbackUrl: wh.callbackUrl,
        format: wh.format ?? "JSON",
      },
    });

    const userErrors = result.webhookSubscriptionCreate.userErrors;
    if (userErrors?.length) {
      errors.push(`${wh.topic}: ${userErrors[0].message}`);
    } else {
      registered.push(wh.topic);
    }
  }

  return { registered, errors };
}
```

## Output

- Type-safe GraphQL client with singleton session management
- Structured error handling that distinguishes retryable from permanent errors
- Cursor-based pagination generator for large datasets
- Multi-tenant client factory for apps serving multiple stores
- Codegen-typed operations eliminating manual type definitions
- Bulk operation helpers for large dataset exports
- Webhook registry patterns for programmatic subscription management

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeShopifyCall` | All API calls | Returns `{data, error}` instead of throwing |
| `handleShopifyError` | Error translation | Maps HTTP/GraphQL errors to typed errors |
| Cursor pagination | Large datasets | Memory-efficient streaming with backpressure |
| Bulk operations | 100k+ records | Server-side execution, no client memory pressure |
| Client factory | Multi-tenant apps | Isolated sessions per merchant |

## Examples

### Setting Up a Type-Safe GraphQL Client

Initialize a singleton Shopify client with session caching and a typed `shopifyQuery<T>()` helper for all API calls.

See [Typed GraphQL Client](references/typed-graphql-client.md) for the complete implementation.

### Handling Retryable vs Permanent Errors

Distinguish 429/5xx retryable errors from permanent validation failures using a structured error class and safe call wrapper.

See [Error Handling](references/error-handling.md) for the complete error handling implementation.

### Building a Multi-Tenant App

Create isolated GraphQL clients per merchant with session caching and eviction on app uninstall using a client factory.

See [Multi-Tenant Factory](references/multi-tenant-factory.md) for the complete implementation.

## Resources

- [@shopify/shopify-api Reference](https://github.com/Shopify/shopify-api-js)
- [GraphQL Pagination (Relay Spec)](https://shopify.dev/docs/api/usage/pagination-graphql)
- [@shopify/api-codegen-preset](https://github.com/Shopify/shopify-api-js/tree/main/packages/api-codegen-preset)
- [Bulk Operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)
