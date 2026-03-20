---
name: maintainx-webhooks-events
description: |
  Implement MaintainX webhook handling and event-driven integrations.
  Use when setting up webhooks, handling MaintainX events,
  or building real-time integrations with MaintainX.
  Trigger with phrases like "maintainx webhook", "maintainx events",
  "maintainx notifications", "maintainx real-time", "maintainx triggers".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Webhooks & Events

## Overview
Build real-time integrations with MaintainX using webhooks for work order updates, asset changes, and maintenance notifications. MaintainX fires webhook events when key resources change.

## Prerequisites
- MaintainX account with API access
- HTTPS endpoint accessible from the internet (ngrok for local dev)
- `MAINTAINX_API_KEY` environment variable configured

## Instructions

### Step 1: Register a Webhook

```bash
curl -X POST https://api.getmaintainx.com/v1/webhooks \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.example.com/webhooks/maintainx",
    "events": [
      "workorder.created",
      "workorder.updated",
      "workorder.status_changed",
      "workorder.completed"
    ]
  }'
```

### Step 2: Webhook Receiver (Express)

```typescript
// src/webhook-server.ts
import express from 'express';
import crypto from 'node:crypto';

const app = express();
app.use(express.json({ limit: '1mb' }));

// Signature verification middleware
function verifySignature(secret: string) {
  return (req: express.Request, res: express.Response, next: express.NextFunction) => {
    const signature = req.headers['x-maintainx-signature'] as string;
    if (!signature) {
      return res.status(401).json({ error: 'Missing signature header' });
    }

    const expected = crypto
      .createHmac('sha256', secret)
      .update(JSON.stringify(req.body))
      .digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    next();
  };
}

const WEBHOOK_SECRET = process.env.MAINTAINX_WEBHOOK_SECRET!;

app.post(
  '/webhooks/maintainx',
  verifySignature(WEBHOOK_SECRET),
  async (req, res) => {
    const { event, data, timestamp } = req.body;

    console.log(`[${timestamp}] Event: ${event}, Resource ID: ${data.id}`);

    // Idempotency check
    const eventId = req.headers['x-maintainx-event-id'] as string;
    if (await isProcessed(eventId)) {
      return res.status(200).json({ status: 'already_processed' });
    }

    try {
      await routeEvent(event, data);
      await markProcessed(eventId);
      res.status(200).json({ status: 'ok' });
    } catch (err) {
      console.error('Webhook handler error:', err);
      res.status(500).json({ error: 'Processing failed' });
    }
  },
);

app.listen(3000, () => console.log('Webhook server listening on :3000'));
```

### Step 3: Event Router

```typescript
// src/event-handlers.ts

type EventHandler = (data: any) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  'workorder.created': async (data) => {
    console.log(`New work order: #${data.id} "${data.title}"`);
    // Notify Slack, create ticket, etc.
    if (data.priority === 'HIGH') {
      await sendSlackAlert(`High priority WO created: ${data.title}`);
    }
  },

  'workorder.status_changed': async (data) => {
    console.log(`WO #${data.id}: ${data.previousStatus} → ${data.status}`);
    if (data.status === 'COMPLETED') {
      await syncCompletionToERP(data);
    }
  },

  'workorder.completed': async (data) => {
    console.log(`WO #${data.id} completed at ${data.completedAt}`);
    await generateCompletionReport(data);
  },

  'workorder.updated': async (data) => {
    await syncWorkOrderToDataWarehouse(data);
  },
};

export async function routeEvent(event: string, data: any) {
  const handler = handlers[event];
  if (handler) {
    await handler(data);
  } else {
    console.warn(`Unhandled event type: ${event}`);
  }
}
```

### Step 4: Idempotency Store

```typescript
// src/idempotency.ts
// Use Redis in production; Map for dev/testing
const processed = new Map<string, boolean>();

export async function isProcessed(eventId: string): Promise<boolean> {
  return processed.has(eventId);
}

export async function markProcessed(eventId: string): Promise<void> {
  processed.set(eventId, true);
  // In production: await redis.setex(`event:${eventId}`, 86400, '1');
}
```

### Step 5: Local Development with ngrok

```bash
# Start your webhook server
npm run dev

# In another terminal, expose it with ngrok
ngrok http 3000
# Copy the https URL (e.g., https://abc123.ngrok-free.app)

# Register the ngrok URL as a webhook
curl -X POST https://api.getmaintainx.com/v1/webhooks \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://abc123.ngrok-free.app/webhooks/maintainx",
    "events": ["workorder.created", "workorder.status_changed"]
  }'
```

### Step 6: List and Manage Webhooks

```bash
# List all registered webhooks
curl -s https://api.getmaintainx.com/v1/webhooks \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq .

# Delete a webhook (replace ID)
curl -X DELETE https://api.getmaintainx.com/v1/webhooks/456 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY"
```

## Output
- Webhook endpoint with HMAC signature verification
- Event router dispatching to type-specific handlers
- Idempotency guard preventing duplicate processing
- Local dev setup with ngrok for testing webhooks
- Webhook registration and management via REST API

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 401 on webhook registration | Invalid API key | Verify `MAINTAINX_API_KEY` |
| Webhook not firing | URL not reachable | Ensure HTTPS, check firewall, test with ngrok |
| Duplicate events | Retries from MaintainX | Implement idempotency with event ID deduplication |
| Signature mismatch | Wrong secret or body mutation | Verify raw body is used for HMAC, check secret value |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [ngrok Documentation](https://ngrok.com/docs)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-vulnerabilities-guide)

## Next Steps
For performance optimization, see `maintainx-performance-tuning`.

## Examples

**Slack notification on high-priority work orders**:

```typescript
async function sendSlackAlert(message: string) {
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `:rotating_light: MaintainX Alert: ${message}`,
    }),
  });
}
```

**Polling fallback when webhooks are unavailable**:

```typescript
// Poll every 60 seconds for status changes
async function pollWorkOrders(client: MaintainXClient, since: string) {
  const { workOrders } = await client.getWorkOrders({
    updatedAtGte: since,
    limit: 50,
  });
  for (const wo of workOrders) {
    await routeEvent('workorder.updated', wo);
  }
  return new Date().toISOString();
}
```
