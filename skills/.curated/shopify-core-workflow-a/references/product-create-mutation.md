ProductCreate mutation with ProductCreateInput (2024-10+ split from old ProductInput), including options and variants setup.

```typescript
// As of 2024-10, productCreate uses ProductCreateInput (not the old ProductInput)
const CREATE_PRODUCT = `
  mutation productCreate($input: ProductCreateInput!) {
    productCreate(product: $input) {
      product {
        id
        title
        handle
        status
        variants(first: 10) {
          edges {
            node {
              id
              title
              price
              sku
              inventoryQuantity
            }
          }
        }
      }
      userErrors {
        field
        message
        code
      }
    }
  }
`;

const response = await client.request(CREATE_PRODUCT, {
  variables: {
    input: {
      title: "Premium Cotton T-Shirt",
      descriptionHtml: "<p>Soft 100% organic cotton tee.</p>",
      vendor: "My Brand",
      productType: "Apparel",
      tags: ["cotton", "organic", "summer"],
      status: "DRAFT", // ACTIVE, DRAFT, or ARCHIVED
      productOptions: [
        {
          name: "Size",
          values: [{ name: "S" }, { name: "M" }, { name: "L" }, { name: "XL" }],
        },
        {
          name: "Color",
          values: [{ name: "Black" }, { name: "White" }, { name: "Navy" }],
        },
      ],
    },
  },
});

// ALWAYS check userErrors — Shopify returns 200 even on validation failures
if (response.data.productCreate.userErrors.length > 0) {
  console.error("Validation errors:", response.data.productCreate.userErrors);
  // Example: [{ field: ["title"], message: "Title can't be blank", code: "BLANK" }]
}
```
