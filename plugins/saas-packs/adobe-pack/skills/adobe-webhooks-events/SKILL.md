---
name: adobe-webhooks-events
description: |
  Implement Adobe I/O Events webhook registration, RSA-SHA256 signature
  verification, challenge handshake, and event-driven architectures
  with Creative Cloud, Experience Platform, and Firefly Services events.
  Trigger with phrases like "adobe webhook", "adobe events",
  "adobe I/O events", "adobe event registration", "adobe notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Webhooks & Events

## Overview

Implement Adobe I/O Events webhook endpoints with proper challenge-response handshake, RSA-SHA256 digital signature verification, and event routing for Creative Cloud Libraries, Experience Platform, and Firefly Services events.

## Prerequisites

- Adobe Developer Console project with Events API enabled
- HTTPS endpoint accessible from the internet
- `@adobe/aio-lib-events` installed (optional, for SDK approach)
- Understanding of Adobe I/O Events architecture

## Instructions

### Step 1: Register Webhook via Adobe I/O Events API

```typescript
// Register a webhook endpoint programmatically
import { getAccessToken } from '../adobe/client';

interface EventRegistration {
  name: string;
  description: string;
  webhookUrl: string;
  eventsOfInterest: Array<{
    provider_id: string;   // Event provider (e.g., Creative Cloud)
    event_code: string;    // Specific event type
  }>;
  deliveryType: 'webhook' | 'webhook_batch';
}

export async function registerWebhook(reg: EventRegistration): Promise<any> {
  const token = await getAccessToken();

  const response = await fetch(
    `https://api.adobe.io/events/${process.env.ADOBE_IMS_ORG_ID}/integrations/${process.env.ADOBE_INTEGRATION_ID}/registrations`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        client_id: process.env.ADOBE_CLIENT_ID,
        name: reg.name,
        description: reg.description,
        webhook_url: reg.webhookUrl,
        events_of_interest: reg.eventsOfInterest,
        delivery_type: reg.deliveryType || 'webhook',
      }),
    }
  );

  if (!response.ok) throw new Error(`Registration failed: ${await response.text()}`);
  return response.json();
}

// Example: Register for Creative Cloud Library events
await registerWebhook({
  name: 'CC Library Updates',
  description: 'Track Creative Cloud Library changes',
  webhookUrl: 'https://api.yourapp.com/webhooks/adobe',
  eventsOfInterest: [
    { provider_id: 'ccstorage', event_code: 'library_create' },
    { provider_id: 'ccstorage', event_code: 'library_update' },
    { provider_id: 'ccstorage', event_code: 'library_delete' },
  ],
  deliveryType: 'webhook',
});
```

### Step 2: Implement Challenge-Response Handshake

When registering a webhook, Adobe sends a `GET` request with a `challenge` query parameter. Your endpoint must respond with the challenge value:

```typescript
import express from 'express';
const app = express();

app.get('/webhooks/adobe', (req, res) => {
  // Adobe challenge verification during registration
  const challenge = req.query.challenge as string;
  if (challenge) {
    console.log('Adobe webhook challenge received');
    return res.status(200).json({ challenge });
  }
  res.status(400).json({ error: 'Missing challenge parameter' });
});
```

### Step 3: Verify RSA-SHA256 Digital Signatures

Adobe I/O Events uses RSA-SHA256 (not HMAC). Public keys are served from `static.adobeioevents.com`:

```typescript
import crypto from 'crypto';

const publicKeyCache = new Map<string, string>();

async function fetchPublicKey(keyPath: string): Promise<string> {
  if (publicKeyCache.has(keyPath)) return publicKeyCache.get(keyPath)!;
  const res = await fetch(`https://static.adobeioevents.com${keyPath}`);
  if (!res.ok) throw new Error(`Failed to fetch Adobe public key: ${res.status}`);
  const key = await res.text();
  publicKeyCache.set(keyPath, key);
  return key;
}

