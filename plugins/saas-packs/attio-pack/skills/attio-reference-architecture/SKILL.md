---
name: attio-reference-architecture
description: |
  Production reference architecture for Attio CRM integrations -- layered
  project structure, sync patterns, webhook processing, and multi-environment setup.
  Trigger: "attio architecture", "attio best practices", "attio project structure",
  "how to organize attio", "attio integration design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Reference Architecture

## Overview

Production architecture for applications that integrate with the Attio REST API (`https://api.attio.com/v2`). Covers project layout, layered service design, sync patterns, and operational concerns.

## Project Structure

```
my-attio-integration/
├── src/
│   ├── attio/                        # Attio API layer (isolated)
│   │   ├── client.ts                 # Typed fetch wrapper with retry
│   │   ├── types.ts                  # Attio API types (AttioRecord, AttioError, etc.)
│   │   ├── config.ts                 # Environment-based config loader
│   │   └── errors.ts                 # AttioApiError class
│   ├── services/                     # Business logic (uses attio/ layer)
│   │   ├── contacts.ts              # People/company sync logic
│   │   ├── pipeline.ts              # Deal pipeline management
│   │   ├── activity.ts              # Notes, tasks, comments
│   │   └── sync.ts                  # Bi-directional sync orchestrator
│   ├── webhooks/                     # Incoming webhook handlers
│   │   ├── router.ts                # Event type routing
│   │   ├── verify.ts                # Signature verification
│   │   └── handlers/
│   │       ├── record-events.ts     # record.created/updated/deleted/merged
│   │       ├── entry-events.ts      # list-entry.created/updated/deleted
│   │       └── activity-events.ts   # note/task/comment events
│   ├── api/                         # Outbound API routes
│   │   ├── health.ts                # Health check (includes Attio)
│   │   └── webhooks.ts              # Webhook receiver endpoint
│   ├── cache/                       # Caching layer
│   │   ├── schema-cache.ts          # Object/attribute definitions (30min TTL)
│   │   └── record-cache.ts          # Record data (5min TTL, webhook invalidation)
│   └── index.ts                     # App entrypoint
├── tests/
│   ├── mocks/                       # MSW handlers for Attio API
│   ├── unit/                        # Service logic tests (mocked API)
│   └── integration/                 # Live API tests (CI-gated)
├── config/
│   ├── attio.development.json
│   ├── attio.staging.json
│   └── attio.production.json
├── .env.example
└── .github/workflows/attio.yml
```

## Layered Architecture

```
┌──────────────────────────────────────────────────┐
│  API Layer (routes, webhook endpoint)            │
│  - Receives HTTP requests                        │
│  - Validates webhook signatures                  │
│  - Returns health status                         │
├──────────────────────────────────────────────────┤
│  Service Layer (business logic)                  │
│  - Contact sync, pipeline management             │
│  - Bi-directional data mapping                   │
│  - Event-driven automations                      │
├──────────────────────────────────────────────────┤
│  Attio Layer (API client, types, errors)         │
│  - Typed fetch wrapper with retry                │
│  - Error normalization (AttioApiError)            │
│  - Pagination helpers                            │
├──────────────────────────────────────────────────┤
│  Infrastructure Layer (cache, queue, monitoring)  │
│  - LRU + Redis caching with webhook invalidation │
│  - Rate limit queue (p-queue)                    │
│  - Structured logging and metrics                │
└──────────────────────────────────────────────────┘
```

**Rule:** Each layer only calls the layer directly below it. The API layer never calls the Attio client directly.

## Core Components

### Component 1: Service Layer Facade

```typescript
// src/services/contacts.ts
import { AttioClient } from "../attio/client";
import { cachedGet, invalidateRecord } from "../cache/record-cache";
import type { AttioRecord } from "../attio/types";

export class ContactService {
  constructor(private client: AttioClient) {}

  async findByEmail(email: string): Promise<AttioRecord | null> {
    const res = await this.client.post<{ data: AttioRecord[] }>(
      "/objects/people/records/query",
      {
        filter: { email_addresses: email },
        limit: 1,
      }
    );
    return res.data[0] || null;
  }

  async upsertPerson(data: {
    email: string;
    firstName: string;
    lastName: string;
    company?: string;
  }): Promise<AttioRecord> {
    // Use PUT (assert) for idempotent upsert
    const res = await this.client.put<{ data: AttioRecord }>(
      "/objects/people/records",
      {
        data: {
          values: {
            email_addresses: [data.email],
            name: [{
              first_name: data.firstName,
              last_name: data.lastName,
              full_name: `${data.firstName} ${data.lastName}`,
            }],
            ...(data.company ? { company: [{ target_object: "companies", target_record_id: data.company }] } : {}),
          },
        },
      }
    );
    return res.data;
  }

  async addToPipeline(
    recordId: string,
    listSlug: string,
    stage: string,
    value?: { currency: string; amount: number }
  ): Promise<void> {
    await this.client.post(`/lists/${listSlug}/entries`, {
      data: {
        parent_record_id: recordId,
        parent_object: "people",
        values: {
          stage: [{ status: stage }],
          ...(value ? {
            deal_value: [{ currency_code: value.currency, currency_value: value.amount }],
          } : {}),
        },
      },
    });
  }

  async addNote(recordId: string, title: string, content: string): Promise<void> {
    await this.client.post("/notes", {
      data: {
        parent_object: "people",
        parent_record_id: recordId,
        title,
        format: "markdown",
        content,
      },
    });
  }
}
```

