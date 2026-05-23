# Variant C: Microservice (Complex)

## Variant C: Microservice (Complex)

**Best for:** Enterprise, 100K+ DAU, strict SLAs

```
vercel-service/              # Dedicated microservice
├── src/
│   ├── api/
│   │   ├── grpc/
│   │   │   └── vercel.proto
│   │   └── rest/
│   │       └── routes.ts
│   ├── domain/
│   │   ├── entities/
│   │   ├── events/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── vercel/
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
├── order-service/       # Calls vercel-service
├── payment-service/
└── notification-service/
```

### Key Characteristics

- Dedicated Vercel microservice
- gRPC for internal communication
- Event-driven architecture
- Database per service
- Kubernetes autoscaling
- Distributed tracing
- Circuit breaker per service

### Code Pattern

```typescript
// Event-driven with domain isolation
class VercelAggregate {
  private events: DomainEvent[] = [];

  process(command: VercelCommand): void {
    // Domain logic
    const result = this.execute(command);

    // Emit domain event
    this.events.push(new VercelProcessedEvent(result));
  }

  getUncommittedEvents(): DomainEvent[] {
    return [...this.events];
  }
}

// Event handler
@EventHandler(VercelProcessedEvent)
class VercelEventHandler {
  async handle(event: VercelProcessedEvent): Promise<void> {
    // Saga orchestration
    await this.sagaOrchestrator.continue(event);
  }
}
```

---
