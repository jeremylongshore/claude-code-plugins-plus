---
name: webflow-sdk-patterns
description: |
  Apply production-ready Webflow SDK patterns — singleton client, typed error handling,
  pagination helpers, and raw response access for the webflow-api package.
  Use when implementing Webflow integrations, refactoring SDK usage,
  or establishing team coding standards.
  Trigger with phrases like "webflow SDK patterns", "webflow best practices",
  "webflow code patterns", "idiomatic webflow", "webflow typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow SDK Patterns

## Overview

Production-ready patterns for the `webflow-api` SDK (v3.x). Covers singleton client,
typed error handling, pagination, raw response headers, and multi-tenant factory.

## Prerequisites

- `webflow-api` v3.x installed
- TypeScript 5+ project
- Familiarity with async/await and the Webflow Data API v2

## Instructions

### Pattern 1: Singleton Client with Configuration

```typescript
// src/webflow/client.ts
import { WebflowClient } from "webflow-api";

interface WebflowConfig {
  accessToken: string;
  timeout?: number;   // Request timeout in ms (default: SDK default)
  maxRetries?: number; // Auto-retry on 429/5xx (default: 2)
}

let instance: WebflowClient | null = null;

export function getWebflowClient(config?: Partial<WebflowConfig>): WebflowClient {
  if (!instance) {
    const token = config?.accessToken || process.env.WEBFLOW_API_TOKEN;
    if (!token) throw new Error("WEBFLOW_API_TOKEN required");

    instance = new WebflowClient({
      accessToken: token,
      // The SDK supports timeout and maxRetries natively
      ...(config?.timeout && { timeout: config.timeout }),
      ...(config?.maxRetries !== undefined && { maxRetries: config.maxRetries }),
    });
  }
  return instance;
}

// Reset client (useful for token rotation)
export function resetWebflowClient(): void {
  instance = null;
}
```

### Pattern 2: Typed Error Handling

The SDK throws `WebflowError` subclasses. Handle them by type:

```typescript
import { WebflowClient } from "webflow-api";

// SDK errors are subclasses of WebflowError
// Common HTTP status codes: 400, 401, 403, 404, 409, 429, 500

async function safeWebflowCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ data: T | null; error: string | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err: any) {
    const statusCode = err.statusCode || err.status;
    const message = err.message || String(err);

    // Log with context for debugging
    console.error(`[Webflow] ${context} failed:`, {
      status: statusCode,
      message,
      body: err.body,
    });

    // Classify the error
    switch (statusCode) {
      case 401:
        console.error("Token invalid or revoked. Rotate token.");
        break;
      case 403:
        console.error("Missing required scope. Check token scopes.");
        break;
      case 404:
        console.error("Resource not found. Verify IDs.");
        break;
      case 409:
        console.error("Conflict — item may already exist with this slug.");
        break;
      case 429:
        console.error("Rate limited. SDK will auto-retry with backoff.");
        break;
      default:
        if (statusCode >= 500) {
          console.error("Webflow server error. Retry later.");
        }
    }

    return { data: null, error: message };
  }
}

// Usage
const { data: sites, error } = await safeWebflowCall(
  () => webflow.sites.list(),
  "sites.list"
);
```

### Pattern 3: Pagination Helper

Webflow v2 uses offset-based pagination. Iterate through all pages:

```typescript
interface PaginatedResult<T> {
  items: T[];
  pagination: { limit: number; offset: number; total: number };
}

async function fetchAllItems<T>(
  fetcher: (offset: number, limit: number) => Promise<PaginatedResult<T>>,
  pageSize = 100
): Promise<T[]> {
  const allItems: T[] = [];
  let offset = 0;

  while (true) {
    const result = await fetcher(offset, pageSize);
    allItems.push(...result.items);

    if (allItems.length >= result.pagination.total) break;
    offset += pageSize;
  }

  return allItems;
}

// Usage: Fetch all items from a collection
const allItems = await fetchAllItems((offset, limit) =>
  webflow.collections.items.listItems(collectionId, { offset, limit })
    .then(res => ({
      items: res.items || [],
      pagination: res.pagination || { limit, offset, total: 0 },
    }))
);
```

