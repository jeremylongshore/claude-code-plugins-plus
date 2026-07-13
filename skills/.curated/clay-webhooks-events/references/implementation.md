# Clay Webhooks & Events - Implementation Details

## Configuration

### Webhook Signature Verification

```typescript
import crypto from 'crypto';
import { Request, Response, NextFunction } from 'express';

function verifyClaySignature(secret: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const signature = req.headers['x-clay-signature'] as string;
    const timestamp = req.headers['x-clay-timestamp'] as string;

    if (!signature || !timestamp) {
      return res.status(401).json({ error: 'Missing signature headers' });
    }

    // Prevent replay attacks: reject if older than 5 minutes
    const age = Math.abs(Date.now() / 1000 - parseInt(timestamp));
    if (age > 300) {
      return res.status(401).json({ error: 'Timestamp too old' });
    }

    const payload = `${timestamp}.${JSON.stringify(req.body)}`;
    const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    next();
  };
}
```

## Advanced Patterns

### Event Router with Type-Safe Handlers

```typescript
type ClayEventType =
  | 'enrichment.completed'
  | 'enrichment.failed'
  | 'table.row_added'
  | 'table.row_updated'
  | 'export.completed';

interface ClayWebhookEvent {
  id: string;
  type: ClayEventType;
  created_at: string;
  data: Record<string, any>;
}

type EventHandler = (event: ClayWebhookEvent) => Promise<void>;

class ClayEventRouter {
  private handlers = new Map<ClayEventType, EventHandler[]>();

  on(type: ClayEventType, handler: EventHandler) {
    const existing = this.handlers.get(type) ?? [];
    this.handlers.set(type, [...existing, handler]);
  }

  async dispatch(event: ClayWebhookEvent): Promise<void> {
    const handlers = this.handlers.get(event.type) ?? [];
    if (handlers.length === 0) {
      console.warn(`No handler for event type: ${event.type}`);
      return;
    }
    await Promise.allSettled(handlers.map((h) => h(event)));
  }
}

// Usage
const router = new ClayEventRouter();

router.on('enrichment.completed', async (event) => {
  const { person_id, enrichment_data } = event.data;
  await db.updateContact(person_id, enrichment_data);
});

router.on('enrichment.failed', async (event) => {
  const { person_id, error } = event.data;
  console.error(`Enrichment failed for ${person_id}: ${error}`);
  await retryQueue.add({ person_id, attempts: 1 });
});

router.on('export.completed', async (event) => {
  const { export_id, download_url } = event.data;
  await notifyTeam(`Clay export ready: ${download_url}`);
});
```

### Idempotent Event Processing

```typescript
class IdempotentProcessor {
  private processed = new Set<string>();

  constructor(private redis: Redis) {}

  async processEvent(event: ClayWebhookEvent): Promise<boolean> {
    const key = `clay:event:${event.id}`;
    const exists = await this.redis.set(key, '1', 'EX', 86400, 'NX');

    if (!exists) {
      console.log(`Duplicate event ${event.id}, skipping`);
      return false;
    }

    return true;
  }
}
```

### Webhook Endpoint with Express

```typescript
import express from 'express';

const app = express();
app.use(express.json({ limit: '1mb' }));

app.post('/api/clay/webhook',
  verifyClaySignature(process.env.CLAY_WEBHOOK_SECRET!),
  async (req, res) => {
    const event: ClayWebhookEvent = req.body;

    // Acknowledge immediately (Clay retries on timeout)
    res.status(200).json({ received: true });

    // Process asynchronously
    try {
      const isNew = await idempotent.processEvent(event);
      if (isNew) await eventRouter.dispatch(event);
    } catch (err) {
      console.error('Event processing failed:', err);
    }
  }
);
```

## Troubleshooting

### Testing Webhooks Locally

```bash
# Use ngrok to expose local endpoint
ngrok http 3000

# Register the ngrok URL with Clay
curl -X PUT \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -d '{"webhook_url": "https://abc123.ngrok.io/api/clay/webhook"}' \
  https://api.clay.com/v1/webhooks

# Trigger a test event
curl -X POST \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  https://api.clay.com/v1/webhooks/test
```

### Debugging Signature Failures

```typescript
function debugSignature(req: Request) {
  const sig = req.headers['x-clay-signature'];
  const ts = req.headers['x-clay-timestamp'];
  const body = JSON.stringify(req.body);
  const computed = crypto.createHmac('sha256', process.env.CLAY_WEBHOOK_SECRET!)
    .update(`${ts}.${body}`)
    .digest('hex');
  console.log({ received: sig, computed, match: sig === computed, bodyLen: body.length });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
