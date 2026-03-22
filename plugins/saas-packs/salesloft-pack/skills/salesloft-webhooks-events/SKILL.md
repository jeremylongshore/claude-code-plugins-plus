---
name: salesloft-webhooks-events
description: |
  Implement SalesLoft webhook handling with signature verification and event routing.
  Use when setting up webhook endpoints, handling activity notifications,
  or syncing SalesLoft data to external systems in real-time.
  Trigger: "salesloft webhook", "salesloft events", "salesloft notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Webhooks & Events

## Overview

Handle SalesLoft webhook notifications for real-time data sync. SalesLoft sends webhooks for person updates, email events (sent, opened, clicked, replied, bounced), call completions, and cadence membership changes. Webhooks use HMAC-SHA256 signatures.

## Instructions

### Step 1: Register Webhook in SalesLoft

Configure webhooks in SalesLoft Settings > Integrations > Webhooks:
- URL: `https://your-app.com/webhooks/salesloft`
- Events: Select specific events (person.updated, email.sent, etc.)
- Copy the webhook signing secret

### Step 2: Signature Verification

```typescript
import crypto from 'crypto';
import express from 'express';

function verifySalesloftWebhook(
  rawBody: Buffer,
  signature: string,
  timestamp: string,
): boolean {
  const secret = process.env.SALESLOFT_WEBHOOK_SECRET!;

  // Replay protection: reject webhooks older than 5 minutes
  const age = Math.abs(Date.now() / 1000 - parseInt(timestamp));
  if (age > 300) return false;

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${rawBody.toString()}`)
    .digest('hex');

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

### Step 3: Event Router

```typescript
interface SalesloftWebhookEvent {
  event_type: string; // e.g., 'person.created', 'email.sent', 'call.completed'
  event_id: string;
  data: Record<string, any>;
  created_at: string;
}

const handlers: Record<string, (data: any) => Promise<void>> = {
  'person.created': async (data) => {
    console.log(`New person: ${data.email_address}`);
    await syncToExternalCRM(data);
  },
  'person.updated': async (data) => {
    await updateExternalCRM(data.id, data);
  },
  'email.sent': async (data) => {
    await logActivity('email_sent', data);
  },
  'email.opened': async (data) => {
    await logActivity('email_opened', data);
  },
  'email.clicked': async (data) => {
    await logActivity('email_clicked', data);
  },
  'email.replied': async (data) => {
    await logActivity('email_replied', data);
    await notifySalesRep(data.person_id, 'Reply received!');
  },
  'email.bounced': async (data) => {
    await markEmailInvalid(data.person_id);
  },
  'call.completed': async (data) => {
    await logActivity('call', { ...data, duration: data.duration });
  },
};
```

### Step 4: Express Webhook Endpoint

```typescript
const app = express();

app.post('/webhooks/salesloft',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const sig = req.headers['x-salesloft-signature'] as string;
    const ts = req.headers['x-salesloft-timestamp'] as string;

    if (!verifySalesloftWebhook(req.body, sig, ts)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event: SalesloftWebhookEvent = JSON.parse(req.body.toString());

    // Idempotency: skip already-processed events
    if (await isProcessed(event.event_id)) {
      return res.status(200).json({ status: 'already_processed' });
    }

    // Respond immediately, process async
    res.status(200).json({ received: true });

    try {
      const handler = handlers[event.event_type];
      if (handler) {
        await handler(event.data);
        await markProcessed(event.event_id);
      }
    } catch (err) {
      console.error(`Failed: ${event.event_type} ${event.event_id}`, err);
      await queueForRetry(event);
    }
  }
);
```

### Step 5: Idempotency Store

```typescript
import { Redis } from 'ioredis';
const redis = new Redis(process.env.REDIS_URL!);

async function isProcessed(eventId: string): Promise<boolean> {
  return (await redis.exists(`sl:event:${eventId}`)) === 1;
}

async function markProcessed(eventId: string): Promise<void> {
  await redis.set(`sl:event:${eventId}`, '1', 'EX', 604800); // 7-day TTL
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret or body parsing | Use raw body parser, verify secret |
| Duplicate events | Webhook retries | Idempotency check by `event_id` |
| Timeout on processing | Heavy handler logic | Respond 200 immediately, process async |
| Missing events | Wrong event subscription | Check webhook config in SalesLoft dashboard |

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [SalesLoft Developer Portal](https://developers.salesloft.com/)

## Next Steps

For performance optimization, see `salesloft-performance-tuning`.
