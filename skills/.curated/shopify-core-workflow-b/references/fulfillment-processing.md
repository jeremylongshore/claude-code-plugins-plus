Two-step fulfillment processing: query fulfillment orders, then create fulfillment with tracking info.

### Step 3a: Get fulfillment orders

```typescript
const GET_FULFILLMENT_ORDERS = `
  query fulfillmentOrders($orderId: ID!) {
    order(id: $orderId) {
      fulfillmentOrders(first: 10) {
        edges {
          node {
            id
            status  # OPEN, IN_PROGRESS, CLOSED, CANCELLED
            assignedLocation {
              name
            }
            lineItems(first: 20) {
              edges {
                node {
                  id
                  totalQuantity
                  remainingQuantity
                }
              }
            }
          }
        }
      }
    }
  }
`;
```

### Step 3b: Create fulfillment with tracking

```typescript
const CREATE_FULFILLMENT = `
  mutation fulfillmentCreate($fulfillment: FulfillmentInput!) {
    fulfillmentCreate(fulfillment: $fulfillment) {
      fulfillment {
        id
        status
        trackingInfo {
          number
          url
          company
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(CREATE_FULFILLMENT, {
  variables: {
    fulfillment: {
      lineItemsByFulfillmentOrder: [
        {
          fulfillmentOrderId: "gid://shopify/FulfillmentOrder/99999",
          fulfillmentOrderLineItems: [
            {
              id: "gid://shopify/FulfillmentOrderLineItem/11111",
              quantity: 2,
            },
          ],
        },
      ],
      trackingInfo: {
        number: "1Z999AA10123456784",
        url: "https://www.ups.com/track?tracknum=1Z999AA10123456784",
        company: "UPS",
      },
      notifyCustomer: true,
    },
  },
});
```
