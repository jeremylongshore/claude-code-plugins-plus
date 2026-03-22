---
name: salesloft-reference-architecture
description: |
  Production architecture for SalesLoft API integrations with service layer,
  webhook processing, and CRM sync patterns.
  Use when designing new SalesLoft integrations or reviewing project structure.
  Trigger: "salesloft architecture", "salesloft project structure", "salesloft design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Reference Architecture

## Overview

Production architecture for SalesLoft API integrations: typed API client, service layer with caching, webhook processor, and background sync. Designed around SalesLoft's REST API v2 with cost-based rate limiting.

## Project Structure

```
salesloft-integration/
├── src/
│   ├── salesloft/
│   │   ├── client.ts           # Axios wrapper with rate-limit handling
│   │   ├── types.ts            # Person, Cadence, Activity types
│   │   ├── paginator.ts        # AsyncGenerator pagination
│   │   └── errors.ts           # SalesloftApiError class
│   ├── services/
│   │   ├── people-sync.ts      # Bidirectional people sync
│   │   ├── cadence-manager.ts  # Cadence CRUD + enrollment
│   │   └── activity-tracker.ts # Email/call activity aggregation
│   ├── webhooks/
│   │   ├── handler.ts          # Signature verification + routing
│   │   └── processors/        # Per-event-type processors
│   ├── jobs/
│   │   ├── incremental-sync.ts # Cron: sync changed records
│   │   └── engagement-report.ts# Cron: aggregate daily metrics
│   └── api/
│       ├── health.ts           # /health endpoint
│       └── webhooks.ts         # /webhooks/salesloft endpoint
├── config/
│   ├── default.json
│   ├── production.json
│   └── test.json
└── tests/
    ├── unit/
    └── integration/
```

## Architecture Diagram

```
┌─────────────────────────────────┐
│           API Layer             │
│  /health  /webhooks/salesloft   │
├─────────────────────────────────┤
│         Service Layer           │
│  PeopleSync  CadenceManager    │
│  ActivityTracker               │
├─────────────────────────────────┤
│       SalesLoft Client          │
│  Typed API  Pagination  Retry  │
├─────────────────────────────────┤
│       Infrastructure            │
│  Redis Cache  BullMQ Jobs      │
│  PostgreSQL  Prometheus        │
└─────────────────────────────────┘
         │              ▲
         ▼              │
┌─────────────────────────────────┐
│     SalesLoft REST API v2       │
│  /people  /cadences  /webhooks  │
│  Rate: 600 cost/min             │
└─────────────────────────────────┘
```

## Key Components

### Typed API Models

```typescript
// src/salesloft/types.ts
export interface SalesloftPerson {
  id: number;
  display_name: string;
  email_address: string;
  first_name: string;
  last_name: string;
  title: string | null;
  company_name: string | null;
  phone: string | null;
  city: string | null;
  state: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface SalesloftCadence {
  id: number;
  name: string;
  current_state: 'draft' | 'active' | 'paused' | 'archived';
  team_cadence: boolean;
  counts: { people_count: number };
}

export interface SalesloftActivity {
  id: number;
  action_type: 'email' | 'phone' | 'other' | 'integration';
  person_id: number;
  cadence_id: number | null;
  created_at: string;
}
```

### Service Layer Pattern

```typescript
// src/services/people-sync.ts
export class PeopleSyncService {
  constructor(
    private salesloft: SalesloftClient,
    private db: Database,
    private cache: LRUCache<string, any>,
  ) {}

  async syncIncremental(): Promise<{ created: number; updated: number }> {
    const lastSync = await this.db.getLastSyncTime('people');
    const stats = { created: 0, updated: 0 };

    for await (const person of this.salesloft.paginate<SalesloftPerson>(
      '/people.json', { updated_at: { gt: lastSync } }
    )) {
      const existing = await this.db.findPersonBySlId(person.id);
      if (existing) {
        await this.db.updatePerson(person);
        stats.updated++;
      } else {
        await this.db.createPerson(person);
        stats.created++;
      }
      this.cache.delete(`person:${person.email_address}`);
    }

    await this.db.setLastSyncTime('people', new Date().toISOString());
    return stats;
  }
}
```

### Background Job

```typescript
// src/jobs/incremental-sync.ts
import { CronJob } from 'cron';

new CronJob('*/5 * * * *', async () => { // Every 5 minutes
  const service = new PeopleSyncService(salesloft, db, cache);
  const stats = await service.syncIncremental();
  console.log(`Sync: +${stats.created} created, ~${stats.updated} updated`);
}).start();
```

## Error Handling

| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| API Client | 429 rate limit | Automatic retry with `Retry-After` |
| Webhook Handler | Invalid signature | Reject 401, log for investigation |
| Sync Job | Partial failure | Resume from last successful `updated_at` |
| Cache | Redis unavailable | Fall through to API (graceful degradation) |

## Resources

- [SalesLoft API Reference](https://api.salesloft.com/swagger/index.html)
- [SalesLoft Developer Portal](https://developers.salesloft.com/)

## Next Steps

See individual skill docs for deep-dives on each component.
