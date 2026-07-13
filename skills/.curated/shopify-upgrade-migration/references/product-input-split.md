# ProductInput Split (2024-10)

In API version 2024-10, Shopify split `ProductInput` into separate types for create and update operations.

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
