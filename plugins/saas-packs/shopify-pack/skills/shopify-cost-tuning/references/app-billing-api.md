Complete GraphQL mutation for creating a recurring app subscription charge via the Shopify Billing API.

```typescript
// Create a recurring charge
const CREATE_SUBSCRIPTION = `
  mutation appSubscriptionCreate(
    $name: String!,
    $lineItems: [AppSubscriptionLineItemInput!]!,
    $returnUrl: URL!,
    $test: Boolean
  ) {
    appSubscriptionCreate(
      name: $name,
      lineItems: $lineItems,
      returnUrl: $returnUrl,
      test: $test
    ) {
      appSubscription {
        id
        status
      }
      confirmationUrl
      userErrors { field message }
    }
  }
`;

const response = await client.request(CREATE_SUBSCRIPTION, {
  variables: {
    name: "Pro Plan",
    returnUrl: "https://your-app.com/billing/callback",
    test: process.env.NODE_ENV !== "production", // test charges in dev
    lineItems: [
      {
        plan: {
          appRecurringPricingDetails: {
            price: { amount: 9.99, currencyCode: "USD" },
            interval: "EVERY_30_DAYS",
          },
        },
      },
    ],
  },
});

// Redirect merchant to confirmationUrl to approve the charge
```
