Patterns for splitting expensive Shopify GraphQL queries into cheaper ones.

## When to Split

Split a query when:
- `requestedQueryCost` exceeds 500 points
- You have nested connections deeper than 2 levels
- You need data from multiple unrelated resource types

## Pattern 1: Flatten Nested Connections

Instead of fetching products with nested variants and metafields in one query:

```graphql
# BAD: Triple nesting = cost explosion
{
  products(first: 50) {
    edges {
      node {
        id
        title
        variants(first: 20) {
          edges {
            node {
              id
              price
              metafields(first: 5) {
                edges { node { key value } }
              }
            }
          }
        }
      }
    }
  }
}
# requestedQueryCost: ~6,052
```

Split into two queries:

```graphql
# Query 1: Get products and variant IDs (cost: ~222)
{
  products(first: 50) {
    edges {
      node {
        id
        title
        variants(first: 20) {
          edges {
            node {
              id
              price
            }
          }
        }
      }
    }
  }
}

# Query 2: Get metafields for specific variants you care about (cost: ~52)
{
  nodes(ids: ["gid://shopify/ProductVariant/111", "gid://shopify/ProductVariant/222"]) {
    ... on ProductVariant {
      id
      metafields(first: 5) {
        edges { node { key value namespace type } }
      }
    }
  }
}
```

## Pattern 2: Paginate Aggressively

```graphql
# BAD: 250 items at once
{
  products(first: 250) {
    edges { node { id title status } }
    pageInfo { hasNextPage endCursor }
  }
}
# requestedQueryCost: ~502

# GOOD: Small pages, paginate with cursor
{
  products(first: 25, after: $cursor) {
    edges { node { id title status } }
    pageInfo { hasNextPage endCursor }
  }
}
# requestedQueryCost: ~52
```

Implementation for cursor-based pagination:

```typescript
async function paginateAll(client: any, query: string, variables: any = {}) {
  const allItems: any[] = [];
  let cursor: string | null = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const response = await client.request(query, {
      variables: { ...variables, after: cursor, first: 25 },
    });

    // Extract the connection (works for any top-level connection)
    const connectionKey = Object.keys(response.data).find(
      (k) => response.data[k]?.edges
    );
    const connection = response.data[connectionKey!];

    allItems.push(...connection.edges.map((e: any) => e.node));
    hasNextPage = connection.pageInfo.hasNextPage;
    cursor = connection.pageInfo.endCursor;

    // Respect rate limits
    const available = response.extensions?.cost?.throttleStatus?.currentlyAvailable;
    if (available && available < 100) {
      const waitMs = ((100 - available) / 50) * 1000;
      await new Promise((r) => setTimeout(r, waitMs));
    }
  }

  return allItems;
}
```

## Pattern 3: Use `nodes` Query for Known IDs

When you already have IDs, the `nodes` query is cheaper than filtering:

```graphql
# BAD: Query with filter to find specific products
{
  products(first: 100, query: "id:123 OR id:456 OR id:789") {
    edges { node { id title variants(first: 10) { edges { node { id price } } } } }
  }
}
# requestedQueryCost: ~1,202 (100 * (1 + 12))

# GOOD: Direct lookup by GID
{
  nodes(ids: [
    "gid://shopify/Product/123",
    "gid://shopify/Product/456",
    "gid://shopify/Product/789"
  ]) {
    ... on Product {
      id
      title
      variants(first: 10) {
        edges { node { id price } }
      }
    }
  }
}
# requestedQueryCost: ~39 (3 * (1 + 12))
```

## Pattern 4: Separate Reads from Writes

Never combine mutations with expensive queries:

```typescript
// BAD: Mutation + expensive re-fetch in one request
const UPDATE_AND_FETCH = `
  mutation {
    productUpdate(input: { id: "gid://shopify/Product/123", title: "New" }) {
      product {
        id title
        variants(first: 100) { edges { node { id price sku inventoryQuantity } } }
        images(first: 50) { edges { node { url altText } } }
      }
    }
  }
`;

// GOOD: Mutation returns minimal data, separate query if needed
const UPDATE = `
  mutation productUpdate($input: ProductUpdateInput!) {
    productUpdate(product: $input) {
      product { id title updatedAt }
      userErrors { field message }
    }
  }
`;
// Then fetch only if needed, with targeted fields
```
