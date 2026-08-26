---
name: appfolio-hello-world
description: 'Query AppFolio properties, units, and tenants via REST API.

  Trigger: "appfolio hello world".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Hello World

## Overview

Get started with the AppFolio Property Manager API through a verified provider-issued client configuration. This skill walks through safe first reads for a property listing and a tenant count; create or update operations belong only in a separately approved synthetic sandbox workflow.

## Prerequisites

- AppFolio Stack Partner account with API access
- A managed, provider-issued base URL and authentication client confirmed for
  the target portfolio; do not use a guessed hostname or credential scheme
- Node.js 18+ and TypeScript

## Instructions

### Step 1: Configure the Client

```typescript
async function appfolioFetch(path: string) {
  const res = await createVerifiedAppFolioClient().get(path);
  if (res.status < 200 || res.status >= 300) throw new Error(`AppFolio ${res.status}`);
  return res.data;
}
```

### Step 2: List Properties

```typescript
const properties = await appfolioFetch("/properties?page_size=10");
console.log(`Found ${properties.length} properties`);
properties.forEach((p: any) => console.log(`  property ID: ${p.id}`));
```

### Step 3: Get Tenant Details

```typescript
const tenants = await appfolioFetch(`/tenants?property_id=${properties[0].id}`);
console.log(`Retrieved ${tenants.length} tenant records for the approved fixture`);
```

### Step 4: Stop Before Writes

```typescript
// Do not create a work order as a quickstart test. Continue only with the
// synthetic, idempotent workflow in appfolio-core-workflow-b.
```

## Output

A successful run proves the managed client and an approved safe-read endpoint work, returning only property IDs and a tenant-record count in its local output.

## Examples

For a first integration check, configure the verified sandbox client, query one
approved synthetic property page, and confirm its status, property IDs, and
tenant count without recording addresses, names, unit numbers, or credentials.
Do not create a work order merely to test access. If the portfolio contract,
safe-read fixture, or response authorization is not verified, stop the run and
use the credential owner’s staging process before attempting any mutation.

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