### Pattern 4: Raw Response Access (Headers)

Access rate limit headers using `.withRawResponse()`:

```typescript
async function getWithRateLimitInfo(siteId: string) {
  // .withRawResponse() returns { data, rawResponse }
  const response = await webflow.sites.get(siteId)
    // @ts-ignore — withRawResponse is available on all SDK methods
    ;

  // For rate limit monitoring, use a wrapper that extracts headers
  const rawFetch = await fetch(
    `https://api.webflow.com/v2/sites/${siteId}`,
    {
      headers: {
        Authorization: `Bearer ${process.env.WEBFLOW_API_TOKEN}`,
        "Content-Type": "application/json",
      },
    }
  );

  const rateLimitRemaining = rawFetch.headers.get("X-RateLimit-Remaining");
  const rateLimitLimit = rawFetch.headers.get("X-RateLimit-Limit");
  const retryAfter = rawFetch.headers.get("Retry-After");

  console.log(`Rate limit: ${rateLimitRemaining}/${rateLimitLimit}`);

  return rawFetch.json();
}
```

### Pattern 5: Multi-Tenant Factory

For apps serving multiple Webflow workspaces:

```typescript
const clients = new Map<string, WebflowClient>();

export function getClientForTenant(tenantId: string): WebflowClient {
  if (!clients.has(tenantId)) {
    const token = getTenantToken(tenantId); // From your DB/vault

    clients.set(
      tenantId,
      new WebflowClient({ accessToken: token })
    );
  }
  return clients.get(tenantId)!;
}

// Rotate a tenant's token without downtime
export function rotateTenantToken(tenantId: string, newToken: string): void {
  clients.set(
    tenantId,
    new WebflowClient({ accessToken: newToken })
  );
}
```

### Pattern 6: Bulk Operations Helper

The CMS bulk endpoints accept up to 100 items per request:

```typescript
async function bulkCreateItems(
  collectionId: string,
  items: Array<{ fieldData: Record<string, any>; isDraft?: boolean }>,
  batchSize = 100
): Promise<string[]> {
  const createdIds: string[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);

    const result = await webflow.collections.items.createItemsBulk(
      collectionId,
      { items: batch }
    );

    if (result.items) {
      createdIds.push(...result.items.map(item => item.id!));
    }

    console.log(`Created batch ${Math.floor(i / batchSize) + 1}: ${batch.length} items`);
  }

  return createdIds;
}
```

### Pattern 7: Zod Validation for API Responses

```typescript
import { z } from "zod";

const WebflowSiteSchema = z.object({
  id: z.string(),
  displayName: z.string(),
  shortName: z.string(),
  lastPublished: z.string().nullable(),
  customDomains: z.array(z.object({
    url: z.string(),
  })).optional(),
});

const WebflowCollectionItemSchema = z.object({
  id: z.string(),
  isDraft: z.boolean(),
  isArchived: z.boolean(),
  createdOn: z.string(),
  lastUpdated: z.string(),
  fieldData: z.record(z.unknown()),
});

// Validate API responses at runtime
async function getValidatedSite(siteId: string) {
  const site = await webflow.sites.get(siteId);
  return WebflowSiteSchema.parse(site);
}
```

## Output

- Type-safe singleton client with configuration
- Structured error handling by HTTP status code
- Pagination helper for large collections
- Rate limit header monitoring
- Multi-tenant client factory
- Bulk CMS operations (100 items/batch)
- Runtime response validation with Zod

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Safe wrapper | All API calls | Prevents uncaught exceptions |
| Status classification | Error triage | Clear remediation path |
| Pagination helper | Large datasets | No missed items |
| Zod validation | Response integrity | Catches API changes |
| Token rotation | Security compliance | Zero-downtime rotation |

## Resources

- [SDK npm package](https://www.npmjs.com/package/webflow-api)
- [SDK GitHub repo](https://github.com/webflow/js-webflow-api)
- [API Reference](https://developers.webflow.com/data/reference/rest-introduction)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply patterns in `webflow-core-workflow-a` for CMS content management.
