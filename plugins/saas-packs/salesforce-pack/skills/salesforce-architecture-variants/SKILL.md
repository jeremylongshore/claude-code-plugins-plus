---
name: salesforce-architecture-variants
description: |
  Choose and implement Salesforce integration architecture patterns for different scales.
  Use when designing new Salesforce integrations, choosing between polling/event-driven/Heroku Connect,
  or planning migration paths for Salesforce applications.
  Trigger with phrases like "salesforce architecture", "salesforce integration pattern",
  "how to structure salesforce integration", "salesforce event-driven", "salesforce Heroku Connect".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Architecture Variants

## Overview
Three validated architecture blueprints for Salesforce integrations: Direct API (simple), Event-Driven (scalable), and Middleware/iPaaS (enterprise). Each pattern addresses different scale, latency, and complexity requirements.

## Prerequisites
- Understanding of your data volume and sync frequency requirements
- Decision on unidirectional vs bidirectional data flow
- Knowledge of Salesforce edition (affects available features like CDC)

## Variant A: Direct API Integration (Simple)

**Best for:** MVPs, < 50K records/day, single-direction sync

```
┌─────────────┐     jsforce       ┌─────────────┐
│   Your App  │ ──── REST API ──▶ │  Salesforce  │
│ (Node.js)   │ ◀── SOQL/SOSL ── │     Org      │
└─────────────┘                   └─────────────┘

Data flow:
- App queries SF via SOQL (polling or on-demand)
- App writes to SF via sObject CRUD
- Scheduled cron for periodic sync
```

### Key Characteristics
- Single jsforce connection per process
- Polling-based reads (cron schedule)
- Direct REST writes
- In-memory or Redis caching for describe/metadata
- Suitable for: internal tools, admin dashboards, simple data sync

### Code Pattern
```typescript
// Cron-based sync — runs every 15 minutes
import cron from 'node-cron';

cron.schedule('*/15 * * * *', async () => {
  const conn = await getConnection();

  // Fetch recently modified accounts
  const accounts = await conn.query(`
    SELECT Id, Name, Industry, AnnualRevenue
    FROM Account
    WHERE LastModifiedDate >= ${fifteenMinutesAgo}
  `);

  // Sync to local database
  for (const account of accounts.records) {
    await localDb.upsert('accounts', mapFromSalesforce(account));
  }
});
```

---

## Variant B: Event-Driven Integration (Scalable)

**Best for:** Real-time sync, 50K-5M records/day, bidirectional flow

```
┌─────────────┐                      ┌─────────────┐
│   Your App  │ ◀─── CDC Events ───  │  Salesforce  │
│  (listener) │   Change Data Capture │     Org      │
│             │                      │              │
│             │ ── Bulk API 2.0 ──▶  │              │
│             │    (write-back)      │              │
└──────┬──────┘                      └─────────────┘
       │
  ┌────▼────┐
  │  Queue  │  (Redis/SQS/Pub-Sub)
  │  (async │
  │  writes)│
  └─────────┘
```

### Key Characteristics
- CDC for real-time change notifications (no polling waste)
- Bulk API 2.0 for high-volume writes
- Queue-based async processing for write-back
- ReplayId tracking for event resumption
- Suitable for: CRM sync, data warehouse ETL, real-time dashboards

### Code Pattern
```typescript
// Event-driven — near-real-time sync
import { getConnection } from './salesforce/connection';

const conn = await getConnection();

// Subscribe to Account changes via CDC
conn.streaming.topic('/data/AccountChangeEvent').subscribe(async (event) => {
  const { changeType, recordIds, changedFields } = event.payload.ChangeEventHeader;

  switch (changeType) {
    case 'CREATE':
      await localDb.insert('accounts', mapFromSalesforce(event.payload));
      break;
    case 'UPDATE':
      await localDb.update('accounts', recordIds[0], mapChangedFields(event.payload, changedFields));
      break;
    case 'DELETE':
      await localDb.delete('accounts', recordIds[0]);
      break;
  }
});

// Write-back via queue (async, decoupled)
queue.process('sync-to-salesforce', async (job) => {
  const conn = await getConnection();
  await conn.sobject(job.data.objectType).upsert(
    job.data.records,
    'External_ID__c'
  );
});
```

### Required Salesforce Features
- Change Data Capture (Enterprise Edition+)
- Platform Events (all editions)
- Bulk API 2.0 (all editions with API access)

---

## Variant C: Middleware/iPaaS Integration (Enterprise)

**Best for:** Multi-system integration, 5M+ records/day, complex transformations

```
┌─────────────┐                ┌─────────────┐               ┌─────────────┐
│   Your App  │ ── API ──────▶ │  Middleware  │ ── REST ────▶ │  Salesforce  │
│             │                │ (MuleSoft/   │               │     Org      │
│             │                │  Workato/    │ ◀─ CDC ──────│              │
│             │ ◀─ Webhooks ── │  Zapier)     │               │              │
└─────────────┘                └──────┬───────┘               └─────────────┘
                                      │
                                ┌─────▼──────┐
                                │  Other      │
                                │  Systems    │
                                │ (ERP, DW,   │
                                │  Marketing) │
                                └─────────────┘
```

### Key Characteristics
- Middleware handles transformation, routing, error handling
- Pre-built Salesforce connectors (no custom code for basic sync)
- Visual flow builders for business users
- Enterprise monitoring and audit trails
- Suitable for: multi-system integration, complex business rules, compliance-heavy

### iPaaS Options
| Platform | Salesforce Integration | Best For |
|----------|----------------------|----------|
| MuleSoft | Native (Salesforce owns it) | Enterprise, complex flows |
| Heroku Connect | Bi-directional auto-sync | Simple sync to Postgres |
| Workato | Pre-built recipes | Business user automation |
| Zapier | Trigger-based | Simple 1:1 integrations |
| Dell Boomi | Enterprise iPaaS | Legacy system integration |

---

## Decision Matrix

| Factor | Direct API (A) | Event-Driven (B) | Middleware (C) |
|--------|---------------|-------------------|----------------|
| Records/day | < 50K | 50K-5M | 5M+ |
| Latency | Minutes (polling) | Seconds (CDC) | Depends on config |
| Direction | Usually one-way | Bidirectional | Multi-directional |
| API call efficiency | Medium | High (no polling) | High (batched) |
| Complexity | Low | Medium | Low (config-driven) |
| Cost | jsforce only | jsforce + queue infra | iPaaS license ($$$) |
| SF Edition required | Any with API | Enterprise+ (CDC) | Any |
| Team skills | Node.js developers | Node.js + streaming | Business analysts OK |

## Migration Path

```
Variant A (Direct API)
    │
    │  Growing data volume / need real-time sync
    ▼
Variant B (Event-Driven)
    │
    │  Multiple systems / compliance / no-code needed
    ▼
Variant C (Middleware/iPaaS)
```

## Output
- Architecture variant selected based on requirements
- Integration pattern implemented
- Data flow documented
- Scaling path planned

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Polling misses changes | Interval too long | Switch to CDC (Variant B) |
| CDC events lost | No replay tracking | Persist last replayId |
| API limits exhausted | Polling too frequently | Batch with Collections/Bulk API |
| Middleware cost too high | Over-engineered | Start with Variant A or B |

## Resources
- [Salesforce Integration Patterns](https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/)
- [Change Data Capture](https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/)
- [MuleSoft Salesforce Connector](https://docs.mulesoft.com/salesforce-connector/latest/)
- [Heroku Connect](https://devcenter.heroku.com/articles/heroku-connect)

## Next Steps
For common anti-patterns, see `salesforce-known-pitfalls`.
