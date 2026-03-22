---
name: apollo-sdk-patterns
description: |
  Apply production-ready Apollo.io SDK patterns.
  Use when implementing Apollo integrations, refactoring API usage,
  or establishing team coding standards.
  Trigger with phrases like "apollo sdk patterns", "apollo best practices",
  "apollo code patterns", "idiomatic apollo", "apollo client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api]

---
# Apollo SDK Patterns

## Overview
Production-ready patterns for Apollo.io API integration. Apollo has no official SDK — these patterns wrap the REST API (`https://api.apollo.io/api/v1/`) with type safety, retry logic, pagination, and bulk operations. All requests use the `x-api-key` header.

## Prerequisites
- Completed `apollo-install-auth` setup
- TypeScript 5+ with strict mode

## Instructions

### Step 1: Type-Safe Client with Zod Validation
```typescript
// src/apollo/client.ts
import axios, { AxiosInstance } from 'axios';
import { z } from 'zod';

const ConfigSchema = z.object({
  apiKey: z.string().min(10, 'API key too short'),
  baseURL: z.string().url().default('https://api.apollo.io/api/v1'),
  timeout: z.number().default(30_000),
});

let instance: AxiosInstance | null = null;

export function getApolloClient(config?: Partial<z.input<typeof ConfigSchema>>): AxiosInstance {
  if (instance) return instance;

  const parsed = ConfigSchema.parse({
    apiKey: config?.apiKey ?? process.env.APOLLO_API_KEY,
    ...config,
  });

  instance = axios.create({
    baseURL: parsed.baseURL,
    timeout: parsed.timeout,
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': parsed.apiKey,
    },
  });

  return instance;
}

// Reset for testing
export function resetClient() { instance = null; }
```

### Step 2: Custom Error Classes
```typescript
// src/apollo/errors.ts
import { AxiosError } from 'axios';

export class ApolloApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public endpoint: string,
    public retryable: boolean,
    public requestId?: string,
  ) {
    super(message);
    this.name = 'ApolloApiError';
  }

  static fromAxios(err: AxiosError): ApolloApiError {
    const status = err.response?.status ?? 0;
    const body = err.response?.data as any;
    return new ApolloApiError(
      body?.message ?? err.message,
      status,
      err.config?.url ?? 'unknown',
      [429, 500, 502, 503, 504].includes(status),
      err.response?.headers?.['x-request-id'],
    );
  }
}

export class ApolloRateLimitError extends ApolloApiError {
  constructor(
    public retryAfterMs: number,
    endpoint: string,
  ) {
    super(`Rate limited on ${endpoint}`, 429, endpoint, true);
    this.name = 'ApolloRateLimitError';
  }
}
```

### Step 3: Retry with Exponential Backoff
```typescript
// src/apollo/retry.ts
import { ApolloApiError } from './errors';

export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: { maxRetries?: number; baseMs?: number; maxMs?: number } = {},
): Promise<T> {
  const { maxRetries = 3, baseMs = 1000, maxMs = 30_000 } = opts;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const isRetryable = err instanceof ApolloApiError && err.retryable;
      if (!isRetryable || attempt === maxRetries) throw err;

      const jitter = Math.random() * 500;
      const delay = Math.min(baseMs * 2 ** attempt + jitter, maxMs);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Async Pagination Iterator
Apollo endpoints return `pagination.total_entries` and accept `page`/`per_page`. The People Search API limits to 500 pages (50,000 records).

```typescript
// src/apollo/paginator.ts
import { getApolloClient } from './client';
import { withRetry } from './retry';

export async function* paginate<T>(
  endpoint: string,
  body: Record<string, unknown>,
  itemKey: string = 'people',
  perPage: number = 100,
  maxPages: number = 500,
): AsyncGenerator<T[], void, undefined> {
  const client = getApolloClient();
  let page = 1;
  let totalPages = Infinity;

  while (page <= Math.min(totalPages, maxPages)) {
    const { data } = await withRetry(() =>
      client.post(endpoint, { ...body, page, per_page: perPage }),
    );

    const items: T[] = data[itemKey] ?? [];
    totalPages = data.pagination?.total_pages ?? 1;
    if (items.length === 0) break;

    yield items;
    page++;
  }
}

