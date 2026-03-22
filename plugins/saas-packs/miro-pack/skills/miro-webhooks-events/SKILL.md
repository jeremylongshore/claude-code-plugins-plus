---
name: miro-webhooks-events
description: |
  Implement Miro REST API v2 webhooks with board subscriptions, event handling,
  and signature verification for real-time board change notifications.
  Trigger with phrases like "miro webhook", "miro events",
  "miro board subscription", "miro real-time", "miro notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, webhooks, events]
compatible-with: claude-code
---

# Miro Webhooks & Events

## Overview

Receive real-time notifications when items on a Miro board change. Miro uses **board subscriptions** via the `/v2-experimental/webhooks/board_subscriptions` endpoint. All board item types are supported except tags, connectors, and comments.

## Prerequisites

- Access token with `boards:read` scope
- HTTPS endpoint accessible from the internet
- Webhook signing secret (generated when creating subscription)

## Create a Board Subscription

```typescript
// POST https://api.miro.com/v2-experimental/webhooks/board_subscriptions
async function createBoardSubscription(boardId: string, callbackUrl: string) {
  const response = await fetch(
    'https://api.miro.com/v2-experimental/webhooks/board_subscriptions',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        boardId,
        callbackUrl,       // Must be HTTPS
        status: 'enabled', // 'enabled' | 'disabled'
      }),
    }
  );

  const subscription = await response.json();
  console.log(`Subscription created: ${subscription.id}`);
  console.log(`Type: ${subscription.type}`);  // 'board_subscription'
  return subscription;
}
```

## Manage Subscriptions

```typescript
// List subscriptions
// GET https://api.miro.com/v2-experimental/webhooks/board_subscriptions
const list = await miroFetch('/v2-experimental/webhooks/board_subscriptions');

// Get a specific subscription
// GET https://api.miro.com/v2-experimental/webhooks/board_subscriptions/{subscription_id}
const sub = await miroFetch(`/v2-experimental/webhooks/board_subscriptions/${subId}`);

// Update subscription (enable/disable)
// PATCH https://api.miro.com/v2-experimental/webhooks/board_subscriptions/{subscription_id}
await miroFetch(`/v2-experimental/webhooks/board_subscriptions/${subId}`, 'PATCH', {
  status: 'disabled',
});

// Delete subscription
// DELETE https://api.miro.com/v2-experimental/webhooks/board_subscriptions/{subscription_id}
await miroFetch(`/v2-experimental/webhooks/board_subscriptions/${subId}`, 'DELETE');
```

## Event Payload Structure

When a board item is created, updated, or deleted, Miro sends a POST request to your callback URL:

```json
{
  "event": "board_subscription_changed",
  "type": "update",
  "boardId": "uXjVN1234567890",
  "item": {
    "id": "3458764500000001",
    "type": "sticky_note"
  },
  "changes": [
    {
      "property": "data.content",
      "previousValue": "Old text",
      "newValue": "Updated text"
    }
  ],
  "createdAt": "2025-01-15T10:30:00Z",
  "createdBy": {
    "id": "user-123",
    "type": "user"
  }
}
```

### Event Types

| `type` Value | Description | Item Types |
|-------------|-------------|------------|
| `create` | New item added to board | All except tags, connectors, comments |
| `update` | Item content/position/style changed | All except tags, connectors, comments |
| `delete` | Item removed from board | All except tags, connectors, comments |

## Webhook Handler (Express.js)

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// CRITICAL: Use raw body parser for signature verification
app.post('/webhooks/miro',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // Step 1: Verify signature
    const signature = req.headers['x-miro-signature'] as string;
    if (!verifySignature(req.body, signature)) {
      console.error('Invalid webhook signature — possible forgery');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Step 2: Parse event
    const event = JSON.parse(req.body.toString());

    // Step 3: Respond quickly (within 10 seconds)
    res.status(200).json({ received: true });

    // Step 4: Process asynchronously
    processEvent(event).catch(err =>
      console.error(`Failed to process event: ${err.message}`)
    );
  }
);

