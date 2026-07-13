Order query with financial/fulfillment status, line items, customer, and shipping data plus pagination.

```typescript
const QUERY_ORDERS = `
  query orders($first: Int!, $query: String, $after: String) {
    orders(first: $first, query: $query, after: $after, sortKey: CREATED_AT, reverse: true) {
      edges {
        node {
          id
          name                    # "#1001"
          createdAt
          displayFinancialStatus  # PAID, PENDING, REFUNDED, etc.
          displayFulfillmentStatus # FULFILLED, UNFULFILLED, PARTIALLY_FULFILLED
          totalPriceSet {
            shopMoney { amount currencyCode }
          }
          customer {
            id
            displayName
            email
          }
          lineItems(first: 10) {
            edges {
              node {
                title
                quantity
                variant {
                  id
                  sku
                  price
                }
                originalTotalSet {
                  shopMoney { amount currencyCode }
                }
              }
            }
          }
          shippingAddress {
            address1
            city
            province
            country
            zip
          }
        }
        cursor
      }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

// Shopify order query syntax:
// "financial_status:paid"
// "fulfillment_status:unfulfilled"
// "created_at:>2024-01-01"
// "name:#1001"
// "email:customer@example.com"
// "tag:rush"
const data = await client.request(QUERY_ORDERS, {
  variables: {
    first: 25,
    query: "financial_status:paid AND fulfillment_status:unfulfilled",
  },
});
```