// Usage:
// for await (const batch of paginate('/mixed_people/api_search', {
//   q_organization_domains_list: ['stripe.com'],
// })) {
//   await processBatch(batch);
// }
```

### Step 5: Bulk Enrichment with Rate Awareness
Apollo's Bulk People Enrichment endpoint handles up to 10 records per call.

```typescript
// src/apollo/bulk-enrich.ts
import { getApolloClient } from './client';
import { withRetry } from './retry';

interface EnrichmentDetail {
  email?: string;
  linkedin_url?: string;
  first_name?: string;
  last_name?: string;
  organization_domain?: string;
}

export async function bulkEnrichPeople(
  details: EnrichmentDetail[],
  opts: { revealPersonalEmails?: boolean; revealPhoneNumber?: boolean } = {},
): Promise<any[]> {
  const client = getApolloClient();
  const results: any[] = [];

  // Apollo bulk endpoint accepts max 10 at a time
  for (let i = 0; i < details.length; i += 10) {
    const batch = details.slice(i, i + 10);

    const { data } = await withRetry(() =>
      client.post('/people/bulk_match', {
        details: batch,
        reveal_personal_emails: opts.revealPersonalEmails ?? false,
        reveal_phone_number: opts.revealPhoneNumber ?? false,
      }),
    );

    results.push(...(data.matches ?? []));

    // Brief pause between batches to respect rate limits
    if (i + 10 < details.length) {
      await new Promise((r) => setTimeout(r, 500));
    }
  }

  return results;
}
```

## Output
- `src/apollo/client.ts` — Zod-validated singleton with `x-api-key` header
- `src/apollo/errors.ts` — `ApolloApiError` + `ApolloRateLimitError` with retryable flag
- `src/apollo/retry.ts` — Exponential backoff with jitter
- `src/apollo/paginator.ts` — Async generator for paginated endpoints (500-page limit)
- `src/apollo/bulk-enrich.ts` — Batch enrichment via `/people/bulk_match` (10 per call)

## Error Handling
| Pattern | When to Use |
|---------|-------------|
| Singleton client | Always — one client instance per process |
| Retry | 429 rate limits, 5xx server errors |
| Pagination | Search results > 100 records |
| Bulk enrichment | Multiple contacts need email/phone data |
| Custom errors | Typed catch blocks distinguishing auth vs rate limit vs server |

## Examples

### Full Pipeline: Search, Paginate, Enrich
```typescript
import { paginate } from './apollo/paginator';
import { bulkEnrichPeople } from './apollo/bulk-enrich';

async function enrichLeadsAtCompany(domain: string) {
  const allPeople: any[] = [];
  for await (const batch of paginate('/mixed_people/api_search', {
    q_organization_domains_list: [domain],
    person_seniorities: ['vp', 'director', 'c_suite'],
  })) {
    allPeople.push(...batch);
  }
  console.log(`Found ${allPeople.length} decision-makers at ${domain}`);

  // Bulk enrich only those without email
  const toEnrich = allPeople
    .filter((p) => !p.email && p.linkedin_url)
    .map((p) => ({ linkedin_url: p.linkedin_url }));

  const enriched = await bulkEnrichPeople(toEnrich);
  console.log(`Enriched ${enriched.length} contacts`);
}
```

## Resources
- [Apollo API Overview](https://docs.apollo.io/docs/api-overview)
- [Bulk People Enrichment](https://docs.apollo.io/reference/bulk-people-enrichment)
- [Zod Schema Validation](https://zod.dev/)

## Next Steps
Proceed to `apollo-core-workflow-a` for lead search implementation.
