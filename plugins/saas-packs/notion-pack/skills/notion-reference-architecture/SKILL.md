---
name: notion-reference-architecture
description: |
  Implement a production-ready Notion integration architecture with proper layering.
  Use when designing new Notion integrations, reviewing project structure,
  or establishing architecture standards for Notion applications.
  Trigger with phrases like "notion architecture", "notion project structure",
  "how to organize notion", "notion layout", "notion reference architecture".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Reference Architecture

## Overview
Production-ready architecture for Notion integrations with proper layering: API client, service layer, caching, error handling, and testing.

## Prerequisites
- `@notionhq/client` installed
- TypeScript project with strict mode
- Understanding of your integration requirements

## Instructions

### Step 1: Project Structure
```
my-notion-integration/
├── src/
│   ├── notion/
│   │   ├── client.ts           # Singleton client, retry config
│   │   ├── types.ts            # Typed wrappers for properties
│   │   ├── extractors.ts       # Property value extraction helpers
│   │   └── errors.ts           # Error classification
│   ├── services/
│   │   ├── database.service.ts # Business logic for database operations
│   │   ├── page.service.ts     # Page CRUD operations
│   │   └── sync.service.ts     # Sync/polling logic
│   ├── api/
│   │   ├── routes.ts           # Express/Next.js routes
│   │   └── webhooks.ts         # Webhook handler
│   ├── cache/
│   │   └── notion-cache.ts     # LRU or Redis cache layer
│   └── index.ts
├── tests/
│   ├── unit/
│   │   ├── extractors.test.ts
│   │   └── database.service.test.ts
│   └── integration/
│       └── notion-api.test.ts
├── .env.example
└── package.json
```

### Step 2: Client Layer
```typescript
// src/notion/client.ts
import { Client, LogLevel } from '@notionhq/client';

let client: Client | null = null;

export function getNotionClient(): Client {
  if (!client) {
    if (!process.env.NOTION_TOKEN) {
      throw new Error('NOTION_TOKEN required');
    }
    client = new Client({
      auth: process.env.NOTION_TOKEN,
      logLevel: process.env.NODE_ENV === 'development' ? LogLevel.DEBUG : LogLevel.WARN,
      timeoutMs: 30_000,
    });
  }
  return client;
}

// For testing — allow client injection
export function setNotionClient(mockClient: Client) {
  client = mockClient;
}
```

### Step 3: Type-Safe Property Extractors
```typescript
// src/notion/extractors.ts
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

export function extractTitle(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'title' ? p.title.map(t => t.plain_text).join('') : '';
}

export function extractSelect(page: PageObjectResponse, prop: string): string | null {
  const p = page.properties[prop];
  return p?.type === 'select' ? p.select?.name ?? null : null;
}

export function extractMultiSelect(page: PageObjectResponse, prop: string): string[] {
  const p = page.properties[prop];
  return p?.type === 'multi_select' ? p.multi_select.map(s => s.name) : [];
}

export function extractNumber(page: PageObjectResponse, prop: string): number | null {
  const p = page.properties[prop];
  return p?.type === 'number' ? p.number : null;
}

export function extractDate(page: PageObjectResponse, prop: string): { start: string; end: string | null } | null {
  const p = page.properties[prop];
  return p?.type === 'date' && p.date ? { start: p.date.start, end: p.date.end } : null;
}

export function extractCheckbox(page: PageObjectResponse, prop: string): boolean {
  const p = page.properties[prop];
  return p?.type === 'checkbox' ? p.checkbox : false;
}

export function extractRichText(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'rich_text' ? p.rich_text.map(t => t.plain_text).join('') : '';
}

export function extractRelation(page: PageObjectResponse, prop: string): string[] {
  const p = page.properties[prop];
  return p?.type === 'relation' ? p.relation.map(r => r.id) : [];
}
```

