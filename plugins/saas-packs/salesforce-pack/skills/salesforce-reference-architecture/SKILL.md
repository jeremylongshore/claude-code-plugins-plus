---
name: salesforce-reference-architecture
description: |
  Implement Salesforce integration reference architecture with jsforce, SFDX, and event-driven patterns.
  Use when designing new Salesforce integrations, reviewing project structure,
  or establishing architecture standards for Salesforce-connected applications.
  Trigger with phrases like "salesforce architecture", "salesforce project structure",
  "salesforce integration design", "how to organize salesforce code", "salesforce layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Reference Architecture

## Overview
Production-ready architecture patterns for Salesforce integrations, covering Node.js integration apps, SFDX metadata projects, and event-driven sync architectures.

## Prerequisites
- Understanding of layered architecture
- jsforce and Salesforce CLI experience
- TypeScript project setup
- Decision on sync model (polling vs event-driven)

## Project Structure

### Node.js Integration App
```
my-sf-integration/
├── src/
│   ├── salesforce/
│   │   ├── connection.ts       # Singleton jsforce connection with auto-refresh
│   │   ├── types.ts            # Typed sObject interfaces (Account, Contact, etc.)
│   │   ├── queries.ts          # SOQL query builders
│   │   ├── mutations.ts        # Create/update/delete operations
│   │   └── events.ts           # CDC and Platform Event subscribers
│   ├── services/
│   │   ├── account-sync.ts     # Business logic for Account sync
│   │   ├── contact-sync.ts     # Business logic for Contact sync
│   │   └── opportunity-sync.ts # Pipeline/forecast sync
│   ├── api/
│   │   ├── routes.ts           # Express/Fastify routes
│   │   └── health.ts           # Health check with SF connectivity
│   ├── jobs/
│   │   ├── full-sync.ts        # Scheduled full data sync
│   │   └── incremental-sync.ts # CDC-based incremental sync
│   └── index.ts
├── tests/
│   ├── unit/                   # Mocked jsforce tests
│   └── integration/            # Live sandbox tests
├── config/
│   ├── default.json            # Shared config
│   └── production.json         # Production overrides
└── package.json
```

### SFDX Metadata Project (Apex, LWC, Triggers)
```
my-sf-app/
├── force-app/main/default/
│   ├── classes/                # Apex classes
│   │   ├── AccountTriggerHandler.cls
│   │   ├── ContactService.cls
│   │   └── IntegrationService.cls
│   ├── triggers/               # Apex triggers
│   │   └── AccountTrigger.trigger
│   ├── lwc/                    # Lightning Web Components
│   │   └── accountList/
│   ├── objects/                # Custom object metadata
│   │   └── Integration_Log__c/
│   ├── permissionsets/
│   │   └── Integration_API_Access.permissionset-meta.xml
│   └── flows/                  # Screen/record-triggered flows
├── scripts/apex/               # Anonymous Apex scripts
├── config/
│   └── project-scratch-def.json
└── sfdx-project.json
```

## Integration Patterns

### Pattern A: Polling-Based Sync
```
┌─────────────┐     SOQL Query      ┌─────────────┐
│   Your App  │ ──────────────────▶  │  Salesforce  │
│  (cron job) │  SELECT ... WHERE    │     Org      │
│             │ ◀──────────────────  │              │
│             │     JSON Records     │              │
└─────────────┘                      └─────────────┘

Pros: Simple, works with any edition
Cons: Latency (polling interval), wastes API calls on empty polls
Use: Small data volumes, non-real-time requirements
```

### Pattern B: Event-Driven Sync (Recommended)
```
┌─────────────┐                      ┌─────────────┐
│   Your App  │ ◀─── CDC Events ───  │  Salesforce  │
│  (listener) │   /data/Change*      │     Org      │
│             │                      │              │
│             │ ── REST API ───────▶ │              │
│             │   Write-back         │              │
└─────────────┘                      └─────────────┘

Pros: Real-time, no wasted API calls, scalable
Cons: Requires Enterprise+, CDC setup, event replay handling
Use: Real-time sync, high-volume changes
```

### Pattern C: Bi-Directional Sync (Heroku Connect)
```
┌─────────────┐     SQL Queries      ┌─────────────┐
│   Your App  │ ──────────────────▶  │   Postgres   │
│             │ ◀──────────────────  │ (Heroku DB)  │
└─────────────┘                      └──────┬───────┘
                                            │
                                     Heroku Connect
                                     (automatic sync)
                                            │
                                     ┌──────▼───────┐
                                     │  Salesforce  │
                                     │     Org      │
                                     └─────────────┘

Pros: Zero API calls from your app, automatic bi-directional sync
Cons: Heroku cost, 10-min sync delay, limited to standard objects
Use: Heavy read/write, SQL-friendly teams
```

## Key Architecture Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Connection management | Singleton with auto-refresh | 1 connection per process, handles token expiry |
| SOQL queries | Typed query builders | Prevents field name typos, enables refactoring |
| Bulk operations | Bulk API 2.0 for 10K+, Collections for <200 | Optimizes API call consumption |
| Error handling | Map SF error codes to domain errors | `INVALID_FIELD` → `SchemaError`, etc. |
| Real-time sync | CDC over polling | No wasted API calls, sub-second latency |
| Data mapping | Explicit field mapping layer | Decouples app schema from SF schema |
| Testing | Mock jsforce in unit tests | Fast tests without org dependency |

## Data Mapping Layer

```typescript
// src/salesforce/mappers.ts
// Decouple your app's domain model from Salesforce field names

interface AppContact {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  companyId: string;
}

function fromSalesforceContact(sf: any): AppContact {
  return {
    id: sf.Id,
    firstName: sf.FirstName || '',
    lastName: sf.LastName,
    email: sf.Email || '',
    companyId: sf.AccountId || '',
  };
}

function toSalesforceContact(app: Partial<AppContact>): Record<string, any> {
  const sf: Record<string, any> = {};
  if (app.firstName !== undefined) sf.FirstName = app.firstName;
  if (app.lastName !== undefined) sf.LastName = app.lastName;
  if (app.email !== undefined) sf.Email = app.email;
  if (app.companyId !== undefined) sf.AccountId = app.companyId;
  return sf;
}
```

## Output
- Node.js integration project with layered architecture
- SFDX metadata project structure
- Integration pattern selected (polling, event-driven, or Heroku Connect)
- Data mapping layer decoupling app from SF schema

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Tight coupling to SF schema | Direct field access | Add mapping layer |
| N+1 queries | Loop with individual queries | Use relationship SOQL or Collections |
| Stale cache | TTL too long | Use CDC events to invalidate |
| Event loss | No replay tracking | Persist last replayId |

## Resources
- [Salesforce Integration Patterns](https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/)
- [Heroku Connect](https://devcenter.heroku.com/articles/heroku-connect)
- [Change Data Capture](https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/)
- [jsforce Documentation](https://jsforce.github.io/document/)

## Next Steps
For multi-environment setup, see `salesforce-multi-env-setup`.
