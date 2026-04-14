# REST to GraphQL Migration

Side-by-side comparison of REST vs GraphQL Admin API patterns plus a mapping table for common endpoints.

```typescript
// BEFORE: REST Admin API
const restClient = new shopify.clients.Rest({ session });
const { body } = await restClient.get({
  path: "products",
  query: { limit: 50, status: "active" },
});
const products = body.products;

// AFTER: GraphQL Admin API
const graphqlClient = new shopify.clients.Graphql({ session });
const response = await graphqlClient.request(`{
  products(first: 50, query: "status:active") {
    edges {
      node {
        id
        title
        status
        variants(first: 10) {
          edges { node { id price sku } }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}`);
const products = response.data.products.edges.map((e: any) => e.node);
```

## Common REST-to-GraphQL Mappings

| REST Endpoint | GraphQL Query/Mutation |
|--------------|----------------------|
| `GET /products.json` | `query { products(first: N) { edges { node { ... } } } }` |
| `POST /products.json` | `mutation { productCreate(product: $input) { ... } }` |
| `PUT /products/{id}.json` | `mutation { productUpdate(product: $input) { ... } }` |
| `GET /orders.json` | `query { orders(first: N) { edges { node { ... } } } }` |
| `GET /customers/{id}.json` | `query { customer(id: $id) { ... } }` |
| `POST /webhooks.json` | `mutation { webhookSubscriptionCreate(...) { ... } }` |
