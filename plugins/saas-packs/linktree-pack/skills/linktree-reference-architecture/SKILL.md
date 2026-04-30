---
name: linktree-reference-architecture
description: 'Reference Architecture for Linktree.

  Trigger: "linktree reference architecture".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree Reference Architecture

## Overview
Design a read-optimized integration layer for the Linktree link-in-bio platform. The extreme read-to-write ratio on public profiles drives a two-tier cache with async analytics, keeping the hot path free from downstream blocking.

## Instructions
1. Provision the prerequisites below and configure Linktree API credentials.
2. Deploy the service layer with the cache-aside pattern for profile reads.
3. Wire the webhook ingester to invalidate cache on profile mutations.
4. Start the click event consumer to populate the analytics store.
5. Adjust Redis TTLs and rate-limit buckets to match your traffic profile.

## Prerequisites
- Node.js 18+, TypeScript 5, Redis 7, RabbitMQ or SQS, PostgreSQL 15
- Linktree API credentials with `profile:read` and `links:write` scopes

## Architecture Diagram
```
Client --> API Gateway --> LinktreeService --> Linktree API
                                |
                 +--------------+--------------+
                 v              v              v
           Redis Cache    Event Queue    Analytics DB
           (profiles)    (clicks/views)  (aggregates)
```

## Service Layer
```typescript
class LinktreeService {
  constructor(
    private api: LinktreeApiClient,
    private cache: ProfileCache,
    private events: EventPublisher
  ) {}

  async getProfile(username: string): Promise<Profile> {
    const cached = await this.cache.get(`profile:${username}`);
    if (cached) return cached;
    const profile = await this.api.fetchProfile(username);
    await this.cache.set(`profile:${username}`, profile, 300);
    return profile;
  }

  async updateLinks(profileId: string, links: LinkUpdate[]): Promise<void> {
    await this.api.patchLinks(profileId, links);
    await this.cache.invalidate(`profile:${profileId}`);
    await this.events.publish('links.updated', { profileId, count: links.length });
  }
}
```

## Caching Strategy
```typescript
class ProfileCache {
  constructor(private redis: RedisClient) {}

  async get(key: string): Promise<Profile | null> {
    const raw = await this.redis.get(key);
    return raw ? JSON.parse(raw) : null;
  }

  async set(key: string, data: Profile, ttl: number): Promise<void> {
    await this.redis.setEx(key, ttl, JSON.stringify(data));
  }

  async invalidate(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length) await this.redis.del(keys);
  }
}
// TTLs: profiles 5 min, link lists 2 min, analytics summaries 15 min
```

## Event Pipeline
```typescript
class ClickEventConsumer {
  constructor(private queue: MessageQueue, private db: AnalyticsStore) {}

  async start(): Promise<void> {
    await this.queue.subscribe('link.clicked', async (evt: ClickEvent) => {
      await this.db.incrementClickCount(evt.linkId, evt.timestamp);
      await this.db.recordReferrer(evt.linkId, evt.referrer);
    });
  }
}

class WebhookIngester {
  async handle(payload: WebhookPayload): Promise<void> {
    if (payload.event === 'profile.updated') {
      await this.cache.invalidate(`profile:${payload.profileId}`);
    }
    await this.queue.publish(payload.event, payload.data);
  }
}
```

## Data Model
```typescript
interface Profile {
  id: string; username: string; displayName: string;
  bio: string; avatarUrl: string; links: Link[];
  theme: ThemeConfig; lastModified: Date;
}
interface Link {
  id: string; title: string; url: string;
  position: number; clickCount: number; enabled: boolean;
}
interface ClickEvent {
  linkId: string; profileId: string; referrer: string;
  timestamp: Date; geo: { country: string; region: string };
}
```

## Output
Running this architecture produces a cached profile API, a real-time click analytics pipeline, and webhook-driven cache invalidation that keeps profiles fresh within 5 minutes of any update.

## Scaling Considerations
- Shard Redis by username hash prefix to distribute hot profiles across nodes
- Batch click events into 10-second micro-windows before writing to analytics
- Use token-bucket rate limiting per Linktree API key (150 req/min default)
- Deploy read replicas behind cache so warm profiles never hit the upstream API

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Linktree API | 429 rate limit | Exponential backoff with jitter, serve stale cache |
| Redis | Connection lost | Fall through to API direct, warm cache on reconnect |
| Event Queue | Consumer lag | Dead-letter after 3 retries, alert on DLQ depth |
| Webhook Ingester | Duplicate delivery | Idempotent upsert keyed on event ID |
| Analytics Store | Write timeout | Buffer in memory, flush on recovery |

## Examples
```bash
# Fetch a profile through the cached service layer
curl http://localhost:3000/api/profiles/myusername
# Trigger a manual cache invalidation after bulk link update
curl -X POST http://localhost:3000/api/cache/invalidate/myusername
```

## Resources
- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-deploy-integration`.
