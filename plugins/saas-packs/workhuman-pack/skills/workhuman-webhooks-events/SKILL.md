---
name: workhuman-webhooks-events
description: |
  Implement Workhuman webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Workhuman event notifications securely.
  Trigger with phrases like "workhuman webhook", "workhuman events",
  "workhuman webhook signature", "handle workhuman events", "workhuman notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, workhuman]
---

# Workhuman Webhooks & Events

## Overview
Securely handle Workhuman webhooks with signature validation and replay protection.

## Prerequisites
- Workhuman webhook secret configured
- HTTPS endpoint accessible from internet
- Understanding of cryptographic signatures
- Redis or database for idempotency (optional)

## Webhook Endpoint Setup

### Express.js
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// IMPORTANT: Raw body needed for signature verification
app.post('/webhooks/workhuman',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-workhuman-signature'] as string;
    const timestamp = req.headers['x-workhuman-timestamp'] as string;

    if (!verifyWorkhumanSignature(req.body, signature, timestamp)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await handleWorkhumanEvent(event);

    res.status(200).json({ received: true });
  }
);
```

## Signature Verification

```typescript
function verifyWorkhumanSignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.WORKHUMAN_WEBHOOK_SECRET!;

  // Reject old timestamps (replay attack protection)
  const timestampAge = Date.now() - parseInt(timestamp) * 1000;
  if (timestampAge > 300000) { // 5 minutes
    console.error('Webhook timestamp too old');
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload.toString()}`;
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');

  // Timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}
```

## Event Handler Pattern

```typescript
type WorkhumanEventType = 'resource.created' | 'resource.updated' | 'resource.deleted';

interface WorkhumanEvent {
  id: string;
  type: WorkhumanEventType;
  data: Record<string, any>;
  created: string;
}

const eventHandlers: Record<WorkhumanEventType, (data: any) => Promise<void>> = {
  'resource.created': async (data) => { /* handle */ },
  'resource.updated': async (data) => { /* handle */ },
  'resource.deleted': async (data) => { /* handle */ }
};

async function handleWorkhumanEvent(event: WorkhumanEvent): Promise<void> {
  const handler = eventHandlers[event.type];

  if (!handler) {
    console.log(`Unhandled event type: ${event.type}`);
    return;
  }

  try {
    await handler(event.data);
    console.log(`Processed ${event.type}: ${event.id}`);
  } catch (error) {
    console.error(`Failed to process ${event.type}: ${event.id}`, error);
    throw error; // Rethrow to trigger retry
  }
}
```

## Idempotency Handling

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function isEventProcessed(eventId: string): Promise<boolean> {
  const key = `workhuman:event:${eventId}`;
  const exists = await redis.exists(key);
  return exists === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `workhuman:event:${eventId}`;
  await redis.set(key, '1', 'EX', 86400 * 7); // 7 days TTL
}
```

## Webhook Testing

```bash
# Use Workhuman CLI to send test events
workhuman webhooks trigger resource.created --url http://localhost:3000/webhooks/workhuman

# Or use webhook.site for debugging
curl -X POST https://webhook.site/your-uuid \
  -H "Content-Type: application/json" \
  -d '{"type": "resource.created", "data": {}}'
```

## Instructions

### Step 1: Register Webhook Endpoint
Configure your webhook URL in the Workhuman dashboard.

### Step 2: Implement Signature Verification
Use the signature verification code to validate incoming webhooks.

### Step 3: Handle Events
Implement handlers for each event type your application needs.

### Step 4: Add Idempotency
Prevent duplicate processing with event ID tracking.

## Output
- Secure webhook endpoint
- Signature validation enabled
- Event handlers implemented
- Replay attack protection active

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Timestamp rejected | Clock drift | Check server time sync |
| Duplicate events | Missing idempotency | Implement event ID tracking |
| Handler timeout | Slow processing | Use async queue |

## Examples

### Testing Webhooks Locally
```bash
# Use ngrok to expose local server
ngrok http 3000

# Send test webhook
curl -X POST https://your-ngrok-url/webhooks/workhuman \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {}}'
```

## Resources
- [Workhuman Webhooks Guide](https://docs.workhuman.com/webhooks)
- [Webhook Security Best Practices](https://docs.workhuman.com/webhooks/security)

## Next Steps
For performance optimization, see `workhuman-performance-tuning`.