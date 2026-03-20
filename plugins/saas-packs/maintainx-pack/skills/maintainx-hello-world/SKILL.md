---
name: maintainx-hello-world
description: |
  Create a minimal working MaintainX example - your first work order.
  Use when starting a new MaintainX integration, testing your setup,
  or learning basic MaintainX API patterns.
  Trigger with phrases like "maintainx hello world", "maintainx example",
  "maintainx quick start", "create first work order", "simple maintainx code".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Hello World

## Overview
Create your first work order using the MaintainX REST API -- the core building block of CMMS operations.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Valid `MAINTAINX_API_KEY` environment variable
- Node.js 18+ or curl

## Instructions

### Step 1: Create a Work Order (curl)

```bash
curl -X POST https://api.getmaintainx.com/v1/workorders \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello World - Test Work Order",
    "description": "First API-created work order. Safe to delete.",
    "priority": "LOW",
    "status": "OPEN"
  }' | jq .
```

Expected response:
```json
{
  "id": 12345,
  "title": "Hello World - Test Work Order",
  "status": "OPEN",
  "priority": "LOW",
  "createdAt": "2026-03-19T12:00:00Z"
}
```

### Step 2: Create a Work Order (TypeScript)

```typescript
// hello-maintainx.ts
import { MaintainXClient } from './maintainx/client';

async function helloMaintainX() {
  const client = new MaintainXClient();

  // Create a basic work order
  const { data: workOrder } = await client.createWorkOrder({
    title: 'HVAC Filter Replacement - Building A',
    description: 'Replace air filters in units 1-4 on the 3rd floor.',
    priority: 'MEDIUM',
  });
  console.log('Created work order:', workOrder.id);

  // Retrieve it back to confirm
  const { data: fetched } = await client.getWorkOrder(workOrder.id);
  console.log('Work order status:', fetched.status);
  console.log('Created at:', fetched.createdAt);

  // List open work orders
  const { data: list } = await client.getWorkOrders({
    status: 'OPEN',
    limit: 5,
  });
  console.log(`Found ${list.workOrders.length} open work orders`);
}

helloMaintainX();
```

### Step 3: Verify and Clean Up

```bash
# List recent work orders to confirm creation
curl -s "https://api.getmaintainx.com/v1/workorders?limit=3" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.workOrders[] | {id, title, status}'

# Delete the test work order (replace ID)
curl -X DELETE "https://api.getmaintainx.com/v1/workorders/12345" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY"
```

## Output
- Working code file that creates a MaintainX work order via REST API
- Console output showing the created work order ID, status, and timestamp
- Verified retrieval of the created work order

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing required `title` field | Include at least `title` in the POST body |
| 401 Unauthorized | Invalid API key | Check `MAINTAINX_API_KEY` environment variable |
| 403 Forbidden | Plan limitations | Verify API access on your subscription |
| 422 Unprocessable | Invalid enum value | Use valid `priority` (`NONE`, `LOW`, `MEDIUM`, `HIGH`) |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Work Orders Help](https://help.getmaintainx.com/about-work-orders)

## Next Steps
Proceed to `maintainx-local-dev-loop` for development workflow setup.

## Examples

**Create a work order tied to an asset**:

```typescript
const wo = await client.createWorkOrder({
  title: 'Conveyor Belt #7 - Bearing Replacement',
  description: 'Replace worn bearings on the main drive shaft.',
  priority: 'HIGH',
  assetId: 98765,       // Link to equipment asset
  locationId: 54321,    // Link to facility location
  assignees: [{ type: 'USER', id: 111 }],
  dueDate: '2026-03-25T17:00:00Z',
});
```

**Create a work order from a preventive maintenance template**:

```bash
curl -X POST https://api.getmaintainx.com/v1/workorders \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Monthly Fire Extinguisher Inspection",
    "priority": "MEDIUM",
    "categories": ["PREVENTIVE"],
    "procedureId": 7890
  }'
```