async function verifyAdobeSignature(rawBody: Buffer, headers: Record<string, string>): Promise<boolean> {
  for (const idx of ['1', '2']) {
    const sig = headers[`x-adobe-digital-signature-${idx}`];
    const keyPath = headers[`x-adobe-public-key${idx}-path`];
    if (!sig || !keyPath) continue;

    try {
      const publicKey = await fetchPublicKey(keyPath);
      const verifier = crypto.createVerify('RSA-SHA256');
      verifier.update(rawBody);
      if (verifier.verify(publicKey, sig, 'base64')) return true;
    } catch (err) {
      console.warn(`Adobe signature-${idx} verification error:`, err);
    }
  }
  return false;
}
```

### Step 4: Event Handler with Routing

```typescript
// POST handler for incoming events
app.post('/webhooks/adobe',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // Verify signature
    if (!await verifyAdobeSignature(req.body, req.headers as any)) {
      console.error('Invalid Adobe webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());

    // Route by event type
    try {
      await routeAdobeEvent(event);
      res.status(200).json({ received: true });
    } catch (error: any) {
      console.error('Event processing failed:', error);
      res.status(500).json({ error: error.message });
    }
  }
);

// Event type definitions
type AdobeEventType =
  | 'library_create'
  | 'library_update'
  | 'library_delete'
  | 'asset_created'
  | 'asset_updated';

interface AdobeEvent {
  event_id: string;
  event: {
    type: AdobeEventType;
    activitystreams?: any;
    xdmEntity?: any;
  };
  recipient_client_id: string;
}

const eventHandlers: Partial<Record<AdobeEventType, (event: AdobeEvent) => Promise<void>>> = {
  library_create: async (event) => {
    console.log('New CC Library created:', event.event_id);
    // Sync library metadata to your database
  },
  library_update: async (event) => {
    console.log('CC Library updated:', event.event_id);
    // Refresh cached library data
  },
  library_delete: async (event) => {
    console.log('CC Library deleted:', event.event_id);
    // Remove from local cache/database
  },
};

async function routeAdobeEvent(event: AdobeEvent): Promise<void> {
  const handler = eventHandlers[event.event.type];
  if (handler) {
    await handler(event);
  } else {
    console.log(`Unhandled Adobe event type: ${event.event.type}`);
  }
}
```

### Step 5: Idempotency (Prevent Duplicate Processing)

```typescript
import { Redis } from 'ioredis';
const redis = new Redis(process.env.REDIS_URL);

async function processEventIdempotently(event: AdobeEvent): Promise<boolean> {
  const key = `adobe:event:${event.event_id}`;
  // SET NX with 7-day TTL — returns null if key already exists
  const result = await redis.set(key, '1', 'EX', 86400 * 7, 'NX');

  if (!result) {
    console.log(`Duplicate Adobe event skipped: ${event.event_id}`);
    return false; // Already processed
  }

  await routeAdobeEvent(event);
  return true;
}
```

## Output

- Webhook registered with Adobe I/O Events
- Challenge-response handshake handler for registration
- RSA-SHA256 signature verification with key caching
- Event routing by type with handler pattern
- Idempotency via Redis to prevent duplicate processing

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Challenge response 400 | Missing JSON content-type | Return `{ challenge }` as JSON |
| Signature always invalid | Not using raw body | Use `express.raw()` before parsing |
| Events not arriving | Registration failed | Check I/O Events dashboard for status |
| Duplicate events | No idempotency | Track `event_id` in Redis/DB |
| Public key fetch fails | Network/firewall | Whitelist `static.adobeioevents.com` |

## Resources

- [Adobe I/O Events Webhooks Guide](https://developer.adobe.com/events/docs/guides/)
- [I/O Events Registration API](https://developer.adobe.com/events/docs/guides/api/registration-api)
- [Signature Verification SDK](https://developer.adobe.com/events/docs/guides/sdk/sdk_signature_verification/)
- [CC Libraries Events](https://developer.adobe.com/creative-cloud-libraries/docs/integrate/guides/configuring-events-webhooks/)

## Next Steps

For performance optimization, see `adobe-performance-tuning`.
