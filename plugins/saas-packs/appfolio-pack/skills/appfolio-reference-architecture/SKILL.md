---
name: appfolio-reference-architecture
description: |
  Reference architecture for AppFolio property management integration.
  Trigger: "appfolio architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Reference Architecture

## Overview

Production architecture for property management integrations with the AppFolio Stack API. Designed for multi-property portfolios requiring real-time vacancy tracking, tenant lifecycle management, work order routing, and accounting reconciliation. Key design drivers: data freshness for leasing decisions, idempotent sync for financial accuracy, and tenant-facing portal responsiveness.

## Architecture Diagram
```
Dashboard (React) ──→ Property Service ──→ Redis Cache ──→ AppFolio Stack API
                           ↓                                 /properties
                      Queue (Bull) ──→ Sync Worker           /tenants
                           ↓                                 /leases
                      Webhook Handler ←── AppFolio Events    /work-orders
                           ↓                                 /bills
                      Accounting Sync ──→ QuickBooks/Xero
```

## Service Layer
```typescript
class PropertyService {
  constructor(private client: AppFolioClient, private cache: CacheLayer) {}

  async getPortfolioSummary(propertyIds: string[]): Promise<PortfolioSummary> {
    const properties = await Promise.all(
      propertyIds.map(id => this.cache.getOrFetch(`prop:${id}`, () => this.client.get(`/properties/${id}`)))
    );
    return { totalUnits: properties.reduce((sum, p) => sum + p.units.length, 0),
             vacancyRate: this.calcVacancy(properties), pendingWorkOrders: await this.getPendingOrders(propertyIds) };
  }

  async routeWorkOrder(order: WorkOrderRequest): Promise<string> {
    const property = await this.client.get(`/properties/${order.propertyId}`);
    const vendor = this.selectVendor(property.region, order.category);
    return this.client.post('/work-orders', { ...order, assigned_vendor: vendor });
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  properties: { ttl: 300, prefix: 'prop' },     // 5 min — changes infrequently
  tenants:    { ttl: 120, prefix: 'tenant' },    // 2 min — moderate churn
  leases:     { ttl: 60,  prefix: 'lease' },     // 1 min — financial accuracy
  workOrders: { ttl: 30,  prefix: 'wo' },        // 30s — real-time tracking
  vacancies:  { ttl: 15,  prefix: 'vacancy' },   // 15s — leasing speed matters
};
// Webhook-driven invalidation: AppFolio events flush matching cache keys immediately
```

## Event Pipeline
```typescript
class PropertyEventPipeline {
  private queue = new Bull('appfolio-events', { redis: process.env.REDIS_URL });

  async onWebhook(event: AppFolioEvent): Promise<void> {
    await this.queue.add(event.type, event, { attempts: 3, backoff: { type: 'exponential', delay: 2000 } });
  }

  async processLeaseEvent(event: LeaseEvent): Promise<void> {
    if (event.type === 'lease.signed') await this.updateVacancy(event.propertyId);
    if (event.type === 'lease.terminated') await this.triggerMoveOutWorkflow(event);
  }

  async processWorkOrderEvent(event: WorkOrderEvent): Promise<void> {
    if (event.status === 'completed') await this.reconcileVendorInvoice(event);
  }
}
```

## Data Model
```typescript
interface Property { id: string; name: string; address: Address; units: Unit[]; region: string; }
interface Tenant   { id: string; name: string; email: string; leaseId: string; balance: number; }
interface Lease    { id: string; propertyId: string; unitId: string; tenantId: string; startDate: string; endDate: string; monthlyRent: number; status: 'active' | 'pending' | 'terminated'; }
interface WorkOrder { id: string; propertyId: string; unitId: string; category: 'plumbing' | 'electrical' | 'hvac' | 'general'; status: string; assignedVendor: string; }
```

## Scaling Considerations
- Partition sync workers by property region to avoid cross-region API rate limits
- Use read replicas for dashboard queries; write path goes through event pipeline
- Batch tenant notifications (rent reminders, maintenance updates) via queue to avoid email rate limits
- Cache vacancy data aggressively — leasing agents hit this endpoint 10x more than any other
- Shard work order routing by property portfolio to enable independent scaling per management group

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Property sync | AppFolio 429 rate limit | Exponential backoff with jitter, per-property circuit breaker |
| Lease webhook | Duplicate event delivery | Idempotency key on lease ID + event timestamp |
| Work order routing | Vendor API timeout | Queue retry with fallback to manual assignment |
| Accounting sync | Balance mismatch | Reconciliation queue with human review flag |
| Tenant portal | Cache miss storm | Stale-while-revalidate pattern, circuit breaker on API layer |

## Resources
- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps
See `appfolio-deploy-integration`.
