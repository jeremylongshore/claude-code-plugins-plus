---
name: linear-webhooks-events
description: |
  Configure and handle Linear webhooks for real-time event processing.
  Use when setting up webhooks, handling Linear events,
  or building real-time integrations.
  Trigger with phrases like "linear webhooks", "linear events",
  "linear real-time", "handle linear webhook", "linear webhook setup".
allowed-tools: Read, Write, Edit, Bash(ngrok:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Webhooks & Events

## Overview
Set up and handle Linear webhooks for real-time event processing. Linear sends webhook payloads for issues, comments, projects, cycles, and other entities with HMAC-SHA256 signature verification.

## Prerequisites
- Linear workspace admin access
- Public HTTPS endpoint for webhook delivery
- Webhook signing secret (generated during webhook creation)

## Instructions

### Step 1: Create Webhook Endpoint
Build a webhook receiver with signature verification.

```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// IMPORTANT: parse raw body for signature verification
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const signature = req.headers["linear-signature"] as string;
  const delivery = req.headers["linear-delivery"] as string;
  const eventType = req.headers["linear-event"] as string;
  const body = req.body.toString();

  // Verify HMAC-SHA256 signature
  const expected = crypto
    .createHmac("sha256", process.env.LINEAR_WEBHOOK_SECRET!)
    .update(body)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    console.error(`Invalid signature for delivery ${delivery}`);
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(body);
  console.log(`Received ${eventType} ${event.action} (delivery: ${delivery})`);

  // Process asynchronously, respond quickly
  processEvent(event).catch(err => console.error("Processing failed:", err));
  res.status(200).json({ received: true });
});

app.listen(3000);
```

### Step 2: Event Processing Router
Route events by entity type and action.

```typescript
interface LinearWebhookPayload {
  action: "create" | "update" | "remove";
  type: string;  // "Issue", "Comment", "Project", "Cycle", etc.
  data: Record<string, any>;
  url: string;
  actor?: { id: string; type: string; name?: string };
  updatedFrom?: Record<string, any>;  // Previous values on update
  createdAt: string;
  webhookTimestamp: number;
}

type EventHandler = (event: LinearWebhookPayload) => Promise<void>;

const handlers: Record<string, Record<string, EventHandler>> = {
  Issue: {
    create: async (e) => {
      console.log(`New issue: ${e.data.identifier} — ${e.data.title}`);
      await notifySlack(`New issue: [${e.data.identifier}](${e.url}) ${e.data.title}`);
    },
    update: async (e) => {
      // Check what changed using updatedFrom
      if (e.updatedFrom?.stateId) {
        console.log(`${e.data.identifier} state changed to ${e.data.state?.name}`);
        if (e.data.state?.type === "completed") {
          await notifySlack(`Done: [${e.data.identifier}](${e.url}) ${e.data.title}`);
        }
      }
      if (e.updatedFrom?.assigneeId) {
        console.log(`${e.data.identifier} assigned to ${e.data.assignee?.name}`);
      }
    },
    remove: async (e) => {
      console.log(`Issue deleted: ${e.data.identifier}`);
    },
  },
  Comment: {
    create: async (e) => {
      console.log(`New comment on ${e.data.issue?.identifier}: ${e.data.body?.substring(0, 80)}`);
    },
  },
  Project: {
    update: async (e) => {
      if (e.updatedFrom?.state) {
        console.log(`Project "${e.data.name}" status: ${e.data.state}`);
      }
    },
  },
};

async function processEvent(event: LinearWebhookPayload): Promise<void> {
  const handler = handlers[event.type]?.[event.action];
  if (handler) {
    await handler(event);
  } else {
    console.log(`Unhandled: ${event.type}.${event.action}`);
  }
}
```

### Step 3: Idempotent Event Processing
Linear may retry webhook deliveries. Use the `Linear-Delivery` header as a deduplication key.

```typescript
const processedDeliveries = new Set<string>();

function isNewDelivery(deliveryId: string): boolean {
  if (processedDeliveries.has(deliveryId)) return false;
  processedDeliveries.add(deliveryId);
  // Clean up old entries periodically
  if (processedDeliveries.size > 10000) {
    const entries = [...processedDeliveries];
    entries.slice(0, 5000).forEach(id => processedDeliveries.delete(id));
  }
  return true;
}

// In webhook handler:
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const delivery = req.headers["linear-delivery"] as string;
  // ... signature verification ...

  if (!isNewDelivery(delivery)) {
    return res.status(200).json({ status: "duplicate, skipped" });
  }

  // Process event...
});
```

### Step 4: Register Webhook in Linear
```bash
# Via Linear UI: Settings > API > Webhooks > New webhook
# URL: https://your-app.com/webhooks/linear
# Select resource types: Issues, Comments, Projects

# Or via API:
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { webhookCreate(input: { url: \"https://your-app.com/webhooks/linear\", resourceTypes: [\"Issue\", \"Comment\", \"Project\"], allPublicTeams: true }) { success webhook { id enabled } } }"
  }'
```

### Step 5: Local Development with ngrok
```bash
# Start your webhook server
npm run dev  # listening on port 3000

# In another terminal, expose via ngrok
ngrok http 3000
# Copy the https://*.ngrok.io URL

# Create a webhook in Linear with the ngrok URL
# Settings > API > Webhooks > New webhook
# URL: https://abc123.ngrok.io/webhooks/linear
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid signature` (401) | Wrong webhook secret or body parsing | Use `express.raw()`, verify secret matches Linear settings |
| Webhook not received | URL not publicly accessible | Check HTTPS, firewall, ngrok tunnel |
| Duplicate processing | Linear retried delivery | Deduplicate using `Linear-Delivery` header |
| `Timeout` on delivery | Handler takes too long | Respond 200 immediately, process async |
| Missing `updatedFrom` | Field didn't change | `updatedFrom` only contains changed fields |

## Examples

### Slack Notification on Issue State Change
```typescript
async function notifySlack(message: string) {
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: message }),
  });
}

// In Issue.update handler:
if (e.updatedFrom?.stateId && e.data.state?.type === "completed") {
  await notifySlack(
    `:white_check_mark: *${e.data.identifier}* completed by ${e.actor?.name}\n${e.data.title}`
  );
}
```

### List Active Webhooks
```typescript
const client = getLinearClient();
const webhooks = await client.webhooks();
for (const wh of webhooks.nodes) {
  console.log(`${wh.url} — enabled: ${wh.enabled}, types: ${wh.resourceTypes}`);
}
```

## Output
- Express webhook endpoint with HMAC-SHA256 signature verification
- Event router dispatching by entity type and action
- Idempotent delivery processing using deduplication set
- Webhook registration via API and UI
- ngrok setup for local development testing

## Resources
- [Linear Webhooks Documentation](https://developers.linear.app/docs/graphql/webhooks)
- [Webhook Events Reference](https://developers.linear.app/docs/graphql/webhooks#webhook-events)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps
Optimize performance with `linear-performance-tuning`.
