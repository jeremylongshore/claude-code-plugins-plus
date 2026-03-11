# MaintainX Reference Architecture - Implementation Guide

> Full implementation details and code examples for the `maintainx-reference-architecture` skill.

# MaintainX Reference Architecture

## Overview

Production-grade architecture patterns for building scalable, maintainable MaintainX integrations.

## Prerequisites

- Understanding of distributed systems
- Cloud platform experience
- MaintainX API familiarity

## Architecture Patterns

### Pattern 1: Event-Driven Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                     MaintainX Platform                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Work Orders  │  │   Assets     │  │  Locations   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                    │
│                    ┌──────▼──────┐                             │
│                    │  Webhooks   │                             │
│                    └──────┬──────┘                             │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Your Integration Layer                          │
│                                                                    │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐  │
│  │ Webhook Handler│───▶│  Event Queue   │───▶│ Event Processor│  │
│  │   (Express)    │    │   (Redis/SQS)  │    │   (Workers)    │  │
│  └────────────────┘    └────────────────┘    └───────┬────────┘  │
│                                                      │           │
│  ┌────────────────┐    ┌────────────────┐    ┌──────▼────────┐  │
│  │  API Gateway   │───▶│ MaintainX Client│───▶│  Data Store   │  │
│  │   (REST/GraphQL)    │   (Cached)     │    │  (PostgreSQL) │  │
│  └────────────────┘    └────────────────┘    └───────────────┘  │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    External Systems                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │   ERP    │  │   SCADA  │  │  BI/Reports│ │  Slack  │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└───────────────────────────────────────────────────────────────────┘
```

### Pattern 2: Sync Gateway Architecture

```typescript
// src/architecture/sync-gateway.ts

interface SyncGatewayConfig {
  pollInterval: number;
  batchSize: number;
  retryPolicy: RetryPolicy;
}

class MaintainXSyncGateway {
  private client: MaintainXClient;
  private cache: CacheManager;
  private eventEmitter: EventEmitter;
  private syncState: Map<string, Date>;

  constructor(config: SyncGatewayConfig) {
    this.client = new CachedMaintainXClient(new MaintainXClient());
    this.cache = new CacheManager(process.env.REDIS_URL!);
    this.eventEmitter = new EventEmitter();
    this.syncState = new Map();
  }

  // Bi-directional sync
  async sync(): Promise<SyncResult> {
    const result: SyncResult = {
      inbound: { created: 0, updated: 0, deleted: 0 },
      outbound: { created: 0, updated: 0, deleted: 0 },
    };

    // Inbound: MaintainX -> Local
    await this.syncInbound(result.inbound);

    // Outbound: Local -> MaintainX
    await this.syncOutbound(result.outbound);

    return result;
  }

  private async syncInbound(stats: SyncStats): Promise<void> {
    const lastSync = this.syncState.get('workorders') || new Date(0);

    // Fetch changes since last sync
    const changes = await this.client.getWorkOrders({
      updatedAfter: lastSync.toISOString(),
      limit: 100,
    });

    for (const wo of changes.workOrders) {
      const local = await this.localStore.getWorkOrder(wo.id);

      if (!local) {
        await this.localStore.createWorkOrder(wo);
        stats.created++;
        this.eventEmitter.emit('workorder:created', wo);
      } else if (new Date(wo.updatedAt) > new Date(local.updatedAt)) {
        await this.localStore.updateWorkOrder(wo);
        stats.updated++;
        this.eventEmitter.emit('workorder:updated', wo);
      }
    }

    this.syncState.set('workorders', new Date());
  }

  private async syncOutbound(stats: SyncStats): Promise<void> {
    // Get pending local changes
    const pendingChanges = await this.localStore.getPendingChanges();

    for (const change of pendingChanges) {
      try {
        switch (change.action) {
          case 'create':
            await this.client.createWorkOrder(change.data);
            stats.created++;
            break;
          case 'update':
            // await this.client.updateWorkOrder(change.id, change.data);
            stats.updated++;
            break;
        }

        await this.localStore.markSynced(change.id);
      } catch (error) {
        console.error(`Failed to sync change ${change.id}:`, error);
      }
    }
  }

  // Subscribe to events
  on(event: string, handler: (data: any) => void): void {
    this.eventEmitter.on(event, handler);
  }
}
```

### Pattern 3: Multi-Tenant Architecture

```typescript
// src/architecture/multi-tenant.ts

interface Tenant {
  id: string;
  name: string;
  maintainxApiKey: string;
  maintainxOrgId?: string;
  config: TenantConfig;
}

class MultiTenantMaintainXService {
  private tenantClients: Map<string, MaintainXClient> = new Map();
  private tenantStore: TenantStore;

  async getClientForTenant(tenantId: string): Promise<MaintainXClient> {
    // Check cache
    if (this.tenantClients.has(tenantId)) {
      return this.tenantClients.get(tenantId)!;
    }

    // Load tenant config
    const tenant = await this.tenantStore.getTenant(tenantId);
    if (!tenant) {
      throw new Error(`Tenant ${tenantId} not found`);
    }

    // Create client with tenant's API key
    const client = new MaintainXClient({
      apiKey: tenant.maintainxApiKey,
      orgId: tenant.maintainxOrgId,
    });

    this.tenantClients.set(tenantId, client);
    return client;
  }

  // Tenant-scoped operations
  async getWorkOrdersForTenant(
    tenantId: string,
    params?: WorkOrderQueryParams
  ): Promise<WorkOrder[]> {
    const client = await this.getClientForTenant(tenantId);
    const response = await client.getWorkOrders(params);
    return response.workOrders;
  }

