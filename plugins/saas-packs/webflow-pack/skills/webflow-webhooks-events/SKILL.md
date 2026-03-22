---
name: webflow-webhooks-events
description: |
  Implement Webflow webhook registration, signature verification, and event handling
  for form_submission, site_publish, ecomm_new_order, page_created, and more.
  Use when setting up webhook endpoints, implementing event-driven workflows,
  or handling Webflow notifications.
  Trigger with phrases like "webflow webhook", "webflow events",
  "webflow webhook signature", "handle webflow events", "webflow notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Webhooks & Events

## Overview

Register, verify, and handle Webflow Data API v2 webhooks. Covers all trigger types,
HMAC signature verification, idempotent processing, and event routing patterns.

## Prerequisites

- Webflow API token with `sites:write` scope (for registering webhooks)
- HTTPS endpoint accessible from the internet
- `crypto` module (Node.js built-in)
- Redis or database for idempotency (optional)

## Webhook API Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List webhooks | GET | `/v2/sites/{site_id}/webhooks` |
| Create webhook | POST | `/v2/sites/{site_id}/webhooks` |
| Get webhook | GET | `/v2/webhooks/{webhook_id}` |
| Delete webhook | DELETE | `/v2/webhooks/{webhook_id}` |

**Limits:** Max 75 webhook registrations per `triggerType` per site.

## Supported Trigger Types

| triggerType | Description | Payload |
|-------------|-------------|---------|
| `form_submission` | Form submitted on site | Form data, submitter info |
| `site_publish` | Site published | Site ID, publish domains |
| `page_created` | New page created | Page ID, title, slug |
| `page_metadata_updated` | Page SEO/meta changed | Page ID, updated fields |
| `page_deleted` | Page removed | Page ID |
| `ecomm_new_order` | New ecommerce order | Order details, items, customer |
| `ecomm_order_changed` | Order status updated | Order ID, new status |
| `collection_item_created` | CMS item created | Collection ID, item data |
| `collection_item_changed` | CMS item updated | Collection ID, item data |
| `collection_item_deleted` | CMS item removed | Collection ID, item ID |
| `collection_item_unpublished` | CMS item unpublished | Collection ID, item ID |

## Instructions

### Step 1: Register Webhooks via API

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

const siteId = process.env.WEBFLOW_SITE_ID!;
const webhookUrl = "https://your-app.com/webhooks/webflow";

async function registerWebhooks() {
  const triggerTypes = [
    "form_submission",
    "site_publish",
    "ecomm_new_order",
    "collection_item_created",
    "collection_item_changed",
  ];

  for (const triggerType of triggerTypes) {
    const webhook = await webflow.webhooks.create(siteId, {
      triggerType,
      url: webhookUrl,
      // form_submission supports filtering to a specific form
      ...(triggerType === "form_submission" && {
        filter: { name: "contact-form" }, // Filter by form name
      }),
    });

    console.log(`Registered: ${triggerType} -> ${webhook.id}`);
  }
}

// List existing webhooks
async function listWebhooks() {
  const { webhooks } = await webflow.webhooks.list(siteId);
  for (const wh of webhooks!) {
    console.log(`${wh.triggerType}: ${wh.url} (${wh.id})`);
  }
}

// Delete a webhook
async function deleteWebhook(webhookId: string) {
  await webflow.webhooks.delete(webhookId);
}
```

### Step 2: Webhook Endpoint with Signature Verification

```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// CRITICAL: Use raw body for signature verification
app.post(
  "/webhooks/webflow",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-webflow-signature"] as string;
    const secret = process.env.WEBFLOW_WEBHOOK_SECRET!;

    // Verify HMAC-SHA256 signature
    if (!verifySignature(req.body, signature, secret)) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());

    // Respond immediately — process async
    res.status(200).json({ received: true });

    // Handle event asynchronously
    try {
      await handleWebflowEvent(event);
    } catch (error) {
      console.error("Webhook processing error:", error);
    }
  }
);

function verifySignature(
  rawBody: Buffer,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) return false;

  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("hex");

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false; // Length mismatch
  }
}
```

### Step 3: Event Router

```typescript
type WebflowTriggerType =
  | "form_submission"
  | "site_publish"
  | "page_created"
  | "page_metadata_updated"
  | "page_deleted"
  | "ecomm_new_order"
  | "ecomm_order_changed"
  | "collection_item_created"
  | "collection_item_changed"
  | "collection_item_deleted"
  | "collection_item_unpublished";

interface WebflowWebhookEvent {
  triggerType: WebflowTriggerType;
  payload: Record<string, any>;
  site: { id: string; shortName: string };
}

