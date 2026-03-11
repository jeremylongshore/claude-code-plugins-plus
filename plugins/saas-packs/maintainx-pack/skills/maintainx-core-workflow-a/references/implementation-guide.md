# MaintainX Core Workflow A: Work Order Lifecycle - Implementation Guide

> Full implementation details and code examples for the `maintainx-core-workflow-a` skill.

# MaintainX Core Workflow A: Work Order Lifecycle

## Overview

Master the complete work order lifecycle in MaintainX - from creation through completion. Work orders are the core unit of maintenance operations.

## Prerequisites

- Completed `maintainx-install-auth` setup
- Understanding of maintenance operations
- MaintainX account with work order permissions

## Work Order Lifecycle

```
                    ┌─────────────┐
                    │    OPEN     │
                    │  (Created)  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ IN_PROGRESS │◄────┐
                    │  (Started)  │     │
                    └──────┬──────┘     │
                           │            │
              ┌────────────┴────────────┤
              │                         │
              ▼                         │
       ┌─────────────┐                  │
       │   ON_HOLD   │──────────────────┘
       │  (Waiting)  │
       └─────────────┘
              │
              │ (Resume or Close)
              ▼
       ┌─────────────┐
       │    DONE     │
       │ (Completed) │
       └─────────────┘
```

## Instructions

### Step 1: Create Work Order

```typescript
// src/workflows/work-order-lifecycle.ts
import { MaintainXClient } from '../api/maintainx-client';

interface CreateWorkOrderInput {
  title: string;
  description?: string;
  priority: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  assigneeIds?: string[];
  assetId?: string;
  locationId?: string;
  dueDate?: Date;
  categories?: string[];
  customFields?: Record<string, any>;
}

export async function createWorkOrder(
  client: MaintainXClient,
  input: CreateWorkOrderInput
) {
  const workOrder = await client.createWorkOrder({
    title: input.title,
    description: input.description,
    priority: input.priority,
    assignees: input.assigneeIds,
    assetId: input.assetId,
    locationId: input.locationId,
    dueDate: input.dueDate?.toISOString(),
  });

  console.log(`Created work order: ${workOrder.id}`);
  console.log(`Status: ${workOrder.status}`);
  console.log(`Priority: ${workOrder.priority}`);

  return workOrder;
}

// Example: Create emergency repair work order
async function createEmergencyRepair(client: MaintainXClient) {
  return createWorkOrder(client, {
    title: 'URGENT: Conveyor Belt Failure - Line 3',
    description: `
## Problem
Conveyor belt stopped unexpectedly on production line 3.
Loud grinding noise before failure.

## Impact
- Production halted
- Estimated loss: $5,000/hour

## Initial Assessment
- Belt appears worn
- Motor may need inspection
- Safety lockout applied

## Required
1. Inspect motor and belt
2. Replace worn components
3. Test operation before restart
    `,
    priority: 'HIGH',
    assetId: 'asset_conveyor_003',
    locationId: 'loc_production_floor',
  });
}
```

### Step 2: Assign Work Order

```typescript
// Assign technicians to work order
async function assignWorkOrder(
  client: MaintainXClient,
  workOrderId: string,
  assigneeIds: string[]
) {
  // Note: Check MaintainX API for update endpoint availability
  // This may require PATCH /workorders/{id}

  // For now, create new work order with assignments
  // or use MaintainX web interface for assignment updates

  console.log(`Assigning work order ${workOrderId} to:`, assigneeIds);

  // If update endpoint available:
  // return client.updateWorkOrder(workOrderId, { assignees: assigneeIds });
}

// Find available technicians
async function findAvailableTechnicians(client: MaintainXClient) {
  const users = await client.getUsers({ limit: 100 });

  // Filter to maintenance technicians
  const technicians = users.users.filter(
    user => user.role === 'TECHNICIAN' || user.role === 'MAINTENANCE'
  );

  return technicians;
}
```

### Step 3: Work Order Status Transitions

```typescript
// Status transition logic
type WorkOrderStatus = 'OPEN' | 'IN_PROGRESS' | 'ON_HOLD' | 'DONE';

interface StatusTransition {
  from: WorkOrderStatus;
  to: WorkOrderStatus;
  reason?: string;
}

const validTransitions: StatusTransition[] = [
  { from: 'OPEN', to: 'IN_PROGRESS' },
  { from: 'IN_PROGRESS', to: 'ON_HOLD', reason: 'Waiting for parts' },
  { from: 'IN_PROGRESS', to: 'DONE' },
  { from: 'ON_HOLD', to: 'IN_PROGRESS' },
  { from: 'ON_HOLD', to: 'DONE' },
];

function isValidTransition(from: WorkOrderStatus, to: WorkOrderStatus): boolean {
  return validTransitions.some(t => t.from === from && t.to === to);
}

async function transitionWorkOrder(
  client: MaintainXClient,
  workOrderId: string,
  newStatus: WorkOrderStatus,
  notes?: string
) {
  const workOrder = await client.getWorkOrder(workOrderId);
  const currentStatus = workOrder.status as WorkOrderStatus;

  if (!isValidTransition(currentStatus, newStatus)) {
    throw new Error(
      `Invalid transition: ${currentStatus} -> ${newStatus}`
    );
  }

  console.log(`Transitioning ${workOrderId}: ${currentStatus} -> ${newStatus}`);
  if (notes) {
    console.log(`Notes: ${notes}`);
  }

  // Update via API if available, or via MaintainX interface
  // return client.updateWorkOrder(workOrderId, { status: newStatus });
}
```

