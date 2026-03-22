---
name: hubspot-sdk-patterns
description: |
  Apply production-ready @hubspot/api-client SDK patterns for TypeScript.
  Use when implementing HubSpot integrations, building typed wrappers,
  or establishing team standards for HubSpot CRM operations.
  Trigger with phrases like "hubspot SDK patterns", "hubspot best practices",
  "hubspot typed client", "hubspot api-client wrapper", "idiomatic hubspot".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot SDK Patterns

## Overview

Production-ready patterns for the `@hubspot/api-client` SDK covering typed wrappers, error handling, batch operations, and pagination.

## Prerequisites

- `@hubspot/api-client` v13+ installed
- TypeScript 5+ with strict mode
- Understanding of HubSpot CRM object model

## Instructions

### Step 1: Typed Client Wrapper

```typescript
// src/hubspot/client.ts
import * as hubspot from '@hubspot/api-client';
import type {
  SimplePublicObjectInputForCreate,
  SimplePublicObject,
  PublicObjectSearchRequest,
} from '@hubspot/api-client/lib/codegen/crm/contacts';

interface HubSpotConfig {
  accessToken: string;
  retries?: number;
}

let instance: hubspot.Client | null = null;

export function getClient(config?: HubSpotConfig): hubspot.Client {
  if (!instance) {
    instance = new hubspot.Client({
      accessToken: config?.accessToken || process.env.HUBSPOT_ACCESS_TOKEN!,
      numberOfApiCallRetries: config?.retries ?? 3,
    });
  }
  return instance;
}
```

### Step 2: Error Classification

```typescript
// src/hubspot/errors.ts
export class HubSpotApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly category: string,
    public readonly correlationId: string,
    public readonly retryable: boolean
  ) {
    super(message);
    this.name = 'HubSpotApiError';
  }
}

export function classifyError(error: any): HubSpotApiError {
  const status = error?.code || error?.statusCode || error?.response?.status || 500;
  const body = error?.body || error?.response?.body || {};
  const correlationId = body.correlationId || 'unknown';

  const retryable = [429, 500, 502, 503, 504].includes(status);

  const categoryMap: Record<number, string> = {
    400: 'VALIDATION_ERROR',
    401: 'AUTHENTICATION_ERROR',
    403: 'AUTHORIZATION_ERROR',
    404: 'NOT_FOUND',
    409: 'CONFLICT',
    429: 'RATE_LIMIT',
    500: 'INTERNAL_ERROR',
  };

  return new HubSpotApiError(
    body.message || error.message || 'Unknown HubSpot error',
    status,
    categoryMap[status] || 'UNKNOWN',
    correlationId,
    retryable
  );
}

// Usage wrapper
export async function safeCall<T>(operation: () => Promise<T>): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    throw classifyError(error);
  }
}
```

### Step 3: Typed CRM Operations

```typescript
// src/hubspot/contacts.ts
import * as hubspot from '@hubspot/api-client';
import type { SimplePublicObject } from '@hubspot/api-client/lib/codegen/crm/contacts';
import { getClient } from './client';
import { safeCall } from './errors';

// Define your contact properties as a type
interface ContactProperties {
  firstname?: string;
  lastname?: string;
  email: string;
  phone?: string;
  company?: string;
  lifecyclestage?: 'subscriber' | 'lead' | 'marketingqualifiedlead'
    | 'salesqualifiedlead' | 'opportunity' | 'customer' | 'evangelist';
}

const CONTACT_PROPS = ['firstname', 'lastname', 'email', 'phone', 'company', 'lifecyclestage'];

export async function createContact(props: ContactProperties): Promise<SimplePublicObject> {
  return safeCall(() =>
    getClient().crm.contacts.basicApi.create({
      properties: props as Record<string, string>,
      associations: [],
    })
  );
}

export async function getContact(id: string): Promise<SimplePublicObject> {
  return safeCall(() =>
    getClient().crm.contacts.basicApi.getById(id, CONTACT_PROPS)
  );
}

export async function updateContact(
  id: string,
  props: Partial<ContactProperties>
): Promise<SimplePublicObject> {
  return safeCall(() =>
    getClient().crm.contacts.basicApi.update(id, {
      properties: props as Record<string, string>,
    })
  );
}

export async function findContactByEmail(email: string): Promise<SimplePublicObject | null> {
  const result = await safeCall(() =>
    getClient().crm.contacts.searchApi.doSearch({
      filterGroups: [{
        filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
      }],
      properties: CONTACT_PROPS,
      limit: 1,
      after: 0,
      sorts: [],
    })
  );
  return result.results[0] || null;
}
```

