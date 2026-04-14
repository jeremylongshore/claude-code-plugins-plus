# Event Handler Pattern

Typed webhook event dispatcher with HMAC verification, immediate 200 response, and async processing.

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
