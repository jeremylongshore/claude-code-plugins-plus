---
name: supabase-webhooks-events
description: |
  Supabase webhook signature validation and event handling.
  Use when implementing webhook endpoints or processing Supabase events.
  Trigger with phrases like "supabase webhook", "supabase events",
  "supabase webhook signature", "handle supabase events".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Webhooks & Events

## Overview
Securely handle Supabase webhooks with signature validation and replay protection.

## Prerequisites
- supabase-install-auth completed
- Web server running (Express, Fastify, etc.)
- Supabase webhook secret from dashboard
- HTTPS endpoint for production

## Instructions

### Step 1: Webhook Endpoint Setup

### Express.js
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// IMPORTANT: Raw body needed for signature verification
app.post('/webhooks/supabase',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-supabase-signature'] as string;
    const timestamp = req.headers['x-supabase-timestamp'] as string;

    if (!verifySupabaseSignature(req.body, signature, timestamp)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await handleSupabaseEvent(event);

    res.status(200).json({ received: true });
  }
);
```

## Signature Verification

```typescript
function verifySupabaseSignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.SUPABASE_WEBHOOK_SECRET!;

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
type SupabaseEventType = 'resource.created' | 'resource.updated' | 'resource.deleted';

interface SupabaseEvent {
  id: string;
  type: SupabaseEventType;
  data: Record<string, any>;
  created: string;
}

const eventHandlers: Record<SupabaseEventType, (data: any) => Promise<void>> = {
  'resource.created': async (data) => { /* handle */ },
  'resource.updated': async (data) => { /* handle */ },
  'resource.deleted': async (data) => { /* handle */ }
};

async function handleSupabaseEvent(event: SupabaseEvent): Promise<void> {
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
  const key = `supabase:event:${eventId}`;
  const exists = await redis.exists(key);
  return exists === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `supabase:event:${eventId}`;
  await redis.set(key, '1', 'EX', 86400 * 7); // 7 days TTL
}
```

### Step 2: Webhook Testing

```bash
# Use Supabase CLI to send test events
supabase functions invoke webhook-handler

# Or use webhook.site for debugging
curl -X POST https://webhook.site/your-uuid \
  -H "Content-Type: application/json" \
  -d '{"type": "resource.created", "data": {}}'
```

## Output
- Webhook endpoint responding with 200 on valid signatures
- Events processed and logged
- Idempotency preventing duplicate processing
- Replay attacks rejected (timestamp validation)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature (401) | Wrong secret or payload tampering | Verify webhook secret matches dashboard |
| Timestamp too old | Replay attack or clock drift | Check server time sync, reject old events |
| Duplicate event | Event processed twice | Implement idempotency with Redis/DB |
| Handler timeout | Slow event processing | Use async queue for heavy processing |

## Examples

### Next.js API Route
```typescript
export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get('x-supabase-signature');

  if (!verifySignature(body, signature)) {
    return Response.json({ error: 'Invalid signature' }, { status: 401 });
  }

  const event = JSON.parse(body);
  await processEvent(event);

  return Response.json({ received: true });
}
```

## Resources
- [Supabase Webhooks Guide](https://supabase.com/docs/webhooks)
- [Webhook Security Best Practices](https://supabase.com/docs/webhooks/security)
- [Event Types Reference](https://supabase.com/docs/webhooks/events)

## Next Steps
For performance optimization, see `supabase-performance-tuning`.