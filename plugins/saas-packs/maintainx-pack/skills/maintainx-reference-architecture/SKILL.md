---
name: maintainx-reference-architecture
description: |
  Production-grade architecture patterns for MaintainX integrations.
  Use when designing system architecture, planning integrations,
  or building enterprise-scale MaintainX solutions.
  Trigger with phrases like "maintainx architecture", "maintainx design",
  "maintainx system design", "maintainx enterprise", "maintainx patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Reference Architecture

## Overview
Production-grade architecture patterns for building scalable, maintainable integrations between MaintainX and enterprise systems (ERP, SCADA, data warehouses).

## Prerequisites
- Understanding of distributed systems
- Cloud platform experience (GCP, AWS, or Azure)
- MaintainX API familiarity

## Instructions

### Step 1: Event-Driven Sync Architecture

The recommended architecture for most MaintainX integrations. Uses webhooks for real-time updates and scheduled jobs for reconciliation.

```
MaintainX API ──webhook──→ Cloud Run ──→ Pub/Sub ──→ Cloud Functions
                                              │
                                              ├──→ BigQuery (analytics)
                                              ├──→ ERP System (SAP, Oracle)
                                              └──→ Notification Service
```

```typescript
// src/architecture/event-driven.ts
import express from 'express';
import { PubSub } from '@google-cloud/pubsub';

const app = express();
const pubsub = new PubSub();
const topic = pubsub.topic('maintainx-events');

// Webhook receiver publishes to Pub/Sub
app.post('/webhooks/maintainx', async (req, res) => {
  const { event, data } = req.body;

  await topic.publishMessage({
    data: Buffer.from(JSON.stringify({ event, data })),
    attributes: { event, resourceId: String(data.id) },
  });

  res.status(200).json({ status: 'queued' });
});

// Subscriber processes events asynchronously
const subscription = pubsub.subscription('maintainx-events-sub');
subscription.on('message', async (message) => {
  const { event, data } = JSON.parse(message.data.toString());

  switch (event) {
    case 'workorder.completed':
      await syncToERP(data);
      await updateAnalytics(data);
      break;
    case 'workorder.created':
      if (data.priority === 'HIGH') {
        await sendUrgentNotification(data);
      }
      break;
  }

  message.ack();
});
```

### Step 2: Bi-Directional Sync Gateway

For integrating MaintainX with ERP systems (SAP, Oracle) where changes flow both ways.

```
ERP (SAP/Oracle) ←──→ Sync Gateway ←──→ MaintainX API
                          │
                    Conflict Resolution
                    + Audit Trail
                    + Sync State DB
```

```typescript
// src/architecture/sync-gateway.ts

interface SyncRecord {
  externalId: string;     // ERP system ID
  maintainxId: number;    // MaintainX ID
  lastSyncAt: string;
  syncDirection: 'inbound' | 'outbound' | 'bidirectional';
  hash: string;           // Content hash for change detection
}

class SyncGateway {
  constructor(
    private maintainx: MaintainXClient,
    private erp: ERPClient,
    private db: SyncStateDB,
  ) {}

  // MaintainX → ERP
  async syncToERP(workOrder: any) {
    const existing = await this.db.findByMaintainxId(workOrder.id);

    if (existing && this.hash(workOrder) === existing.hash) {
      return; // No change, skip
    }

    const erpRecord = this.mapToERP(workOrder);
    if (existing) {
      await this.erp.update(existing.externalId, erpRecord);
    } else {
      const created = await this.erp.create(erpRecord);
      await this.db.create({
        externalId: created.id,
        maintainxId: workOrder.id,
        lastSyncAt: new Date().toISOString(),
        syncDirection: 'outbound',
        hash: this.hash(workOrder),
      });
    }
  }

  // ERP → MaintainX
  async syncFromERP(erpRecord: any) {
    const existing = await this.db.findByExternalId(erpRecord.id);
    const woData = this.mapFromERP(erpRecord);

    if (existing) {
      await this.maintainx.updateWorkOrder(existing.maintainxId, woData);
    } else {
      const created = await this.maintainx.createWorkOrder(woData);
      await this.db.create({
        externalId: erpRecord.id,
        maintainxId: created.id,
        lastSyncAt: new Date().toISOString(),
        syncDirection: 'inbound',
        hash: this.hash(created),
      });
    }
  }

  private mapToERP(wo: any) {
    return {
      title: wo.title,
      status: this.mapStatus(wo.status),
      priority: wo.priority,
      completedAt: wo.completedAt,
    };
  }

  private mapFromERP(erp: any) {
    return {
      title: erp.description,
      priority: erp.urgency === 'HIGH' ? 'HIGH' : 'MEDIUM',
    };
  }

  private mapStatus(status: string) {
    const map: Record<string, string> = {
      OPEN: 'PLANNED',
      IN_PROGRESS: 'ACTIVE',
      COMPLETED: 'FINISHED',
      CLOSED: 'ARCHIVED',
    };
    return map[status] || 'UNKNOWN';
  }

  private hash(obj: any): string {
    return require('crypto').createHash('md5')
      .update(JSON.stringify(obj)).digest('hex');
  }
}
```

