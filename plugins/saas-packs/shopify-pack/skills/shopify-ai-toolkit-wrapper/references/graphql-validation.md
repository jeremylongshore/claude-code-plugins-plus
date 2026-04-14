Using the Shopify MCP server to validate GraphQL queries against your store's schema.

## Why Validate Before Executing

Shopify's GraphQL API evolves across API versions. Fields get deprecated, renamed, or restructured. Validating against your store's live schema catches:

- Deprecated fields that will break in upcoming versions
- Type mismatches in mutation inputs
- Missing required fields
- Fields that require higher API scopes

## Common Deprecated Field Mappings

| Deprecated | Current | API Version Changed |
|-----------|---------|-------------------|
| `priceRange` | `priceRangeV2` | 2022-10 |
| `img_url` filter | `image_url` filter | 2023-04 |
| `ProductInput` (unified) | `ProductCreateInput` / `ProductUpdateInput` | 2024-10 |
| `inventoryBulkAdjustQuantityAtLocation` | `inventoryAdjustQuantities` | 2023-10 |
| `collectionPublish` | `publishablePublish` | 2023-04 |
| `productPublish` | `publishablePublish` | 2023-04 |

## Schema Introspection Query

If using the MCP server's introspection capabilities, it runs queries like:

```graphql
{
  __type(name: "ProductCreateInput") {
    name
    kind
    inputFields {
      name
      type {
        name
        kind
        ofType { name kind }
      }
      defaultValue
    }
  }
}
```

This reveals the exact shape your store's API version expects.

## Common Validation Errors

### Field Not Found

```
Error: Cannot query field "priceRange" on type "Product". 
Did you mean "priceRangeV2"?
```

**Fix**: Update to the current field name. Check the API changelog for your version.

### Wrong Input Type

```
Error: Variable "$input" got invalid value. 
In field "title": Expected type "String!", found null.
```

**Fix**: Required fields (marked with `!`) must be provided and non-null.

### Scope Insufficient

```
Error: Access denied for productCreate mutation.
Requires write_products scope.
```

**Fix**: Update your app's scopes in the Shopify partner dashboard and reinstall.

### API Version Mismatch

```
Error: Field "productSet" doesn't exist on type "Mutation".
```

**Fix**: `productSet` was introduced in 2024-01. Update your API version or use `productCreate` + `productUpdate`.

## Version-Specific Gotchas

### 2024-10: Product Input Split

Before 2024-10:
```graphql
mutation productCreate($input: ProductInput!) { ... }
mutation productUpdate($input: ProductInput!) { ... }
```

After 2024-10:
```graphql
mutation productCreate($input: ProductCreateInput!) { ... }
mutation productUpdate($input: ProductUpdateInput!) { ... }
```

The fields differ between create and update. For example, `handle` is only settable on create, not update.

### 2023-10: Inventory Adjustments

Before:
```graphql
mutation inventoryBulkAdjustQuantityAtLocation(
  $inventoryItemAdjustments: [InventoryAdjustItemInput!]!,
  $locationId: ID!
) { ... }
```

After:
```graphql
mutation inventoryAdjustQuantities(
  $input: InventoryAdjustQuantitiesInput!
) { ... }
```

The new mutation supports adjusting quantities across multiple locations in a single call.

## Using `LATEST_API_VERSION`

When using `@shopify/shopify-api`, always use the constant instead of hardcoding:

```typescript
import { LATEST_API_VERSION } from "@shopify/shopify-api";

const client = new shopify.clients.Graphql({
  session,
  apiVersion: LATEST_API_VERSION, // Always current
});
```
