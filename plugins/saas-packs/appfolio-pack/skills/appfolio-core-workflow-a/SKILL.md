---
name: appfolio-core-workflow-a
description: 'Build property management dashboard with AppFolio API data.

  Trigger: "appfolio property dashboard".

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
# AppFolio — Property & Tenant Management

## Overview

Primary workflow for AppFolio property management integration. Covers the full property
lifecycle: creating and updating property records, managing tenant profiles and lease
agreements, and querying occupancy data. Uses the AppFolio Stack API with OAuth 2.0
client credentials for server-to-server access. All endpoints return JSON and support
pagination via `cursor` parameters for large portfolios.

## Instructions

### Step 1: Authenticate and Initialize Client

```typescript
const token = await fetch('https://api.appfolio.com/oauth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.APPFOLIO_CLIENT_ID!,
    client_secret: process.env.APPFOLIO_CLIENT_SECRET!,
    scope: 'properties tenants leases',
  }),
}).then(r => r.json());
const headers = { Authorization: `Bearer ${token.access_token}`, 'Content-Type': 'application/json' };
```

### Step 2: Create or Update a Property

```typescript
const property = await fetch('https://api.appfolio.com/v1/properties', {
  method: 'POST', headers,
  body: JSON.stringify({
    name: 'Sunrise Apartments',
    address: { street: '100 Main St', city: 'Austin', state: 'TX', zip: '78701' },
    type: 'residential',
    units: [
      { number: '101', bedrooms: 2, bathrooms: 1, rent: 1450 },
      { number: '102', bedrooms: 1, bathrooms: 1, rent: 1100 },
    ],
  }),
}).then(r => r.json());
console.log(`Property created: ${property.id}`);
```

### Step 3: Add a Tenant and Lease

```typescript
const tenant = await fetch('https://api.appfolio.com/v1/tenants', {
  method: 'POST', headers,
  body: JSON.stringify({
    first_name: 'Alex', last_name: 'Rivera',
    email: 'alex.rivera@example.com', phone: '512-555-0199',
  }),
}).then(r => r.json());

await fetch('https://api.appfolio.com/v1/leases', {
  method: 'POST', headers,
  body: JSON.stringify({
    property_id: property.id, unit_number: '101',
    tenant_id: tenant.id, start_date: '2026-05-01', end_date: '2027-04-30',
    monthly_rent: 1450, security_deposit: 1450,
  }),
}).then(r => r.json());
```

### Step 4: Query Occupancy

```typescript
const units = await fetch(
  `https://api.appfolio.com/v1/properties/${property.id}/units?status=vacant`,
  { headers },
).then(r => r.json());
console.log(`Vacant units: ${units.data.length} of ${units.meta.total}`);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Expired or invalid token | Re-authenticate with client credentials |
| `404 Not Found` | Wrong property/tenant ID | Verify resource ID exists before referencing |
| `422 Unprocessable` | Missing required fields | Check `errors[]` array in response body |
| `409 Conflict` | Duplicate lease for unit | Query existing leases before creating |
| `429 Too Many Requests` | Rate limit exceeded | Back off using `Retry-After` header value |

## Output

A successful run creates a property with units, adds a tenant, binds them via a lease,
and reports vacancy counts. Console output confirms each resource ID on creation.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

Continue with `appfolio-core-workflow-b` for maintenance requests and payment tracking.