### Step 3: Analytics Data Pipeline

```
MaintainX API ──scheduled──→ Cloud Functions ──→ BigQuery
                                                    │
                                              Looker / Metabase
                                                    │
                                              KPI Dashboards:
                                              - MTTR (Mean Time to Repair)
                                              - PM Compliance %
                                              - Work Order Backlog
                                              - Asset Downtime
```

```typescript
// src/architecture/analytics-pipeline.ts

interface MaintenanceKPIs {
  mttr: number;           // Mean Time to Repair (hours)
  pmCompliance: number;   // Preventive Maintenance compliance %
  backlog: number;        // Open work orders count
  completionRate: number; // Orders completed / orders created
}

async function calculateKPIs(client: MaintainXClient): Promise<MaintenanceKPIs> {
  const completed = await paginate(
    (cursor) => client.getWorkOrders({ status: 'COMPLETED', limit: 100, cursor }),
    'workOrders',
  );

  const open = await paginate(
    (cursor) => client.getWorkOrders({ status: 'OPEN', limit: 100, cursor }),
    'workOrders',
  );

  // MTTR: Average time from OPEN to COMPLETED
  const repairTimes = completed
    .filter((wo: any) => wo.createdAt && wo.completedAt)
    .map((wo: any) => {
      const created = new Date(wo.createdAt).getTime();
      const completed = new Date(wo.completedAt).getTime();
      return (completed - created) / 3600000; // hours
    });

  const mttr = repairTimes.length > 0
    ? repairTimes.reduce((a: number, b: number) => a + b, 0) / repairTimes.length
    : 0;

  // PM Compliance
  const pmOrders = completed.filter((wo: any) =>
    wo.categories?.includes('PREVENTIVE'),
  );
  const allPM = [...pmOrders, ...open.filter((wo: any) =>
    wo.categories?.includes('PREVENTIVE'),
  )];
  const pmCompliance = allPM.length > 0 ? (pmOrders.length / allPM.length) * 100 : 100;

  return {
    mttr: Math.round(mttr * 10) / 10,
    pmCompliance: Math.round(pmCompliance),
    backlog: open.length,
    completionRate: completed.length / (completed.length + open.length) * 100,
  };
}
```

### Step 4: Multi-Site Architecture

```
Site A (Plant)           Site B (Warehouse)        Site C (Office)
  └── Local Agent           └── Local Agent            └── Local Agent
        │                         │                          │
        └─────────── Central Hub (Cloud Run) ────────────────┘
                          │
                    MaintainX API
                    (Org-level access)
```

```typescript
// Central hub routing requests by site
const siteConfigs = {
  'plant-austin': { orgId: 'org-1', apiKey: process.env.MX_KEY_PLANT },
  'warehouse-dallas': { orgId: 'org-2', apiKey: process.env.MX_KEY_WAREHOUSE },
  'office-houston': { orgId: 'org-3', apiKey: process.env.MX_KEY_OFFICE },
};

function getClientForSite(siteId: string): MaintainXClient {
  const config = siteConfigs[siteId as keyof typeof siteConfigs];
  if (!config) throw new Error(`Unknown site: ${siteId}`);
  return new MaintainXClient(config.apiKey, config.orgId);
}
```

## Output
- Event-driven architecture with Pub/Sub for decoupled processing
- Bi-directional sync gateway with conflict resolution and audit trail
- Analytics pipeline calculating maintenance KPIs (MTTR, PM compliance)
- Multi-site architecture with per-site API key isolation

## Error Handling
| Pattern | Failure Mode | Mitigation |
|---------|-------------|------------|
| Event-driven | Pub/Sub delivery failure | Dead letter queue, retry policy |
| Bi-directional sync | Conflict on same record | Last-write-wins or manual resolution |
| Analytics pipeline | Incomplete data fetch | Retry with backfill, validate counts |
| Multi-site | One site API key expired | Independent health checks per site |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [Event-Driven Architecture](https://martinfowler.com/articles/event-driven.html)

## Next Steps
For multi-environment setup, see `maintainx-multi-env-setup`.

## Examples

**SCADA integration** (pulling sensor data into MaintainX work orders):

```typescript
// Auto-create work order when equipment sensor exceeds threshold
async function handleSensorAlert(sensorId: string, value: number, threshold: number) {
  const asset = await findAssetBySensorId(sensorId);

  await client.createWorkOrder({
    title: `Sensor Alert: ${asset.name} - ${sensorId} exceeded threshold`,
    description: `Value: ${value} (threshold: ${threshold}). Auto-generated from SCADA.`,
    priority: value > threshold * 1.5 ? 'HIGH' : 'MEDIUM',
    assetId: asset.maintainxId,
    categories: ['CORRECTIVE'],
  });
}
```
