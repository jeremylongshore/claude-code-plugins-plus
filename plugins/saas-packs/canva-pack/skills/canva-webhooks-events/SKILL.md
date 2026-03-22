---
name: canva-webhooks-events
description: |
  Implement Canva Connect API webhook handling with JWK signature verification.
  Use when setting up webhook endpoints, handling Canva event notifications,
  or implementing real-time design collaboration features.
  Trigger with phrases like "canva webhook", "canva events",
  "canva notifications", "handle canva events", "canva JWK".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Webhooks & Events

## Overview

Receive real-time notifications from Canva via webhooks when users comment on designs, request folder access, share designs, or interact with your integration. Canva sends signed JWT payloads verified with public JWK keys.

## Prerequisites

- Canva integration with `collaboration:event` scope enabled
- HTTPS endpoint accessible from the internet
- JWK verification library (`jose` recommended)
- Webhook URL configured in your integration settings

## Setup

### Step 1: Configure Webhooks in Canva

1. Go to your integration settings at [canva.dev](https://www.canva.dev)
2. Under **Notifications**, enable **collaboration:event**
3. Enter your webhook URL: `https://your-app.com/webhooks/canva`
4. Save the configuration

### Step 2: Implement JWK Signature Verification

```typescript
// src/canva/webhooks.ts
import { createRemoteJWKSet, jwtVerify, JWTPayload } from 'jose';

// Canva publishes public keys at this endpoint
// GET https://api.canva.com/rest/v1/connect/keys
const CANVA_JWKS = createRemoteJWKSet(
  new URL('https://api.canva.com/rest/v1/connect/keys')
);

interface CanvaWebhookPayload extends JWTPayload {
  notification_type: string;
  notification: Record<string, any>;
  timestamp: string;
  user_id: string;
  team_id: string;
}

export async function verifyCanvaWebhook(
  rawBody: string
): Promise<CanvaWebhookPayload | null> {
  try {
    const { payload } = await jwtVerify(rawBody, CANVA_JWKS, {
      issuer: 'canva',
    });
    return payload as CanvaWebhookPayload;
  } catch (error) {
    console.error('Webhook verification failed:', error);
    return null;
  }
}
```

### Step 3: Express Webhook Endpoint

```typescript
import express from 'express';
import { verifyCanvaWebhook } from './canva/webhooks';

const app = express();

// IMPORTANT: Accept raw text body for JWT verification
app.post('/webhooks/canva',
  express.text({ type: '*/*' }),
  async (req, res) => {
    const payload = await verifyCanvaWebhook(req.body);

    if (!payload) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Must return 200 to acknowledge — other codes = error
    res.status(200).json({ received: true });

    // Process async to avoid timeout
    handleCanvaEvent(payload).catch(console.error);
  }
);
```

### Step 4: Event Handler

```typescript
// Canva webhook notification types
type CanvaNotificationType =
  | 'comment'                    // New comment on a design
  | 'design_access_requested'   // Someone requests design access
  | 'design_approval_requested' // Approval workflow triggered
  | 'design_approval_response'  // Approval accepted/rejected
  | 'design_mention'            // User @mentioned in a design
  | 'folder_access_requested'   // Folder access request
  | 'design_shared'             // Design shared with user
  | 'folder_shared'             // Folder shared with user
  | 'suggestion'                // Design suggestion made
  | 'team_invite'               // Team invitation
  | 'design_approval_reviewer_invalidated'; // Reviewer removed

const handlers: Record<string, (notification: any) => Promise<void>> = {
  comment: async (data) => {
    console.log(`Comment on design ${data.design_id}: ${data.message}`);
    // Sync comment to your ticketing system, Slack, etc.
  },

  design_access_requested: async (data) => {
    console.log(`Access requested for design ${data.design_id} by user ${data.requesting_user_id}`);
    // Auto-approve or notify admin
  },

  design_shared: async (data) => {
    console.log(`Design ${data.design_id} shared with permissions: ${data.permissions}`);
    // Update your access control records
  },

  folder_access_requested: async (data) => {
    console.log(`Folder access requested: ${data.folder_id}`);
  },
};

async function handleCanvaEvent(payload: CanvaWebhookPayload): Promise<void> {
  const handler = handlers[payload.notification_type];

  if (!handler) {
    console.log(`Unhandled notification type: ${payload.notification_type}`);
    return;
  }

  try {
    await handler(payload.notification);
    console.log(`Processed ${payload.notification_type} at ${payload.timestamp}`);
  } catch (error) {
    console.error(`Failed to process ${payload.notification_type}:`, error);
  }
}
```

## Required Scopes per Event Type

| Event | Required Scopes |
|-------|----------------|
| comment | `collaboration:event`, `design:meta:read`, `comment:read` |
| design_access_requested | `collaboration:event`, `design:meta:read` |
| design_shared | `collaboration:event`, `design:meta:read` |
| folder_access_requested | `collaboration:event`, `folder:read` |
| design_mention | `collaboration:event`, `design:meta:read` |

**Scopes are explicit** — you must enable each one individually.

## Idempotency

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function processIdempotent(
  notificationId: string,
  handler: () => Promise<void>
): Promise<void> {
  const key = `canva:webhook:${notificationId}`;
  const alreadyProcessed = await redis.set(key, '1', 'EX', 604800, 'NX'); // 7 days, NX = only if not exists

  if (!alreadyProcessed) {
    console.log(`Duplicate webhook skipped: ${notificationId}`);
    return;
  }

  await handler();
}
```

## Testing Webhooks Locally

```bash
# 1. Expose local server via ngrok
ngrok http 3000

# 2. Set the ngrok HTTPS URL in your Canva integration settings
# e.g., https://abc123.ngrok-free.app/webhooks/canva

# 3. Trigger events by commenting on a design shared with the authorized user
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 on webhook | JWK verification failed | Check `jose` library version, key URL |
| No events received | Webhook URL not configured | Set URL in integration settings |
| Duplicate events | No idempotency | Implement notification ID tracking |
| Events delayed | Processing too slow | Return 200 immediately, process async |
| Missing event types | Scopes not enabled | Enable `collaboration:event` + per-type scopes |

## Resources

- [Canva Webhooks](https://www.canva.dev/docs/connect/webhooks/)
- [Webhook Keys API](https://www.canva.dev/docs/connect/api-reference/webhooks/keys/)
- [jose Library](https://github.com/panva/jose)

## Next Steps

For performance optimization, see `canva-performance-tuning`.
