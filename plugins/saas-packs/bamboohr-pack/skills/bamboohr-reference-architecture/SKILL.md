---
name: bamboohr-reference-architecture
description: |
  Implement BambooHR reference architecture for production HR data pipelines.
  Use when designing new BambooHR integrations, building employee sync systems,
  or establishing architecture standards for BambooHR-powered applications.
  Trigger with phrases like "bamboohr architecture", "bamboohr design",
  "bamboohr project structure", "bamboohr system design", "bamboohr pipeline".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, architecture]
compatible-with: claude-code
---

# BambooHR Reference Architecture

## Overview

Production-ready architecture for BambooHR integrations covering the three most common patterns: real-time employee sync, HR data pipeline, and employee lifecycle automation.

## Prerequisites

- Understanding of layered architecture and event-driven design
- BambooHR API knowledge from earlier skills in this pack
- TypeScript project setup with Node.js 18+

## Instructions

### Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Your Application                       │
├──────────────┬───────────────┬────────────────────────────┤
│  API Layer   │  Sync Engine  │  Webhook Handler           │
│  /api/*      │  (Cron/Queue) │  /webhooks/bamboohr        │
├──────────────┴───────────────┴────────────────────────────┤
│                   Service Layer                            │
│  EmployeeService  │  TimeOffService  │  ReportService     │
├───────────────────┴──────────────────┴────────────────────┤
│                BambooHR Client Layer                       │
│  BambooHRClient  │  Cache  │  RetryHandler  │  Metrics    │
├───────────────────┴─────────┴────────────────┴────────────┤
│                   Data Layer                               │
│  PostgreSQL (employees)  │  Redis (cache)  │  S3 (files)  │
└───────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   BambooHR REST API    │
              │ api.bamboohr.com/api/  │
              │   gateway.php/{co}/v1  │
              └────────────────────────┘
```

### Project Structure

```
bamboohr-integration/
├── src/
│   ├── bamboohr/
│   │   ├── client.ts              # HTTP client (from sdk-patterns)
│   │   ├── types.ts               # BambooHR API response types
│   │   ├── retry.ts               # Retry with Retry-After support
│   │   ├── cache.ts               # LRU + Redis cache layer
│   │   └── metrics.ts             # Request counting and latency
│   ├── services/
│   │   ├── employee-sync.ts       # Incremental directory sync
│   │   ├── time-off.ts            # PTO balance and request management
│   │   ├── reports.ts             # Custom report generation
│   │   └── lifecycle.ts           # Onboarding/offboarding automation
│   ├── handlers/
│   │   ├── webhook.ts             # Webhook signature verification + routing
│   │   └── events.ts              # Employee change event processors
│   ├── api/
│   │   ├── health.ts              # Health check endpoint
│   │   ├── employees.ts           # REST API for local employee data
│   │   └── reports.ts             # Report generation endpoints
│   ├── jobs/
│   │   ├── full-sync.ts           # Scheduled full directory sync
│   │   ├── incremental-sync.ts    # Frequent delta sync
│   │   └── report-export.ts       # Scheduled report export
│   └── db/
│       ├── schema.sql             # PostgreSQL schema
│       └── queries.ts             # Database queries
├── tests/
│   ├── unit/
│   │   ├── client.test.ts
│   │   ├── employee-sync.test.ts
│   │   └── webhook.test.ts
│   ├── integration/
│   │   └── bamboohr-live.test.ts
│   └── mocks/
│       └── bamboohr-handlers.ts   # MSW handlers
├── config/
│   ├── default.json
│   ├── production.json
│   └── test.json
└── docker-compose.yml             # PostgreSQL + Redis for local dev
```

### Step 1: Data Model

```sql
-- db/schema.sql
CREATE TABLE bamboohr_employees (
  id               INTEGER PRIMARY KEY,  -- BambooHR employee ID
  first_name       TEXT NOT NULL,
  last_name        TEXT NOT NULL,
  display_name     TEXT,
  work_email       TEXT,
  job_title        TEXT,
  department       TEXT,
  division         TEXT,
  location         TEXT,
  supervisor_id    INTEGER REFERENCES bamboohr_employees(id),
  status           TEXT DEFAULT 'Active',
  hire_date        DATE,
  termination_date DATE,
  employee_number  TEXT,
  raw_data         JSONB,                -- Full BambooHR response
  synced_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_employees_status ON bamboohr_employees(status);
CREATE INDEX idx_employees_department ON bamboohr_employees(department);
CREATE INDEX idx_employees_synced ON bamboohr_employees(synced_at);

CREATE TABLE bamboohr_sync_log (
  id            SERIAL PRIMARY KEY,
  sync_type     TEXT NOT NULL,  -- 'full', 'incremental', 'webhook'
  started_at    TIMESTAMPTZ NOT NULL,
  completed_at  TIMESTAMPTZ,
  employees_created  INTEGER DEFAULT 0,
  employees_updated  INTEGER DEFAULT 0,
  employees_deleted  INTEGER DEFAULT 0,
  errors        JSONB DEFAULT '[]',
  status        TEXT DEFAULT 'running'  -- 'running', 'completed', 'failed'
);
```

### Step 2: Employee Sync Service

```typescript
// src/services/employee-sync.ts
import { BambooHRClient } from '../bamboohr/client';
import { db } from '../db/queries';

const SYNC_FIELDS = [
  'firstName', 'lastName', 'displayName', 'workEmail',
  'jobTitle', 'department', 'division', 'location',
  'supervisor', 'status', 'hireDate', 'terminationDate',
  'employeeNumber',
];

export class EmployeeSyncService {
  constructor(private client: BambooHRClient) {}

  async fullSync(): Promise<SyncResult> {
    const log = await db.createSyncLog('full');

    try {
      // One API call for all employee data
      const report = await this.client.customReport(SYNC_FIELDS);
      const result = { created: 0, updated: 0, deleted: 0, errors: [] as string[] };

      for (const emp of report.employees) {
        try {
          const existing = await db.getEmployee(parseInt(emp.id));
          if (existing) {
            await db.updateEmployee(parseInt(emp.id), emp);
            result.updated++;
          } else {
            await db.createEmployee(parseInt(emp.id), emp);
            result.created++;
          }
        } catch (err) {
          result.errors.push(`Employee ${emp.id}: ${(err as Error).message}`);
        }
      }

      // Mark employees not in report as inactive
      const activeIds = new Set(report.employees.map(e => parseInt(e.id)));
      const localEmployees = await db.getActiveEmployeeIds();
      for (const localId of localEmployees) {
        if (!activeIds.has(localId)) {
          await db.deactivateEmployee(localId);
          result.deleted++;
        }
      }

      await db.completeSyncLog(log.id, result);
      return result;
    } catch (err) {
      await db.failSyncLog(log.id, (err as Error).message);
      throw err;
    }
  }

  async incrementalSync(): Promise<SyncResult> {
    const lastSync = await db.getLastSyncTimestamp();
    const changed = await this.client.request<any>(
      'GET', `/employees/changed/?since=${lastSync}`,
    );

    const changedIds = Object.keys(changed.employees || {});
    if (changedIds.length === 0) return { created: 0, updated: 0, deleted: 0, errors: [] };

    // Fetch details for changed employees only
    const result = { created: 0, updated: 0, deleted: 0, errors: [] as string[] };
    for (const id of changedIds) {
      const emp = await this.client.getEmployee(id, SYNC_FIELDS);
      // Upsert logic...
    }

    return result;
  }

  async handleWebhookEvent(employeeId: string, action: string, fields: Record<string, string>) {
    switch (action) {
      case 'Created':
        await db.createEmployee(parseInt(employeeId), fields);
        break;
      case 'Updated':
        await db.updateEmployee(parseInt(employeeId), fields);
        break;
      case 'Deleted':
        await db.deactivateEmployee(parseInt(employeeId));
        break;
    }
  }
}
```

### Step 3: Employee Lifecycle Automation

```typescript
// src/services/lifecycle.ts
export class EmployeeLifecycleService {
  constructor(
    private bamboohr: BambooHRClient,
    private slackClient: any,
    private googleAdmin: any,
  ) {}

  async onNewEmployee(employeeId: string, fields: Record<string, string>) {
    const { firstName, lastName, workEmail, department, jobTitle, supervisor } = fields;

    // 1. Create Google Workspace account
    await this.googleAdmin.createUser({
      primaryEmail: workEmail,
      name: { givenName: firstName, familyName: lastName },
      orgUnitPath: `/departments/${department}`,
    });

    // 2. Add to Slack
    await this.slackClient.inviteUser(workEmail);
    await this.slackClient.addToChannel(workEmail, `#${department.toLowerCase()}`);

    // 3. Notify manager
    await this.slackClient.sendDM(supervisor, {
      text: `Your new report ${firstName} ${lastName} (${jobTitle}) starts soon. ` +
            `BambooHR profile: https://${process.env.BAMBOOHR_COMPANY_DOMAIN}.bamboohr.com/employees/employee.php?id=${employeeId}`,
    });

    console.log(`Onboarding complete for ${firstName} ${lastName}`);
  }

  async onEmployeeTerminated(employeeId: string, fields: Record<string, string>) {
    const { workEmail, firstName, lastName } = fields;

    // 1. Disable Google Workspace account
    await this.googleAdmin.suspendUser(workEmail);

    // 2. Deactivate Slack
    await this.slackClient.deactivateUser(workEmail);

    // 3. Archive in downstream systems
    console.log(`Offboarding complete for ${firstName} ${lastName}`);
  }

  async onDepartmentChanged(employeeId: string, fields: Record<string, string>) {
    const { workEmail, department } = fields;

    // Update Google Workspace OU
    await this.googleAdmin.moveUser(workEmail, `/departments/${department}`);

    // Update Slack channels
    await this.slackClient.addToChannel(workEmail, `#${department.toLowerCase()}`);
  }
}
```

### Step 4: Sync Scheduling

```typescript
// src/jobs/sync-scheduler.ts
import cron from 'node-cron';

// Full sync: daily at 2 AM
cron.schedule('0 2 * * *', async () => {
  console.log('Starting full BambooHR sync...');
  const result = await syncService.fullSync();
  console.log(`Full sync: ${result.created} created, ${result.updated} updated, ${result.deleted} deleted`);
});

// Incremental sync: every 15 minutes (safety net for missed webhooks)
cron.schedule('*/15 * * * *', async () => {
  const result = await syncService.incrementalSync();
  if (result.created + result.updated + result.deleted > 0) {
    console.log(`Incremental sync: ${JSON.stringify(result)}`);
  }
});
```

### Step 5: Configuration Management

```typescript
// config/bamboohr.ts
export interface BambooHRIntegrationConfig {
  api: {
    companyDomain: string;
    apiKey: string;
    timeoutMs: number;
    maxRetries: number;
  };
  sync: {
    fullSyncCron: string;
    incrementalSyncCron: string;
    batchSize: number;
  };
  cache: {
    directoryTtlMs: number;
    employeeTtlMs: number;
    redisUrl?: string;
  };
  webhook: {
    secret: string;
    path: string;
    replayWindowMs: number;
  };
}

