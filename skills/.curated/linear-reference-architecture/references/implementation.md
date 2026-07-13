# Linear Reference Architecture - Implementation Details

## Pattern 1: Simple Integration

Best for: Small teams, single applications

```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Linear SDK   │  │ Cache Layer  │  │ Webhook      │  │
│  │ (API calls)  │  │ (In-memory)  │  │ Handler      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Linear API         │
              │   api.linear.app     │
              └──────────────────────┘
```

```typescript
// Simple architecture implementation
// lib/simple-linear.ts
import { LinearClient } from "@linear/sdk";

const cache = new Map<string, { data: any; expires: number }>();

export class SimpleLinearService {
  private client: LinearClient;

  constructor() {
    this.client = new LinearClient({
      apiKey: process.env.LINEAR_API_KEY!,
    });
  }

  async getWithCache<T>(key: string, fetcher: () => Promise<T>, ttl = 300): Promise<T> {
    const cached = cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return cached.data;
    }

    const data = await fetcher();
    cache.set(key, { data, expires: Date.now() + ttl * 1000 });
    return data;
  }

  async getTeams() {
    return this.getWithCache("teams", () => this.client.teams());
  }
}
```

## Pattern 2: Service-Oriented Architecture

Best for: Medium teams, multiple applications

```
┌────────────────────────────────────────────────────────────────┐
│                       API Gateway                               │
└────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ Issues Service  │  │ Projects Service│  │ Notifications Svc   │
│ (CRUD + sync)   │  │ (Planning)      │  │ (Slack, Email)      │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ Linear Gateway  │
                    │ (Rate limiting, │
                    │  caching, auth) │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Linear API    │
                    └─────────────────┘
```

```typescript
// lib/linear-gateway.ts
import { LinearClient } from "@linear/sdk";
import Redis from "ioredis";

export class LinearGateway {
  private client: LinearClient;
  private redis: Redis;
  private rateLimiter: RateLimiter;

  constructor() {
    this.client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    this.redis = new Redis(process.env.REDIS_URL);
    this.rateLimiter = new RateLimiter({
      maxRequests: 1000, // Leave buffer from 1500 limit
      windowMs: 60000,
    });
  }

  async execute<T>(operation: string, fn: () => Promise<T>): Promise<T> {
    const cacheKey = `linear:${operation}`;
    const cached = await this.redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    await this.rateLimiter.acquire();

    const start = Date.now();
    try {
      const result = await fn();
      await this.redis.setex(cacheKey, 60, JSON.stringify(result));
      metrics.requestDuration.observe(Date.now() - start);
      return result;
    } catch (error) {
      metrics.errors.inc({ operation });
      throw error;
    }
  }
}
```

## Pattern 3: Event-Driven Architecture

Best for: Large teams, real-time requirements

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Event Bus (Kafka/SQS)                        │
└─────────────────────────────────────────────────────────────────────┘
         ▲                         │                        │
         │                         ▼                        ▼
┌─────────────────┐       ┌─────────────────┐      ┌─────────────────┐
│ Webhook Ingester│       │ Event Processor │      │ Notification    │
│ (Linear events) │       │ (Business logic)│      │ Service         │
└─────────────────┘       └─────────────────┘      └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ State Store     │
                          │ (PostgreSQL)    │
                          └─────────────────┘
```

```typescript
// services/webhook-ingester.ts
import { Kafka } from "kafkajs";

const kafka = new Kafka({ brokers: [process.env.KAFKA_BROKER!] });
const producer = kafka.producer();

export async function ingestWebhook(event: LinearWebhookEvent): Promise<void> {
  if (!verifySignature(event)) {
    throw new Error("Invalid signature");
  }

  await producer.send({
    topic: `linear.${event.type.toLowerCase()}`,
    messages: [{
      key: event.data.id,
      value: JSON.stringify(event),
      headers: {
        action: event.action,
        timestamp: event.webhookTimestamp.toString(),
      },
    }],
  });
}

// services/event-processor.ts
const consumer = kafka.consumer({ groupId: "linear-processor" });
await consumer.subscribe({ topics: ["linear.issue", "linear.comment"] });

await consumer.run({
  eachMessage: async ({ topic, message }) => {
    const event = JSON.parse(message.value!.toString());
    switch (topic) {
      case "linear.issue":
        await processIssueEvent(event);
        break;
      case "linear.comment":
        await processCommentEvent(event);
        break;
    }
  },
});
```

## Pattern 4: CQRS with Event Sourcing

Best for: Complex domains, audit requirements

```typescript
// cqrs/event-store.ts
interface StoredEvent {
  id: string;
  aggregateId: string;
  aggregateType: string;
  eventType: string;
  data: Record<string, unknown>;
  metadata: {
    userId: string;
    correlationId: string;
    causationId: string;
    timestamp: Date;
  };
  version: number;
}

class EventStore {
  async append(aggregateId: string, events: StoredEvent[]): Promise<void> {
    await db.transaction(async (tx) => {
      for (const event of events) {
        await tx.insert(eventsTable).values(event);
      }
    });
    for (const event of events) {
      await eventBus.publish(event);
    }
  }

  async getEvents(aggregateId: string): Promise<StoredEvent[]> {
    return db.select().from(eventsTable)
      .where(eq(eventsTable.aggregateId, aggregateId))
      .orderBy(eventsTable.version);
  }
}

// Projector for read model
class IssueProjector {
  @Subscribe("IssueCreated")
  async onIssueCreated(event: StoredEvent): Promise<void> {
    await db.insert(issueReadModel).values({
      id: event.aggregateId,
      ...event.data,
      createdAt: event.metadata.timestamp,
    });
  }

  @Subscribe("IssueUpdated")
  async onIssueUpdated(event: StoredEvent): Promise<void> {
    await db.update(issueReadModel)
      .set(event.data)
      .where(eq(issueReadModel.id, event.aggregateId));
  }
}
```

## Project Structure

```
linear-integration/
├── src/
│   ├── api/                    # REST/GraphQL API
│   │   ├── routes/
│   │   └── middleware/
│   ├── services/               # Business logic
│   │   ├── issue-service.ts
│   │   ├── project-service.ts
│   │   └── sync-service.ts
│   ├── infrastructure/         # External integrations
│   │   ├── linear/
│   │   │   ├── client.ts
│   │   │   ├── cache.ts
│   │   │   └── webhook-handler.ts
│   │   ├── database/
│   │   └── cache/
│   ├── domain/                 # Domain models
│   │   ├── issue.ts
│   │   └── project.ts
│   └── config/                 # Configuration
│       └── index.ts
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── infrastructure/             # IaC
    ├── terraform/
    └── kubernetes/
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