### Component 2: Webhook Event Router

```typescript
// src/webhooks/router.ts
import type { AttioWebhookEvent } from "../attio/types";

type EventHandler = (event: AttioWebhookEvent) => Promise<void>;

export class WebhookRouter {
  private handlers = new Map<string, EventHandler[]>();

  on(eventType: string, handler: EventHandler): void {
    const existing = this.handlers.get(eventType) || [];
    this.handlers.set(eventType, [...existing, handler]);
  }

  async route(event: AttioWebhookEvent): Promise<void> {
    const handlers = this.handlers.get(event.event_type) || [];
    if (handlers.length === 0) {
      console.log(`No handler for event: ${event.event_type}`);
      return;
    }
    await Promise.allSettled(handlers.map((h) => h(event)));
  }
}

// Usage
const router = new WebhookRouter();
router.on("record.created", async (event) => {
  if (event.object?.api_slug === "people") {
    await syncNewContactToExternalCRM(event.record!.id.record_id);
  }
});
router.on("record.updated", async (event) => {
  invalidateRecord(event.record!.id.record_id);
});
router.on("list-entry.created", async (event) => {
  await triggerPipelineAutomation(event);
});
```

### Component 3: Bi-Directional Sync

```typescript
// src/services/sync.ts
export class AttioSyncService {
  private lastSyncCursor: string | null = null;

  /** Outbound: push local changes to Attio */
  async pushToAttio(localContact: LocalContact): Promise<string> {
    const attioRecord = await this.contacts.upsertPerson({
      email: localContact.email,
      firstName: localContact.firstName,
      lastName: localContact.lastName,
    });
    return attioRecord.id.record_id;
  }

  /** Inbound: pull Attio changes to local (webhook-driven) */
  async handleAttioChange(event: AttioWebhookEvent): Promise<void> {
    if (event.event_type === "record.updated") {
      const record = await this.client.get<{ data: AttioRecord }>(
        `/objects/${event.object!.api_slug}/records/${event.record!.id.record_id}`
      );
      await this.updateLocalFromAttio(record.data);
    }
  }

  /** Full sync: reconcile all records (run periodically or on demand) */
  async fullSync(objectSlug: string): Promise<{ created: number; updated: number }> {
    let created = 0, updated = 0;
    const PAGE_SIZE = 500;
    let offset = 0;

    while (true) {
      const page = await this.client.post<{ data: AttioRecord[] }>(
        `/objects/${objectSlug}/records/query`,
        { limit: PAGE_SIZE, offset }
      );

      for (const record of page.data) {
        const existed = await this.upsertLocal(record);
        existed ? updated++ : created++;
      }

      if (page.data.length < PAGE_SIZE) break;
      offset += PAGE_SIZE;
    }

    return { created, updated };
  }
}
```

### Component 4: Multi-Environment Config

```typescript
// src/attio/config.ts
interface AttioEnvironmentConfig {
  apiKey: string;
  webhookSecret: string;
  baseUrl: string;
  cache: { schemaTtlMs: number; recordTtlMs: number };
  rateLimit: { concurrency: number; intervalCap: number };
}

const configs: Record<string, Partial<AttioEnvironmentConfig>> = {
  development: {
    cache: { schemaTtlMs: 60_000, recordTtlMs: 10_000 },
    rateLimit: { concurrency: 2, intervalCap: 5 },
  },
  staging: {
    cache: { schemaTtlMs: 300_000, recordTtlMs: 60_000 },
    rateLimit: { concurrency: 5, intervalCap: 8 },
  },
  production: {
    cache: { schemaTtlMs: 1_800_000, recordTtlMs: 300_000 },
    rateLimit: { concurrency: 10, intervalCap: 15 },
  },
};

export function loadConfig(): AttioEnvironmentConfig {
  const env = process.env.NODE_ENV || "development";
  const envConfig = configs[env] || configs.development;
  return {
    apiKey: requireEnv("ATTIO_API_KEY"),
    webhookSecret: process.env.ATTIO_WEBHOOK_SECRET || "",
    baseUrl: "https://api.attio.com/v2",
    cache: envConfig.cache!,
    rateLimit: envConfig.rateLimit!,
  };
}

function requireEnv(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env: ${key}`);
  return val;
}
```

## Data Flow Diagram

```
External System                    Your Application                      Attio CRM
     │                                   │                                  │
     │  Local change ──────────────────▶ │                                  │
     │                                   │  PUT /objects/people/records ──▶ │
     │                                   │  ◀── 200 { data: record }       │
     │                                   │                                  │
     │                                   │       Webhook: record.updated    │
     │                                   │  ◀──────────────────────────── │
     │  ◀── Sync update ──────────────  │                                  │
     │                                   │  GET /objects/.../records/... ─▶ │
     │                                   │  ◀── 200 { data: record }       │
```

## Error Handling

| Architecture issue | Symptom | Fix |
|-------------------|---------|-----|
| Service calls client directly | Tight coupling, hard to test | Add service layer facade |
| No cache invalidation | Stale data after updates | Webhook-driven cache invalidation |
| Sync conflicts | Both sides updated same record | Last-write-wins or conflict resolution queue |
| No circuit breaker | Attio outage cascades | Add circuit breaker in Attio layer |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Objects and Lists](https://docs.attio.com/docs/objects-and-lists)
- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)
- [Attio Developer Platform](https://attio.com/platform/developers)

## Next Steps

This is the capstone skill. For specific implementations, refer to the individual skills in this pack.
