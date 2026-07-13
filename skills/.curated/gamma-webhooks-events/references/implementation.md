# Gamma Webhooks & Events - Implementation Details

## Register Webhook

```typescript
const webhook = await gamma.webhooks.create({
  url: 'https://your-app.com/webhooks/gamma',
  events: ['presentation.created', 'presentation.updated', 'presentation.exported', 'presentation.deleted'],
  secret: process.env.GAMMA_WEBHOOK_SECRET,
});
```

## Webhook Handler with Signature Verification

```typescript
import express from 'express';
import crypto from 'crypto';

function verifySignature(payload: string, signature: string): boolean {
  const secret = process.env.GAMMA_WEBHOOK_SECRET!;
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(`sha256=${expected}`));
}

router.post('/gamma', express.raw({ type: 'application/json' }), async (req, res) => {
  const signature = req.headers['x-gamma-signature'] as string;
  if (!verifySignature(req.body.toString(), signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true }); // Acknowledge quickly
  await processEvent(event); // Process async
});
```

## Event Processing

```typescript
interface GammaEvent { id: string; type: string; data: any; timestamp: string; }

const handlers: Record<string, (data: any) => Promise<void>> = {
  'presentation.created': async (data) => {
    await notifyTeam(`New presentation created: ${data.title}`);
    await updateDatabase({ presentationId: data.id, status: 'created' });
  },
  'presentation.updated': async (data) => {
    await updateDatabase({ presentationId: data.id, status: 'updated' });
  },
  'presentation.exported': async (data) => {
    await sendExportNotification(data.userId, data.exportUrl);
  },
  'presentation.deleted': async (data) => {
    await cleanupAssets(data.id);
  },
};

export async function processEvent(event: GammaEvent) {
  const handler = handlers[event.type];
  if (!handler) { console.warn('Unhandled event type:', event.type); return; }
  try {
    await handler(event.data);
    await recordEventProcessed(event.id);
  } catch (err) {
    await recordEventFailed(event.id, err);
  }
}
```

## Event Queue for Reliability

```typescript
import Bull from 'bull';

const eventQueue = new Bull('gamma-events', { redis: process.env.REDIS_URL });

export async function queueEvent(event: GammaEvent) {
  await eventQueue.add(event, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 5000 },
  });
}

eventQueue.process(async (job) => { await processEvent(job.data); });

eventQueue.on('failed', (job, err) => {
  console.error(`Event ${job.id} failed:`, err.message);
});
```

## Webhook Management

```typescript
// List, update, delete, test webhooks
const webhooks = await gamma.webhooks.list();
await gamma.webhooks.update(webhookId, { events: ['presentation.created', 'presentation.exported'] });
await gamma.webhooks.delete(webhookId);
await gamma.webhooks.test(webhookId);
```

## Event Types Reference

| Event | Description | Payload |
|-------|-------------|---------|
| `presentation.created` | New presentation | id, title, userId |
| `presentation.updated` | Slides modified | id, changes[] |
| `presentation.exported` | Export completed | id, format, url |
| `presentation.deleted` | Presentation removed | id |
| `presentation.shared` | Sharing updated | id, shareSettings |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
