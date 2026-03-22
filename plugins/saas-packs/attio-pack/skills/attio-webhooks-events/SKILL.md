---
name: attio-webhooks-events
description: |
  Implement Attio v2 webhooks -- subscribe to record/list/note/task events,
  verify signatures, filter by object or attribute, and handle idempotently.
  Trigger: "attio webhook", "attio events", "attio webhook signature",
  "handle attio events", "attio notifications", "attio real-time".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Webhooks & Events

## Overview

Attio v2 webhooks deliver real-time event notifications to your HTTPS endpoint. You can subscribe to specific event types and filter by object, list, or attribute to reduce volume. Webhooks are managed via `POST /v2/webhooks` and verified with HMAC-SHA256 signatures.

## Prerequisites

- HTTPS endpoint accessible from the internet
- Scopes: `webhook:read-write`
- `ATTIO_WEBHOOK_SECRET` stored securely

## Attio Webhook Event Types

| Category | Event types |
|----------|------------|
| Record | `record.created`, `record.updated`, `record.deleted`, `record.merged` |
| List Entry | `list-entry.created`, `list-entry.updated`, `list-entry.deleted` |
| Note | `note.created`, `note.updated`, `note.deleted` |
| Task | `task.created`, `task.updated`, `task.deleted` |
| Comment | `comment.created`, `comment.updated`, `comment.deleted` |
| List | `list.created`, `list.updated`, `list.deleted` |
| Object Attribute | `object-attribute.created`, `object-attribute.updated` |
| List Attribute | `list-attribute.created`, `list-attribute.updated` |
| Workspace Member | `workspace-member.created`, `workspace-member.updated` |
| Call Recording | `call-recording.created`, `call-recording.updated` |

## Instructions

### Step 1: Create a Webhook Subscription

```typescript
// Register webhook with event filtering
const webhook = await client.post<{
  data: {
    id: { workspace_id: string; webhook_id: string };
    target_url: string;
    subscriptions: Array<{ event_type: string; filter?: object }>;
    created_at: string;
  };
}>("/webhooks", {
  target_url: "https://yourapp.com/api/webhooks/attio",
  subscriptions: [
    // All record events
    { event_type: "record.created" },
    { event_type: "record.updated" },
    { event_type: "record.deleted" },

    // Only deal list-entry events (filtered)
    {
      event_type: "list-entry.created",
      filter: { list: { $eq: "sales_pipeline" } },
    },

    // Only updates to a specific attribute
    {
      event_type: "record.updated",
      filter: {
        $and: [
          { object: { $eq: "deals" } },
          { attribute: { $eq: "stage" } },
        ],
      },
    },

    // Notes and tasks
    { event_type: "note.created" },
    { event_type: "task.created" },
  ],
});

console.log("Webhook ID:", webhook.data.id.webhook_id);
```

### Step 2: List and Manage Webhooks

```typescript
// List all webhooks
const webhooks = await client.get<{
  data: Array<{
    id: { webhook_id: string };
    target_url: string;
    subscriptions: Array<{ event_type: string }>;
  }>;
}>("/webhooks");

// Get a specific webhook
const wh = await client.get(`/webhooks/${webhookId}`);

// Update webhook subscriptions
await client.patch(`/webhooks/${webhookId}`, {
  subscriptions: [
    { event_type: "record.created" },
    { event_type: "record.updated" },
  ],
});

// Delete a webhook
await client.delete(`/webhooks/${webhookId}`);
```

### Step 3: Webhook Endpoint with Signature Verification

```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// CRITICAL: Use raw body for signature verification
app.post(
  "/api/webhooks/attio",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-attio-signature"] as string;
    const timestamp = req.headers["x-attio-timestamp"] as string;

    // 1. Verify signature
    if (!verifyAttioWebhook(req.body, signature, timestamp)) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    // 2. Parse event
    const event = JSON.parse(req.body.toString());

    // 3. Return 200 immediately (Attio expects fast response)
    res.status(200).json({ received: true });

    // 4. Process asynchronously
    try {
      await processEvent(event);
    } catch (err) {
      console.error("Event processing failed:", event.event_type, err);
    }
  }
);

function verifyAttioWebhook(
  rawBody: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.ATTIO_WEBHOOK_SECRET!;

  // Reject timestamps older than 5 minutes (replay protection)
  const age = Date.now() - parseInt(timestamp) * 1000;
  if (age > 300_000) {
    console.error("Webhook timestamp too old:", age, "ms");
    return false;
  }

  // Compute expected signature
  const payload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  // Timing-safe comparison
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false;
  }
}
```

