ProductUpdate mutation with ProductUpdateInput (separate from create as of 2024-10), including metafield updates.

```typescript
// 2024-10+: productUpdate uses ProductUpdateInput (separate from create)
const UPDATE_PRODUCT = `
  mutation productUpdate($input: ProductUpdateInput!) {
    productUpdate(product: $input) {
      product {
        id
        title
        status
        updatedAt
      }
      userErrors {
        field
        message
      }
    }
  }
`;

await client.request(UPDATE_PRODUCT, {
  variables: {
    input: {
      id: "gid://shopify/Product/1234567890",
      title: "Updated Product Title",
      status: "ACTIVE",
      metafields: [
        {
          namespace: "custom",
          key: "care_instructions",
          value: "Machine wash cold",
          type: "single_line_text_field",
        },
      ],
    },
  },
});
```
