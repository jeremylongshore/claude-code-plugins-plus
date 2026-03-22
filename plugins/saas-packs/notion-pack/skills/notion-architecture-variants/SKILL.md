---
name: notion-architecture-variants
description: |
  Choose and implement Notion validated architecture blueprints for different scales.
  Use when designing new Notion integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Notion applications.
  Trigger with phrases like "notion architecture", "notion blueprint",
  "how to structure notion", "notion project layout", "notion microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion Architecture Variants

## Overview
Three validated architecture blueprints for Notion integrations.

## Prerequisites
- Understanding of team size and DAU requirements
- Knowledge of deployment infrastructure
- Clear SLA requirements
- Growth projections available

## Variant A: Monolith (Simple)

**Best for:** MVPs, small teams, < 10K daily active users

```
my-app/
├── src/
│   ├── notion/
│   │   ├── client.ts          # Singleton client
│   │   ├── types.ts           # Types
│   │   └── middleware.ts      # Express middleware
│   ├── routes/
│   │   └── api/
│   │       └── notion.ts    # API routes
│   └── index.ts
├── tests/
│   └── notion.test.ts
└── package.json
```

### Key Characteristics
- Single deployment unit
- Synchronous Notion calls in request path
- In-memory caching
- Simple error handling

### Code Pattern
```typescript
// Direct integration in route handler
app.post('/api/create', async (req, res) => {
  try {
    const result = await notionClient.create(req.body);
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
│   │   ├── notion/
│   │   │   ├── client.ts      # Client wrapper
│   │   │   ├── service.ts     # Business logic
│   │   │   ├── repository.ts  # Data access
│   │   │   └── types.ts
│   │   └── index.ts           # Service exports
│   ├── controllers/
│   │   └── notion.ts
│   ├── routes/
│   ├── middleware/
│   ├── queue/
│   │   └── notion-processor.ts  # Async processing
│   └── index.ts
├── config/
│   └── notion/
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
class NotionService {
  constructor(
    private client: NotionClient,
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
    await this.queue.enqueue('notion.post-create', result);

    return result;
  }
}
```

---

## Variant C: Microservice (Complex)

**Best for:** Enterprise, 100K+ DAU, strict SLAs

```
notion-service/              # Dedicated microservice
├── src/
│   ├── api/
│   │   ├── grpc/
│   │   │   └── notion.proto
│   │   └── rest/
│   │       └── routes.ts
│   ├── domain/
│   │   ├── entities/
│   │   ├── events/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── notion/
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
├── order-service/       # Calls notion-service
├── payment-service/
└── notification-service/
```

### Key Characteristics
- Dedicated Notion microservice
- gRPC for internal communication
- Event-driven architecture
- Database per service
- Kubernetes autoscaling
- Distributed tracing
- Circuit breaker per service

### Code Pattern
```typescript
// Event-driven with domain isolation
class NotionAggregate {
  private events: DomainEvent[] = [];

  process(command: NotionCommand): void {
    // Domain logic
    const result = this.execute(command);

    // Emit domain event
    this.events.push(new NotionProcessedEvent(result));
  }

  getUncommittedEvents(): DomainEvent[] {
    return [...this.events];
  }
}

// Event handler
@EventHandler(NotionProcessedEvent)
class NotionEventHandler {
  async handle(event: NotionProcessedEvent): Promise<void> {
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

## Migration Path

```
Monolith → Service Layer:
1. Extract Notion code to service/
2. Add caching layer
3. Add background processing

Service Layer → Microservice:
1. Create dedicated notion-service repo
2. Define gRPC contract
3. Add event bus
4. Deploy to Kubernetes
5. Migrate traffic gradually
```

## Instructions

### Step 1: Assess Requirements
Use the decision matrix to identify appropriate variant.

### Step 2: Choose Architecture
Select Monolith, Service Layer, or Microservice based on needs.

### Step 3: Implement Structure
Set up project layout following the chosen blueprint.

### Step 4: Plan Migration Path
Document upgrade path for future scaling.

## Output
- Architecture variant selected
- Project structure implemented
- Migration path documented
- Appropriate patterns applied

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Over-engineering | Wrong variant choice | Start simpler |
| Performance issues | Wrong layer | Add caching/async |
| Team friction | Complex architecture | Simplify or train |
| Deployment complexity | Microservice overhead | Consider service layer |

## Examples

### Quick Variant Check
```bash
# Count team size and DAU to select variant
echo "Team: $(git log --format='%ae' | sort -u | wc -l) developers"
echo "DAU: Check analytics dashboard"
```

## Resources
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)
- [Microservices Guide](https://martinfowler.com/microservices/)
- [Notion Architecture Guide](https://docs.notion.com/architecture)

## Next Steps
For common anti-patterns, see `notion-known-pitfalls`.