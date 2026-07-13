Webhook subscription health check query and common delivery issues.

```typescript
// Check webhook subscription health
const WEBHOOK_STATUS = `{
  webhookSubscriptions(first: 50) {
    edges {
      node {
        id
        topic
        endpoint {
          ... on WebhookHttpEndpoint {
            callbackUrl
          }
        }
        format
        apiVersion
        createdAt
        updatedAt
      }
    }
  }
}`;

// Common webhook delivery issues:
// 1. Your endpoint returns non-200 — Shopify retries 19 times over 48 hours
// 2. Response takes > 5 seconds — Shopify considers it failed
// 3. Endpoint is HTTP (not HTTPS) — Shopify won't deliver
// 4. SSL certificate invalid — delivery fails silently
```
