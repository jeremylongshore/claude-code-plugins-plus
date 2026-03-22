---
name: klingai-webhooks-events
description: |
  Implement Kling AI webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Kling AI event notifications securely.
  Trigger with phrases like "klingai webhook", "klingai events",
  "klingai webhook signature", "handle klingai events", "klingai notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Webhooks & Events

## Overview
Securely handle Kling AI webhooks with signature validation and replay protection.

## Prerequisites
- Kling AI webhook secret configured
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
app.post('/webhooks/klingai',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-klingai-signature'] as string;
    const timestamp = req.headers['x-klingai-timestamp'] as string;

    if (!verifyKling AISignature(req.body, signature, timestamp)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await handleKling AIEvent(event);

    res.status(200).json({ received: true });
  }
);
```

## Signature Verification

```typescript
function verifyKling AISignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.KLINGAI_WEBHOOK_SECRET!;

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
type Kling AIEventType = 'resource.created' | 'resource.updated' | 'resource.deleted';

interface Kling AIEvent {
  id: string;
  type: Kling AIEventType;
  data: Record<string, any>;
  created: string;
}

const eventHandlers: Record<Kling AIEventType, (data: any) => Promise<void>> = {
  'resource.created': async (data) => { /* handle */ },
  'resource.updated': async (data) => { /* handle */ },
  'resource.deleted': async (data) => { /* handle */ }
};

async function handleKling AIEvent(event: Kling AIEvent): Promise<void> {
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
  const key = `klingai:event:${eventId}`;
  const exists = await redis.exists(key);
  return exists === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `klingai:event:${eventId}`;
  await redis.set(key, '1', 'EX', 86400 * 7); // 7 days TTL
}
```

## Webhook Testing

```bash
# Use Kling AI CLI to send test events
klingai webhooks trigger resource.created --url http://localhost:3000/webhooks/klingai

# Or use webhook.site for debugging
curl -X POST https://webhook.site/your-uuid \
  -H "Content-Type: application/json" \
  -d '{"type": "resource.created", "data": {}}'
```

## Instructions

### Step 1: Register Webhook Endpoint
Configure your webhook URL in the Kling AI dashboard.

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
curl -X POST https://your-ngrok-url/webhooks/klingai \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {}}'
```

## Resources
- [Kling AI Webhooks Guide](https://docs.klingai.com/webhooks)
- [Webhook Security Best Practices](https://docs.klingai.com/webhooks/security)

## Next Steps
For performance optimization, see `klingai-performance-tuning`.