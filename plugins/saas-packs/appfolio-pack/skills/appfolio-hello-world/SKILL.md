---
name: appfolio-hello-world
description: |
  Query AppFolio properties, units, and tenants via REST API.
  Trigger: "appfolio hello world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Hello World

## Overview

Get started with the AppFolio Property Manager API by authenticating with your client credentials and making your first API calls. This skill walks through connecting to the REST API, fetching a property listing, retrieving tenant details, and creating a basic work order — the essential operations for any AppFolio integration.

## Prerequisites

- AppFolio Stack Partner account with API access
- `APPFOLIO_CLIENT_ID` and `APPFOLIO_CLIENT_SECRET` environment variables set
- Node.js 18+ and TypeScript

## Instructions

### Step 1: Configure the Client

```typescript
const APPFOLIO_BASE = process.env.APPFOLIO_BASE_URL || "https://yourcompany.appfolio.com/api/v1";

async function appfolioFetch(path: string) {
  const credentials = Buffer.from(
    `${process.env.APPFOLIO_CLIENT_ID}:${process.env.APPFOLIO_CLIENT_SECRET}`
  ).toString("base64");
  const res = await fetch(`${APPFOLIO_BASE}${path}`, {
    headers: { Authorization: `Basic ${credentials}`, Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`AppFolio ${res.status}: ${await res.text()}`);
  return res.json();
}
```

### Step 2: List Properties

```typescript
const properties = await appfolioFetch("/properties?page_size=10");
console.log(`Found ${properties.length} properties`);
properties.forEach((p: any) => console.log(`  ${p.id}: ${p.address_line1}, ${p.city}`));
```

### Step 3: Get Tenant Details

```typescript
const tenants = await appfolioFetch(`/tenants?property_id=${properties[0].id}`);
tenants.forEach((t: any) => console.log(`  ${t.name} — Unit ${t.unit_number}`));
```

### Step 4: Create a Work Order

```typescript
const workOrder = await fetch(`${APPFOLIO_BASE}/work_orders`, {
  method: "POST",
  headers: {
    Authorization: `Basic ${Buffer.from(`${process.env.APPFOLIO_CLIENT_ID}:${process.env.APPFOLIO_CLIENT_SECRET}`).toString("base64")}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    property_id: properties[0].id,
    description: "Leaky faucet in kitchen",
    priority: "normal",
  }),
});
console.log("Work order created:", (await workOrder.json()).id);
```

## Output

A successful run produces authenticated API responses: a list of properties with addresses, tenant details for the first property, and a new work order ID confirming write access.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid client_id or secret | Verify credentials in environment variables |
| `403 Forbidden` | API scope not granted | Check Stack Partner permissions for the endpoint |
| `404 Not Found` | Wrong base URL or endpoint | Confirm your company subdomain and API version |
| `422 Unprocessable` | Missing required fields | Validate property_id and required body params |
| `429 Too Many Requests` | Rate limit exceeded | Add backoff delay, batch requests |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-core-workflow-a` for full property and tenant management workflows.
