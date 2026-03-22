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

Production-ready patterns for the `@shopify/shopify-api` library: singleton clients, typed GraphQL operations, session management, cursor-based pagination, and error handling wrappers.

## Prerequisites

- `@shopify/shopify-api` v9+ installed
- Familiarity with Shopify's GraphQL Admin API
- Understanding of async/await and TypeScript generics

## Instructions

### Step 1: Typed GraphQL Client Wrapper

```typescript
// src/shopify/client.ts
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, Session, GraphqlClient } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: "2024-10",
  isCustomStoreApp: !!process.env.SHOPIFY_ACCESS_TOKEN,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN,
});

// Singleton session cache per shop
const sessionCache = new Map<string, Session>();

export function getSession(shop: string): Session {
  if (!sessionCache.has(shop)) {
    const session = shopify.session.customAppSession(shop);
    sessionCache.set(shop, session);
  }
  return sessionCache.get(shop)!;
}

export function getGraphqlClient(shop: string): GraphqlClient {
  return new shopify.clients.Graphql({
    session: getSession(shop),
  });
}

// Typed query helper
export async function shopifyQuery<T = any>(
  shop: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const client = getGraphqlClient(shop);
  const response = await client.request(query, { variables });
  return response.data as T;
}
```

### Step 2: Error Handling with Shopify Error Types

```typescript
// src/shopify/errors.ts
import { HttpResponseError, GraphqlQueryError } from "@shopify/shopify-api";

export class ShopifyServiceError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly shopifyRequestId?: string,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "ShopifyServiceError";
  }
}

export function handleShopifyError(error: unknown): never {
  if (error instanceof HttpResponseError) {
    const retryable = [429, 500, 502, 503, 504].includes(error.response.code);
    throw new ShopifyServiceError(
      `Shopify API ${error.response.code}: ${error.message}`,
      error.response.code,
      retryable,
      error.response.headers?.["x-request-id"] as string,
      error
    );
  }

  if (error instanceof GraphqlQueryError) {
    // GraphQL errors in the response body
    const msg = error.body?.errors
      ?.map((e: any) => e.message)
      .join("; ") || error.message;
    throw new ShopifyServiceError(msg, 200, false, undefined, error);
  }

  throw error;
}

// Safe wrapper
export async function safeShopifyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: ShopifyServiceError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    try {
      handleShopifyError(err);
    } catch (shopifyErr) {
      return { data: null, error: shopifyErr as ShopifyServiceError };
    }
    return { data: null, error: err as ShopifyServiceError };
  }
}
```

### Step 3: Cursor-Based Pagination

```typescript
// src/shopify/pagination.ts
// Shopify uses Relay-style cursor pagination for all list queries

interface PageInfo {
  hasNextPage: boolean;
  endCursor: string | null;
}

interface PaginatedResult<T> {
  edges: Array<{ node: T; cursor: string }>;
  pageInfo: PageInfo;
}

export async function* paginateShopify<T>(
  shop: string,
  query: string,
  connectionPath: string, // e.g. "products" or "orders"
  variables: Record<string, unknown> = {},
  pageSize: number = 50
): AsyncGenerator<T[], void, undefined> {
  let cursor: string | null = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const response = await shopifyQuery(shop, query, {
      ...variables,
      first: pageSize,
      after: cursor,
    });

    // Navigate to the connection in the response
    const connection = connectionPath
      .split(".")
      .reduce((obj: any, key) => obj[key], response) as PaginatedResult<T>;

    yield connection.edges.map((e) => e.node);

    hasNextPage = connection.pageInfo.hasNextPage;
    cursor = connection.pageInfo.endCursor;
  }
}

// Usage example:
// for await (const batch of paginateShopify<Product>(
//   "store.myshopify.com",
//   PRODUCTS_QUERY,
//   "products",
//   { query: "status:active" }
// )) {
//   await processProducts(batch);
// }
```

### Step 4: Multi-Tenant Client Factory

```typescript
// src/shopify/factory.ts
// For apps installed on multiple stores

import { Session, GraphqlClient } from "@shopify/shopify-api";

interface TenantConfig {
  shop: string;
  accessToken: string;
}

class ShopifyClientFactory {
  private clients = new Map<string, GraphqlClient>();

  getClient(config: TenantConfig): GraphqlClient {
    if (!this.clients.has(config.shop)) {
      const session = new Session({
        id: config.shop,
        shop: config.shop,
        state: "",
        isOnline: false,
        accessToken: config.accessToken,
      });

      this.clients.set(
        config.shop,
        new shopify.clients.Graphql({ session })
      );
    }
    return this.clients.get(config.shop)!;
  }

  // Evict when merchant uninstalls
  removeClient(shop: string): void {
    this.clients.delete(shop);
  }
}

export const clientFactory = new ShopifyClientFactory();
```

### Step 5: Response Validation with Zod

```typescript
// src/shopify/validators.ts
import { z } from "zod";

// Validate Shopify product response shape
const ShopifyMoneySchema = z.object({
  amount: z.string(),
  currencyCode: z.string(),
});

const ShopifyProductSchema = z.object({
  id: z.string().startsWith("gid://shopify/Product/"),
  title: z.string(),
  handle: z.string(),
  status: z.enum(["ACTIVE", "ARCHIVED", "DRAFT"]),
  totalInventory: z.number(),
  variants: z.object({
    edges: z.array(z.object({
      node: z.object({
        id: z.string(),
        title: z.string(),
        price: z.string(),
        sku: z.string().nullable(),
      }),
    })),
  }),
});

export type ShopifyProduct = z.infer<typeof ShopifyProductSchema>;

// Validated fetch
export async function fetchProducts(shop: string): Promise<ShopifyProduct[]> {
  const data = await shopifyQuery(shop, PRODUCTS_QUERY);
  return data.products.edges.map(
    (e: any) => ShopifyProductSchema.parse(e.node)
  );
}
```

## Output

- Type-safe GraphQL client with singleton session management
- Structured error handling that distinguishes retryable from permanent errors
- Cursor-based pagination generator for large datasets
- Multi-tenant client factory for apps serving multiple stores
- Zod validation for API response shape verification

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeShopifyCall` | All API calls | Returns `{data, error}` instead of throwing |
| `handleShopifyError` | Error translation | Maps HTTP/GraphQL errors to typed errors |
| Cursor pagination | Large datasets | Memory-efficient streaming with backpressure |
| Zod validation | Response parsing | Catches breaking API changes immediately |
| Client factory | Multi-tenant apps | Isolated sessions per merchant |

## Examples

### Retry with Exponential Backoff

```typescript
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (err instanceof ShopifyServiceError && err.retryable && attempt < maxRetries) {
        const delay = baseDelayMs * Math.pow(2, attempt - 1) + Math.random() * 500;
        console.warn(`Shopify retry ${attempt}/${maxRetries} in ${delay.toFixed(0)}ms`);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Unreachable");
}
```

## Resources

- [@shopify/shopify-api Reference](https://github.com/Shopify/shopify-api-js)
- [GraphQL Pagination (Relay Spec)](https://shopify.dev/docs/api/usage/pagination-graphql)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply patterns in `shopify-core-workflow-a` for real-world product management.
