---
name: hubspot-reference-architecture
description: |
  Implement a production-ready HubSpot integration architecture with layered design.
  Use when designing new HubSpot integrations, reviewing project structure,
  or establishing architecture standards for HubSpot CRM applications.
  Trigger with phrases like "hubspot architecture", "hubspot project structure",
  "hubspot integration design", "hubspot best practices layout", "hubspot layers".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Reference Architecture

## Overview

Production-ready layered architecture for HubSpot CRM integrations with typed clients, service abstraction, caching, and webhook handling.

## Prerequisites

- TypeScript 5+ project
- `@hubspot/api-client` v13+ installed
- Understanding of layered architecture patterns

## Instructions

### Step 1: Project Structure

```
my-hubspot-integration/
├── src/
│   ├── hubspot/                    # HubSpot infrastructure layer
│   │   ├── client.ts              # Singleton @hubspot/api-client wrapper
│   │   ├── types.ts               # HubSpot-specific types
│   │   ├── errors.ts              # Error classification
│   │   ├── cache.ts               # Response caching
│   │   └── associations.ts        # Association type constants
│   ├── services/                   # Business logic layer
│   │   ├── contact.service.ts     # Contact CRUD + business rules
│   │   ├── deal.service.ts        # Deal pipeline operations
│   │   ├── company.service.ts     # Company management
│   │   └── sync.service.ts        # Data synchronization
│   ├── api/                        # API layer
│   │   ├── routes/
│   │   │   ├── contacts.ts        # REST endpoints
│   │   │   ├── deals.ts
│   │   │   └── webhooks.ts        # Webhook receiver
│   │   └── middleware/
│   │       ├── auth.ts            # Request auth
│   │       └── webhook-verify.ts  # HubSpot signature verification
│   ├── jobs/                       # Background jobs
│   │   ├── sync-contacts.ts       # Scheduled sync
│   │   └── process-webhooks.ts    # Async event processing
│   └── index.ts
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── mocks/hubspot.ts       # Shared mock factory
│   └── integration/
│       └── hubspot.integration.test.ts
├── config/
│   ├── default.ts                 # Shared config
│   └── production.ts              # Production overrides
└── package.json
```

### Step 2: Infrastructure Layer

```typescript
// src/hubspot/client.ts
import * as hubspot from '@hubspot/api-client';

let instance: hubspot.Client | null = null;

export function getHubSpotClient(): hubspot.Client {
  if (!instance) {
    instance = new hubspot.Client({
      accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
      numberOfApiCallRetries: 3,
    });
  }
  return instance;
}

// src/hubspot/associations.ts
// Default association type IDs (HUBSPOT_DEFINED category)
export const ASSOCIATION_TYPES = {
  CONTACT_TO_COMPANY: 1,
  CONTACT_TO_DEAL: 3,
  COMPANY_TO_DEAL: 5,
  CONTACT_TO_TICKET: 16,
  NOTE_TO_CONTACT: 202,
  TASK_TO_CONTACT: 204,
  NOTE_TO_DEAL: 214,
} as const;

// src/hubspot/errors.ts
export class HubSpotError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly category: string,
    public readonly correlationId: string,
    public readonly retryable: boolean
  ) {
    super(message);
    this.name = 'HubSpotError';
  }
}

export function wrapError(error: any): HubSpotError {
  const status = error?.code || error?.statusCode || 500;
  const body = error?.body || {};
  return new HubSpotError(
    body.message || error.message,
    status,
    body.category || 'UNKNOWN',
    body.correlationId || '',
    [429, 500, 502, 503, 504].includes(status)
  );
}
```

### Step 3: Service Layer

