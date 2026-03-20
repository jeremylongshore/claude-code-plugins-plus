---
name: apollo-webhooks-events
description: |
  Implement Apollo.io webhook handling.
  Use when receiving Apollo webhooks, processing event notifications,
  or building event-driven integrations.
  Trigger with phrases like "apollo webhooks", "apollo events",
  "apollo notifications", "apollo webhook handler", "apollo triggers".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Webhooks & Events

## Overview
Implement webhook handlers for Apollo.io to receive real-time notifications about contact updates, sequence events, and engagement activities. Apollo fires webhooks for events like `contact.created`, `contact.updated`, `sequence.replied`, and `sequence.bounced`.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ with Express or Fastify
- Publicly reachable endpoint (use ngrok for local dev)
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Define Event Types
```typescript
// src/webhooks/types.ts
export type ApolloEventType =
  | 'contact.created'
  | 'contact.updated'
  | 'contact.deleted'
  | 'sequence.replied'
  | 'sequence.bounced'
  | 'sequence.opened'
  | 'sequence.clicked'
  | 'sequence.unsubscribed'
  | 'account.updated';

export interface ApolloWebhookPayload {
  event: ApolloEventType;
  data: Record<string, any>;
  timestamp: string;
  webhook_id: string;
}
```

### Step 2: Create the Webhook Endpoint
```typescript
// src/webhooks/server.ts
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json({ limit: '1mb' }));

const WEBHOOK_SECRET = process.env.APOLLO_WEBHOOK_SECRET!;

function verifySignature(payload: string, signature: string): boolean {
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected),
  );
}

app.post('/webhooks/apollo', (req, res) => {
  const signature = req.headers['x-apollo-signature'] as string;
  const rawBody = JSON.stringify(req.body);

  if (signature && !verifySignature(rawBody, signature)) {
    console.error('Invalid webhook signature');
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Acknowledge immediately, process async
  res.status(200).json({ received: true });

  processWebhook(req.body).catch((err) =>
    console.error('Webhook processing failed:', err),
  );
});

app.listen(3000, () => console.log('Webhook server on port 3000'));
```

### Step 3: Implement Event Handlers
```typescript
// src/webhooks/handlers.ts
import { ApolloWebhookPayload, ApolloEventType } from './types';

type EventHandler = (data: Record<string, any>) => Promise<void>;

const handlers: Record<ApolloEventType, EventHandler> = {
  'contact.created': async (data) => {
    console.log(`New contact: ${data.first_name} ${data.last_name} (${data.email})`);
    // Sync to your CRM or database
    await syncContactToDatabase(data);
  },

  'contact.updated': async (data) => {
    console.log(`Contact updated: ${data.id}`);
    await updateContactInDatabase(data);
  },

  'contact.deleted': async (data) => {
    console.log(`Contact deleted: ${data.id}`);
    await markContactDeleted(data.id);
  },

  'sequence.replied': async (data) => {
    console.log(`Reply from ${data.contact_email} on sequence ${data.sequence_id}`);
    // Notify sales rep, pause sequence for this contact
    await notifySalesRep(data);
  },

  'sequence.bounced': async (data) => {
    console.warn(`Bounce: ${data.contact_email} — ${data.bounce_type}`);
    await handleBounce(data);
  },

  'sequence.opened': async (data) => {
    await trackEngagement('open', data);
  },

  'sequence.clicked': async (data) => {
    await trackEngagement('click', data);
  },

  'sequence.unsubscribed': async (data) => {
    await handleUnsubscribe(data);
  },

  'account.updated': async (data) => {
    await syncAccountData(data);
  },
};

export async function processWebhook(payload: ApolloWebhookPayload) {
  const handler = handlers[payload.event];
  if (!handler) {
    console.warn(`Unhandled event type: ${payload.event}`);
    return;
  }
  await handler(payload.data);
}
```

### Step 4: Add Idempotency Protection
```typescript
// src/webhooks/idempotency.ts
const processedEvents = new Map<string, number>();  // webhook_id -> timestamp
const TTL_MS = 24 * 60 * 60 * 1000;  // 24 hours

export function isDuplicate(webhookId: string): boolean {
  // Clean expired entries
  const now = Date.now();
  for (const [id, ts] of processedEvents) {
    if (now - ts > TTL_MS) processedEvents.delete(id);
  }

  if (processedEvents.has(webhookId)) return true;
  processedEvents.set(webhookId, now);
  return false;
}

// Use in the endpoint:
// if (isDuplicate(req.body.webhook_id)) {
//   return res.status(200).json({ received: true, duplicate: true });
// }
```

### Step 5: Register the Webhook in Apollo
```bash
# Register your endpoint via Apollo API
curl -X POST https://api.apollo.io/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "'$APOLLO_API_KEY'",
    "url": "https://your-domain.com/webhooks/apollo",
    "events": ["contact.created", "contact.updated", "sequence.replied", "sequence.bounced"],
    "active": true
  }'
```

## Output
- Express webhook endpoint with HMAC signature verification
- Event type definitions and typed handler registry
- Idempotency layer preventing duplicate processing
- Handlers for all Apollo event types (contact, sequence, account)
- Webhook registration via Apollo API

## Error Handling
| Issue | Resolution |
|-------|------------|
| Invalid signature | Verify `APOLLO_WEBHOOK_SECRET` matches Apollo config |
| Unknown event type | Log and return 200 (do not reject) |
| Processing failure | Return 200 immediately, process async, retry failed jobs |
| Duplicate events | Check `webhook_id` with idempotency map before processing |

## Examples

### Local Development with ngrok
```bash
# Start your webhook server
node dist/webhooks/server.js &

# Expose locally via ngrok
ngrok http 3000

# Register the ngrok URL as your webhook endpoint
curl -X POST https://api.apollo.io/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "'$APOLLO_API_KEY'",
    "url": "https://abc123.ngrok.io/webhooks/apollo",
    "events": ["contact.created", "sequence.replied"],
    "active": true
  }'
```

## Resources
- [Apollo Webhooks Documentation](https://apolloio.github.io/apollo-api-docs/#webhooks)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-best-practices)
- [ngrok for Local Development](https://ngrok.com/docs)

## Next Steps
Proceed to `apollo-performance-tuning` for optimization.