  // Cross-tenant aggregation (for admin dashboards)
  async getWorkOrderCountByTenant(): Promise<Map<string, number>> {
    const counts = new Map<string, number>();
    const tenants = await this.tenantStore.getAllTenants();

    await Promise.all(
      tenants.map(async (tenant) => {
        const client = await this.getClientForTenant(tenant.id);
        const response = await client.getWorkOrders({ limit: 1 });
        // Use total from response metadata if available
        counts.set(tenant.id, response.workOrders.length);
      })
    );

    return counts;
  }
}
```

### Pattern 4: CQRS with Event Sourcing

```typescript
// src/architecture/cqrs.ts

// Commands - Write side
interface CreateWorkOrderCommand {
  type: 'CreateWorkOrder';
  payload: {
    title: string;
    description?: string;
    priority: string;
    assetId?: string;
  };
  metadata: {
    userId: string;
    timestamp: Date;
  };
}

class CommandHandler {
  private client: MaintainXClient;
  private eventStore: EventStore;

  async handle(command: CreateWorkOrderCommand): Promise<void> {
    // Execute command
    const workOrder = await this.client.createWorkOrder(command.payload);

    // Store event
    await this.eventStore.append({
      streamId: `workorder-${workOrder.id}`,
      type: 'WorkOrderCreated',
      data: workOrder,
      metadata: command.metadata,
    });

    // Publish event for projections
    await this.eventBus.publish('WorkOrderCreated', workOrder);
  }
}

// Queries - Read side
interface WorkOrderReadModel {
  id: string;
  title: string;
  status: string;
  priority: string;
  assetName?: string;
  locationName?: string;
  createdAt: Date;
  // Denormalized for fast reads
}

class WorkOrderProjection {
  private readStore: ReadStore;

  // Event handlers update read model
  async onWorkOrderCreated(event: WorkOrderCreatedEvent): Promise<void> {
    await this.readStore.upsert({
      id: event.data.id,
      title: event.data.title,
      status: event.data.status,
      priority: event.data.priority,
      assetName: event.data.asset?.name,
      locationName: event.data.location?.name,
      createdAt: new Date(event.data.createdAt),
    });
  }

  // Fast read queries
  async getOpenWorkOrders(): Promise<WorkOrderReadModel[]> {
    return this.readStore.find({ status: 'OPEN' });
  }
}
```

### Pattern 5: Microservices Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway                                   │
│                     (Kong / AWS API GW)                              │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ Work Order Service │  │   Asset Service   │  │ Notification Svc  │
│                    │  │                    │  │                   │
│ ┌────────────────┐ │  │ ┌────────────────┐ │  │ ┌───────────────┐│
│ │MaintainX Client│ │  │ │MaintainX Client│ │  │ │ Slack/Email   ││
│ └────────────────┘ │  │ └────────────────┘ │  │ └───────────────┘│
│ ┌────────────────┐ │  │ ┌────────────────┐ │  │ ┌───────────────┐│
│ │   PostgreSQL   │ │  │ │   PostgreSQL   │ │  │ │    Redis      ││
│ └────────────────┘ │  │ └────────────────┘ │  │ └───────────────┘│
└─────────┬──────────┘  └─────────┬──────────┘  └─────────┬────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                          ┌───────▼───────┐
                          │  Message Bus   │
                          │ (Kafka/RabbitMQ)│
                          └───────────────┘
```

## Implementation Guidelines

### Separation of Concerns

```typescript
// src/layers/domain.ts - Business logic
class WorkOrderDomain {
  canTransitionTo(currentStatus: string, newStatus: string): boolean {
    // Business rules only - no MaintainX specifics
  }
}

// src/layers/application.ts - Use cases
class WorkOrderService {
  async completeWorkOrder(id: string, completionData: any): Promise<void> {
    // Orchestrates domain + infrastructure
  }
}

// src/layers/infrastructure.ts - MaintainX integration
class MaintainXRepository {
  async save(workOrder: WorkOrderEntity): Promise<void> {
    // MaintainX API calls
  }
}
```

### Error Boundaries

```typescript
// src/architecture/error-boundaries.ts

class MaintainXIntegrationError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean = false
  ) {
    super(message);
    this.name = 'MaintainXIntegrationError';
  }
}

// Wrap all MaintainX calls
async function withErrorBoundary<T>(
  operation: () => Promise<T>,
  context: string
): Promise<T> {
  try {
    return await operation();
  } catch (error: any) {
    const status = error.response?.status;

    if (status === 429) {
      throw new MaintainXIntegrationError(
        'Rate limited',
        'RATE_LIMITED',
        true
      );
    }

    if (status >= 500) {
      throw new MaintainXIntegrationError(
        'MaintainX service unavailable',
        'SERVICE_UNAVAILABLE',
        true
      );
    }

    throw new MaintainXIntegrationError(
      `${context}: ${error.message}`,
      'INTEGRATION_ERROR',
      false
    );
  }
}
```

## Output

- Event-driven architecture pattern
- Sync gateway for bi-directional sync
- Multi-tenant architecture
- CQRS with event sourcing
- Microservices integration

## Architecture Decision Records

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API caching | Redis | Fast, supports TTL, cluster mode |
| Message queue | Redis/SQS | Simple, reliable, scales well |
| Database | PostgreSQL | ACID, JSON support, mature |
| Event store | PostgreSQL | Simplicity over dedicated event store |

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [Martin Fowler - Patterns](https://martinfowler.com/)
- [Microsoft - Cloud Design Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/)

## Next Steps

For multi-environment setup, see `maintainx-multi-env-setup`.