### Step 4: Event Handler with Type Routing

```typescript
interface AttioWebhookEvent {
  event_type: string;
  id: { event_id: string };
  created_at: string;
  actor: { type: string; id: string };
  object?: { id: { object_id: string }; api_slug: string };
  record?: { id: { record_id: string } };
  list?: { id: { list_id: string }; api_slug: string };
  entry?: { id: { entry_id: string } };
  // Additional fields vary by event type
}

type EventHandler = (event: AttioWebhookEvent) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  "record.created": async (event) => {
    const objectSlug = event.object?.api_slug;
    const recordId = event.record?.id?.record_id;
    console.log(`New ${objectSlug} record: ${recordId}`);

    if (objectSlug === "people") {
      // Fetch full record details
      const person = await client.get(
        `/objects/people/records/${recordId}`
      );
      await syncPersonToExternalSystem(person);
    }
  },

  "record.updated": async (event) => {
    console.log(`Updated ${event.object?.api_slug}: ${event.record?.id?.record_id}`);
    // Re-sync updated record
  },

  "record.deleted": async (event) => {
    console.log(`Deleted record: ${event.record?.id?.record_id}`);
    // Remove from external system
  },

  "record.merged": async (event) => {
    console.log(`Records merged into: ${event.record?.id?.record_id}`);
    // Update references in external system
  },

  "list-entry.created": async (event) => {
    console.log(`New entry in ${event.list?.api_slug}: ${event.entry?.id?.entry_id}`);
    // Trigger pipeline automation
  },

  "note.created": async (event) => {
    console.log("New note created");
    // Sync to external note system
  },

  "task.created": async (event) => {
    console.log("New task created");
    // Create corresponding task in project management tool
  },
};

async function processEvent(event: AttioWebhookEvent): Promise<void> {
  const handler = handlers[event.event_type];
  if (!handler) {
    console.log(`Unhandled event type: ${event.event_type}`);
    return;
  }
  await handler(event);
}
```

### Step 5: Idempotent Event Processing

```typescript
// Deduplicate events using a Set, Redis, or database
const processedEvents = new Set<string>();

async function processEventIdempotently(event: AttioWebhookEvent): Promise<void> {
  const eventId = event.id.event_id;

  if (processedEvents.has(eventId)) {
    console.log(`Duplicate event skipped: ${eventId}`);
    return;
  }

  await processEvent(event);
  processedEvents.add(eventId);

  // Clean up old entries (keep last 10,000)
  if (processedEvents.size > 10_000) {
    const entries = Array.from(processedEvents);
    entries.slice(0, entries.length - 10_000).forEach((id) => processedEvents.delete(id));
  }
}

// For production, use Redis:
// await redis.set(`attio:event:${eventId}`, "1", "EX", 86400 * 7);
```

### Step 6: Local Webhook Testing

```bash
# Expose local server with ngrok
ngrok http 3000

# Register ngrok URL as webhook target
curl -X POST https://api.attio.com/v2/webhooks \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://abc123.ngrok.io/api/webhooks/attio",
    "subscriptions": [{"event_type": "record.created"}]
  }'

# Create a test record to trigger the webhook
curl -X POST https://api.attio.com/v2/objects/people/records \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "values": {
        "email_addresses": ["webhook-test@example.com"],
        "name": [{"first_name": "Test", "last_name": "Webhook"}]
      }
    }
  }'

# Remember to delete the test webhook when done
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Signature mismatch | Wrong secret or body parsed before verification | Use `express.raw()`, verify raw body |
| Duplicate events | No idempotency | Track event IDs in Redis/DB |
| Missed events | Handler returns non-200 | Return 200 immediately, process async |
| Too many events | No filtering | Add filters to webhook subscriptions |
| Webhook deleted | Attio cleanup or token revoked | Re-register webhook, monitor with health check |

## Resources

- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)
- [Attio Webhook Events Reference](https://docs.attio.com/rest-api/webhook-reference/record-events/recordcreated)
- [Attio List Webhooks](https://docs.attio.com/rest-api/endpoint-reference/webhooks/list-webhooks)

## Next Steps

For performance optimization, see `attio-performance-tuning`.
