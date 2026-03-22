---
name: flexport-core-workflow-b
description: |
  Execute Flexport secondary workflow: commercial invoices, products catalog, and freight invoices.
  Use when managing commercial invoices for customs, maintaining product catalogs,
  or handling freight billing through the Flexport API.
  Trigger: "flexport invoice", "flexport products", "flexport customs documents".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Core Workflow B: Invoices & Products

## Overview

Manage Flexport commercial invoices for customs clearance, maintain the product catalog for landed cost calculations, and handle freight billing. These APIs complement the booking/shipment workflow in `flexport-core-workflow-a`.

## Prerequisites

- Completed `flexport-install-auth` setup
- Existing shipments or bookings (from workflow A)
- Product SKUs defined in your system

## Instructions

### Step 1: Manage Product Catalog

```typescript
const BASE = 'https://api.flexport.com';
const headers = {
  'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
  'Flexport-Version': '2',
  'Content-Type': 'application/json',
};

// POST /products — add products to the Flexport Product Library
const product = await fetch(`${BASE}/products`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    name: 'Industrial Widget Type A',
    sku: 'WIDGET-A',
    hs_code: '8479.89',              // Harmonized System code for customs
    country_of_origin: 'CN',
    unit_cost: { amount: 12.50, currency: 'USD' },
    weight: { value: 2.5, unit: 'kg' },
    dimensions: { length: 30, width: 20, height: 15, unit: 'cm' },
  }),
}).then(r => r.json());

console.log(`Product: ${product.data.id} | SKU: ${product.data.sku}`);
```

### Step 2: Create Commercial Invoices

```typescript
// POST /commercial_invoices — required for customs clearance
const invoice = await fetch(`${BASE}/commercial_invoices`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    shipment_id: 'shp_abc123',
    invoice_number: 'CI-2025-001',
    seller: { name: 'Shanghai Supplier Co.' },
    buyer: { name: 'Acme Corp' },
    line_items: [
      {
        product_id: product.data.id,
        quantity: 500,
        unit_price: { amount: 12.50, currency: 'USD' },
        total_price: { amount: 6250.00, currency: 'USD' },
      },
    ],
    total_value: { amount: 6250.00, currency: 'USD' },
    currency: 'USD',
    incoterm: 'FOB',
  }),
}).then(r => r.json());

console.log(`Invoice: ${invoice.data.id} | Total: $${invoice.data.total_value.amount}`);
```

### Step 3: Retrieve Freight Invoices

```typescript
// GET /freight_invoices — Flexport billing for freight services
const freightInvoices = await fetch(
  `${BASE}/freight_invoices?status=outstanding&per=10`, { headers }
).then(r => r.json());

freightInvoices.data.records.forEach((inv: any) => {
  console.log(`${inv.invoice_number} | ${inv.status} | $${inv.total.amount}`);
  inv.line_items?.forEach((li: any) => {
    console.log(`  ${li.description}: $${li.amount.amount}`);
  });
});
```

### Step 4: Search Products by SKU

```typescript
// GET /products — search and filter product catalog
const products = await fetch(
  `${BASE}/products?sku=WIDGET&per=25`, { headers }
).then(r => r.json());

products.data.records.forEach((p: any) => {
  console.log(`${p.sku} | ${p.name} | HS: ${p.hs_code} | Origin: ${p.country_of_origin}`);
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422 invalid HS code` | Malformed Harmonized System code | Use 6-10 digit HS codes (e.g., `8479.89`) |
| `404 shipment not found` | Wrong shipment ID on invoice | Verify shipment exists first |
| `400 missing line items` | Invoice has no products | Add at least one line item |
| `409 duplicate invoice` | Invoice number reused | Use unique invoice numbers per shipment |

## Examples

### Update Product HS Code

```typescript
await fetch(`${BASE}/products/${productId}`, {
  method: 'PATCH',
  headers,
  body: JSON.stringify({ hs_code: '8479.89.9599' }),  // More specific code
});
```

### Bulk Product Import

```typescript
const products = csvData.map(row => ({
  name: row.name, sku: row.sku, hs_code: row.hsCode,
  country_of_origin: row.origin,
  unit_cost: { amount: parseFloat(row.cost), currency: 'USD' },
}));

for (const product of products) {
  await fetch(`${BASE}/products`, { method: 'POST', headers, body: JSON.stringify(product) });
}
```

## Resources

- [Products API Tutorial](https://developers.flexport.com/tutorials/products-api-tutorial/)
- [Commercial Invoices Tutorial](https://developers.flexport.com/tutorials/commercial-invoices-api-tutorial/)
- [Freight Invoices Tutorial](https://developers.flexport.com/tutorials/freight-invoices-api-tutorial/)

## Next Steps

For common errors, see `flexport-common-errors`.
