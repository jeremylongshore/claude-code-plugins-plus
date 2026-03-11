# Customer.io SDK Patterns - Implementation Guide

### Pattern 1: Type-Safe Client
```typescript
// types/customerio.ts
export interface UserAttributes {
  email: string;
  first_name?: string;
  last_name?: string;
  created_at?: number;
  plan?: 'free' | 'pro' | 'enterprise';
  [key: string]: string | number | boolean | undefined;
}

export interface EventData {
  [key: string]: string | number | boolean | object;
}

export type EventName =
  | 'signed_up'
  | 'subscription_started'
  | 'subscription_cancelled'
  | 'feature_used'
  | 'email_verified';

// lib/customerio-client.ts
import { TrackClient, RegionUS } from '@customerio/track';
import type { UserAttributes, EventData, EventName } from '../types/customerio';

export class TypedCustomerIO {
  private client: TrackClient;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  }

  async identify(userId: string, attributes: UserAttributes): Promise<void> {
    await this.client.identify(userId, {
      ...attributes,
      _updated_at: Math.floor(Date.now() / 1000)
    });
  }

  async track(userId: string, event: EventName, data?: EventData): Promise<void> {
    await this.client.track(userId, { name: event, data });
  }
}
```

### Pattern 2: Retry with Exponential Backoff
```typescript
// lib/customerio-resilient.ts
import { TrackClient } from '@customerio/track';

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000
};

async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      if (attempt === config.maxRetries) break;

      // Don't retry on 4xx errors (client errors)
      if (error instanceof Error && error.message.includes('4')) {
        throw error;
      }

      const delay = Math.min(
        config.baseDelay * Math.pow(2, attempt),
        config.maxDelay
      );
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

export class ResilientCustomerIO {
  private client: TrackClient;

  constructor(siteId: string, apiKey: string) {
    this.client = new TrackClient(siteId, apiKey, { region: RegionUS });
  }

  async identify(userId: string, attributes: Record<string, any>) {
    return withRetry(() => this.client.identify(userId, attributes));
  }

  async track(userId: string, event: string, data?: Record<string, any>) {
    return withRetry(() => this.client.track(userId, { name: event, data }));
  }
}
```

### Pattern 3: Event Queue with Batching
```typescript
// lib/customerio-queue.ts
interface QueuedEvent {
  userId: string;
  event: string;
  data?: Record<string, any>;
  timestamp: number;
}

export class CustomerIOQueue {
  private queue: QueuedEvent[] = [];
  private flushInterval: NodeJS.Timer | null = null;
  private maxBatchSize = 100;
  private flushIntervalMs = 5000;

  constructor(private client: TrackClient) {
    this.startAutoFlush();
  }

  enqueue(userId: string, event: string, data?: Record<string, any>) {
    this.queue.push({
      userId,
      event,
      data,
      timestamp: Date.now()
    });

    if (this.queue.length >= this.maxBatchSize) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, this.maxBatchSize);

    await Promise.allSettled(
      batch.map(item =>
        this.client.track(item.userId, {
          name: item.event,
          data: { ...item.data, _queued_at: item.timestamp }
        })
      )
    );
  }

  private startAutoFlush() {
    this.flushInterval = setInterval(() => this.flush(), this.flushIntervalMs);
  }

  async shutdown(): Promise<void> {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    await this.flush();
  }
}
```

### Pattern 4: Singleton with Lazy Initialization
```typescript
// lib/customerio-singleton.ts
import { TrackClient, RegionUS } from '@customerio/track';

let instance: TrackClient | null = null;

export function getCustomerIO(): TrackClient {
  if (!instance) {
    if (!process.env.CUSTOMERIO_SITE_ID || !process.env.CUSTOMERIO_API_KEY) {
      throw new Error('Customer.io credentials not configured');
    }
    instance = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID,
      process.env.CUSTOMERIO_API_KEY,
      { region: RegionUS }
    );
  }
  return instance;
}

// Usage
import { getCustomerIO } from './lib/customerio-singleton';
await getCustomerIO().identify('user-123', { email: 'user@example.com' });
```
