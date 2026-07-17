# Event Sync Queue Implementation (TypeScript)

Extracted from SKILL.md § 4. A token-bucket queue that collects events for up to
5 seconds or until 100 accumulate, then flushes one batch (one batch = one API
call), converting a 10K events/minute storm into 100 calls/minute — well within
the 600 calls/minute budget.

```typescript
interface SyncQueue {
  events: ProductEvent[];
  timer: ReturnType<typeof setTimeout> | null;
}

const BATCH_SIZE = 100;      // HubSpot batch/update limit
const FLUSH_INTERVAL_MS = 5_000;

class HubSpotEventSyncQueue {
  private queue: ProductEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly token: string;
  private readonly redis: RedisClient;
  private readonly dlq: DeadLetterQueue;

  constructor(token: string, redis: RedisClient, dlq: DeadLetterQueue) {
    this.token = token;
    this.redis = redis;
    this.dlq = dlq;
  }

  push(event: ProductEvent): void {
    this.queue.push(event);
    if (this.queue.length >= BATCH_SIZE) {
      this.flush(); // flush immediately on full batch
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), FLUSH_INTERVAL_MS);
    }
  }

  async flush(): Promise<void> {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, BATCH_SIZE);
    await this.processBatch(batch);

    // If more remain (queue grew while flushing), flush again immediately
    if (this.queue.length > 0) this.flush();
  }

  private async processBatch(events: ProductEvent[]): Promise<void> {
    // Resolve contacts by email via upsert — auto-creates on miss
    const inputs = events.map((e) => ({
      idProperty: "email",
      id: e.email,
      properties: this.serializeProperties(e.properties),
    }));

    const res = await withRetry(() =>
      fetch("https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ inputs }),
      }),
    );

    await this.handle207(res, events);
  }

  private serializeProperties(
    props: Record<string, string | number | boolean>,
  ): Record<string, string> {
    // HubSpot batch API requires all values as strings
    return Object.fromEntries(
      Object.entries(props).map(([k, v]) => [k, String(v)]),
    );
  }
}
```
