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

Flexport logistics data encompasses shipment records, bills of lading, customs declarations, commercial invoices, tracking events, and trade compliance documents. This data crosses international borders and regulatory jurisdictions, requiring strict handling for PII (shipper/consignee contacts), controlled export data (HS codes, ITAR items), and financial records (invoices, duty payments). All integrations must enforce GDPR/CCPA compliance, customs data retention mandates, and C-TPAT supply chain security standards.

## Data Classification

| Data Type | Sensitivity | Retention | Encryption |
|-----------|-------------|-----------|------------|
| Shipment records | Medium | 1 year post-delivery | AES-256 at rest |
| Customs declarations | High (trade compliance) | 5 years (CBP requirement) | AES-256 + TLS |
| Commercial invoices | High (financial) | 7 years (tax/audit) | AES-256 at rest |
| Contact PII (shipper/consignee) | High | Until deletion request | Field-level encryption |
| Tracking events | Low | 90 days | TLS in transit |

## Data Import

```typescript
interface FlexportShipment {
  id: string; ref: string; status: string;
  shipper: { name: string; email: string; address: string };
  consignee: { name: string; email: string; address: string };
  hsCode: string; incoterm: string; cargoReadyDate: string;
}

async function importShipments(cursor?: string): Promise<FlexportShipment[]> {
  const allShipments: FlexportShipment[] = [];
  let nextCursor = cursor;
  do {
    const res = await fetch(`https://api.flexport.com/v2/shipments?page[after]=${nextCursor || ''}`, {
      headers: { Authorization: `Bearer ${process.env.FLEXPORT_API_TOKEN}` },
    });
    const data = await res.json();
    for (const s of data.data) {
      if (!s.id || !s.attributes.ref) throw new Error(`Invalid shipment: missing required fields`);
      allShipments.push(s.attributes);
    }
    nextCursor = data.links?.next ? new URL(data.links.next).searchParams.get('page[after]') : null;
  } while (nextCursor);
  return allShipments;
}
```

## Data Export

```typescript
async function exportShipmentsCSV(shipments: FlexportShipment[], dest: string) {
  const REDACT_FIELDS = ['email', 'phone', 'street_address', 'tax_id'];
  const sanitized = shipments.map(s => {
    const copy = JSON.parse(JSON.stringify(s));
    for (const field of REDACT_FIELDS) {
      if (copy.shipper?.[field]) copy.shipper[field] = '[REDACTED]';
      if (copy.consignee?.[field]) copy.consignee[field] = '[REDACTED]';
    }
    return copy;
  });
  // Validate no restricted HS codes in export payload
  const restricted = sanitized.filter(s => s.hsCode?.startsWith('9A'));
  if (restricted.length > 0) throw new Error(`Export blocked: ${restricted.length} ITAR-restricted items`);
  const csv = [Object.keys(sanitized[0]).join(','), ...sanitized.map(r => Object.values(r).join(','))].join('\n');
  await writeFile(dest, csv, 'utf-8');
}
```

## Data Validation

```typescript
function validateShipment(s: FlexportShipment): string[] {
  const errors: string[] = [];
  if (!s.id) errors.push('Missing shipment ID');
  if (!s.ref || s.ref.length > 50) errors.push('Invalid shipment reference');
  if (!s.hsCode || !/^\d{4,10}$/.test(s.hsCode)) errors.push(`Invalid HS code: ${s.hsCode}`);
  if (!['EXW','FOB','CIF','DDP','DAP'].includes(s.incoterm)) errors.push(`Unknown incoterm: ${s.incoterm}`);
  if (!s.shipper?.name || !s.consignee?.name) errors.push('Missing shipper or consignee name');
  if (s.cargoReadyDate && isNaN(Date.parse(s.cargoReadyDate))) errors.push('Invalid cargo ready date');
  return errors;
}
```

## Compliance

- [ ] PII fields (shipper/consignee contacts) encrypted at field level, redacted in logs
- [ ] Customs declarations retained 5 years per CBP/EU customs code requirements
- [ ] Commercial invoices retained 7 years for tax audit compliance
- [ ] GDPR right-to-erasure: redact PII but preserve shipment skeleton for business continuity
- [ ] CCPA opt-out signals honored for California-origin shipments
- [ ] ITAR/EAR restricted HS codes flagged and blocked from unauthorized export
- [ ] C-TPAT supply chain security: validate trading partner identities before data sharing
- [ ] Audit trail for all data access, export, and deletion operations

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| API 429 rate limit | Too many shipment fetches | Implement exponential backoff with jitter |
| Invalid HS code rejected | Incorrect tariff classification | Validate against WCO HS nomenclature before submission |
| GDPR deletion timeout | Large contact footprint across shipments | Batch updates in transactions of 100 records |
| Customs data missing | Incomplete booking submission | Require mandatory fields at import validation step |
| Export blocked by ITAR flag | Restricted HS code in payload | Route to trade compliance officer for manual review |

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [CBP Data Retention Requirements](https://www.cbp.gov/trade)

## Next Steps

See `flexport-security-basics`.
