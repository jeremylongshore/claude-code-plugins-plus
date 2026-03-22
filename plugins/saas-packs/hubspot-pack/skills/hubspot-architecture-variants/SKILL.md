---
name: hubspot-architecture-variants
description: |
  Choose and implement HubSpot integration architecture for different scales.
  Use when designing new HubSpot integrations, choosing between embedded/service/gateway
  patterns, or planning architecture for HubSpot CRM applications.
  Trigger with phrases like "hubspot architecture", "hubspot design pattern",
  "how to structure hubspot", "hubspot integration pattern", "hubspot microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Architecture Variants

## Overview

Three validated architecture patterns for HubSpot CRM integrations at different scales, from embedded client to dedicated API gateway.

## Prerequisites

- Understanding of team size and daily API call volume
- Knowledge of deployment infrastructure
- Clear sync requirements (real-time vs batch)

## Instructions

### Variant A: Embedded Client (Simple)

**Best for:** MVPs, small teams, < 10K contacts, < 50K API calls/day

```
your-app/
├── src/
│   ├── hubspot/
│   │   ├── client.ts       # @hubspot/api-client singleton
│   │   └── contacts.ts     # Direct CRM operations
│   ├── routes/
│   │   └── api.ts           # API routes that call HubSpot directly
│   └── index.ts
```

```typescript
// Direct integration in route handlers
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

app.get('/api/contacts', async (req, res) => {
  const page = await client.crm.contacts.basicApi.getPage(
    20, req.query.after as string, ['email', 'firstname', 'lastname']
  );
  res.json(page);
});

app.post('/api/contacts', async (req, res) => {
  const contact = await client.crm.contacts.basicApi.create({
    properties: req.body,
    associations: [],
  });
  res.status(201).json(contact);
});
```

**Pros:** Fast to build, simple to understand, one deployment
**Cons:** No fault isolation, HubSpot latency in user request path

---

### Variant B: Service Layer with Async Queue

**Best for:** Growing teams, 10K-100K contacts, 50K-300K API calls/day

```
your-app/
├── src/
│   ├── services/
│   │   └── hubspot/
│   │       ├── client.ts       # Singleton with circuit breaker
│   │       ├── contact.ts      # Business logic layer
│   │       ├── deal.ts
│   │       └── sync.ts         # Background sync
│   ├── queue/
│   │   └── hubspot-worker.ts   # Process async operations
│   ├── cache/
│   │   └── hubspot-cache.ts    # Redis cache layer
│   ├── routes/
│   └── index.ts
```

```typescript
// Service layer abstracts HubSpot from route handlers
class ContactService {
  private client = getHubSpotClient();
  private cache: Redis;
  private queue: BullQueue;

  async getContact(id: string): Promise<Contact> {
    // Check cache first
    const cached = await this.cache.get(`contact:${id}`);
    if (cached) return JSON.parse(cached);

    // Fetch from HubSpot
    const contact = await this.client.crm.contacts.basicApi.getById(
      id, ['email', 'firstname', 'lastname', 'lifecyclestage']
    );

    // Cache for 5 minutes
    await this.cache.setex(`contact:${id}`, 300, JSON.stringify(contact));
    return contact;
  }

  async createContact(data: CreateContactInput): Promise<{ jobId: string }> {
    // Enqueue for async processing (fast API response)
    const job = await this.queue.add('create-contact', data);
    return { jobId: job.id };
  }
}

// Background worker
queue.process('create-contact', async (job) => {
  const contact = await client.crm.contacts.basicApi.create({
    properties: job.data,
    associations: [],
  });
  // Invalidate cache, send notification, etc.
  await cache.del(`contacts:list`);
  return contact;
});
```

**Pros:** Fault isolation, fast API responses, caching, background processing
**Cons:** More complexity, Redis dependency, two process types

---

### Variant C: Dedicated HubSpot Gateway

**Best for:** Enterprise, 100K+ contacts, multiple services needing CRM access

```
hubspot-gateway/               # Standalone service
├── src/
│   ├── api/
│   │   ├── grpc/              # Internal gRPC API
│   │   │   └── hubspot.proto
│   │   └── rest/              # REST API (optional)
│   ├── domain/
│   │   ├── contacts.ts        # Domain logic
│   │   ├── deals.ts
│   │   └── sync.ts
│   ├── infrastructure/
│   │   ├── hubspot-client.ts  # SDK wrapper
│   │   ├── rate-limiter.ts    # Centralized rate limiting
│   │   ├── cache.ts           # Redis cache
│   │   └── circuit-breaker.ts
│   └── index.ts
├── k8s/
│   ├── deployment.yaml
│   └── hpa.yaml

other-services/
├── order-service/      # Calls hubspot-gateway
├── marketing-service/  # Calls hubspot-gateway
└── analytics-service/  # Calls hubspot-gateway
```

```typescript
// All HubSpot access goes through the gateway
// Gateway handles rate limiting, caching, and circuit breaking

// Centralized rate limiter ensures all services share the 10 req/sec limit
class CentralizedRateLimiter {
  private redis: Redis;
  private maxPerSecond = 8; // leave headroom

  async acquire(): Promise<void> {
    const key = `hubspot:ratelimit:${Math.floor(Date.now() / 1000)}`;
    const count = await this.redis.incr(key);
    await this.redis.expire(key, 2);

    if (count > this.maxPerSecond) {
      throw new Error('HubSpot rate limit -- waiting');
    }
  }
}
```

**Pros:** Single point of rate limiting, all services share cache, independent scaling
**Cons:** Network hop, operational complexity, gRPC/REST contract management

---

### Decision Matrix

| Factor | Embedded | Service Layer | Gateway |
|--------|----------|---------------|---------|
| Team size | 1-3 | 3-15 | 15+ |
| Contacts | < 10K | 10K-100K | 100K+ |
| Services using CRM | 1 | 1-2 | 3+ |
| Sync model | Synchronous | Async queue | Event-driven |
| Cache | In-memory | Redis | Redis + CDN |
| Rate limit mgmt | SDK built-in | App-level | Centralized |
| Fault isolation | None | Partial | Full |
| Time to build | Days | 1-2 weeks | 3-4 weeks |

### Migration Path

```
Embedded → Service Layer:
  1. Extract HubSpot client to services/hubspot/
  2. Add Redis cache layer
  3. Move writes to background queue

Service Layer → Gateway:
  1. Extract to standalone service
  2. Define gRPC/REST contract
  3. Add centralized rate limiter
  4. Migrate services one at a time
```

## Output

- Three validated architecture patterns with code examples
- Decision matrix for choosing the right pattern
- Migration path from simpler to more complex architectures

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Over-engineering | Wrong variant choice | Start with Embedded, evolve |
| Rate limit shared | Multiple services hitting HubSpot | Move to Gateway pattern |
| Cache inconsistency | No invalidation strategy | Invalidate on webhook events |
| Gateway single point of failure | No redundancy | Run multiple replicas + HPA |

## Resources

- [HubSpot API Client GitHub](https://github.com/HubSpot/hubspot-api-nodejs)
- [HubSpot API Usage Guidelines](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [Monolith First (Martin Fowler)](https://martinfowler.com/bliki/MonolithFirst.html)

## Next Steps

For common anti-patterns, see `hubspot-known-pitfalls`.
