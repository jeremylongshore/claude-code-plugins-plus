# Incoming Webhooks (Notifications) — Full Walkthrough

Handle incoming Intercom webhooks with signature verification, a topic router,
and idempotency so retried deliveries never double-process.

## Step 1: Webhook Endpoint with Signature Verification

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

## Step 2: Notification Payload Shape

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

## Step 3: Topic-Based Event Router

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

## Step 4: Idempotency (Prevent Duplicate Processing)

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
