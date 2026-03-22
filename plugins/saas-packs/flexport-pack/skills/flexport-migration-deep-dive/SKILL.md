---
name: flexport-migration-deep-dive
description: |
  Execute major migration strategies for Flexport including migrating from
  legacy freight forwarders, ERP system integration, and strangler fig patterns.
  Trigger: "flexport migration", "migrate to flexport", "flexport ERP integration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Migration Deep Dive

## Overview

Guide for migrating to Flexport from legacy freight forwarders, manual spreadsheet workflows, or other logistics platforms. Uses a strangler fig pattern to gradually move operations to the Flexport API while maintaining existing systems.

## Migration Scenarios

| From | To | Complexity | Timeline |
|------|----|-----------|----------|
| Spreadsheet/email | Flexport API | Low | 2-4 weeks |
| Legacy freight forwarder API | Flexport API | Medium | 4-8 weeks |
| ERP (SAP, Oracle) | ERP + Flexport | High | 8-16 weeks |
| Multiple forwarders | Flexport consolidated | High | 6-12 weeks |

## Instructions

### Phase 1: Data Migration — Product Catalog

```typescript
// Migrate product catalog from legacy system to Flexport Product Library
async function migrateProducts(legacyProducts: LegacyProduct[]) {
  const results = { success: 0, failed: 0, errors: [] as string[] };

  for (const legacy of legacyProducts) {
    try {
      await fetch('https://api.flexport.com/products', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          name: legacy.description,
          sku: legacy.partNumber,
          hs_code: legacy.tariffCode,
          country_of_origin: legacy.originCountry,
          unit_cost: { amount: legacy.unitCost, currency: legacy.currency },
          weight: { value: legacy.weightKg, unit: 'kg' },
        }),
      });
      results.success++;
    } catch (err) {
      results.failed++;
      results.errors.push(`${legacy.partNumber}: ${err}`);
    }
  }

  console.log(`Products migrated: ${results.success}/${legacyProducts.length}`);
  return results;
}
```

### Phase 2: Strangler Fig — Dual-Write

```typescript
// During migration, write to both systems
class DualWriteShipmentService {
  constructor(
    private legacy: LegacyForwarderClient,
    private flexport: FlexportClient,
    private featureFlags: FeatureFlags,
  ) {}

  async createBooking(params: BookingParams) {
    // Always write to legacy during migration
    const legacyResult = await this.legacy.createBooking(params);

    // Write to Flexport if enabled for this route
    if (this.featureFlags.isEnabled('flexport_booking', { route: params.route })) {
      try {
        const fpResult = await this.flexport.createBooking(params);
        // Compare results for validation
        this.compareResults(legacyResult, fpResult);
      } catch (err) {
        // Log but don't fail — legacy is still primary
        logger.warn({ err, route: params.route }, 'Flexport dual-write failed');
      }
    }

    return legacyResult;  // Legacy is source of truth during migration
  }
}
```

### Phase 3: Cutover — Route by Route

```typescript
// Migrate routes one at a time, validate, then cut over
const MIGRATION_PHASES = [
  { routes: ['CNSHA-USLAX'], startDate: '2025-04-01', description: 'Shanghai-LA (highest volume)' },
  { routes: ['CNSHA-DEHAM', 'CNSHA-NLRTM'], startDate: '2025-05-01', description: 'Asia-Europe' },
  { routes: ['*'], startDate: '2025-06-01', description: 'All remaining routes' },
];

// Validate migration readiness per route
async function validateRoute(route: string): Promise<{
  productsCovered: boolean;
  webhooksWorking: boolean;
  dataParity: boolean;
}> {
  // Check all products on this route exist in Flexport
  const products = await db.products.findMany({ where: { routes: { has: route } } });
  const fpProducts = await flexport('/products?per=100');
  const fpSkus = new Set(fpProducts.data.records.map((p: any) => p.sku));
  const productsCovered = products.every(p => fpSkus.has(p.sku));

  return { productsCovered, webhooksWorking: true, dataParity: true };
}
```

### Phase 4: Decommission Legacy

```typescript
// After all routes migrated and validated
async function decommissionLegacy() {
  // Final data sync — export all historical data
  const allShipments = await legacy.exportAllShipments();
  await archiveToS3(allShipments, 'legacy-forwarder-archive');

  // Disable legacy API keys
  // Remove dual-write code paths
  // Update monitoring to Flexport-only alerts
  logger.info('Legacy forwarder decommissioned');
}
```

## Migration Checklist

- [ ] Product catalog migrated and validated
- [ ] Purchase order history exported
- [ ] Webhook endpoints configured and tested
- [ ] Dual-write enabled for first route
- [ ] Data parity validated between systems
- [ ] Stakeholders notified of cutover schedule
- [ ] Rollback procedure documented and tested
- [ ] Legacy system archived (not deleted)

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)
- [Flexport API Reference](https://apidocs.flexport.com/)
- [Products API Tutorial](https://developers.flexport.com/tutorials/products-api-tutorial/)

## Next Steps

This completes the Flexport skill pack. Start with `flexport-install-auth` for new integrations.
