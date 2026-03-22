---
name: flexport-hello-world
description: |
  Create a minimal working Flexport example — list shipments and track containers.
  Use when starting a new Flexport integration, testing your setup,
  or learning the Flexport REST API v2 patterns.
  Trigger: "flexport hello world", "flexport example", "flexport quick start".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Hello World

## Overview

List shipments and retrieve tracking milestones using the Flexport REST API v2. Flexport has no npm SDK -- you call `https://api.flexport.com` directly with bearer token auth and a `Flexport-Version: 2` header.

## Prerequisites

- `FLEXPORT_API_KEY` environment variable set
- Completed `flexport-install-auth` setup
- Node.js 18+ (uses native `fetch`)

## Instructions

### Step 1: List Your Shipments

```typescript
// src/flexport/hello.ts
const BASE = 'https://api.flexport.com';
const headers = {
  'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
  'Flexport-Version': '2',
  'Content-Type': 'application/json',
};

// List shipments with pagination
const res = await fetch(`${BASE}/shipments?per=5&page=1`, { headers });
const { data } = await res.json();

data.records.forEach((shipment: any) => {
  console.log(`${shipment.id} | ${shipment.status} | ${shipment.freight_type}`);
  console.log(`  Origin: ${shipment.origin_port?.name ?? 'N/A'}`);
  console.log(`  Dest:   ${shipment.destination_port?.name ?? 'N/A'}`);
});
```

### Step 2: Get Shipment Details with Milestones

```typescript
// Retrieve a single shipment with tracking milestones
const shipmentId = data.records[0].id;
const detail = await fetch(`${BASE}/shipments/${shipmentId}`, { headers }).then(r => r.json());

console.log(`\nShipment ${detail.data.id}:`);
console.log(`  Status: ${detail.data.status}`);
console.log(`  Cargo ready: ${detail.data.cargo_ready_date}`);
console.log(`  Containers: ${detail.data.containers?.length ?? 0}`);
```

### Step 3: List Containers on a Shipment

```typescript
// Get container details for ocean freight shipments
const containers = await fetch(
  `${BASE}/shipments/${shipmentId}/containers`, { headers }
).then(r => r.json());

containers.data.records.forEach((c: any) => {
  console.log(`Container ${c.container_number} | ${c.container_type} | ${c.status}`);
});
```

## Output

```
shp_abc123 | in_transit | ocean
  Origin: Shanghai Port
  Dest:   Los Angeles Port

Shipment shp_abc123:
  Status: in_transit
  Cargo ready: 2025-03-01
  Containers: 2

Container MSKU1234567 | 40ft_hc | in_transit
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check `FLEXPORT_API_KEY` env var |
| 404 Not Found | Wrong shipment ID | Verify ID from `/shipments` list |
| 422 Unprocessable | Bad query params | Check `per`/`page` are integers |
| Empty records array | No shipments yet | Create a booking first or use sandbox |

## Examples

### Python Quick Start

```python
import os, requests

BASE = 'https://api.flexport.com'
headers = {
    'Authorization': f'Bearer {os.environ["FLEXPORT_API_KEY"]}',
    'Flexport-Version': '2',
}

shipments = requests.get(f'{BASE}/shipments', headers=headers, params={'per': 5}).json()
for s in shipments['data']['records']:
    print(f"{s['id']} | {s['status']} | {s['freight_type']}")
```

### cURL One-Liner

```bash
curl -s -H "Authorization: Bearer $FLEXPORT_API_KEY" \
     -H "Flexport-Version: 2" \
     https://api.flexport.com/shipments?per=3 | jq '.data.records[] | {id, status, freight_type}'
```

## Resources

- [Shipment API Tutorial](https://developers.flexport.com/tutorials/shipment-api-tutorial/)
- [Flexport API Reference](https://apidocs.flexport.com/)
- [Developer Portal](https://developers.flexport.com/)

## Next Steps

Proceed to `flexport-local-dev-loop` for development workflow setup.
