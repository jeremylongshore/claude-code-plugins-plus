# Webhook Registration via GraphQL

Register webhook subscriptions using the `webhookSubscriptionCreate` mutation for all critical event topics.

```typescript
// Register a webhook subscription
const REGISTER_WEBHOOK = `
  mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
    webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
      webhookSubscription {
        id
        topic
        endpoint {
          ... on WebhookHttpEndpoint {
            callbackUrl
          }
        }
        format
      }
      userErrors { field message }
    }
  }
`;

// Common webhook topics
const topics = [
  "ORDERS_CREATE",
  "ORDERS_UPDATED",
  "ORDERS_PAID",
  "ORDERS_FULFILLED",
  "PRODUCTS_CREATE",
  "PRODUCTS_UPDATE",
  "PRODUCTS_DELETE",
  "CUSTOMERS_CREATE",
  "CUSTOMERS_UPDATE",
  "APP_UNINSTALLED",
  "INVENTORY_LEVELS_UPDATE",
];

for (const topic of topics) {
  await client.request(REGISTER_WEBHOOK, {
    variables: {
      topic,
      webhookSubscription: {
        callbackUrl: "https://your-app.example.com/webhooks",
        format: "JSON",
      },
    },
  });
}
```
