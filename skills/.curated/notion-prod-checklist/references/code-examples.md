# Notion Production Checklist — Code Examples

## Access Verification Script

Programmatically verify all target databases and pages are shared with the integration before deployment.

```typescript
async function verifyAccess(notion: Client, targets: { id: string; type: 'database' | 'page' }[]) {
  const results: { id: string; type: string; accessible: boolean; error?: string }[] = [];

  for (const target of targets) {
    try {
      if (target.type === 'database') {
        await notion.databases.retrieve({ database_id: target.id });
      } else {
        await notion.pages.retrieve({ page_id: target.id });
      }
      results.push({ ...target, accessible: true });
    } catch (error) {
      results.push({
        ...target,
        accessible: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  const failures = results.filter((r) => !r.accessible);
  if (failures.length > 0) {
    console.error('ACCESS FAILURES:', JSON.stringify(failures, null, 2));
    throw new Error(`${failures.length} target(s) not accessible — share them with the integration`);
  }

  console.log(`All ${results.length} targets accessible`);
}
```

## Rate-Limited Queue Setup

Enforce Notion's 3 req/sec limit using `p-queue` with interval-based concurrency control.

```typescript
import PQueue from 'p-queue';

// Enforce Notion's 3 req/sec limit
const notionQueue = new PQueue({
  intervalCap: 3,
  interval: 1000,
  carryoverConcurrencyCount: true,
});

// All Notion calls go through the queue
async function queryDatabase(databaseId: string, filter?: any) {
  return notionQueue.add(() =>
    notion.databases.query({
      database_id: databaseId,
      filter,
    })
  );
}

// Bulk operations — safe even with 500+ items
async function createManyPages(pages: CreatePageParams[]) {
  const results = [];
  for (const page of pages) {
    const result = await notionQueue.add(() => notion.pages.create(page));
    results.push(result);
  }
  return results;
}
```

## Generic Paginator

Handle pagination for any Notion list endpoint, collecting all results across multiple pages.

```typescript
async function collectAllPages<T>(
  queryFn: (cursor?: string) => Promise<{ results: T[]; has_more: boolean; next_cursor: string | null }>
): Promise<T[]> {
  const allResults: T[] = [];
  let cursor: string | undefined = undefined;

  do {
    const response = await notionQueue.add(() => queryFn(cursor));
    allResults.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return allResults;
}

// Usage: get ALL items from a database (not just first 100)
const allItems = await collectAllPages((cursor) =>
  notion.databases.query({
    database_id: dbId,
    start_cursor: cursor,
    page_size: 100,
  })
);
```

## Typed Error Handler

Use `isNotionClientError` for discriminated error handling with specific responses per error code.

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function safeDatabaseQuery(databaseId: string) {
  try {
    return await notion.databases.query({ database_id: databaseId });
  } catch (error) {
    if (isNotionClientError(error)) {
      switch (error.code) {
        case APIErrorCode.ObjectNotFound:
          console.error(`Database ${databaseId} not found — verify sharing`);
          return null;

        case APIErrorCode.ValidationError:
          console.error(`Validation error: ${error.message}`);
          throw error;

        case APIErrorCode.Unauthorized:
          console.error('CRITICAL: Notion token unauthorized — alert ops team');
          throw error;

        case APIErrorCode.RateLimited:
          console.warn('Rate limited — SDK retry may have been exhausted');
          throw error;

        case APIErrorCode.RestrictedResource:
          console.error('Integration missing capability for this operation');
          throw error;

        default:
          console.error(`Notion API error: ${error.code} — ${error.message}`);
          throw error;
      }
    }

    console.error('Non-API error calling Notion:', error);
    throw error;
  }
}
```

## Retry with Exponential Backoff

For custom HTTP clients or edge cases where SDK retry is insufficient.

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const status = error?.status;
      const retryable = [429, 500, 502, 503].includes(status);

      if (!retryable || attempt === maxRetries) {
        throw error;
      }

      const retryAfter = error?.headers?.['retry-after'];
      const delayMs = retryAfter
        ? parseInt(retryAfter, 10) * 1000
        : baseDelayMs * Math.pow(2, attempt);

      console.warn(`Retrying in ${delayMs}ms (attempt ${attempt + 1}/${maxRetries}, status ${status})`);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw new Error('Unreachable');
}
```

