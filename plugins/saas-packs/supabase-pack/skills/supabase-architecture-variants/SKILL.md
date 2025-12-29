---
name: supabase-architecture-variants
description: |
  Supabase validated architecture blueprints for different use cases.
  Use when choosing architecture pattern for Supabase integration.
  Trigger with phrases like "supabase architecture", "supabase blueprint",
  "how to structure supabase", "supabase project layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Architecture Variants

## Overview
Three validated architecture blueprints for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- Understanding of team size and traffic expectations
- Knowledge of deployment environment
- Scalability requirements defined

## Instructions

### Step 1: Choose Variant - Monolith (Simple)

**Best for:** MVPs, small teams, < 10K daily active users

```
my-app/
├── src/
│   ├── supabase/
│   │   ├── client.ts          # Singleton client
│   │   ├── types.ts           # Types
│   │   └── middleware.ts      # Express middleware
│   ├── routes/
│   │   └── api/
│   │       └── supabase.ts    # API routes
│   └── index.ts
├── tests/
│   └── supabase.test.ts
└── package.json
```

### Key Characteristics
- Single deployment unit
- Synchronous Supabase calls in request path
- In-memory caching
- Simple error handling

### Code Pattern
```typescript
// Direct integration in route handler
app.post('/api/create', async (req, res) => {
  try {
    const result = await supabaseClient.create(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

---

## Variant B: Service Layer (Moderate)

**Best for:** Growing startups, 10K-100K DAU, multiple integrations

```
my-app/
├── src/
│   ├── services/
│   │   ├── supabase/
│   │   │   ├── client.ts      # Client wrapper
│   │   │   ├── service.ts     # Business logic
│   │   │   ├── repository.ts  # Data access
│   │   │   └── types.ts
│   │   └── index.ts           # Service exports
│   ├── controllers/
│   │   └── supabase.ts
│   ├── routes/
│   ├── middleware/
│   ├── queue/
│   │   └── supabase-processor.ts  # Async processing
│   └── index.ts
├── config/
│   └── supabase/
└── package.json
```

### Key Characteristics
- Separation of concerns
- Background job processing
- Redis caching
- Circuit breaker pattern
- Structured error handling

### Code Pattern
```typescript
// Service layer abstraction
class SupabaseService {
  constructor(
    private client: SupabaseClient,
    private cache: CacheService,
    private queue: QueueService
  ) {}

  async createResource(data: CreateInput): Promise<Resource> {
    // Business logic before API call
    const validated = this.validate(data);

    // Check cache
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // API call with retry
    const result = await this.withRetry(() =>
      this.client.create(validated)
    );

    // Cache result
    await this.cache.set(cacheKey, result, 300);

    // Async follow-up
    await this.queue.enqueue('supabase.post-create', result);

    return result;
  }
}
```

---

## Variant C: Microservice (Complex)

**Best for:** Enterprise, 100K+ DAU, strict SLAs

```
supabase-service/              # Dedicated microservice
├── src/
│   ├── api/
│   │   ├── grpc/
│   │   │   └── supabase.proto
│   │   └── rest/
│   │       └── routes.ts
│   ├── domain/
│   │   ├── entities/
│   │   ├── events/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── supabase/
│   │   │   ├── client.ts
│   │   │   ├── mapper.ts
│   │   │   └── circuit-breaker.ts
│   │   ├── cache/
│   │   ├── queue/
│   │   └── database/
│   └── index.ts
├── config/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
└── package.json

other-services/
├── order-service/       # Calls supabase-service
├── payment-service/
└── notification-service/
```

### Key Characteristics
- Dedicated Supabase microservice
- gRPC for internal communication
- Event-driven architecture
- Database per service
- Kubernetes autoscaling
- Distributed tracing
- Circuit breaker per service

### Code Pattern
```typescript
// Event-driven with domain isolation
class SupabaseAggregate {
  private events: DomainEvent[] = [];

  process(command: SupabaseCommand): void {
    // Domain logic
    const result = this.execute(command);

    // Emit domain event
    this.events.push(new SupabaseProcessedEvent(result));
  }

  getUncommittedEvents(): DomainEvent[] {
    return [...this.events];
  }
}

// Event handler
@EventHandler(SupabaseProcessedEvent)
class SupabaseEventHandler {
  async handle(event: SupabaseProcessedEvent): Promise<void> {
    // Saga orchestration
    await this.sagaOrchestrator.continue(event);
  }
}
```

---

## Decision Matrix

| Factor | Monolith | Service Layer | Microservice |
|--------|----------|---------------|--------------|
| Team Size | 1-5 | 5-20 | 20+ |
| DAU | < 10K | 10K-100K | 100K+ |
| Deployment Frequency | Weekly | Daily | Continuous |
| Failure Isolation | None | Partial | Full |
| Operational Complexity | Low | Medium | High |
| Time to Market | Fastest | Moderate | Slowest |

### Step 2: Migration Path

```
Monolith → Service Layer:
1. Extract Supabase code to service/
2. Add caching layer
3. Add background processing

Service Layer → Microservice:
1. Create dedicated supabase-service repo
2. Define gRPC contract
3. Add event bus
4. Deploy to Kubernetes
5. Migrate traffic gradually
```

## Output
- Architecture variant selected based on team/traffic
- Project structure matching chosen variant
- Migration path documented for future scaling
- Decision matrix for trade-off analysis

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Over-engineering | Started with microservice | Simplify to monolith, scale later |
| Performance issues | Wrong variant for traffic | Re-evaluate decision matrix |
| Team confusion | Inconsistent patterns | Document ADRs, enforce through code review |
| Deployment complexity | Microservice overhead | Consider service mesh or platform team |

## Examples

### ADR for Architecture Choice

```markdown
# ADR-002: Supabase Integration Architecture

## Status
Accepted

## Context
We need to integrate Supabase for [use case].
Team size: 5, Expected DAU: 50K

## Decision
Service Layer (Variant B)

## Rationale
- Team is small but growing
- Traffic will scale in 6 months
- Need background processing for webhooks

## Consequences
- +: Ready for growth
- -: Slightly more complex than monolith
```

## Resources
- [Microservices Trade-offs](https://martinfowler.com/articles/microservice-trade-offs.html)
- [Supabase Architecture Guide](https://supabase.com/docs/architecture)
- [Domain-Driven Design](https://domainlanguage.com/ddd/)

## Next Steps
For common anti-patterns, see `supabase-known-pitfalls`.