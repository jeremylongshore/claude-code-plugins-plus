Detailed breakdown of how Shopify calculates GraphQL query cost.

## Cost Formula

```
Total Cost = sum of all field costs at each level
```

**Rules:**

1. **Scalar fields on a root query**: 1 point each
2. **Object fields**: 1 point for the object + cost of its children
3. **Connection fields**: 2 points for the connection + (`first` or `last` param * cost of each node)
4. **Nested connections**: costs multiply — this is where queries explode

## Examples with Calculations

### Simple Query (Low Cost)

```graphql
{
  shop {          # 1 point (object)
    name          # 1 point (scalar)
    email         # 1 point (scalar)
  }
}
# Total requestedQueryCost: 3
```

### Single Connection

```graphql
{
  products(first: 10) {   # 2 points (connection overhead)
    edges {
      node {
        id               # 1 point per node
        title            # 1 point per node
      }
    }
  }
}
# Cost: 2 + (10 * 2) = 22 requestedQueryCost
```

### Nested Connection

```graphql
{
  products(first: 10) {           # 2 (connection)
    edges {
      node {
        id                        # 1 per product
        title                     # 1 per product
        variants(first: 5) {      # 2 (connection) per product
          edges {
            node {
              id                  # 1 per variant
              price               # 1 per variant
            }
          }
        }
      }
    }
  }
}
# Per variant: 2 fields = 2
# Per product variants connection: 2 + (5 * 2) = 12
# Per product: 2 fields + 12 (variants) = 14
# Total: 2 (products connection) + (10 * 14) = 142 requestedQueryCost
```

### Triple Nesting (Dangerous)

```graphql
{
  products(first: 50) {
    edges {
      node {
        variants(first: 20) {
          edges {
            node {
              metafields(first: 10) {
                edges {
                  node { key value }
                }
              }
            }
          }
        }
      }
    }
  }
}
# Per metafield: 2 fields = 2
# Per variant metafields: 2 + (10 * 2) = 22
# Per variant total: 22
# Per product variants: 2 + (20 * 22) = 442
# Total: 2 + (50 * 442) = 22,102 requestedQueryCost
# This EXCEEDS the 1,000 point maximum — will return MAX_COST_EXCEEDED
```

## requestedQueryCost vs actualQueryCost

The `requestedQueryCost` assumes all connections return the maximum `first` items. The `actualQueryCost` is calculated after execution based on how many items actually existed.

```json
{
  "extensions": {
    "cost": {
      "requestedQueryCost": 142,
      "actualQueryCost": 38
    }
  }
}
```

In this example, the query requested `products(first: 10)` but only 3 products existed, so the actual cost was much lower. **Shopify deducts `actualQueryCost` from your bucket, not `requestedQueryCost`.** However, Shopify uses `requestedQueryCost` to decide whether to reject the query upfront with `MAX_COST_EXCEEDED`.

## Inline Fragments

Inline fragments (`... on Type`) add the cost of their fields to each node:

```graphql
{
  nodes(ids: ["gid://shopify/Product/1", "gid://shopify/Collection/2"]) {
    ... on Product {
      title          # 1 per Product node
      description    # 1 per Product node
    }
    ... on Collection {
      title          # 1 per Collection node
      productsCount  # 1 per Collection node
    }
  }
}
# Cost: sum of all possible fragment fields per node (worst case)
```

## Cost Budget Strategy

| Query Type | Target Cost | Reasoning |
|-----------|-------------|-----------|
| Interactive (user-facing) | < 100 | Leave room for concurrent queries |
| Background sync | < 500 | Single query at a time, can wait for restore |
| One-time migration | Use bulk operations | Bypass cost system entirely |
| Dashboard polling | < 50 | Runs frequently, must not accumulate |
