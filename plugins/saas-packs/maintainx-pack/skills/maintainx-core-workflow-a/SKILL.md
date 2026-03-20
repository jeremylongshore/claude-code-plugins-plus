---
name: maintainx-core-workflow-a
description: |
  Execute MaintainX primary workflow: Work Order lifecycle management.
  Use when creating, updating, and managing work orders through their full lifecycle,
  from creation to completion with all status transitions.
  Trigger with phrases like "maintainx work order", "create work order",
  "work order lifecycle", "maintenance task", "manage work orders".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Core Workflow A: Work Order Lifecycle

## Overview
Master the complete work order lifecycle in MaintainX -- from creation through completion. Work orders are the core unit of maintenance operations.

## Prerequisites
- Completed `maintainx-install-auth` setup
- `MAINTAINX_API_KEY` environment variable configured
- MaintainX account with work order permissions

## Status Transition Flow

```
OPEN ──→ IN_PROGRESS ──→ COMPLETED ──→ CLOSED
  │           │               ↑
  │           ↓               │
  │        ON_HOLD ───────────┘
  │
  └──→ CLOSED (cancelled)
```

## Instructions

### Step 1: Create a Work Order

```typescript
import { MaintainXClient } from './maintainx/client';

const client = new MaintainXClient();

// Create a corrective work order
const { data: wo } = await client.createWorkOrder({
  title: 'Pump Station #3 - Seal Leak Repair',
  description: 'Detected water leak at the mechanical seal. Needs immediate attention.',
  priority: 'HIGH',
  status: 'OPEN',
  assignees: [{ type: 'USER', id: 4521 }],
  assetId: 8901,
  locationId: 2345,
  dueDate: '2026-03-21T17:00:00Z',
  categories: ['CORRECTIVE'],
});

console.log(`Work order #${wo.id} created`);
```

### Step 2: Update Status Through Lifecycle

```typescript
// Technician starts work
await client.updateWorkOrder(wo.id, {
  status: 'IN_PROGRESS',
});

// Put on hold (waiting for parts)
await client.updateWorkOrder(wo.id, {
  status: 'ON_HOLD',
  onHoldReason: 'Waiting for replacement seal kit from supplier',
});

// Resume and complete
await client.updateWorkOrder(wo.id, {
  status: 'IN_PROGRESS',
});

await client.updateWorkOrder(wo.id, {
  status: 'COMPLETED',
  completionNotes: 'Replaced mechanical seal. Tested for 30 min with no leaks.',
});
```

### Step 3: Query Work Orders

```typescript
// Fetch open work orders sorted by priority
const { data: openOrders } = await client.getWorkOrders({
  status: 'OPEN',
  limit: 25,
});

for (const order of openOrders.workOrders) {
  console.log(`#${order.id} [${order.priority}] ${order.title}`);
}

// Paginate through all IN_PROGRESS orders
async function getAllInProgress() {
  const allOrders = [];
  let cursor: string | undefined;

  do {
    const { data } = await client.getWorkOrders({
      status: 'IN_PROGRESS',
      limit: 100,
      cursor,
    });
    allOrders.push(...data.workOrders);
    cursor = data.cursor;
  } while (cursor);

  return allOrders;
}
```

### Step 4: Add Comments and Attachments

```typescript
// Add a technician note
await client.request('POST', `/workorders/${wo.id}/comments`, {
  body: 'Arrived on site. Isolating pump before disassembly.',
});

// Add a completion photo (URL-based)
await client.request('POST', `/workorders/${wo.id}/files`, {
  url: 'https://storage.example.com/photos/seal-repair-complete.jpg',
  name: 'seal-repair-complete.jpg',
});
```

### Step 5: Assign to Teams

```typescript
// Assign to a team instead of individual
const { data: teams } = await client.request('GET', '/teams');
const mechTeam = teams.teams.find((t: any) => t.name === 'Mechanical');

await client.updateWorkOrder(wo.id, {
  assignees: [{ type: 'TEAM', id: mechTeam.id }],
});
```

## Output
- Work orders created with full metadata (title, description, priority, assignees, asset, location)
- Status transitions executed through the complete lifecycle
- Paginated query results for filtering work orders
- Comments and files attached to work orders

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing `title` field | Include at least `title` in POST body |
| 404 Not Found | Invalid asset/location/user ID | Verify referenced IDs exist via GET endpoints |
| 403 Forbidden | Insufficient permissions | Check user role has work order write access |
| 422 Invalid transition | Invalid status change (e.g., CLOSED to OPEN) | Follow the status transition flow above |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Work Orders Help](https://help.getmaintainx.com/about-work-orders)
- [Complete a Work Order](https://help.getmaintainx.com/complete-a-work-order)

## Next Steps
For asset and location management, see `maintainx-core-workflow-b`.

## Examples

**Bulk-create preventive maintenance work orders**:

```typescript
const pmSchedule = [
  { title: 'Weekly HVAC Filter Check', priority: 'LOW', categories: ['PREVENTIVE'] },
  { title: 'Monthly Fire Extinguisher Inspection', priority: 'MEDIUM', categories: ['PREVENTIVE'] },
  { title: 'Quarterly Elevator Safety Audit', priority: 'HIGH', categories: ['PREVENTIVE'] },
];

for (const pm of pmSchedule) {
  const { data } = await client.createWorkOrder(pm);
  console.log(`PM created: #${data.id} - ${data.title}`);
}
```

**Filter work orders by date range**:

```bash
curl -s "https://api.getmaintainx.com/v1/workorders?createdAtGte=2026-03-01T00:00:00Z&createdAtLte=2026-03-31T23:59:59Z&limit=50" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.workOrders | length'
```