### Step 4: Complete Work Order with Documentation

```typescript
interface CompletionReport {
  workOrderId: string;
  completedBy: string;
  completedAt: Date;
  timeSpent: number; // minutes
  partsUsed: { partId: string; quantity: number }[];
  notes: string;
  attachments?: string[];
}

async function completeWorkOrder(
  client: MaintainXClient,
  report: CompletionReport
) {
  console.log('=== Work Order Completion Report ===');
  console.log(`Work Order: ${report.workOrderId}`);
  console.log(`Completed By: ${report.completedBy}`);
  console.log(`Completed At: ${report.completedAt.toISOString()}`);
  console.log(`Time Spent: ${report.timeSpent} minutes`);

  if (report.partsUsed.length > 0) {
    console.log('Parts Used:');
    report.partsUsed.forEach(p =>
      console.log(`  - Part ${p.partId}: ${p.quantity}`)
    );
  }

  console.log(`Notes: ${report.notes}`);

  // Mark as complete
  // await transitionWorkOrder(client, report.workOrderId, 'DONE', report.notes);

  return report;
}
```

### Step 5: Full Workflow Example

```typescript
// Complete work order workflow
async function executeMaintenanceWorkflow(client: MaintainXClient) {
  // 1. Create work order
  const workOrder = await createWorkOrder(client, {
    title: 'Scheduled PM - HVAC Unit Inspection',
    description: `
Monthly preventive maintenance inspection for HVAC unit.

## Checklist
- [ ] Check filters
- [ ] Inspect belts
- [ ] Verify refrigerant levels
- [ ] Clean coils
- [ ] Test thermostat
- [ ] Document readings
    `,
    priority: 'MEDIUM',
    assetId: 'asset_hvac_001',
    locationId: 'loc_building_a',
  });

  console.log(`\n1. Work order created: ${workOrder.id}`);

  // 2. Assign to technician
  const technicians = await findAvailableTechnicians(client);
  if (technicians.length > 0) {
    console.log(`\n2. Would assign to: ${technicians[0].firstName} ${technicians[0].lastName}`);
  }

  // 3. Start work (transition to IN_PROGRESS)
  console.log('\n3. Transitioning to IN_PROGRESS');
  // await transitionWorkOrder(client, workOrder.id, 'IN_PROGRESS');

  // 4. Complete work
  console.log('\n4. Completing work order');
  await completeWorkOrder(client, {
    workOrderId: workOrder.id,
    completedBy: 'tech_001',
    completedAt: new Date(),
    timeSpent: 45,
    partsUsed: [
      { partId: 'part_filter_20x25', quantity: 2 },
    ],
    notes: 'Replaced filters. All readings normal. Next PM due in 30 days.',
  });

  return workOrder;
}
```

### Step 6: Query Work Orders

```typescript
// Find work orders by various criteria
async function queryWorkOrders(client: MaintainXClient) {
  // Open high-priority work orders
  const urgent = await client.getWorkOrders({
    status: 'OPEN',
    priority: 'HIGH',
    limit: 20,
  });
  console.log(`Urgent open: ${urgent.workOrders.length}`);

  // Work orders for specific asset
  const assetWOs = await client.getWorkOrders({
    assetId: 'asset_pump_001',
    limit: 50,
  });
  console.log(`Asset work orders: ${assetWOs.workOrders.length}`);

  // Overdue work orders
  const today = new Date().toISOString();
  const overdue = await client.getWorkOrders({
    status: 'OPEN',
    // Filter by dueDate in application logic
  });
  const overdueWOs = overdue.workOrders.filter(
    wo => wo.dueDate && new Date(wo.dueDate) < new Date()
  );
  console.log(`Overdue: ${overdueWOs.length}`);

  return { urgent, assetWOs, overdueWOs };
}
```

## Output

- Created work orders with full metadata
- Proper status transitions
- Completion documentation
- Query results for work orders

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing title | Ensure title field is provided |
| 404 Not Found | Invalid asset/location ID | Verify IDs exist in system |
| 403 Forbidden | Insufficient permissions | Check user role and plan tier |
| Invalid transition | Wrong status flow | Follow valid transition paths |

## Work Order Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| title | Yes | Short description of task |
| description | No | Detailed instructions |
| priority | No | NONE, LOW, MEDIUM, HIGH |
| status | Auto | OPEN, IN_PROGRESS, ON_HOLD, DONE |
| assignees | No | Array of user IDs |
| assetId | No | Associated equipment |
| locationId | No | Facility/area |
| dueDate | No | ISO 8601 timestamp |

## Resources

- [MaintainX Work Orders Guide](https://help.getmaintainx.com/about-work-orders)
- [Complete a Work Order](https://help.getmaintainx.com/complete-a-work-order)
- [Work Order Settings](https://help.getmaintainx.com/work-order-settings)

## Next Steps

For asset and location management, see `maintainx-core-workflow-b`.
