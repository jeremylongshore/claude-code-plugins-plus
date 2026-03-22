---
name: klaviyo-webhooks-events
description: |
  Implement Klaviyo webhooks with HMAC-SHA256 signature verification and event handling.
  Use when setting up webhook endpoints, handling Klaviyo event notifications,
  or creating event-driven integrations with Klaviyo.
  Trigger with phrases like "klaviyo webhook", "klaviyo events",
  "klaviyo webhook signature", "handle klaviyo events", "klaviyo notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Webhooks & Events

## Overview

Set up Klaviyo webhooks with HMAC-SHA256 signature verification, event routing, idempotency handling, and the Webhooks API for programmatic subscription management.

## Prerequisites

- Klaviyo account with webhooks enabled
- HTTPS endpoint accessible from internet
- API key with scopes: `webhooks:read`, `webhooks:write`
- Redis or database for idempotency (recommended)

## Klaviyo Webhook Architecture

Klaviyo webhooks fire when specific **topics** occur in your account. Each webhook is signed with a **secret key** using HMAC-SHA256.

| Topic Category | Example Topics |
|---------------|---------------|
| Profile | `profile.created`, `profile.updated`, `profile.deleted` |
| List | `list.member.added`, `list.member.removed` |
| Segment | `segment.member.added`, `segment.member.removed` |
| Campaign | `campaign.sent`, `campaign.delivered` |
| Flow | `flow.triggered`, `flow.message.sent` |
| Event | Custom metric events |

## Instructions

### Step 1: Create a Webhook via API

```typescript
import { ApiKeySession, WebhooksApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const webhooksApi = new WebhooksApi(session);

// Create a webhook subscription
const webhook = await webhooksApi.createWebhook({
  data: {
    type: 'webhook',
    attributes: {
      name: 'Profile Updates',
      endpointUrl: 'https://your-app.com/webhooks/klaviyo',
      // The secret used for HMAC-SHA256 signing
      // Store this as KLAVIYO_WEBHOOK_SIGNING_SECRET
      description: 'Receives profile create/update events',
    },
    relationships: {
      webhookTopics: {
        data: [
          { type: 'webhook-topic', id: 'profile.created' },
          { type: 'webhook-topic', id: 'profile.updated' },
        ],
      },
    },
  },
});

console.log('Webhook ID:', webhook.body.data.id);
// Save the signing secret from the response
```

### Step 2: Signature Verification

```typescript
// src/klaviyo/webhook-verify.ts
import crypto from 'crypto';

/**
 * Verify Klaviyo webhook HMAC-SHA256 signature.
 * Klaviyo sends the signature in the webhook-signature header.
 */
export function verifyWebhookSignature(
  rawBody: Buffer | string,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) return false;

  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(typeof rawBody === 'string' ? rawBody : rawBody.toString())
    .digest('base64');

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false;
  }
}
```

### Step 3: Express Webhook Handler

```typescript
import express from 'express';
import { verifyWebhookSignature } from './klaviyo/webhook-verify';

const app = express();

// CRITICAL: Use raw body parser for signature verification
app.post('/webhooks/klaviyo',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // 1. Verify signature
    const signature = req.headers['webhook-signature'] as string;
    if (!verifyWebhookSignature(
      req.body,
      signature,
      process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET!
    )) {
      console.warn('[Webhook] Invalid signature rejected');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // 2. Parse event
    const event = JSON.parse(req.body.toString());

    // 3. Check idempotency (prevent duplicate processing)
    const eventId = event.id || event.data?.id;
    if (eventId && await isAlreadyProcessed(eventId)) {
      return res.status(200).json({ status: 'already_processed' });
    }

    // 4. Route to handler
    try {
      await routeWebhookEvent(event);
      if (eventId) await markProcessed(eventId);
      res.status(200).json({ received: true });
    } catch (error) {
      console.error('[Webhook] Processing failed:', error);
      res.status(500).json({ error: 'Processing failed' });
    }
  }
);
```

### Step 4: Event Router

```typescript
// src/klaviyo/webhook-router.ts

type WebhookHandler = (data: any) => Promise<void>;

const handlers: Record<string, WebhookHandler> = {
  'profile.created': async (data) => {
    const profile = data.attributes;
    console.log(`New profile: ${profile.email}`);
    // Sync to your database, trigger welcome flow, etc.
    await db.users.upsert({
      email: profile.email,
      firstName: profile.firstName,
      klaviyoProfileId: data.id,
    });
  },

  'profile.updated': async (data) => {
    const profile = data.attributes;
    console.log(`Updated profile: ${profile.email}`);
    await db.users.update({
      where: { klaviyoProfileId: data.id },
      data: { firstName: profile.firstName, lastName: profile.lastName },
    });
  },

  'list.member.added': async (data) => {
    console.log(`Profile ${data.relationships.profile.data.id} added to list ${data.relationships.list.data.id}`);
  },

  'campaign.sent': async (data) => {
    console.log(`Campaign sent: ${data.attributes.name}`);
    await analytics.track('campaign_sent', { campaignId: data.id });
  },
};

export async function routeWebhookEvent(event: any): Promise<void> {
  const topic = event.type || event.topic;
  const handler = handlers[topic];

  if (!handler) {
    console.log(`[Webhook] Unhandled topic: ${topic}`);
    return;
  }

  await handler(event.data || event);
}
```

### Step 5: Idempotency with Redis

```typescript
// src/klaviyo/webhook-idempotency.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
const TTL_SECONDS = 86400 * 7;  // 7 days

export async function isAlreadyProcessed(eventId: string): Promise<boolean> {
  const key = `klaviyo:webhook:${eventId}`;
  return (await redis.exists(key)) === 1;
}

export async function markProcessed(eventId: string): Promise<void> {
  const key = `klaviyo:webhook:${eventId}`;
  await redis.setex(key, TTL_SECONDS, new Date().toISOString());
}
```

### Step 6: List and Manage Webhooks

```typescript
// List all webhooks
const webhooks = await webhooksApi.getWebhooks();
for (const wh of webhooks.body.data) {
  console.log(`${wh.attributes.name}: ${wh.attributes.endpointUrl}`);
}

// Get webhook topics (available event types)
const topics = await webhooksApi.getWebhookTopics();
for (const topic of topics.body.data) {
  console.log(`Topic: ${topic.id} - ${topic.attributes.description}`);
}

// Delete a webhook
await webhooksApi.deleteWebhook({ id: 'WEBHOOK_ID' });
```

## Testing Webhooks Locally

```bash
# 1. Start your app
npm run dev  # localhost:3000

# 2. Expose via ngrok
ngrok http 3000

# 3. Register ngrok URL as webhook endpoint in Klaviyo
# https://abc123.ngrok.io/webhooks/klaviyo

# 4. Trigger an event (e.g., create a profile) and watch your logs
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong signing secret | Verify secret matches webhook creation response |
| Duplicate events | No idempotency | Track event IDs in Redis/DB |
| Webhook timeout | Slow processing | Return 200 immediately, process async |
| Missing events | Wrong topics subscribed | Check webhook topic subscriptions |
| Body parse error | Using JSON body parser | Must use `express.raw()` for signature verification |

## Resources

- [Webhooks API Overview](https://developers.klaviyo.com/en/reference/webhooks_api_overview)
- [Working with System Webhooks](https://developers.klaviyo.com/en/docs/working_with_system_webhooks)
- [Understanding Webhook Status Codes](https://developers.klaviyo.com/en/docs/understanding_webhook_status_codes)

## Next Steps

For performance optimization, see `klaviyo-performance-tuning`.