```typescript
// src/services/contact.service.ts
import type { SimplePublicObject } from '@hubspot/api-client/lib/codegen/crm/contacts';
import { getHubSpotClient } from '../hubspot/client';
import { ASSOCIATION_TYPES } from '../hubspot/associations';
import { wrapError } from '../hubspot/errors';

const CONTACT_PROPS = ['firstname', 'lastname', 'email', 'phone', 'lifecyclestage', 'company'];

export class ContactService {
  private client = getHubSpotClient();

  async findByEmail(email: string): Promise<SimplePublicObject | null> {
    try {
      const result = await this.client.crm.contacts.searchApi.doSearch({
        filterGroups: [{
          filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
        }],
        properties: CONTACT_PROPS,
        limit: 1, after: 0, sorts: [],
      });
      return result.results[0] || null;
    } catch (error) {
      throw wrapError(error);
    }
  }

  async upsert(email: string, properties: Record<string, string>): Promise<SimplePublicObject> {
    const existing = await this.findByEmail(email);
    if (existing) {
      return this.client.crm.contacts.basicApi.update(existing.id, { properties });
    }
    return this.client.crm.contacts.basicApi.create({
      properties: { email, ...properties },
      associations: [],
    });
  }

  async associateWithCompany(contactId: string, companyId: string): Promise<void> {
    await this.client.crm.associations.v4.basicApi.create(
      'contacts', contactId, 'companies', companyId,
      [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: ASSOCIATION_TYPES.CONTACT_TO_COMPANY }]
    );
  }
}

// src/services/deal.service.ts
export class DealService {
  private client = getHubSpotClient();
  private pipelineCache: any[] | null = null;

  async getPipelines() {
    if (!this.pipelineCache) {
      const result = await this.client.crm.pipelines.pipelinesApi.getAll('deals');
      this.pipelineCache = result.results;
    }
    return this.pipelineCache;
  }

  async createInPipeline(
    dealName: string,
    amount: number,
    pipelineName: string,
    stageName: string,
    associations: { contactId?: string; companyId?: string }
  ) {
    const pipelines = await this.getPipelines();
    const pipeline = pipelines.find(p => p.label === pipelineName) || pipelines[0];
    const stage = pipeline.stages.find((s: any) => s.label === stageName) || pipeline.stages[0];

    const assocArray = [];
    if (associations.contactId) {
      assocArray.push({
        to: { id: associations.contactId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED' as const, associationTypeId: 3 }],
      });
    }
    if (associations.companyId) {
      assocArray.push({
        to: { id: associations.companyId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED' as const, associationTypeId: 5 }],
      });
    }

    return this.client.crm.deals.basicApi.create({
      properties: {
        dealname: dealName,
        amount: String(amount),
        pipeline: pipeline.id,
        dealstage: stage.id,
      },
      associations: assocArray,
    });
  }
}
```

### Step 4: Data Flow

```
User Request → API Routes → Service Layer → HubSpot Client → HubSpot API
                                 ↕                   ↕
                            Business Rules      Response Cache
                                 ↕
                            Background Jobs → Webhook Events
```

### Step 5: Configuration

```typescript
// config/default.ts
export const config = {
  hubspot: {
    retries: 3,
    cache: {
      contactTtlMs: 5 * 60 * 1000,     // 5 minutes
      pipelineTtlMs: 60 * 60 * 1000,   // 1 hour
      propertyTtlMs: 60 * 60 * 1000,   // 1 hour
    },
    batch: {
      maxSize: 100,
      concurrency: 5,
    },
  },
};

// config/production.ts
export const productionConfig = {
  hubspot: {
    retries: 5,
    cache: {
      contactTtlMs: 2 * 60 * 1000,     // shorter in prod
    },
  },
};
```

## Output

- Layered architecture separating infrastructure, services, and API
- Typed client with error classification
- Association type constants (no magic numbers)
- Service classes with business logic encapsulation
- Configurable caching and retry policies

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Services import hubspot/, never the reverse |
| Type errors | Missing SDK type imports | Import from `@hubspot/api-client/lib/codegen/crm/` |
| Test isolation | Shared client state | Use `resetHubSpotClient()` in test teardown |
| Cache invalidation | Stale data | Invalidate on webhook events |

## Resources

- [@hubspot/api-client GitHub](https://github.com/HubSpot/hubspot-api-nodejs)
- [CRM Objects Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)
- [Associations v4 API](https://developers.hubspot.com/docs/guides/api/crm/associations)

## Next Steps

For multi-environment setup, see `hubspot-multi-env-setup`.
