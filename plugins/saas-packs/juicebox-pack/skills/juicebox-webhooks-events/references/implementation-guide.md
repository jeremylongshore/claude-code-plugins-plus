# Juicebox Webhooks & Events - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Register Webhook Endpoint
```typescript
// First, configure in Juicebox dashboard or via API
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY!
});

await client.webhooks.create({
  url: 'https://your-app.com/webhooks/juicebox',
  events: [
    'search.completed',
    'profile.enriched',
    'export.ready',
    'quota.warning'
  ],
  secret: process.env.JUICEBOX_WEBHOOK_SECRET
});
```

### Step 2: Implement Webhook Handler
```typescript
// routes/webhooks.ts
import { Router } from 'express';
import crypto from 'crypto';

const router = Router();

// Verify webhook signature
function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${expected}`)
  );
}

router.post('/webhooks/juicebox', express.raw({ type: 'application/json' }), async (req, res) => {
  const signature = req.headers['x-juicebox-signature'] as string;
  const payload = req.body.toString();

  // Verify signature
  if (!verifySignature(payload, signature, process.env.JUICEBOX_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(payload);

  // Acknowledge receipt immediately
  res.status(200).json({ received: true });

  // Process event asynchronously
  await processWebhookEvent(event);
});

export default router;
```

### Step 3: Process Different Event Types
```typescript
// services/webhook-processor.ts
interface WebhookEvent {
  id: string;
  type: string;
  timestamp: string;
  data: any;
}

export async function processWebhookEvent(event: WebhookEvent): Promise<void> {
  console.log(`Processing event: ${event.type} (${event.id})`);

  switch (event.type) {
    case 'search.completed':
      await handleSearchCompleted(event.data);
      break;

    case 'profile.enriched':
      await handleProfileEnriched(event.data);
      break;

    case 'export.ready':
      await handleExportReady(event.data);
      break;

    case 'quota.warning':
      await handleQuotaWarning(event.data);
      break;

    default:
      console.warn(`Unknown event type: ${event.type}`);
  }
}

async function handleSearchCompleted(data: { searchId: string; resultCount: number }) {
  // Notify user that search is complete
  await notificationService.send({
    type: 'search_complete',
    searchId: data.searchId,
    message: `Search completed with ${data.resultCount} results`
  });
}

async function handleProfileEnriched(data: { profileId: string; fields: string[] }) {
  // Update local cache with enriched data
  await cacheService.invalidate(`profile:${data.profileId}`);
  await db.profiles.update({
    where: { id: data.profileId },
    data: { enrichedAt: new Date() }
  });
}

async function handleExportReady(data: { exportId: string; downloadUrl: string }) {
  // Notify user and store download URL
  await notificationService.send({
    type: 'export_ready',
    exportId: data.exportId,
    downloadUrl: data.downloadUrl
  });
}

async function handleQuotaWarning(data: { usage: number; limit: number }) {
  // Alert team about quota usage
  const percentage = (data.usage / data.limit) * 100;
  if (percentage > 80) {
    await alertService.send({
      severity: 'warning',
      message: `Juicebox quota at ${percentage.toFixed(1)}%`
    });
  }
}
```

### Step 4: Implement Retry Logic
```typescript
// lib/webhook-queue.ts
import { Queue } from 'bullmq';

const webhookQueue = new Queue('juicebox-webhooks', {
  connection: { host: 'localhost', port: 6379 }
});

export async function queueWebhookProcessing(event: WebhookEvent): Promise<void> {
  await webhookQueue.add('process', event, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000
    }
  });
}

// Worker
import { Worker } from 'bullmq';

new Worker('juicebox-webhooks', async (job) => {
  await processWebhookEvent(job.data);
}, {
  connection: { host: 'localhost', port: 6379 }
});
```

## Webhook Events Reference

| Event | Description | Payload |
|-------|-------------|---------|
| `search.completed` | Async search finished | searchId, resultCount |
| `profile.enriched` | Profile data enriched | profileId, fields |
| `export.ready` | Bulk export ready | exportId, downloadUrl |
| `quota.warning` | Approaching quota limit | usage, limit |
| `key.rotated` | API key rotated | newKeyPrefix |
