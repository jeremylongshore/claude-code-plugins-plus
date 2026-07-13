# TwinMind Webhooks & Events - Detailed Implementation

## Event Types

```typescript
export enum TwinMindEventType {
  TRANSCRIPTION_STARTED = 'transcription.started',
  TRANSCRIPTION_COMPLETED = 'transcription.completed',
  TRANSCRIPTION_FAILED = 'transcription.failed',
  MEETING_STARTED = 'meeting.started',
  MEETING_ENDED = 'meeting.ended',
  MEETING_PARTICIPANT_JOINED = 'meeting.participant.joined',
  MEETING_PARTICIPANT_LEFT = 'meeting.participant.left',
  SUMMARY_GENERATED = 'summary.generated',
  ACTION_ITEMS_EXTRACTED = 'action_items.extracted',
  CALENDAR_SYNCED = 'calendar.synced',
  USAGE_LIMIT_WARNING = 'usage.limit.warning',
  USAGE_LIMIT_EXCEEDED = 'usage.limit.exceeded',
}

export interface TwinMindEvent<T = any> {
  id: string;
  type: TwinMindEventType;
  created_at: string;
  data: T;
}
```

## Webhook Handler with Signature Verification

```typescript
import crypto from 'crypto';

export function verifySignature(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers['x-twinmind-signature'] as string;
  const timestamp = req.headers['x-twinmind-timestamp'] as string;
  const secret = process.env.TWINMIND_WEBHOOK_SECRET!;

  if (!signature || !timestamp) { res.status(401).json({ error: 'Missing signature' }); return; }

  // Replay protection (5 minute window)
  if (Math.abs(Date.now() - parseInt(timestamp) * 1000) > 5 * 60 * 1000) {
    res.status(401).json({ error: 'Request too old' }); return;
  }

  const payload = `${timestamp}.${JSON.stringify(req.body)}`;
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(`sha256=${expected}`))) {
    res.status(401).json({ error: 'Invalid signature' }); return;
  }
  next();
}

// Handler registry
const handlers = new Map<TwinMindEventType, EventHandler[]>();

export function registerHandler<T>(eventType: TwinMindEventType, handler: (event: TwinMindEvent<T>) => Promise<void>): void {
  const existing = handlers.get(eventType) || [];
  existing.push(handler);
  handlers.set(eventType, existing);
}

export async function handleWebhook(req: Request, res: Response): Promise<void> {
  const event = req.body as TwinMindEvent;
  res.status(200).json({ received: true, event_id: event.id }); // Acknowledge immediately

  try {
    const eventHandlers = handlers.get(event.type as TwinMindEventType);
    if (eventHandlers?.length) {
      await Promise.all(eventHandlers.map(h => h(event)));
    }
  } catch (error) {
    console.error(`Error processing event ${event.id}:`, error);
  }
}
```

## Event Handlers

```typescript
// Transcription completed -> trigger summary
registerHandler(TwinMindEventType.TRANSCRIPTION_COMPLETED, async (event) => {
  const { transcript_id } = event.data;
  const client = getTwinMindClient();
  await client.post('/summarize', { transcript_id });
});

// Meeting ended -> notify Slack + email summary
registerHandler(TwinMindEventType.MEETING_ENDED, async (event) => {
  const { title, duration_seconds, participants, summary_available } = event.data;
  await notifySlack({ channel: '#meetings', message: `"${title}" ended (${Math.round(duration_seconds / 60)} min)` });
  if (summary_available) {
    const summary = await getTwinMindClient().get(`/summaries/${event.data.transcript_id}`);
    await sendEmail({ to: participants, subject: `Summary: ${title}`, body: summary.data.summary });
  }
});

// Action items -> create Linear tasks
registerHandler(TwinMindEventType.ACTION_ITEMS_EXTRACTED, async (event) => {
  if (event.data.action_items.length > 0) {
    await createTasksInLinear(event.data.action_items);
  }
});

// Usage warning -> alert ops
registerHandler(TwinMindEventType.USAGE_LIMIT_WARNING, async (event) => {
  await notifySlack({ channel: '#alerts', message: `TwinMind usage at ${event.data.percent_used}%` });
});
```

## Webhook Registration Script

```typescript
async function registerWebhooks() {
  const client = getTwinMindClient();
  const response = await client.post('/webhooks', {
    url: process.env.WEBHOOK_BASE_URL + '/webhooks/twinmind',
    events: [
      TwinMindEventType.TRANSCRIPTION_COMPLETED,
      TwinMindEventType.MEETING_ENDED,
      TwinMindEventType.SUMMARY_GENERATED,
      TwinMindEventType.ACTION_ITEMS_EXTRACTED,
      TwinMindEventType.USAGE_LIMIT_WARNING,
    ],
    enabled: true,
  });
  console.log('Webhook Secret:', response.data.secret);
}
```

## Retry Queue

```typescript
class WebhookRetryQueue {
  private queue: FailedEvent[] = [];
  private maxRetries = 5;
  private baseDelayMs = 60000;

  async add(event: TwinMindEvent, error: Error): Promise<void> {
    const existing = this.queue.find(f => f.event.id === event.id);
    if (existing) {
      existing.attempts++;
      existing.nextRetry = new Date(Date.now() + this.baseDelayMs * Math.pow(2, existing.attempts));
      if (existing.attempts >= this.maxRetries) {
        await this.moveToDeadLetter(existing);
        this.queue = this.queue.filter(f => f.event.id !== event.id);
      }
    } else {
      this.queue.push({ event, attempts: 1, lastError: error.message, nextRetry: new Date(Date.now() + this.baseDelayMs) });
    }
  }

  async processRetries(): Promise<void> {
    const ready = this.queue.filter(f => f.nextRetry <= new Date());
    for (const failed of ready) {
      try {
        const handlers = getHandlersForEvent(failed.event.type);
        await Promise.all(handlers.map(h => h(failed.event)));
        this.queue = this.queue.filter(f => f.event.id !== failed.event.id);
      } catch (error: any) {
        await this.add(failed.event, error);
      }
    }
  }

  private async moveToDeadLetter(failed: FailedEvent): Promise<void> {
    await db.deadLetterQueue.create({ event_id: failed.event.id, payload: failed.event, attempts: failed.attempts });
    await notifySlack({ channel: '#alerts', message: `Webhook failed after ${failed.attempts} attempts: ${failed.event.id}` });
  }
}

export const retryQueue = new WebhookRetryQueue();
setInterval(() => retryQueue.processRetries(), 60000);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
