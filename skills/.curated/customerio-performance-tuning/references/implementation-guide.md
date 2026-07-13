# Customer.io Performance Tuning - Implementation Guide

## Connection Pooling

```typescript
// lib/customerio-pooled.ts
import { TrackClient, RegionUS } from '@customerio/track';
import { Agent as HttpsAgent } from 'https';

const httpsAgent = new HttpsAgent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 100,
  maxFreeSockets: 20,
  timeout: 30000
});

export function createPooledClient(): TrackClient {
  return new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_API_KEY!,
    { region: RegionUS, httpAgent: httpsAgent }
  );
}

let clientInstance: TrackClient | null = null;

export function getClient(): TrackClient {
  if (!clientInstance) {
    clientInstance = createPooledClient();
  }
  return clientInstance;
}
```

## Batch Processing

```typescript
// lib/batch-processor.ts
import { TrackClient } from '@customerio/track';

interface BatchItem {
  type: 'identify' | 'track';
  userId: string;
  data: Record<string, any>;
}

export class BatchProcessor {
  private batch: BatchItem[] = [];
  private batchSize: number;
  private flushInterval: number;
  private timer: NodeJS.Timer | null = null;

  constructor(
    private client: TrackClient,
    options: { batchSize?: number; flushIntervalMs?: number } = {}
  ) {
    this.batchSize = options.batchSize || 100;
    this.flushInterval = options.flushIntervalMs || 1000;
    this.startFlushTimer();
  }

  add(item: BatchItem): void {
    this.batch.push(item);
    if (this.batch.length >= this.batchSize) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.batch.length === 0) return;
    const items = this.batch.splice(0, this.batchSize);
    const concurrency = 10;
    for (let i = 0; i < items.length; i += concurrency) {
      const chunk = items.slice(i, i + concurrency);
      await Promise.all(chunk.map(item => this.processItem(item)));
    }
  }

  private async processItem(item: BatchItem): Promise<void> {
    try {
      if (item.type === 'identify') {
        await this.client.identify(item.userId, item.data);
      } else {
        await this.client.track(item.userId, {
          name: item.data.event,
          data: item.data.properties
        });
      }
    } catch (error) {
      console.error(`Failed to process ${item.type} for ${item.userId}:`, error);
    }
  }

  private startFlushTimer(): void {
    this.timer = setInterval(() => this.flush(), this.flushInterval);
  }

  async shutdown(): Promise<void> {
    if (this.timer) clearInterval(this.timer);
    await this.flush();
  }
}
```

## Async Fire-and-Forget

```typescript
// lib/async-tracker.ts
class AsyncTracker {
  private queue: Array<() => Promise<void>> = [];
  private processing = false;
  private concurrency = 5;

  constructor(private client: TrackClient) {}

  identifyAsync(userId: string, attributes: Record<string, any>): void {
    this.enqueue(() => this.client.identify(userId, attributes));
  }

  trackAsync(userId: string, event: string, data?: Record<string, any>): void {
    this.enqueue(() => this.client.track(userId, { name: event, data }));
  }

  private enqueue(operation: () => Promise<void>): void {
    this.queue.push(operation);
    this.processQueue();
  }

  private async processQueue(): Promise<void> {
    if (this.processing) return;
    this.processing = true;
    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.concurrency);
      await Promise.allSettled(batch.map(op => op()));
    }
    this.processing = false;
  }
}

export const asyncTracker = new AsyncTracker(getClient());
```

## Deduplication Cache

```typescript
// lib/dedup-cache.ts
import { LRUCache } from 'lru-cache';

const identifyCache = new LRUCache<string, boolean>({
  max: 10000,
  ttl: 60000 // 1 minute
});

export function shouldIdentify(userId: string, attributes: Record<string, any>): boolean {
  const cacheKey = `${userId}:${JSON.stringify(attributes)}`;
  if (identifyCache.get(cacheKey)) return false;
  identifyCache.set(cacheKey, true);
  return true;
}

const eventCache = new LRUCache<string, number>({
  max: 50000,
  ttl: 5000 // 5 seconds
});

export function shouldTrack(userId: string, eventName: string, eventId?: string): boolean {
  const cacheKey = eventId || `${userId}:${eventName}:${Date.now()}`;
  if (eventCache.has(cacheKey)) return false;
  eventCache.set(cacheKey, Date.now());
  return true;
}
```

## Regional Routing

```typescript
// lib/regional-client.ts
import { TrackClient, RegionUS, RegionEU } from '@customerio/track';

class RegionalCustomerIO {
  private clients: Map<string, TrackClient> = new Map();

  constructor(config: { us: { siteId: string; apiKey: string }; eu: { siteId: string; apiKey: string } }) {
    this.clients.set('us', new TrackClient(config.us.siteId, config.us.apiKey, { region: RegionUS }));
    this.clients.set('eu', new TrackClient(config.eu.siteId, config.eu.apiKey, { region: RegionEU }));
  }

  async identify(userId: string, attributes: Record<string, any>, region?: string): Promise<void> {
    const client = this.clients.get(region || 'us') || this.clients.get('us')!;
    await client.identify(userId, attributes);
  }
}
```

## Performance Monitoring

```typescript
// lib/performance-monitor.ts
function wrapWithTiming<T>(name: string, operation: () => Promise<T>): Promise<T> {
  const start = Date.now();
  return operation()
    .then(result => {
      metrics.histogram(`customerio.${name}.latency`, Date.now() - start);
      metrics.increment(`customerio.${name}.success`);
      return result;
    })
    .catch(error => {
      metrics.histogram(`customerio.${name}.latency`, Date.now() - start);
      metrics.increment(`customerio.${name}.error`);
      throw error;
    });
}
```