const eventHandlers: Record<WebflowTriggerType, (payload: any) => Promise<void>> = {
  form_submission: async (payload) => {
    console.log("New form submission:", payload.formData);
    // Forward to CRM, send email, etc.
  },

  site_publish: async (payload) => {
    console.log("Site published:", payload.site?.shortName);
    // Invalidate cache, notify team, etc.
  },

  ecomm_new_order: async (payload) => {
    console.log("New order:", payload.orderId);
    // Create invoice, update inventory, notify fulfillment
  },

  ecomm_order_changed: async (payload) => {
    console.log("Order updated:", payload.orderId, payload.status);
    // Update order status in your system
  },

  page_created: async (payload) => {
    console.log("New page:", payload.pageId);
  },

  page_metadata_updated: async (payload) => {
    console.log("Page metadata updated:", payload.pageId);
  },

  page_deleted: async (payload) => {
    console.log("Page deleted:", payload.pageId);
  },

  collection_item_created: async (payload) => {
    console.log("CMS item created:", payload.itemId);
    // Sync to external database, index for search, etc.
  },

  collection_item_changed: async (payload) => {
    console.log("CMS item changed:", payload.itemId);
    // Update external database
  },

  collection_item_deleted: async (payload) => {
    console.log("CMS item deleted:", payload.itemId);
    // Remove from external database
  },

  collection_item_unpublished: async (payload) => {
    console.log("CMS item unpublished:", payload.itemId);
    // Remove from public-facing systems
  },
};

async function handleWebflowEvent(event: WebflowWebhookEvent): Promise<void> {
  const handler = eventHandlers[event.triggerType];

  if (!handler) {
    console.log(`Unhandled event type: ${event.triggerType}`);
    return;
  }

  await handler(event.payload);
  console.log(`Processed: ${event.triggerType}`);
}
```

### Step 4: Idempotent Processing

Prevent duplicate processing with event tracking:

```typescript
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL!);

async function processOnce(
  eventId: string,
  handler: () => Promise<void>
): Promise<boolean> {
  // SET NX — only succeeds if key doesn't exist
  const acquired = await redis.set(
    `webflow:event:${eventId}`,
    Date.now().toString(),
    "EX", 86400 * 7, // 7-day TTL
    "NX"
  );

  if (!acquired) {
    console.log(`Event ${eventId} already processed — skipping`);
    return false;
  }

  try {
    await handler();
    return true;
  } catch (error) {
    // Remove key on failure so retry can process
    await redis.del(`webflow:event:${eventId}`);
    throw error;
  }
}

// Usage in webhook handler
app.post("/webhooks/webflow", /* middleware */, async (req, res) => {
  res.status(200).json({ received: true });

  const event = JSON.parse(req.body.toString());
  const eventId = `${event.triggerType}-${Date.now()}`;

  await processOnce(eventId, () => handleWebflowEvent(event));
});
```

### Step 5: Testing Webhooks Locally

```bash
# Terminal 1: Start your server
npm run dev

# Terminal 2: Expose via ngrok
ngrok http 3000
# Copy the https:// URL

# Terminal 3: Register test webhook
curl -X POST "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/webhooks" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"triggerType\": \"form_submission\",
    \"url\": \"https://your-ngrok-url.ngrok.io/webhooks/webflow\"
  }"

# Now submit a form on your Webflow site — the webhook will hit your local server
```

## Output

- Webhook registrations for all needed trigger types
- HMAC-SHA256 signature verification on every request
- Type-safe event router handling all Webflow events
- Idempotent processing preventing duplicates
- Local testing workflow with ngrok

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Signature mismatch | Wrong secret or body parsing | Use `express.raw()`, not `express.json()` |
| Missing events | Webhook URL unreachable | Verify HTTPS endpoint is accessible |
| Duplicate processing | No idempotency check | Add Redis-based deduplication |
| 75 webhook limit | Too many registrations per trigger | Clean up unused webhooks |
| ngrok tunnel expired | Free tier 2-hour limit | Restart ngrok or use paid plan |

## Resources

- [Webhooks Guide](https://developers.webflow.com/data/docs/working-with-webhooks)
- [Webhooks API Reference](https://developers.webflow.com/data/reference/webhooks)
- [Create Webhook](https://developers.webflow.com/data/reference/webhooks/create)
- [Webhook Event Types](https://developers.webflow.com/data/reference/webhooks/events/form-submission)

## Next Steps

For performance optimization, see `webflow-performance-tuning`.