## Cache with Fallback (Graceful Degradation)

Serve cached data when Notion is unavailable, with source tracking for transparency.

```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 10,  // 10 minutes
});

async function queryWithFallback(databaseId: string, filter?: any) {
  const cacheKey = `db:${databaseId}:${JSON.stringify(filter)}`;

  try {
    const result = await notion.databases.query({ database_id: databaseId, filter });
    cache.set(cacheKey, result);
    return { data: result, source: 'live' as const };
  } catch (error) {
    const cached = cache.get(cacheKey);
    if (cached) {
      console.warn(`Notion unavailable — serving cached data for ${databaseId}`);
      return { data: cached, source: 'cache' as const };
    }

    throw new Error(`Notion unavailable and no cached data for database ${databaseId}`);
  }
}
```

## Property Validator

Validate page properties against Notion's requirements before sending API requests.

```typescript
function validatePageProperties(properties: Record<string, any>): string[] {
  const errors: string[] = [];

  for (const [name, prop] of Object.entries(properties)) {
    if (prop.type === 'title' && (!prop.title || prop.title.length === 0)) {
      errors.push(`${name}: title cannot be empty`);
    }

    if (prop.type === 'rich_text' && Array.isArray(prop.rich_text) && prop.rich_text.length === 0) {
      errors.push(`${name}: rich_text cannot be an empty array (omit the property instead)`);
    }

    if (prop.type === 'number' && typeof prop.number !== 'number' && prop.number !== null) {
      errors.push(`${name}: number must be a number or null, got ${typeof prop.number}`);
    }

    if (prop.type === 'date' && prop.date?.start) {
      const iso = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})?)?$/;
      if (!iso.test(prop.date.start)) {
        errors.push(`${name}: date.start must be ISO 8601 format, got "${prop.date.start}"`);
      }
    }
  }

  return errors;
}
```

## OAuth Token Exchange

For public integrations using OAuth, exchange the authorization code for an access token.

```typescript
async function exchangeCodeForToken(code: string): Promise<OAuthTokenResponse> {
  const response = await fetch('https://api.notion.com/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${Buffer.from(
        `${process.env.NOTION_OAUTH_CLIENT_ID}:${process.env.NOTION_OAUTH_CLIENT_SECRET}`
      ).toString('base64')}`,
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: process.env.NOTION_REDIRECT_URI,
    }),
  });

  if (!response.ok) {
    const body = await response.json();
    throw new Error(`OAuth exchange failed: ${body.error} — ${body.error_description}`);
  }

  return response.json();
}

interface OAuthTokenResponse {
  access_token: string;
  bot_id: string;
  workspace_id: string;
  workspace_name: string;
  owner: { type: string; user?: { id: string } };
}
```

## Full Production Initialization

Complete setup with rate limiting, version pinning, and appropriate log levels.

```typescript
import { Client, isNotionClientError, APIErrorCode, LogLevel } from '@notionhq/client';
import PQueue from 'p-queue';

function createProductionClient() {
  if (!process.env.NOTION_TOKEN) {
    throw new Error('NOTION_TOKEN environment variable is required');
  }

  const client = new Client({
    auth: process.env.NOTION_TOKEN,
    notionVersion: '2022-06-28',
    logLevel: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.DEBUG,
  });

  const queue = new PQueue({
    intervalCap: 3,
    interval: 1000,
    carryoverConcurrencyCount: true,
  });

  return { client, queue };
}

const { client: notion, queue: notionQueue } = createProductionClient();
```
