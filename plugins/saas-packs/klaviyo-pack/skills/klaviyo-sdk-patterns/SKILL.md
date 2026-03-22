---
name: klaviyo-sdk-patterns
description: |
  Apply production-ready Klaviyo SDK patterns for the klaviyo-api package.
  Use when implementing Klaviyo integrations, refactoring SDK usage,
  or establishing team coding standards for Klaviyo API calls.
  Trigger with phrases like "klaviyo SDK patterns", "klaviyo best practices",
  "klaviyo code patterns", "idiomatic klaviyo", "klaviyo wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo SDK Patterns

## Overview

Production-ready patterns for the `klaviyo-api` Node.js SDK: singleton sessions, type-safe wrappers, retry logic, pagination, and multi-tenant support.

## Prerequisites

- `klaviyo-api` package installed
- Completed `klaviyo-install-auth` setup
- TypeScript project with strict mode

## Instructions

### Step 1: Singleton Session Pattern

```typescript
// src/klaviyo/session.ts
import { ApiKeySession } from 'klaviyo-api';

let _session: ApiKeySession | null = null;

export function getSession(apiKey?: string): ApiKeySession {
  if (!_session) {
    const key = apiKey || process.env.KLAVIYO_PRIVATE_KEY;
    if (!key) throw new Error('KLAVIYO_PRIVATE_KEY is required');
    _session = new ApiKeySession(key);
  }
  return _session;
}

// For testing: reset the singleton
export function resetSession(): void {
  _session = null;
}
```

### Step 2: Type-Safe API Wrapper

```typescript
// src/klaviyo/api.ts
import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ListsApi,
  SegmentsApi,
  CampaignsApi,
  FlowsApi,
  MetricsApi,
  TemplatesApi,
  CatalogsApi,
  DataPrivacyApi,
  WebhooksApi,
} from 'klaviyo-api';
import { getSession } from './session';

// Lazy-initialized API clients -- avoids creating unused clients
const apis = {
  get profiles() { return new ProfilesApi(getSession()); },
  get events() { return new EventsApi(getSession()); },
  get lists() { return new ListsApi(getSession()); },
  get segments() { return new SegmentsApi(getSession()); },
  get campaigns() { return new CampaignsApi(getSession()); },
  get flows() { return new FlowsApi(getSession()); },
  get metrics() { return new MetricsApi(getSession()); },
  get templates() { return new TemplatesApi(getSession()); },
  get catalogs() { return new CatalogsApi(getSession()); },
  get dataPrivacy() { return new DataPrivacyApi(getSession()); },
  get webhooks() { return new WebhooksApi(getSession()); },
};

export default apis;
```

### Step 3: Error Handling Wrapper

```typescript
// src/klaviyo/errors.ts

export interface KlaviyoApiError {
  status: number;
  statusText: string;
  errors: Array<{ id: string; code: string; title: string; detail: string }>;
  retryAfter?: number;
}

export function parseKlaviyoError(error: any): KlaviyoApiError {
  return {
    status: error.status || 500,
    statusText: error.statusText || 'Unknown Error',
    errors: error.body?.errors || [{ id: '', code: 'unknown', title: 'Unknown', detail: error.message }],
    retryAfter: error.headers?.['retry-after'] ? parseInt(error.headers['retry-after']) : undefined,
  };
}

export async function safeCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ data: T | null; error: KlaviyoApiError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err: any) {
    const parsed = parseKlaviyoError(err);
    console.error(`[Klaviyo] ${context} failed:`, {
      status: parsed.status,
      errors: parsed.errors.map(e => e.detail),
    });
    return { data: null, error: parsed };
  }
}
```

### Step 4: Retry with Retry-After Header

```typescript
// src/klaviyo/retry.ts

export async function withRetry<T>(
  operation: () => Promise<T>,
  options = { maxRetries: 3, baseDelayMs: 1000 }
): Promise<T> {
  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === options.maxRetries) throw error;

      const status = error.status;
      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Honor Klaviyo's Retry-After header (seconds)
      const retryAfter = error.headers?.['retry-after'];
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : options.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;

      console.log(`[Klaviyo] Retry ${attempt + 1}/${options.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 5: Cursor-Based Pagination

```typescript
// src/klaviyo/pagination.ts

/**
 * Auto-paginate any Klaviyo list endpoint.
 * Klaviyo uses cursor-based pagination with `page[cursor]` param.
 * Each page returns max 20 items (some endpoints allow up to 100).
 */
export async function* paginate<T>(
  fetcher: (pageCursor?: string) => Promise<{
    body: { data: T[]; links?: { next?: string } };
  }>
): AsyncGenerator<T> {
  let cursor: string | undefined;

  do {
    const response = await fetcher(cursor);
    for (const item of response.body.data) {
      yield item;
    }

    // Extract cursor from next link URL
    const nextLink = response.body.links?.next;
    if (nextLink) {
      const url = new URL(nextLink);
      cursor = url.searchParams.get('page[cursor]') || undefined;
    } else {
      cursor = undefined;
    }
  } while (cursor);
}

// Usage: iterate all profiles
// for await (const profile of paginate(cursor => profilesApi.getProfiles({ pageCursor: cursor }))) {
//   console.log(profile.attributes.email);
// }
```

### Step 6: Multi-Tenant Factory

```typescript
// src/klaviyo/multi-tenant.ts
import { ApiKeySession, ProfilesApi, EventsApi, ListsApi } from 'klaviyo-api';

interface TenantApis {
  profiles: ProfilesApi;
  events: EventsApi;
  lists: ListsApi;
}

const tenantCache = new Map<string, TenantApis>();

export function getApisForTenant(tenantId: string, apiKey: string): TenantApis {
  if (!tenantCache.has(tenantId)) {
    const session = new ApiKeySession(apiKey);
    tenantCache.set(tenantId, {
      profiles: new ProfilesApi(session),
      events: new EventsApi(session),
      lists: new ListsApi(session),
    });
  }
  return tenantCache.get(tenantId)!;
}
```

## SDK Conventions

| Convention | Example |
|-----------|---------|
| Property casing | `firstName` (not `first_name`) |
| Response access | `response.body.data` (not `response.data`) |
| Payload structure | `{ data: { type: 'profile', attributes: { ... } } }` |
| Filter syntax | `equals(email,"user@example.com")` |
| Sort syntax | `'-datetime'` (descending), `'datetime'` (ascending) |
| Include relations | `{ include: ['lists'] }` |

## Error Handling

| Error | Status | Retryable | Solution |
|-------|--------|-----------|----------|
| Invalid API key | 401 | No | Check KLAVIYO_PRIVATE_KEY |
| Missing scope | 403 | No | Add required scope to API key |
| Validation error | 400 | No | Fix request payload |
| Rate limited | 429 | Yes | Honor Retry-After header |
| Server error | 500/503 | Yes | Retry with backoff |
| Conflict | 409 | No | Resource already exists; use update |

## Resources

- [klaviyo-api-node README](https://github.com/klaviyo/klaviyo-api-node/blob/main/README.md)
- [API Overview](https://developers.klaviyo.com/en/reference/api_overview)
- [API Versioning](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)

## Next Steps

Apply patterns in `klaviyo-core-workflow-a` for profile and list management.