### Step 4: Batch Operations

```typescript
// src/hubspot/batch.ts
import { getClient } from './client';
import { safeCall } from './errors';

// Batch create contacts (max 100 per batch)
export async function batchCreateContacts(
  contacts: Array<{ properties: Record<string, string> }>
) {
  // POST /crm/v3/objects/contacts/batch/create
  return safeCall(() =>
    getClient().crm.contacts.batchApi.create({
      inputs: contacts.map(c => ({ properties: c.properties, associations: [] })),
    })
  );
}

// Batch read contacts by ID or unique property
export async function batchReadContacts(ids: string[], properties: string[]) {
  // POST /crm/v3/objects/contacts/batch/read
  return safeCall(() =>
    getClient().crm.contacts.batchApi.read({
      inputs: ids.map(id => ({ id })),
      properties,
      propertiesWithHistory: [],
    })
  );
}

// Batch upsert: create or update in one call
export async function batchUpsertContacts(
  contacts: Array<{ properties: Record<string, string> }>,
  idProperty = 'email'
) {
  // POST /crm/v3/objects/contacts/batch/upsert
  const client = getClient();
  return safeCall(() =>
    client.apiRequest({
      method: 'POST',
      path: '/crm/v3/objects/contacts/batch/upsert',
      body: {
        inputs: contacts.map(c => ({
          properties: c.properties,
          idProperty,
          id: c.properties[idProperty],
        })),
      },
    })
  );
}

// Chunk large batches into 100-record groups
export async function batchCreateChunked(
  contacts: Array<{ properties: Record<string, string> }>,
  chunkSize = 100
) {
  const results = [];
  for (let i = 0; i < contacts.length; i += chunkSize) {
    const chunk = contacts.slice(i, i + chunkSize);
    const result = await batchCreateContacts(chunk);
    results.push(result);
  }
  return results;
}
```

### Step 5: Pagination Helper

```typescript
// src/hubspot/pagination.ts
import type { SimplePublicObject } from '@hubspot/api-client/lib/codegen/crm/contacts';
import { getClient } from './client';

export async function* getAllContacts(
  properties: string[],
  limit = 100
): AsyncGenerator<SimplePublicObject> {
  let after: string | undefined;

  do {
    const page = await getClient().crm.contacts.basicApi.getPage(
      limit,
      after,
      properties
    );

    for (const contact of page.results) {
      yield contact;
    }

    after = page.paging?.next?.after;
  } while (after);
}

// Usage
async function exportAllContacts() {
  const allContacts: SimplePublicObject[] = [];
  for await (const contact of getAllContacts(['firstname', 'lastname', 'email'])) {
    allContacts.push(contact);
  }
  console.log(`Exported ${allContacts.length} contacts`);
}
```

## Output

- Type-safe client singleton with automatic retries
- Error classification with retryable detection
- Typed CRUD operations for contacts
- Batch create/read/upsert with chunking
- Async generator for paginated results

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeCall` wrapper | All API calls | Classifies errors, adds correlation IDs |
| `numberOfApiCallRetries` | Transient failures | Built-in SDK retry for 429/5xx |
| Batch chunking | Large datasets | Stays within 100-record batch limit |
| Pagination generator | Full exports | Memory-efficient streaming |

## Examples

### Factory Pattern (Multi-Portal)

```typescript
const clients = new Map<string, hubspot.Client>();

export function getClientForPortal(portalId: string, token: string): hubspot.Client {
  if (!clients.has(portalId)) {
    clients.set(portalId, new hubspot.Client({ accessToken: token }));
  }
  return clients.get(portalId)!;
}
```

## Resources

- [@hubspot/api-client API Reference](https://github.hubspot.com/hubspot-api-nodejs/)
- [CRM Objects API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts)
- [Batch Operations Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)

## Next Steps

Apply patterns in `hubspot-core-workflow-a` for real-world CRM operations.
