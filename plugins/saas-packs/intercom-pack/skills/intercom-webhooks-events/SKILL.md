---
name: intercom-webhooks-events
description: |
  Implement Intercom webhook handling and data event tracking.
  Use when setting up webhook endpoints, processing Intercom notifications,
  or submitting custom data events for contact activity tracking.
  Trigger with phrases like "intercom webhook", "intercom events",
  "intercom webhook signature", "handle intercom events", "intercom data events",
  "track intercom events".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Webhooks & Events

## Overview

Handle incoming Intercom webhooks (notifications) with signature verification and implement outbound data event tracking via the Events API.

## Prerequisites

- HTTPS endpoint accessible from internet
- Webhook secret from Intercom Developer Hub
- `intercom-client` SDK installed
- Redis or database for idempotency (recommended)

## Part 1: Incoming Webhooks (Notifications)

### Step 1: Webhook Endpoint with Signature Verification

Intercom signs webhooks with HMAC-SHA1 via the `X-Hub-Signature` header.

```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// IMPORTANT: Use raw body for signature verification
app.post(
  "/webhooks/intercom",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-hub-signature"] as string;
    const secret = process.env.INTERCOM_WEBHOOK_SECRET!;

    if (!signature) {
      return res.status(401).json({ error: "Missing X-Hub-Signature" });
    }

    // Verify HMAC-SHA1 signature
    const expected = "sha1=" + crypto
      .createHmac("sha1", secret)
      .update(req.body)
      .digest("hex");

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    // MUST respond within 5 seconds or Intercom treats as failure
    // Parse and queue for async processing
    const notification = JSON.parse(req.body.toString());
    res.status(200).json({ received: true });

    // Process asynchronously after responding
    processWebhookAsync(notification).catch(console.error);
  }
);
```

### Step 2: Notification Payload Shape

```typescript
// Every Intercom webhook notification follows this structure
interface IntercomNotification {
  type: "notification_event";
  id: string;                        // Unique notification ID
  topic: string;                     // e.g., "conversation.user.created"
  app_id: string;                    // Your app ID
  created_at: number;                // Unix timestamp
  delivery_attempts: number;         // 1 on first try, 2 on retry
  data: {
    type: "notification_event_data";
    item: any;                       // The actual resource (conversation, contact, etc.)
  };
}

// Example: conversation.user.created
// {
//   "type": "notification_event",
//   "id": "notif_abc123",
//   "topic": "conversation.user.created",
//   "created_at": 1711100000,
//   "data": {
//     "type": "notification_event_data",
//     "item": {
//       "type": "conversation",
//       "id": "123",
//       "state": "open",
//       "source": { "body": "Hi, I need help!" },
//       "contacts": { "contacts": [{ "id": "contact-1", "type": "contact" }] }
//     }
//   }
// }
```

### Step 3: Topic-Based Event Router

```typescript
type WebhookHandler = (data: any) => Promise<void>;

const handlers: Record<string, WebhookHandler> = {
  "conversation.user.created": async (data) => {
    const conversation = data.item;
    console.log(`New conversation: ${conversation.id}`);
    // Notify support channel, auto-assign, etc.
  },

  "conversation.user.replied": async (data) => {
    const conversation = data.item;
    console.log(`Customer replied to: ${conversation.id}`);
    // Update ticket system, escalate if needed
  },

  "conversation.admin.closed": async (data) => {
    const conversation = data.item;
    console.log(`Conversation closed: ${conversation.id}`);
    // Send satisfaction survey, update CRM
  },

  "contact.created": async (data) => {
    const contact = data.item;
    console.log(`New contact: ${contact.id} (${contact.email})`);
    // Sync to CRM, enrich data, trigger welcome flow
  },

  "contact.tag.created": async (data) => {
    const contact = data.item;
    console.log(`Contact tagged: ${contact.id}`);
    // Trigger automation based on tag
  },
};

async function processWebhookAsync(notification: IntercomNotification): Promise<void> {
  const handler = handlers[notification.topic];

  if (!handler) {
    console.log(`Unhandled topic: ${notification.topic}`);
    return;
  }

  try {
    await handler(notification.data);
    console.log(`Processed ${notification.topic}: ${notification.id}`);
  } catch (error) {
    console.error(`Failed ${notification.topic}: ${notification.id}`, error);
    // Dead-letter queue for failed events
  }
}
```