### Step 4: Service Layer
```typescript
// src/services/database.service.ts
import { getNotionClient } from '../notion/client';
import { extractTitle, extractSelect } from '../notion/extractors';
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

export interface TaskItem {
  id: string;
  title: string;
  status: string | null;
  url: string;
  lastEdited: string;
}

export class DatabaseService {
  private notion = getNotionClient();

  async queryTasks(dbId: string, statusFilter?: string): Promise<TaskItem[]> {
    const filter = statusFilter
      ? { property: 'Status', select: { equals: statusFilter } }
      : undefined;

    const pages: PageObjectResponse[] = [];
    let cursor: string | undefined;

    do {
      const response = await this.notion.databases.query({
        database_id: dbId,
        filter,
        sorts: [{ property: 'Created', direction: 'descending' }],
        page_size: 100,
        start_cursor: cursor,
      });

      for (const result of response.results) {
        if ('properties' in result) {
          pages.push(result as PageObjectResponse);
        }
      }

      cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
    } while (cursor);

    return pages.map(page => ({
      id: page.id,
      title: extractTitle(page, 'Name'),
      status: extractSelect(page, 'Status'),
      url: page.url,
      lastEdited: page.last_edited_time,
    }));
  }

  async createTask(dbId: string, title: string, status?: string) {
    const properties: any = {
      Name: { title: [{ text: { content: title } }] },
    };
    if (status) {
      properties.Status = { select: { name: status } };
    }

    return this.notion.pages.create({
      parent: { database_id: dbId },
      properties,
    });
  }

  async updateStatus(pageId: string, status: string) {
    return this.notion.pages.update({
      page_id: pageId,
      properties: { Status: { select: { name: status } } },
    });
  }
}
```

### Step 5: Error Classification
```typescript
// src/notion/errors.ts
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

export type NotionErrorType = 'auth' | 'not_found' | 'validation' | 'rate_limit' | 'server' | 'unknown';

export function classifyError(error: unknown): { type: NotionErrorType; message: string; retryable: boolean } {
  if (!isNotionClientError(error)) {
    return { type: 'unknown', message: String(error), retryable: false };
  }

  switch (error.code) {
    case APIErrorCode.Unauthorized:
      return { type: 'auth', message: 'Invalid token', retryable: false };
    case APIErrorCode.ObjectNotFound:
      return { type: 'not_found', message: 'Resource not found or not shared', retryable: false };
    case APIErrorCode.ValidationError:
      return { type: 'validation', message: error.message, retryable: false };
    case APIErrorCode.RateLimited:
      return { type: 'rate_limit', message: 'Rate limited', retryable: true };
    case APIErrorCode.InternalServerError:
    case APIErrorCode.ServiceUnavailable:
      return { type: 'server', message: error.message, retryable: true };
    default:
      return { type: 'unknown', message: error.message, retryable: false };
  }
}
```

### Step 6: Data Flow

```
Client Request
     │
     ▼
┌──────────────┐
│  API Routes  │  ← Express/Next.js handlers
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐
│   Service    │───▶│    Cache     │  ← LRU / Redis
│    Layer     │    │    Layer     │
└──────┬───────┘    └──────────────┘
       │
       ▼
┌──────────────┐
│   Notion     │  ← @notionhq/client singleton
│   Client     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Notion API  │  ← api.notion.com
└──────────────┘
```

## Output
- Layered project structure with separation of concerns
- Type-safe property extractors for all common types
- Service layer with business logic
- Error classification for consistent handling

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layer imports | Only import downward |
| Property type mismatch | Schema changed in Notion | Use `databases.retrieve` to verify |
| Test isolation | Shared singleton | Use `setNotionClient` for injection |
| Missing types | SDK version mismatch | Update `@notionhq/client` |

## Examples

### Quick Setup
```bash
mkdir -p src/{notion,services,api,cache} tests/{unit,integration}
touch src/notion/{client,types,extractors,errors}.ts
touch src/services/{database,page,sync}.service.ts
```

## Resources
- [Notion API Reference](https://developers.notion.com/reference/intro)
- [@notionhq/client TypeScript Types](https://github.com/makenotion/notion-sdk-js)
- [Working with Databases](https://developers.notion.com/docs/working-with-databases)

## Next Steps
For multi-environment setup, see `notion-multi-env-setup`.
