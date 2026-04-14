---
name: shopify-webhooks-events
description: |
  Register and handle Shopify webhooks including mandatory GDPR compliance topics.
  Use when setting up webhook subscriptions, handling order/product events,
  or implementing the required GDPR webhooks for app store submission.
  Trigger with phrases like "shopify webhook", "shopify events",
  "shopify GDPR webhook", "handle shopify notifications", "shopify webhook register".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Webhooks & Events

## Overview

Register webhooks via GraphQL, handle events with HMAC verification, and implement the mandatory GDPR compliance webhooks required for Shopify App Store submission.

## Prerequisites

- Shopify app with API credentials configured
- HTTPS endpoint accessible from the internet (use `shopify app dev` tunnel for local)
- API secret for HMAC webhook verification

## Instructions

### Step 1: Register Webhooks via GraphQL

Use the `webhookSubscriptionCreate` mutation with `WebhookSubscriptionTopic` and `WebhookSubscriptionInput` to register subscriptions for all critical event topics (orders, products, customers, inventory, app lifecycle).

See [Webhook Registration](references/webhook-registration.md) for the complete implementation.

### Step 2: Configure Mandatory GDPR Webhooks

**Required for App Store submission.** These are configured in `shopify.app.toml`, not via API:

```toml
# shopify.app.toml
[webhooks]
api_version = "2025-04"  # Update quarterly

  # MANDATORY: customers/data_request
  [[webhooks.subscriptions]]
  topics = ["customers/data_request"]
  uri = "/webhooks/gdpr/data-request"

  # MANDATORY: customers/redact
  [[webhooks.subscriptions]]
  topics = ["customers/redact"]
  uri = "/webhooks/gdpr/customers-redact"

  # MANDATORY: shop/redact
  [[webhooks.subscriptions]]
  topics = ["shop/redact"]
  uri = "/webhooks/gdpr/shop-redact"
```

### Step 3: Implement GDPR Webhook Handlers

Three mandatory handlers: (1) customer data request -- collect and send all data for a customer, (2) customer redact -- delete customer personal data and specified orders, (3) shop redact -- delete ALL shop data 48 hours after uninstall.

See [GDPR Webhook Handlers](references/gdpr-webhook-handlers.md) for the complete implementation.

### Step 4: Event Handler Pattern

A typed webhook dispatcher maps topics to handler functions. Verifies HMAC first, responds 200 immediately, then processes asynchronously. Unknown topics are logged but not rejected.

See [Event Handler Pattern](references/event-handler-pattern.md) for the complete implementation.

### Step 5: List and Manage Existing Webhooks

```typescript
// Query all webhook subscriptions
const LIST_WEBHOOKS = `{
  webhookSubscriptions(first: 50) {
    edges {
      node {
        id
        topic
        endpoint {
          ... on WebhookHttpEndpoint { callbackUrl }
        }
        format
        createdAt
      }
    }
  }
}`;

// Delete a webhook
const DELETE_WEBHOOK = `
  mutation webhookSubscriptionDelete($id: ID!) {
    webhookSubscriptionDelete(id: $id) {
      deletedWebhookSubscriptionId
      userErrors { field message }
    }
  }
`;
```

## Output

- Webhook subscriptions registered for critical events
- Mandatory GDPR webhooks implemented (required for App Store)
- HMAC verification on all incoming webhooks
- Async event processing with error handling

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook delivery fails | Endpoint not reachable | Ensure HTTPS, check tunnel is running |
| HMAC validation fails | Wrong API secret | Verify `SHOPIFY_API_SECRET` in Partner Dashboard |
| Webhook not received | Topic not registered | Check `webhookSubscriptions` query |
| App Store rejection | Missing GDPR webhooks | Implement all 3 mandatory handlers |
| Duplicate events | Shopify retries on timeout | Add idempotency with webhook ID tracking |
| Timeout errors | Handler takes > 5 seconds | Respond 200 immediately, process async |

## Examples

### Test Webhook Locally

```bash
# Use Shopify CLI to trigger test webhooks
shopify app webhook trigger --topic orders/create --address http://localhost:3000/webhooks

# Or use curl with a test payload
curl -X POST http://localhost:3000/webhooks \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Topic: orders/create" \
  -H "X-Shopify-Shop-Domain: test.myshopify.com" \
  -H "X-Shopify-Hmac-Sha256: $(echo -n '{"test":true}' | openssl dgst -sha256 -hmac "$SHOPIFY_API_SECRET" -binary | base64)" \
  -d '{"test":true}'
```

## Resources

- [Shopify Webhooks Overview](https://shopify.dev/docs/api/webhooks)
- [Webhook Topics Reference](https://shopify.dev/docs/api/admin-graphql/latest/enums/WebhookSubscriptionTopic)
- [GDPR Mandatory Webhooks](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)
- [Webhook Delivery](https://shopify.dev/docs/apps/build/webhooks)
