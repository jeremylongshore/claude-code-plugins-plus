---
name: appfolio-core-workflow-b
description: 'Automate tenant management and lease operations with AppFolio.

  Trigger: "appfolio tenant management".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio — Work Orders & Maintenance

## Overview

Manage the full lifecycle of maintenance work orders through AppFolio's Stack API.
Use this workflow when tenants submit maintenance requests, when you need to assign
vendors to open work orders, track repair progress across properties, or close out
completed jobs with cost records. This is the secondary workflow — for property
dashboards and leasing, see `appfolio-core-workflow-a`.

## Instructions

### Step 1: Create a Work Order from a Maintenance Request

```typescript
const workOrder = await client.workOrders.create({
  property_id: 'prop_4821',
  unit_id: 'unit_12B',
  category: 'plumbing',
  priority: 'high',
  description: 'Kitchen sink leaking under cabinet — tenant reports water damage',
  requested_by: 'tenant_8934',
  due_date: '2026-04-10',
});
console.log(`Work order ${workOrder.id} created — status: ${workOrder.status}`);
```

### Step 2: Assign a Vendor

```typescript
const assignment = await client.workOrders.assign(workOrder.id, {
  vendor_id: 'vendor_plumb_01',
  scheduled_date: '2026-04-08',
  time_window: '09:00-12:00',
  notes: 'Tenant prefers morning. Enter through side gate.',
});
console.log(`Assigned to ${assignment.vendor_name} on ${assignment.scheduled_date}`);
```

### Step 3: Track Work Order Status

```typescript
const open = await client.workOrders.list({
  property_id: 'prop_4821',
  status: ['open', 'in_progress', 'scheduled'],
  sort: 'priority_desc',
});
open.items.forEach(wo =>
  console.log(`#${wo.id} [${wo.priority}] ${wo.category} — ${wo.status} (due ${wo.due_date})`)
);
```

### Step 4: Close Work Order with Cost Record

```typescript
const closed = await client.workOrders.close(workOrder.id, {
  resolution: 'Replaced P-trap and tightened supply line. No further leaks.',
  labor_cost: 175.00,
  materials_cost: 42.50,
  completed_date: '2026-04-08',
  attachments: ['receipt_plumb_0408.pdf'],
});
console.log(`Closed #${closed.id} — total cost: $${closed.total_cost}`);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Expired or invalid API credentials | Refresh client_id/secret in Stack dashboard |
| `404 Work Order Not Found` | Wrong work order ID or already deleted | Verify ID with `workOrders.list()` |
| `422 Missing required fields` | Category or property_id omitted | Include all required fields per schema |
| `409 Conflict` | Work order already closed | Check status before attempting close |
| `429 Rate Limited` | Exceeded 120 requests/minute | Add exponential backoff with 1s base delay |

## Output

A successful run creates a work order, assigns it to a vendor with a scheduled
service window, and closes it with cost records and resolution notes. The property
manager gets a complete audit trail from request through completion.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-sdk-patterns` for authentication setup and pagination helpers.