### Step 4: Idempotency (Prevent Duplicate Processing)

Intercom retries failed webhooks once after 1 minute. Guard against duplicates:

```typescript
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

async function processIdempotent(
  notification: IntercomNotification,
  handler: () => Promise<void>
): Promise<void> {
  const key = `intercom:webhook:${notification.id}`;

  // SET NX: only succeeds if key doesn't exist
  const acquired = await redis.set(key, "processing", "EX", 86400 * 7, "NX");

  if (!acquired) {
    console.log(`Duplicate webhook skipped: ${notification.id}`);
    return;
  }

  try {
    await handler();
    await redis.set(key, "completed", "EX", 86400 * 7);
  } catch (error) {
    await redis.del(key); // Allow retry on failure
    throw error;
  }
}
```

## Part 2: Outbound Data Events

Submit custom events to track contact activity in Intercom.

### Step 5: Track Data Events

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// Submit a data event
await client.dataEvents.create({
  eventName: "completed-onboarding",
  createdAt: Math.floor(Date.now() / 1000),
  userId: "user-12345", // External ID of the contact
  metadata: {
    steps_completed: 5,
    time_to_complete_minutes: 12,
    plan: "pro",
  },
});

// Event naming convention: past-tense verb-noun
// Good: "placed-order", "upgraded-plan", "invited-teammate"
// Bad: "order", "click", "page_view"
```

### Step 6: Bulk Event Submission

```typescript
// Submit events for multiple users efficiently
async function trackBulkEvents(
  client: IntercomClient,
  events: Array<{ userId: string; eventName: string; metadata?: Record<string, any> }>
): Promise<{ succeeded: number; failed: number }> {
  let succeeded = 0;
  let failed = 0;

  // Intercom doesn't have a batch events endpoint; throttle individual calls
  for (const event of events) {
    try {
      await client.dataEvents.create({
        eventName: event.eventName,
        createdAt: Math.floor(Date.now() / 1000),
        userId: event.userId,
        metadata: event.metadata,
      });
      succeeded++;

      // Rate limit: slight delay between calls
      if (succeeded % 50 === 0) {
        await new Promise(r => setTimeout(r, 500));
      }
    } catch (error) {
      failed++;
      console.error(`Failed to track event for ${event.userId}:`, error);
    }
  }

  return { succeeded, failed };
}
```

## Available Webhook Topics

| Topic | Description |
|-------|-------------|
| `conversation.user.created` | New conversation from contact |
| `conversation.user.replied` | Contact replies to conversation |
| `conversation.admin.replied` | Admin replies to conversation |
| `conversation.admin.closed` | Conversation closed by admin |
| `conversation.admin.opened` | Conversation reopened |
| `conversation.admin.snoozed` | Conversation snoozed |
| `conversation.admin.assigned` | Conversation reassigned |
| `contact.created` | New contact created |
| `contact.signed_up` | Lead converts to user |
| `contact.tag.created` | Tag applied to contact |
| `contact.tag.deleted` | Tag removed from contact |
| `visitor.signed_up` | Visitor becomes lead |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Secret mismatch | Verify secret matches Developer Hub |
| Timeout (5s) | Slow processing | Queue events, respond immediately |
| Duplicate events | Retry delivery | Implement idempotency with Redis |
| Missing topic handler | New topic added | Log unhandled topics, add handler |
| Event rejected (422) | Invalid user_id or event_name | Verify contact exists, use verb-noun naming |

## Resources

- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)
- [Webhook Topics](https://developers.intercom.com/docs/references/webhooks/webhook-models)
- [Webhook Notifications](https://developers.intercom.com/docs/webhooks/webhook-notifications)
- [Data Events API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/data-events)

## Next Steps

For performance optimization, see `intercom-performance-tuning`.
