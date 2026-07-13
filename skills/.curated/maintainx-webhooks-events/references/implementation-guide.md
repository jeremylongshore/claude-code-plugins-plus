# MaintainX Webhooks & Events - Implementation Guide

> Full implementation details and code examples for the `maintainx-webhooks-events` skill.

# MaintainX Webhooks & Events

## Overview

Build real-time integrations with MaintainX using webhooks and event-driven patterns for work order updates, asset changes, and maintenance notifications.

## Prerequisites

- MaintainX account with webhook access
- HTTPS endpoint accessible from internet
- Understanding of webhook security patterns

## MaintainX Event Types

| Event | Description | Use Case |
|-------|-------------|----------|
| `workorder.created` | New work order created | Notify team, sync to external system |
| `workorder.updated` | Work order modified | Track status changes |
| `workorder.completed` | Work order marked done | Trigger follow-up actions |
| `asset.updated` | Asset information changed | Sync asset data |
| `request.created` | Work request submitted | Auto-create work orders |

## Instructions

### Step 1: Webhook Endpoint Setup

```typescript
// src/webhooks/handler.ts
import express, { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';

const router = express.Router();

// Webhook secret from MaintainX (configure in dashboard)
const WEBHOOK_SECRET = process.env.MAINTAINX_WEBHOOK_SECRET;

// Raw body parser for signature verification
router.use('/webhooks/maintainx', express.raw({ type: 'application/json' }));

// Signature verification middleware
function verifySignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers['x-maintainx-signature'] as string;
  const timestamp = req.headers['x-maintainx-timestamp'] as string;

  if (!signature || !timestamp || !WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Missing signature or configuration' });
  }

  // Verify timestamp is recent (prevent replay attacks)
  const timestampMs = parseInt(timestamp) * 1000;
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;

  if (timestampMs < fiveMinutesAgo) {
    return res.status(401).json({ error: 'Timestamp too old' });
  }

  // Compute expected signature
  const payload = `${timestamp}.${req.body.toString()}`;
  const expectedSignature = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');

  // Timing-safe comparison
  const isValid = crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );

  if (!isValid) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Parse body for handlers
  req.body = JSON.parse(req.body.toString());
  next();
}

// Main webhook endpoint
router.post('/webhooks/maintainx', verifySignature, async (req, res) => {
  const event = req.body;

  console.log(`Received webhook: ${event.type}`, event.id);

  try {
    await handleMaintainXEvent(event);
    res.status(200).json({ received: true });
  } catch (error) {
    console.error('Webhook processing error:', error);
    res.status(500).json({ error: 'Processing failed' });
  }
});

export { router as webhookRouter };
```

### Step 2: Event Handler Pattern

```typescript
// src/webhooks/event-handlers.ts

interface MaintainXEvent {
  id: string;
  type: string;
  data: any;
  createdAt: string;
}

type EventHandler = (event: MaintainXEvent) => Promise<void>;

// Handler registry
const eventHandlers: Map<string, EventHandler[]> = new Map();

// Register handler
function on(eventType: string, handler: EventHandler) {
  const handlers = eventHandlers.get(eventType) || [];
  handlers.push(handler);
  eventHandlers.set(eventType, handlers);
}

// Process event
async function handleMaintainXEvent(event: MaintainXEvent): Promise<void> {
  const handlers = eventHandlers.get(event.type) || [];

  if (handlers.length === 0) {
    console.log(`No handlers for event type: ${event.type}`);
    return;
  }

  // Execute all handlers (parallel or sequential based on needs)
  await Promise.all(handlers.map(h => h(event)));
}

// Register handlers
on('workorder.created', async (event) => {
  console.log('New work order:', event.data.title);

  // Example: Send Slack notification
  await sendSlackNotification({
    channel: '#maintenance',
    text: `New work order: ${event.data.title}`,
    attachments: [{
      fields: [
        { title: 'Priority', value: event.data.priority },
        { title: 'Asset', value: event.data.asset?.name || 'N/A' },
        { title: 'Location', value: event.data.location?.name || 'N/A' },
      ],
    }],
  });
});

on('workorder.updated', async (event) => {
  const { previousStatus, currentStatus } = event.data;

  if (previousStatus !== currentStatus) {
    console.log(`Work order status changed: ${previousStatus} -> ${currentStatus}`);

    // Track status transitions
    await trackStatusChange(event.data.id, previousStatus, currentStatus);
  }
});

on('workorder.completed', async (event) => {
  console.log('Work order completed:', event.data.id);

  // Example: Update external system
  await syncToExternalSystem(event.data);

  // Example: Create follow-up tasks
  if (event.data.requiresFollowUp) {
    await createFollowUpWorkOrder(event.data);
  }
});

on('request.created', async (event) => {
  console.log('New work request:', event.data.title);

  // Auto-create work order from request
  const workOrder = await autoCreateWorkOrder(event.data);
  console.log('Auto-created work order:', workOrder.id);
});

export { handleMaintainXEvent, on };
```

### Step 3: Idempotency Handling

```typescript
// src/webhooks/idempotency.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

interface IdempotencyResult {
  isProcessed: boolean;
  result?: any;
}

async function checkIdempotency(eventId: string): Promise<IdempotencyResult> {
  const key = `maintainx:webhook:${eventId}`;
  const result = await redis.get(key);

  if (result) {
    return { isProcessed: true, result: JSON.parse(result) };
  }

  return { isProcessed: false };
}

async function markProcessed(eventId: string, result: any): Promise<void> {
  const key = `maintainx:webhook:${eventId}`;
  // Store for 7 days
  await redis.set(key, JSON.stringify(result), 'EX', 7 * 24 * 60 * 60);
}

// Idempotent event handler wrapper
async function processIdempotent(
  event: MaintainXEvent,
  handler: EventHandler
): Promise<void> {
  // Check if already processed
  const { isProcessed, result } = await checkIdempotency(event.id);

  if (isProcessed) {
    console.log(`Event ${event.id} already processed, skipping`);
    return;
  }

  // Process event
  const handlerResult = await handler(event);

  // Mark as processed
  await markProcessed(event.id, { processedAt: new Date(), result: handlerResult });
}
```

