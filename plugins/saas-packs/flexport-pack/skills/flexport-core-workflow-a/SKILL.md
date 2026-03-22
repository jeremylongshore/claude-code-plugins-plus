---
name: flexport-core-workflow-a
description: |
  Execute Flexport primary workflow: shipment booking and purchase order management.
  Use when creating bookings, managing purchase orders, tracking freight,
  or building the core shipment lifecycle integration.
  Trigger: "flexport booking", "flexport purchase order", "create flexport shipment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Core Workflow A: Bookings & Purchase Orders

## Overview

The primary Flexport integration path: create purchase orders, book shipments, and track cargo through the supply chain. The API v2 uses RESTful endpoints at `https://api.flexport.com` with JSON payloads.

## Prerequisites

- Completed `flexport-install-auth` setup
- Understanding of Flexport freight types (ocean FCL/LCL, air, trucking)
- Valid shipper/consignee addresses configured in Flexport Portal

## Instructions

### Step 1: Create a Purchase Order

```typescript
const BASE = 'https://api.flexport.com';
const headers = {
  'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
  'Flexport-Version': '2',
  'Content-Type': 'application/json',
};

// POST /purchase_orders — create a PO to track inbound goods
const po = await fetch(`${BASE}/purchase_orders`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    name: 'PO-2025-001',
    status: 'open',
    buyer: { name: 'Acme Corp', address: { country: 'US' } },
    seller: { name: 'Shanghai Supplier', address: { country: 'CN' } },
    line_items: [
      { sku: 'WIDGET-A', quantity: 500, unit_of_measure: 'pieces' },
      { sku: 'WIDGET-B', quantity: 200, unit_of_measure: 'pieces' },
    ],
    cargo_ready_date: '2025-04-15',
    must_arrive_by: '2025-05-20',
  }),
}).then(r => r.json());

console.log(`PO created: ${po.data.id}`);
```

### Step 2: Create a Booking

```typescript
// POST /bookings — book freight against a purchase order
const booking = await fetch(`${BASE}/bookings`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    freight_type: 'ocean',          // ocean, air, trucking
    incoterm: 'FOB',                // FOB, CIF, EXW, DDP, etc.
    origin_port: { code: 'CNSHA' }, // Shanghai
    destination_port: { code: 'USLAX' }, // Los Angeles
    cargo_ready_date: '2025-04-15',
    purchase_order_ids: [po.data.id],
    wants_freight_management: true,
    wants_customs_service: true,
  }),
}).then(r => r.json());

console.log(`Booking: ${booking.data.id} | Status: ${booking.data.status}`);
```

### Step 3: Track Shipment Milestones

```typescript
// GET /shipments/:id — once booking is confirmed, a shipment is created
// Milestones include: cargo_ready, departed, arrived, customs_cleared, delivered
const shipment = await fetch(
  `${BASE}/shipments/${booking.data.shipment_id}`, { headers }
).then(r => r.json());

console.log(`Shipment ${shipment.data.id}:`);
console.log(`  Status: ${shipment.data.status}`);
console.log(`  ETD: ${shipment.data.estimated_departure_date}`);
console.log(`  ETA: ${shipment.data.estimated_arrival_date}`);
console.log(`  Legs: ${shipment.data.legs?.length ?? 0}`);
```

### Step 4: Retrieve Documents

```typescript
// GET /shipments/:id/documents — commercial invoices, bills of lading, etc.
const docs = await fetch(
  `${BASE}/shipments/${shipment.data.id}/documents`, { headers }
).then(r => r.json());

docs.data.records.forEach((doc: any) => {
  console.log(`${doc.document_type}: ${doc.file_name} (${doc.url})`);
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422 invalid port code` | Unrecognized UN/LOCODE | Use standard codes like CNSHA, USLAX |
| `400 missing required field` | Incomplete booking | Check `freight_type`, `origin_port`, `destination_port` |
| `409 duplicate PO` | PO name already exists | Use unique `name` field or append timestamp |
| `404 shipment not found` | Booking not yet confirmed | Wait for booking confirmation webhook |

## Examples

### List All Purchase Orders with Filters

```typescript
const pos = await fetch(
  `${BASE}/purchase_orders?status=open&per=25&page=1`, { headers }
).then(r => r.json());

pos.data.records.forEach((po: any) => {
  console.log(`${po.name} | ${po.status} | Ready: ${po.cargo_ready_date}`);
});
```

### Update PO Line Items

```typescript
await fetch(`${BASE}/purchase_orders/${poId}`, {
  method: 'PATCH',
  headers,
  body: JSON.stringify({
    line_items: [{ sku: 'WIDGET-A', quantity: 750 }],  // Updated quantity
  }),
});
```

## Resources

- [Booking API Tutorial](https://developers.flexport.com/tutorials/booking/)
- [Purchase Order API Tutorial](https://developers.flexport.com/tutorials/purchase-order-api-tutorial/)
- [Shipment API Tutorial](https://developers.flexport.com/tutorials/shipment-api-tutorial/)
- [API Reference](https://apidocs.flexport.com/)

## Next Steps

For customs and invoicing workflow, see `flexport-core-workflow-b`.