function verifySignature(rawBody: Buffer, signature: string): boolean {
  if (!signature) return false;

  const secret = process.env.MIRO_WEBHOOK_SECRET!;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expected, 'hex'),
    );
  } catch {
    return false;
  }
}
```

## Event Processing

```typescript
interface MiroBoardEvent {
  event: 'board_subscription_changed';
  type: 'create' | 'update' | 'delete';
  boardId: string;
  item: { id: string; type: string };
  changes?: Array<{ property: string; previousValue: unknown; newValue: unknown }>;
  createdAt: string;
  createdBy: { id: string; type: string };
}

async function processEvent(event: MiroBoardEvent): Promise<void> {
  const { type, boardId, item } = event;

  switch (type) {
    case 'create':
      console.log(`New ${item.type} created on board ${boardId}: ${item.id}`);
      // Fetch full item details if needed
      const fullItem = await miroFetch(`/v2/boards/${boardId}/items/${item.id}`);
      await syncToDatabase(fullItem);
      break;

    case 'update':
      console.log(`${item.type} updated on board ${boardId}: ${item.id}`);
      if (event.changes) {
        for (const change of event.changes) {
          console.log(`  ${change.property}: ${change.previousValue} → ${change.newValue}`);
        }
      }
      await updateInDatabase(item.id, event.changes);
      break;

    case 'delete':
      console.log(`${item.type} deleted from board ${boardId}: ${item.id}`);
      await deleteFromDatabase(item.id);
      break;
  }
}
```

## Idempotency Guard

Miro may deliver the same event multiple times. Prevent duplicate processing:

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function processOnce(eventId: string, handler: () => Promise<void>): Promise<void> {
  const key = `miro:webhook:${eventId}`;

  // SET NX with TTL — returns 'OK' only if key was newly set
  const result = await redis.set(key, '1', 'EX', 86400 * 7, 'NX');  // 7 days TTL
  if (result !== 'OK') {
    console.log(`Duplicate event ${eventId} — skipping`);
    return;
  }

  await handler();
}
```

## Webhook Testing

```bash
# Test with ngrok for local development
ngrok http 3000
# Register https://your-ngrok.ngrok-free.app/webhooks/miro as callback URL

# Manually test your endpoint
curl -X POST http://localhost:3000/webhooks/miro \
  -H "Content-Type: application/json" \
  -H "X-Miro-Signature: $(echo -n '{"event":"board_subscription_changed","type":"create","boardId":"test","item":{"id":"123","type":"sticky_note"}}' | openssl dgst -sha256 -hmac "$MIRO_WEBHOOK_SECRET" | awk '{print $2}')" \
  -d '{"event":"board_subscription_changed","type":"create","boardId":"test","item":{"id":"123","type":"sticky_note"}}'

# Use Pipedream for webhook debugging
# See: https://developers.miro.com/docs/set-up-a-test-endpoint-for-webhooks
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| No events received | Subscription disabled | Check subscription status |
| Invalid signature | Wrong secret | Verify MIRO_WEBHOOK_SECRET matches app settings |
| Event processing timeout | Slow handler | Return 200 immediately, process async |
| Duplicate events | Miro retry delivery | Implement idempotency with event ID |
| Missing item types | Tags/connectors/comments excluded | Use polling for those types |

## Resources

- [Getting Started with Webhooks](https://developers.miro.com/docs/getting-started-with-webhooks)
- [Create Board Subscription](https://developers.miro.com/reference/create-board-subscription)
- [Set Up Test Endpoint](https://developers.miro.com/docs/set-up-a-test-endpoint-for-webhooks)
- [Webhooks with Python](https://developers.miro.com/docs/getting-started-with-webhooks-python)

## Next Steps

For performance optimization, see `miro-performance-tuning`.
