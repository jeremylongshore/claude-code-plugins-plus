---
name: coderabbit-webhooks-events
description: |
  Implement CodeRabbit webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling CodeRabbit event notifications securely.
  Trigger with phrases like "coderabbit webhook", "coderabbit events",
  "coderabbit webhook signature", "handle coderabbit events", "coderabbit notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coderabbit]
---

# CodeRabbit Webhooks & Events

## Overview
Securely handle CodeRabbit webhooks with signature validation and replay protection.

## Prerequisites
- CodeRabbit webhook secret configured
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
app.post('/webhooks/coderabbit',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-coderabbit-signature'] as string;
    const timestamp = req.headers['x-coderabbit-timestamp'] as string;

    if (!verifyCodeRabbitSignature(req.body, signature, timestamp)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await handleCodeRabbitEvent(event);

    res.status(200).json({ received: true });
  }
);
```

## Signature Verification

```typescript
function verifyCodeRabbitSignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.CODERABBIT_WEBHOOK_SECRET!;

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
type CodeRabbitEventType = 'resource.created' | 'resource.updated' | 'resource.deleted';

interface CodeRabbitEvent {
  id: string;
  type: CodeRabbitEventType;
  data: Record<string, any>;
  created: string;
}

const eventHandlers: Record<CodeRabbitEventType, (data: any) => Promise<void>> = {
  'resource.created': async (data) => { /* handle */ },
  'resource.updated': async (data) => { /* handle */ },
  'resource.deleted': async (data) => { /* handle */ }
};

async function handleCodeRabbitEvent(event: CodeRabbitEvent): Promise<void> {
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
  const key = `coderabbit:event:${eventId}`;
  const exists = await redis.exists(key);
  return exists === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `coderabbit:event:${eventId}`;
  await redis.set(key, '1', 'EX', 86400 * 7); // 7 days TTL
}
```

## Webhook Testing

```bash
# Use CodeRabbit CLI to send test events
coderabbit webhooks trigger resource.created --url http://localhost:3000/webhooks/coderabbit

# Or use webhook.site for debugging
curl -X POST https://webhook.site/your-uuid \
  -H "Content-Type: application/json" \
  -d '{"type": "resource.created", "data": {}}'
```

## Instructions

### Step 1: Register Webhook Endpoint
Configure your webhook URL in the CodeRabbit dashboard.

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
curl -X POST https://your-ngrok-url/webhooks/coderabbit \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {}}'
```

## Resources
- [CodeRabbit Webhooks Guide](https://docs.coderabbit.com/webhooks)
- [Webhook Security Best Practices](https://docs.coderabbit.com/webhooks/security)

## Next Steps
For performance optimization, see `coderabbit-performance-tuning`.