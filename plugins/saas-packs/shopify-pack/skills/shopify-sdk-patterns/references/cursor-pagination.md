# Cursor-Based Pagination

Async generator for Relay-style cursor pagination used by all Shopify list queries.

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