export function loadConfig(): BambooHRIntegrationConfig {
  return {
    api: {
      companyDomain: process.env.BAMBOOHR_COMPANY_DOMAIN!,
      apiKey: process.env.BAMBOOHR_API_KEY!,
      timeoutMs: 30_000,
      maxRetries: 3,
    },
    sync: {
      fullSyncCron: '0 2 * * *',
      incrementalSyncCron: '*/15 * * * *',
      batchSize: 100,
    },
    cache: {
      directoryTtlMs: 5 * 60 * 1000,
      employeeTtlMs: 60 * 1000,
      redisUrl: process.env.REDIS_URL,
    },
    webhook: {
      secret: process.env.BAMBOOHR_WEBHOOK_SECRET!,
      path: '/webhooks/bamboohr',
      replayWindowMs: 300_000,
    },
  };
}
```

## Output

- Layered architecture separating API, service, client, and data concerns
- Employee sync with full, incremental, and webhook-driven modes
- PostgreSQL schema for local employee data with audit trail
- Lifecycle automation (onboarding, offboarding, department changes)
- Scheduled sync jobs with cron
- Environment-specific configuration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Sync data gaps | Missed webhooks + long incremental interval | Full sync as daily safety net |
| Duplicate processing | Webhook retry + no idempotency | Idempotency keys in sync log |
| Stale local data | Cache TTL too long | Webhook-based cache invalidation |
| Circular dependencies | Poor layer separation | Strict dependency direction (API > Service > Client > DB) |

## Enterprise Considerations

- **Multi-company**: Deploy separate instances per BambooHR company domain, or use tenant-aware client factory
- **Data residency**: Store employee data in the same region as your BambooHR instance
- **Compliance**: Implement data retention policies; BambooHR data includes PII
- **High availability**: Run sync workers as separate pods/containers from API servers
- **Monitoring**: Alert on sync failures, webhook delivery gaps, and API error spikes

## Resources

- [BambooHR API Documentation](https://documentation.bamboohr.com/docs)
- [BambooHR API Reference](https://documentation.bamboohr.com/reference)
- [BambooHR Webhooks](https://documentation.bamboohr.com/docs/webhooks)

## Flagship Skills

For the complete BambooHR skill pack, start with `bamboohr-install-auth`.
