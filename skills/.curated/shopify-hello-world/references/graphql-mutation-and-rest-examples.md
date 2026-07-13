Examples of creating a product via GraphQL mutation and querying products via the REST Admin API.

### Create a Product via GraphQL Mutation

```typescript
const response = await client.request(`
  mutation productCreate($input: ProductCreateInput!) {
    productCreate(product: $input) {
      product {
        id
        title
        handle
      }
      userErrors {
        field
        message
      }
    }
  }
`, {
  variables: {
    input: {
      title: "Hello World Product",
      descriptionHtml: "<p>Created via Shopify API</p>",
      vendor: "My App",
      productType: "Test",
      tags: ["api-created", "hello-world"],
    },
  },
});

if (response.data.productCreate.userErrors.length > 0) {
  console.error("Errors:", response.data.productCreate.userErrors);
} else {
  console.log("Created:", response.data.productCreate.product.title);
}
```

### REST Admin API (Legacy but Still Supported)

```typescript
const restClient = new shopify.clients.Rest({ session });

// GET /admin/api/{version}/products.json
const { body } = await restClient.get({
  path: "products",
  query: { limit: 5, status: "active" },
});

console.log("Products:", body.products.map((p: any) => p.title));
```
