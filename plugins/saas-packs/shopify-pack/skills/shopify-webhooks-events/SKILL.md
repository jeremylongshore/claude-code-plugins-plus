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

### Step 2: Configure Mandatory GDPR Webhooks

**Required for App Store submission.** These are configured in `shopify.app.toml`, not via API:

```toml
# shopify.app.toml
[webhooks]
api_version = "2024-10"

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

```typescript
// Mandatory GDPR handlers — your app will be REJECTED without these

// 1. Customer Data Request — merchant forwards customer's data request
app.post("/webhooks/gdpr/data-request", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // payload shape:
  // {
  //   "shop_id": 12345,
  //   "shop_domain": "store.myshopify.com",
  //   "orders_requested": [123, 456],
  //   "customer": { "id": 789, "email": "customer@example.com", "phone": "+1234567890" },
  //   "data_request": { "id": 101112 }
  // }

  // Collect all data you have for this customer
  const customerData = await collectCustomerData(payload.customer.id);
  await sendDataToMerchant(payload.shop_domain, customerData);

  res.status(200).send("OK");
});

// 2. Customer Redact — delete customer's personal data
app.post("/webhooks/gdpr/customers-redact", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // payload shape:
  // {
  //   "shop_id": 12345,
  //   "shop_domain": "store.myshopify.com",
  //   "customer": { "id": 789, "email": "customer@example.com", "phone": "+1234567890" },
  //   "orders_to_redact": [123, 456]
  // }

  await deleteCustomerData(payload.customer.id);
  await deleteOrderData(payload.orders_to_redact);

  res.status(200).send("OK");
});

// 3. Shop Redact — 48 hours after app uninstall, delete ALL shop data
app.post("/webhooks/gdpr/shop-redact", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // { "shop_id": 12345, "shop_domain": "store.myshopify.com" }

  await deleteAllShopData(payload.shop_id);

  res.status(200).send("OK");
});
```

### Step 4: Event Handler Pattern

```typescript
import crypto from "crypto";
import express from "express";

type WebhookTopic =
  | "orders/create"
  | "orders/updated"
  | "orders/paid"
  | "products/create"
  | "products/update"
  | "products/delete"
  | "app/uninstalled"
  | "inventory_levels/update";

const handlers: Record<WebhookTopic, (shop: string, payload: any) => Promise<void>> = {
  "orders/create": async (shop, payload) => {
    console.log(`New order ${payload.name} from ${shop}: $${payload.total_price}`);
    // payload has: id, name, email, total_price, line_items[], shipping_address, etc.
  },
  "orders/paid": async (shop, payload) => {
    console.log(`Order ${payload.name} paid: ${payload.financial_status}`);
  },
  "products/update": async (shop, payload) => {
    console.log(`Product updated: ${payload.title} (${payload.id})`);
    // Sync to your catalog
  },
  "products/delete": async (shop, payload) => {
    console.log(`Product deleted: ${payload.id}`);
    // Remove from your catalog
  },
  "app/uninstalled": async (shop, payload) => {
    console.log(`App uninstalled from ${shop}`);
    // Clean up session, disable features, prepare for shop/redact
  },
};

app.post(
  "/webhooks",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const hmac = req.headers["x-shopify-hmac-sha256"] as string;
    const topic = req.headers["x-shopify-topic"] as WebhookTopic;
    const shop = req.headers["x-shopify-shop-domain"] as string;

    if (!verifyShopifyWebhook(req.body, hmac, process.env.SHOPIFY_API_SECRET!)) {
      return res.status(401).send("Invalid HMAC");
    }

    // Respond immediately — Shopify requires 200 within 5 seconds
    res.status(200).send("OK");

    // Process asynchronously
    const payload = JSON.parse(req.body.toString());
    const handler = handlers[topic];
    if (handler) {
      try {
        await handler(shop, payload);
      } catch (err) {
        console.error(`Webhook handler failed for ${topic}:`, err);
        // Shopify will retry failed webhooks (no 200 response)
      }
    } else {
      console.log(`No handler for topic: ${topic}`);
    }
  }
);
```

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

## Next Steps

For performance optimization, see `shopify-performance-tuning`.
