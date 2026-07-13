Customer search query with spending, order count, tags, addresses, and metafields.

```typescript
// Query customers
const SEARCH_CUSTOMERS = `
  query customers($query: String!, $first: Int!) {
    customers(first: $first, query: $query) {
      edges {
        node {
          id
          displayName
          email
          phone
          numberOfOrders
          amountSpent { amount currencyCode }
          tags
          addresses(first: 3) {
            address1
            city
            province
            country
          }
          metafields(first: 5) {
            edges {
              node {
                namespace
                key
                value
                type
              }
            }
          }
        }
      }
    }
  }
`;

// Customer query examples:
// "email:john@example.com"
// "orders_count:>5"
// "total_spent:>100"
// "tag:vip"
// "state:enabled"
const customers = await client.request(SEARCH_CUSTOMERS, {
  variables: {
    query: "orders_count:>5 AND total_spent:>100",
    first: 20,
  },
});
```
