Refund creation mutation with line item restock and customer notification.

```typescript
const REFUND_CREATE = `
  mutation refundCreate($input: RefundInput!) {
    refundCreate(input: $input) {
      refund {
        id
        totalRefundedSet { shopMoney { amount currencyCode } }
      }
      userErrors { field message }
    }
  }
`;

await client.request(REFUND_CREATE, {
  variables: {
    input: {
      orderId: "gid://shopify/Order/12345",
      note: "Customer requested return",
      notify: true,
      refundLineItems: [
        {
          lineItemId: "gid://shopify/LineItem/67890",
          quantity: 1,
          restockType: "RETURN",
        },
      ],
    },
  },
});
```
