# MaintainX Hello World - Implementation Guide

> Full implementation details and code examples for the `maintainx-hello-world` skill.

# MaintainX Hello World

## Overview

Create your first work order using the MaintainX REST API - the core building block of CMMS operations.

## Prerequisites

- Completed `maintainx-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: List Existing Work Orders (Read)

First, verify your connection by listing existing work orders:

```bash
# Using curl
curl -X GET "https://api.getmaintainx.com/v1/workorders?limit=5" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "workOrders": [
    {
      "id": "wo_123456",
      "title": "Weekly Equipment Inspection",
      "status": "OPEN",
      "priority": "MEDIUM",
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ],
  "nextCursor": "eyJpZCI6MTIzNDU2fQ=="
}
```

### Step 2: Create Your First Work Order

```typescript
// hello-maintainx.ts
import { MaintainXClient } from './maintainx/client';

async function createFirstWorkOrder() {
  const client = new MaintainXClient();

  // Create a simple work order
  const workOrder = await client.createWorkOrder({
    title: 'Hello World - Test Work Order',
    description: 'This is my first work order created via the API!',
    priority: 'LOW',
  });

  console.log('Work order created successfully!');
  console.log('ID:', workOrder.data.id);
  console.log('Title:', workOrder.data.title);
  console.log('Status:', workOrder.data.status);

  return workOrder.data;
}

createFirstWorkOrder().catch(console.error);
```

### Step 3: Create Work Order with Asset Assignment

```typescript
// create-maintenance-task.ts
import { MaintainXClient } from './maintainx/client';

async function createMaintenanceTask() {
  const client = new MaintainXClient();

  // First, get an asset to assign
  const assetsResponse = await client.getAssets({ limit: 1 });
  const asset = assetsResponse.data.assets[0];

  // Get a location
  const locationsResponse = await client.getLocations({ limit: 1 });
  const location = locationsResponse.data.locations[0];

  // Create work order with full context
  const workOrder = await client.createWorkOrder({
    title: 'Quarterly HVAC Filter Replacement',
    description: `
      Maintenance Task:
      1. Turn off HVAC unit
      2. Remove old filter
      3. Install new filter (size: 20x25x1)
      4. Turn on unit and verify operation
      5. Log meter reading
    `,
    priority: 'MEDIUM',
    assetId: asset?.id,
    locationId: location?.id,
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
  });

  console.log('Maintenance task created:');
  console.log(JSON.stringify(workOrder.data, null, 2));

  return workOrder.data;
}

createMaintenanceTask().catch(console.error);
```

### Step 4: Full CRUD Example

```typescript
// crud-example.ts
import { MaintainXClient } from './maintainx/client';

async function workOrderCrudExample() {
  const client = new MaintainXClient();

  // CREATE
  console.log('Creating work order...');
  const created = await client.createWorkOrder({
    title: 'API Test - CRUD Demo',
    description: 'Testing full lifecycle',
    priority: 'LOW',
  });
  console.log('Created:', created.data.id);

  // READ
  console.log('\nReading work order...');
  const read = await client.getWorkOrder(created.data.id);
  console.log('Read:', read.data.title);

  // LIST with filtering
  console.log('\nListing open work orders...');
  const list = await client.getWorkOrders({
    status: 'OPEN',
    limit: 10
  });
  console.log('Found', list.data.workOrders.length, 'open work orders');

  // Note: Update and Delete operations depend on your plan tier
  // and may require additional endpoints

  return { created: created.data, read: read.data, list: list.data };
}

workOrderCrudExample().catch(console.error);
```

### Python Example

```python
# hello_maintainx.py
from maintainx_client import MaintainXClient
from datetime import datetime, timedelta

def main():
    client = MaintainXClient()

    # List existing work orders
    print("Fetching existing work orders...")
    work_orders = client.get_work_orders(limit=5)
    print(f"Found {len(work_orders.get('workOrders', []))} work orders")

    # Create new work order
    print("\nCreating new work order...")
    new_wo = client.create_work_order({
        "title": "Hello World - Python API Test",
        "description": "Created via Python MaintainX client",
        "priority": "LOW",
        "dueDate": (datetime.now() + timedelta(days=7)).isoformat() + "Z"
    })

    print(f"Created work order: {new_wo['id']}")
    print(f"Title: {new_wo['title']}")
    print(f"Status: {new_wo['status']}")

if __name__ == "__main__":
    main()
```

## Output

- Working code file with MaintainX client usage
- Successfully created work order in your MaintainX account
- Console output showing:
```
Work order created successfully!
ID: wo_789012
Title: Hello World - Test Work Order
Status: OPEN
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Missing required fields | Include at least `title` field |
| 401 Unauthorized | Invalid API key | Check `MAINTAINX_API_KEY` environment variable |
| 403 Forbidden | Plan limitations | Verify API access on your subscription |
| 422 Unprocessable | Invalid field values | Check enum values (priority, status) |

## Common Field Values

### Work Order Priority
- `NONE` - No priority set
- `LOW` - Low priority
- `MEDIUM` - Medium priority
- `HIGH` - High priority

### Work Order Status
- `OPEN` - New, not started
- `IN_PROGRESS` - Work underway
- `ON_HOLD` - Paused/waiting
- `DONE` - Completed

## Resources

- [MaintainX Work Orders Guide](https://help.getmaintainx.com/about-work-orders)
- [MaintainX API Reference](https://maintainx.dev/)
- [Work Order Settings](https://help.getmaintainx.com/work-order-settings)

## Next Steps

Proceed to `maintainx-local-dev-loop` for development workflow setup.
