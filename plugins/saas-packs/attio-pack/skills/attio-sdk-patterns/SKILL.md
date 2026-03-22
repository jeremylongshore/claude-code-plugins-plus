---
name: attio-sdk-patterns
description: |
  Production-ready patterns for the Attio REST API: typed client,
  retry with backoff, pagination iterators, and multi-tenant factory.
  Trigger: "attio SDK patterns", "attio best practices",
  "attio client wrapper", "idiomatic attio", "attio TypeScript patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio SDK Patterns

## Overview

There is no official Attio Node.js SDK. The API is a clean REST/JSON interface at `https://api.attio.com/v2`. These patterns wrap `fetch` into a production-grade typed client with retry, pagination, and error normalization.

## Prerequisites

- Node.js 18+ (native `fetch`)
- TypeScript 5+
- Completed `attio-install-auth`

## Instructions

### Pattern 1: Typed Client with Error Normalization

```typescript
// src/attio/client.ts
const ATTIO_BASE = "https://api.attio.com/v2";

export class AttioApiError extends Error {
  constructor(
    public statusCode: number,
    public type: string,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "AttioApiError";
  }

  get retryable(): boolean {
    return this.statusCode === 429 || this.statusCode >= 500;
  }
}

export class AttioClient {
  constructor(private apiKey: string) {}

  async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>
  ): Promise<T> {
    const res = await fetch(`${ATTIO_BASE}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new AttioApiError(
        res.status,
        err.type || "unknown",
        err.code || "unknown",
        err.message || `HTTP ${res.status}`
      );
    }

    return res.json() as Promise<T>;
  }

  // Convenience methods for common HTTP verbs
  get<T>(path: string) { return this.request<T>("GET", path); }
  post<T>(path: string, body: Record<string, unknown>) { return this.request<T>("POST", path, body); }
  patch<T>(path: string, body: Record<string, unknown>) { return this.request<T>("PATCH", path, body); }
  put<T>(path: string, body: Record<string, unknown>) { return this.request<T>("PUT", path, body); }
  delete<T>(path: string) { return this.request<T>("DELETE", path); }
}
```

### Pattern 2: Retry with Exponential Backoff

```typescript
// src/attio/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 4, baseMs: 1000, maxMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === config.maxRetries) throw err;

      // Only retry on rate limits (429) and server errors (5xx)
      if (err instanceof AttioApiError && !err.retryable) throw err;

      const delay = Math.min(
        config.baseMs * Math.pow(2, attempt) + Math.random() * 500,
        config.maxMs
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const people = await withRetry(() =>
  client.post("/objects/people/records/query", { limit: 50 })
);
```

### Pattern 3: Cursor-Based Pagination Iterator

Attio uses cursor-based pagination. The initial request omits `offset`; responses include `pagination.next_cursor`.

```typescript
// src/attio/paginate.ts
export async function* paginate<T>(
  client: AttioClient,
  path: string,
  body: Record<string, unknown> = {},
  pageSize = 100
): AsyncGenerator<T> {
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const res = await withRetry(() =>
      client.post<{ data: T[] }>(path, {
        ...body,
        limit: pageSize,
        offset,
      })
    );

    for (const item of res.data) {
      yield item;
    }

    hasMore = res.data.length === pageSize;
    offset += pageSize;
  }
}

// Usage: iterate all companies
for await (const company of paginate(client, "/objects/companies/records/query")) {
  console.log(company);
}
```

### Pattern 4: Singleton with Lazy Init

```typescript
// src/attio/singleton.ts
let _client: AttioClient | null = null;

export function getClient(): AttioClient {
  if (!_client) {
    const key = process.env.ATTIO_API_KEY;
    if (!key) throw new Error("ATTIO_API_KEY not set");
    _client = new AttioClient(key);
  }
  return _client;
}
```

### Pattern 5: Multi-Tenant Factory

```typescript
// src/attio/factory.ts
const tenantClients = new Map<string, AttioClient>();

export function getClientForTenant(tenantId: string): AttioClient {
  if (!tenantClients.has(tenantId)) {
    const key = getTenantApiKey(tenantId); // from DB or secrets manager
    tenantClients.set(tenantId, new AttioClient(key));
  }
  return tenantClients.get(tenantId)!;
}
```

### Pattern 6: Response Validation with Zod

```typescript
import { z } from "zod";

const AttioPersonSchema = z.object({
  id: z.object({
    object_id: z.string(),
    record_id: z.string(),
  }),
  created_at: z.string(),
  values: z.object({
    name: z.array(z.object({
      first_name: z.string().nullable(),
      last_name: z.string().nullable(),
      full_name: z.string().nullable(),
    })),
    email_addresses: z.array(z.object({
      email_address: z.string(),
    })),
  }).passthrough(),
});

// Validated fetch
const raw = await client.post("/objects/people/records/query", { limit: 1 });
const person = AttioPersonSchema.parse(raw.data[0]);
```

## Error Handling

| Pattern | When to Use | Benefit |
|---------|------------|---------|
| `AttioApiError` class | All API calls | Typed error with `retryable` flag |
| `withRetry` wrapper | Any mutating or critical read | Auto-retry on 429/5xx |
| Zod validation | Parsing API responses | Catches schema drift at runtime |
| Multi-tenant factory | SaaS with per-customer tokens | Isolates credentials |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Pagination Guide](https://docs.attio.com/rest-api/guides/pagination)
- [Attio Slugs and IDs](https://docs.attio.com/docs/slugs-and-ids)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply these patterns in `attio-core-workflow-a` (records CRUD) and `attio-core-workflow-b` (lists and entries).
