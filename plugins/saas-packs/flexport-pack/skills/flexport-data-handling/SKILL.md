---
name: flexport-data-handling
description: |
  Implement data handling for Flexport supply chain data including PII redaction,
  shipment data retention, GDPR compliance, and secure document management.
  Trigger: "flexport data handling", "flexport PII", "flexport GDPR", "flexport data retention".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Data Handling

## Overview

Handle Flexport supply chain data with proper PII redaction, data retention policies, and GDPR/CCPA compliance. Shipping data contains sensitive business information (supplier names, addresses, pricing, trade routes) that requires careful handling.

## Instructions

### Step 1: Identify Sensitive Fields

| Field Category | Examples | PII Level |
|---------------|----------|-----------|
| Contact info | Shipper/consignee names, emails, phones | High |
| Addresses | Origin/destination street addresses | High |
| Financial | Invoice amounts, unit costs, freight charges | Medium |
| Trade | HS codes, country of origin, incoterms | Low |
| Tracking | Shipment IDs, container numbers, BOL numbers | Low |

### Step 2: PII Redaction for Logging

```typescript
const REDACT_FIELDS = new Set([
  'email', 'phone', 'contact_name', 'street_address',
  'tax_id', 'bank_account', 'credit_card',
]);

function redactPII(obj: any, depth = 0): any {
  if (depth > 10 || !obj || typeof obj !== 'object') return obj;
  const result: any = Array.isArray(obj) ? [] : {};
  for (const [key, value] of Object.entries(obj)) {
    if (REDACT_FIELDS.has(key)) {
      result[key] = '***REDACTED***';
    } else if (typeof value === 'object') {
      result[key] = redactPII(value, depth + 1);
    } else {
      result[key] = value;
    }
  }
  return result;
}

// Usage in logging
logger.info({ shipment: redactPII(shipmentData) }, 'Shipment processed');
```

### Step 3: Data Retention Policy

```typescript
// Automated cleanup based on retention policy
const RETENTION = {
  shipments: 365,        // 1 year after delivery
  purchase_orders: 730,  // 2 years (tax/audit requirements)
  invoices: 2555,        // 7 years (financial regulations)
  webhookLogs: 90,       // 90 days
  apiLogs: 30,           // 30 days
};

async function enforceRetention() {
  for (const [table, days] of Object.entries(RETENTION)) {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const deleted = await db.$executeRaw`
      DELETE FROM ${table} WHERE created_at < ${cutoff} AND status = 'delivered'
    `;
    logger.info({ table, deleted, cutoffDate: cutoff }, 'Retention cleanup');
  }
}
```

### Step 4: GDPR Right to Erasure

```typescript
async function handleDeletionRequest(contactEmail: string) {
  // Find all shipments associated with this contact
  const shipments = await db.shipments.findMany({
    where: { OR: [{ shipperEmail: contactEmail }, { consigneeEmail: contactEmail }] },
  });

  for (const shipment of shipments) {
    // Redact PII but keep shipment record for business continuity
    await db.shipments.update({
      where: { id: shipment.id },
      data: {
        shipperName: '[REDACTED]',
        shipperEmail: '[REDACTED]',
        consigneeName: '[REDACTED]',
        consigneeEmail: '[REDACTED]',
        streetAddress: '[REDACTED]',
        redactedAt: new Date(),
      },
    });
  }

  logger.info({ email: '[REDACTED]', count: shipments.length }, 'GDPR deletion processed');
}
```

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [GDPR Right to Erasure](https://gdpr.eu/right-to-be-forgotten/)

## Next Steps

For access control, see `flexport-enterprise-rbac`.