### Step 4: Webhook Testing Tools

```typescript
// scripts/test-webhook.ts
import crypto from 'crypto';
import axios from 'axios';

const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:3000/webhooks/maintainx';
const WEBHOOK_SECRET = process.env.MAINTAINX_WEBHOOK_SECRET || 'test-secret';

async function sendTestWebhook(eventType: string, data: any) {
  const timestamp = Math.floor(Date.now() / 1000).toString();

  const payload = JSON.stringify({
    id: `evt_${Date.now()}`,
    type: eventType,
    data,
    createdAt: new Date().toISOString(),
  });

  // Generate signature
  const signedPayload = `${timestamp}.${payload}`;
  const signature = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(signedPayload)
    .digest('hex');

  try {
    const response = await axios.post(WEBHOOK_URL, payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-MaintainX-Signature': signature,
        'X-MaintainX-Timestamp': timestamp,
      },
    });

    console.log('Webhook sent successfully:', response.status);
    console.log('Response:', response.data);
  } catch (error: any) {
    console.error('Webhook failed:', error.response?.data || error.message);
  }
}

// Test different event types
async function runTests() {
  console.log('Testing workorder.created...');
  await sendTestWebhook('workorder.created', {
    id: 'wo_test_001',
    title: 'Test Work Order',
    priority: 'HIGH',
    status: 'OPEN',
    asset: { id: 'asset_001', name: 'Test Asset' },
    location: { id: 'loc_001', name: 'Test Location' },
  });

  console.log('\nTesting workorder.completed...');
  await sendTestWebhook('workorder.completed', {
    id: 'wo_test_001',
    title: 'Test Work Order',
    completedAt: new Date().toISOString(),
    completedBy: { id: 'user_001', name: 'Test User' },
  });

  console.log('\nTesting request.created...');
  await sendTestWebhook('request.created', {
    id: 'req_test_001',
    title: 'Emergency Repair Request',
    description: 'Machine making strange noise',
    requestedBy: { id: 'user_002', name: 'Operator' },
  });
}

runTests().catch(console.error);
```

### Step 5: Webhook Retry Handler

```typescript
// src/webhooks/retry-queue.ts
import Bull from 'bull';

interface WebhookJob {
  event: MaintainXEvent;
  attempt: number;
  maxAttempts: number;
}

const webhookQueue = new Bull<WebhookJob>('maintainx-webhooks', {
  redis: process.env.REDIS_URL,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 1000,
    },
  },
});

// Process jobs
webhookQueue.process(async (job) => {
  const { event, attempt, maxAttempts } = job.data;

  console.log(`Processing webhook ${event.id} (attempt ${attempt}/${maxAttempts})`);

  try {
    await handleMaintainXEvent(event);
    console.log(`Webhook ${event.id} processed successfully`);
  } catch (error) {
    console.error(`Webhook ${event.id} failed:`, error);
    throw error;  // Bull will retry based on config
  }
});

// Add event to queue
async function queueWebhook(event: MaintainXEvent): Promise<void> {
  await webhookQueue.add({
    event,
    attempt: 1,
    maxAttempts: 5,
  });
}

// Failed job handler
webhookQueue.on('failed', (job, err) => {
  console.error(`Webhook job ${job.id} failed after ${job.attemptsMade} attempts:`, err);

  // Alert on final failure
  if (job.attemptsMade >= job.opts.attempts!) {
    alertOnWebhookFailure(job.data.event, err);
  }
});
```

### Step 6: Webhook Dashboard

```typescript
// src/routes/webhook-admin.ts
import { Router } from 'express';

const router = Router();

// List recent webhooks
router.get('/admin/webhooks', async (req, res) => {
  const webhooks = await getRecentWebhooks(50);

  res.json({
    total: webhooks.length,
    webhooks: webhooks.map(w => ({
      id: w.id,
      type: w.type,
      status: w.status,
      processedAt: w.processedAt,
      error: w.error,
    })),
  });
});

// Get webhook details
router.get('/admin/webhooks/:id', async (req, res) => {
  const webhook = await getWebhookById(req.params.id);

  if (!webhook) {
    return res.status(404).json({ error: 'Webhook not found' });
  }

  res.json(webhook);
});

// Retry failed webhook
router.post('/admin/webhooks/:id/retry', async (req, res) => {
  const webhook = await getWebhookById(req.params.id);

  if (!webhook) {
    return res.status(404).json({ error: 'Webhook not found' });
  }

  await queueWebhook(webhook.event);

  res.json({ message: 'Webhook queued for retry' });
});

export { router as webhookAdminRouter };
```

## Output

- Webhook endpoint with signature verification
- Event handler pattern implemented
- Idempotency handling
- Testing tools configured
- Retry queue for reliability
- Admin dashboard for monitoring

## Webhook Best Practices

1. **Always verify signatures** - Never process unsigned webhooks
2. **Respond quickly** - Return 200 within 5 seconds, process async
3. **Implement idempotency** - Handle duplicate deliveries
4. **Use queues** - Don't block webhook response on processing
5. **Monitor failures** - Alert on repeated failures

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-vulnerabilities-guide)
- [Bull Queue Documentation](https://github.com/OptimalBits/bull)

## Next Steps

For performance optimization, see `maintainx-performance-tuning`.
