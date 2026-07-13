Draft order creation with line items, custom items, discounts, and shipping address.

```typescript
const CREATE_DRAFT_ORDER = `
  mutation draftOrderCreate($input: DraftOrderInput!) {
    draftOrderCreate(input: $input) {
      draftOrder {
        id
        name
        totalPriceSet {
          shopMoney { amount currencyCode }
        }
        invoiceUrl
      }
      userErrors {
        field
        message
      }
    }
  }
`;

await client.request(CREATE_DRAFT_ORDER, {
  variables: {
    input: {
      lineItems: [
        {
          variantId: "gid://shopify/ProductVariant/12345",
          quantity: 2,
        },
        {
          title: "Custom Engraving", // Custom line item (no variant)
          originalUnitPrice: "15.00",
          quantity: 1,
        },
      ],
      customerId: "gid://shopify/Customer/67890",
      note: "Rush order — ship priority",
      tags: ["wholesale", "rush"],
      shippingAddress: {
        address1: "123 Main St",
        city: "Portland",
        provinceCode: "OR",
        countryCode: "US",
        zip: "97201",
      },
      appliedDiscount: {
        title: "Wholesale 10%",
        value: 10.0,
        valueType: "PERCENTAGE",
      },
    },
  },
});
```
