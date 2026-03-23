---
name: notion-reference-architecture
description: |
  Design and implement a production-ready Notion integration architecture
  with proper layering, caching, error handling, and testing strategies.
  Use when designing new Notion integrations, reviewing existing project
  structure, establishing architecture standards for Notion applications,
  or migrating from ad-hoc API calls to a layered architecture.
  Trigger: "notion architecture", "notion project structure", "notion
  reference architecture", "notion integration design", "notion layered
  architecture", "notion service pattern".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, architecture]
compatible-with: claude-code
---

# Notion Reference Architecture

## Overview

Production-grade architecture for Notion integrations using `@notionhq/client`. This skill defines a four-layer architecture — client singleton, repository pattern, service layer, and caching — that scales from simple scripts to enterprise applications. It covers multi-integration setups (reader + writer tokens), event-driven processing, headless CMS patterns, and comprehensive testing strategies.

**Notion API version:** `2022-06-28` | **Rate limit:** 3 requests/second per integration | **Max page size:** 100

## Prerequisites

- Node.js 18+ with TypeScript strict mode enabled
- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- A Notion internal integration created at https://www.notion.so/my-integrations
- `NOTION_TOKEN` environment variable set with the integration token
- Target databases/pages shared with the integration via "Add connections"

## Instructions

### Step 1: Establish the Client Singleton with Retry and Rate Limiting

The client layer wraps `@notionhq/client` in a singleton pattern with built-in retry logic. Notion's SDK handles basic retries, but you need explicit rate limiting and configurable timeouts for production use.

```
my-notion-app/
├── src/
│   ├── notion/
│   │   ├── client.ts           # Singleton + retry + rate limiter
│   │   ├── types.ts            # Domain types mapped from Notion properties
│   │   ├── extractors.ts       # Type-safe property extraction helpers
│   │   └── errors.ts           # Error classification and retry decisions
│   ├── repositories/
│   │   ├── database.repo.ts    # NotionDatabaseRepo — query/create/update
│   │   └── page.repo.ts        # NotionPageRepo — page CRUD + blocks
│   ├── services/
│   │   ├── notion.service.ts   # NotionService — business logic orchestration
│   │   ├── sync.service.ts     # Polling/webhook sync coordination
│   │   └── cms.service.ts      # Headless CMS content retrieval
│   ├── cache/
│   │   └── notion-cache.ts     # TTL cache between app and Notion API
│   ├── events/
│   │   ├── queue.ts            # Event queue for webhook/polling events
│   │   └── processors.ts       # Event handlers (page.created, page.updated)
│   └── index.ts
├── tests/
│   ├── unit/
│   │   ├── extractors.test.ts
│   │   ├── database.repo.test.ts
│   │   └── notion.service.test.ts
│   └── integration/
│       └── notion-live.test.ts
├── .env.example
└── tsconfig.json
```

Create the client singleton with rate limiting:

```typescript
// src/notion/client.ts
import { Client, LogLevel } from '@notionhq/client';

let readerClient: Client | null = null;
let writerClient: Client | null = null;

interface ClientOptions {
  token: string;
  logLevel?: LogLevel;
  timeoutMs?: number;
}

function createClient(opts: ClientOptions): Client {
  return new Client({
    auth: opts.token,
    logLevel: opts.logLevel ?? (process.env.NODE_ENV === 'development'
      ? LogLevel.DEBUG : LogLevel.WARN),
    timeoutMs: opts.timeoutMs ?? 30_000,
  });
}

// Primary client — read-heavy operations
export function getReaderClient(): Client {
  if (!readerClient) {
    const token = process.env.NOTION_READER_TOKEN ?? process.env.NOTION_TOKEN;
    if (!token) throw new Error('NOTION_TOKEN or NOTION_READER_TOKEN required');
    readerClient = createClient({ token });
  }
  return readerClient;
}

// Writer client — separate integration with write permissions
export function getWriterClient(): Client {
  if (!writerClient) {
    const token = process.env.NOTION_WRITER_TOKEN ?? process.env.NOTION_TOKEN;
    if (!token) throw new Error('NOTION_TOKEN or NOTION_WRITER_TOKEN required');
    writerClient = createClient({ token });
  }
  return writerClient;
}

// Simple rate limiter: 3 req/s per integration (Notion's limit)
const requestTimestamps: number[] = [];
const MAX_REQUESTS_PER_SECOND = 3;

export async function rateLimitedCall<T>(fn: () => Promise<T>): Promise<T> {
  const now = Date.now();
  // Remove timestamps older than 1 second
  while (requestTimestamps.length > 0 && requestTimestamps[0] < now - 1000) {
    requestTimestamps.shift();
  }
  if (requestTimestamps.length >= MAX_REQUESTS_PER_SECOND) {
    const waitMs = 1000 - (now - requestTimestamps[0]);
    await new Promise(resolve => setTimeout(resolve, waitMs));
  }
  requestTimestamps.push(Date.now());
  return fn();
}

// Retry wrapper with exponential backoff
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 500,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await rateLimitedCall(fn);
    } catch (error: any) {
      const isRetryable = error?.code === 'rate_limited'
        || error?.code === 'internal_server_error'
        || error?.code === 'service_unavailable';
      if (!isRetryable || attempt === maxRetries) throw error;
      const delay = baseDelayMs * Math.pow(2, attempt);
      const retryAfter = error?.headers?.['retry-after'];
      const waitMs = retryAfter ? parseInt(retryAfter) * 1000 : delay;
      await new Promise(resolve => setTimeout(resolve, waitMs));
    }
  }
  throw new Error('Unreachable');
}

// For testing — inject mock clients
export function _setClients(reader: Client | null, writer?: Client | null) {
  readerClient = reader;
  writerClient = writer ?? reader;
}
```

### Step 2: Build the Repository and Service Layers

The repository layer wraps raw Notion API calls with pagination, type extraction, and error handling. The service layer sits above it with business logic, caching, and cross-repository coordination.

**Repository pattern — NotionDatabaseRepo:**

```typescript
// src/repositories/database.repo.ts
import { getReaderClient, getWriterClient, withRetry } from '../notion/client';
import { extractTitle, extractSelect, extractRichText, extractDate }
  from '../notion/extractors';
import type { PageObjectResponse, QueryDatabaseParameters }
  from '@notionhq/client/build/src/api-endpoints';

export interface DatabaseRecord {
  id: string;
  title: string;
  status: string | null;
  description: string;
  dueDate: { start: string; end: string | null } | null;
  url: string;
  lastEdited: string;
}

export class NotionDatabaseRepo {
  // Paginate through all results (Notion caps at 100 per request)
  async queryAll(
    databaseId: string,
    filter?: QueryDatabaseParameters['filter'],
    sorts?: QueryDatabaseParameters['sorts'],
  ): Promise<PageObjectResponse[]> {
    const reader = getReaderClient();
    const pages: PageObjectResponse[] = [];
    let cursor: string | undefined;

    do {
      const response = await withRetry(() =>
        reader.databases.query({
          database_id: databaseId,
          filter,
          sorts: sorts ?? [{ timestamp: 'last_edited_time', direction: 'descending' }],
          page_size: 100,
          start_cursor: cursor,
        })
      );
      for (const result of response.results) {
        if ('properties' in result) {
          pages.push(result as PageObjectResponse);
        }
      }
      cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
    } while (cursor);

    return pages;
  }

  // Map raw Notion pages to typed domain objects
  async getRecords(databaseId: string, statusFilter?: string): Promise<DatabaseRecord[]> {
    const filter = statusFilter
      ? { property: 'Status', select: { equals: statusFilter } }
      : undefined;

    const pages = await this.queryAll(databaseId, filter);
    return pages.map(page => ({
      id: page.id,
      title: extractTitle(page, 'Name'),
      status: extractSelect(page, 'Status'),
      description: extractRichText(page, 'Description'),
      dueDate: extractDate(page, 'Due Date'),
      url: page.url,
      lastEdited: page.last_edited_time,
    }));
  }

  // Create a new page in the database
  async create(
    databaseId: string,
    properties: Record<string, any>,
  ): Promise<string> {
    const writer = getWriterClient();
    const response = await withRetry(() =>
      writer.pages.create({
        parent: { database_id: databaseId },
        properties,
      })
    );
    return response.id;
  }

  // Retrieve the database schema (property names, types, options)
  async getSchema(databaseId: string) {
    const reader = getReaderClient();
    const db = await withRetry(() =>
      reader.databases.retrieve({ database_id: databaseId })
    );
    if (!('properties' in db)) throw new Error('Partial database response');
    return db.properties;
  }
}
```

**Service layer — NotionService with business logic:**

```typescript
// src/services/notion.service.ts
import { NotionDatabaseRepo, type DatabaseRecord } from '../repositories/database.repo';
import { NotionCache } from '../cache/notion-cache';

export class NotionService {
  private dbRepo = new NotionDatabaseRepo();
  private cache = new NotionCache();

  // Business logic: get active tasks with caching
  async getActiveTasks(databaseId: string): Promise<DatabaseRecord[]> {
    const cacheKey = `active-tasks:${databaseId}`;
    const cached = this.cache.get<DatabaseRecord[]>(cacheKey);
    if (cached) return cached;

    const records = await this.dbRepo.getRecords(databaseId, 'In Progress');
    this.cache.set(cacheKey, records, 60_000); // 60s TTL
    return records;
  }

  // Business logic: create task with validation
  async createTask(
    databaseId: string,
    title: string,
    options?: { status?: string; dueDate?: string; assignee?: string },
  ): Promise<string> {
    if (!title.trim()) throw new Error('Task title cannot be empty');

    const properties: Record<string, any> = {
      Name: { title: [{ text: { content: title.trim() } }] },
    };
    if (options?.status) {
      properties.Status = { select: { name: options.status } };
    }
    if (options?.dueDate) {
      properties['Due Date'] = { date: { start: options.dueDate } };
    }

    const pageId = await this.dbRepo.create(databaseId, properties);
    // Invalidate cache after write
    this.cache.delete(`active-tasks:${databaseId}`);
    return pageId;
  }

  // Business logic: validate schema before bulk operations
  async validateSchema(databaseId: string, requiredProps: string[]): Promise<{
    valid: boolean;
    missing: string[];
  }> {
    const schema = await this.dbRepo.getSchema(databaseId);
    const propNames = Object.keys(schema);
    const missing = requiredProps.filter(p => !propNames.includes(p));
    return { valid: missing.length === 0, missing };
  }
}
```

**Caching layer between app and Notion API:**

```typescript
// src/cache/notion-cache.ts
interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

export class NotionCache {
  private store = new Map<string, CacheEntry<any>>();

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data;
  }

  set<T>(key: string, data: T, ttlMs: number = 60_000): void {
    this.store.set(key, { data, expiresAt: Date.now() + ttlMs });
  }

  delete(key: string): void {
    this.store.delete(key);
  }

  // Invalidate all entries matching a prefix
  invalidatePrefix(prefix: string): void {
    for (const key of this.store.keys()) {
      if (key.startsWith(prefix)) this.store.delete(key);
    }
  }

  clear(): void {
    this.store.clear();
  }
}
```

### Step 3: Add Event-Driven Processing and Testing

**Event queue for webhook/polling events:**

Notion does not provide native webhooks (as of API version 2022-06-28). Use polling with `last_edited_time` filters, or integrate a third-party webhook relay service.

```typescript
// src/events/queue.ts
export type NotionEvent = {
  type: 'page.created' | 'page.updated' | 'page.archived';
  pageId: string;
  databaseId: string;
  timestamp: string;
};

type EventHandler = (event: NotionEvent) => Promise<void>;

export class EventQueue {
  private handlers = new Map<string, EventHandler[]>();

  on(eventType: NotionEvent['type'], handler: EventHandler): void {
    const existing = this.handlers.get(eventType) ?? [];
    existing.push(handler);
    this.handlers.set(eventType, existing);
  }

  async emit(event: NotionEvent): Promise<void> {
    const handlers = this.handlers.get(event.type) ?? [];
    await Promise.allSettled(handlers.map(h => h(event)));
  }
}

// src/events/processors.ts
import { EventQueue, type NotionEvent } from './queue';
import { getReaderClient } from '../notion/client';

export function registerProcessors(queue: EventQueue): void {
  queue.on('page.updated', async (event: NotionEvent) => {
    const reader = getReaderClient();
    const page = await reader.pages.retrieve({ page_id: event.pageId });
    console.log(`Page updated: ${event.pageId}`, page);
    // Business logic: sync to external system, send notification, etc.
  });

  queue.on('page.created', async (event: NotionEvent) => {
    console.log(`New page created: ${event.pageId} in ${event.databaseId}`);
    // Business logic: auto-assign, validate required fields, etc.
  });
}
```

**Polling-based change detection (since Notion lacks native webhooks):**

```typescript
// src/services/sync.service.ts
import { NotionDatabaseRepo } from '../repositories/database.repo';
import { EventQueue } from '../events/queue';

export class SyncService {
  private dbRepo = new NotionDatabaseRepo();
  private lastSyncTime: string;
  private knownPageIds = new Set<string>();

  constructor(
    private databaseId: string,
    private eventQueue: EventQueue,
  ) {
    this.lastSyncTime = new Date().toISOString();
  }

  async poll(): Promise<number> {
    const pages = await this.dbRepo.queryAll(this.databaseId, {
      timestamp: 'last_edited_time',
      last_edited_time: { after: this.lastSyncTime },
    });

    let emitted = 0;
    for (const page of pages) {
      const eventType = this.knownPageIds.has(page.id) ? 'page.updated' : 'page.created';
      await this.eventQueue.emit({
        type: eventType,
        pageId: page.id,
        databaseId: this.databaseId,
        timestamp: page.last_edited_time,
      });
      this.knownPageIds.add(page.id);
      emitted++;
    }

    this.lastSyncTime = new Date().toISOString();
    return emitted;
  }

  // Start polling at a fixed interval (respects 3 req/s rate limit)
  startPolling(intervalMs: number = 10_000): NodeJS.Timeout {
    return setInterval(() => this.poll().catch(console.error), intervalMs);
  }
}
```

**Testing: Mock `@notionhq/client` for unit tests:**

```typescript
// tests/unit/database.repo.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NotionDatabaseRepo } from '../../src/repositories/database.repo';
import { _setClients } from '../../src/notion/client';

// Mock the Notion client
function createMockClient(queryResponse: any) {
  return {
    databases: {
      query: vi.fn().mockResolvedValue(queryResponse),
      retrieve: vi.fn(),
    },
    pages: {
      create: vi.fn().mockResolvedValue({ id: 'new-page-id' }),
      update: vi.fn(),
      retrieve: vi.fn(),
    },
    users: { me: vi.fn() },
  } as any;
}

describe('NotionDatabaseRepo', () => {
  let repo: NotionDatabaseRepo;

  beforeEach(() => {
    const mockClient = createMockClient({
      results: [
        {
          id: 'page-1',
          properties: {
            Name: { type: 'title', title: [{ plain_text: 'Task One' }] },
            Status: { type: 'select', select: { name: 'In Progress' } },
            Description: { type: 'rich_text', rich_text: [] },
            'Due Date': { type: 'date', date: null },
          },
          url: 'https://notion.so/page-1',
          last_edited_time: '2025-01-01T00:00:00.000Z',
        },
      ],
      has_more: false,
      next_cursor: null,
    });
    _setClients(mockClient);
    repo = new NotionDatabaseRepo();
  });

  it('queries and maps database records', async () => {
    const records = await repo.getRecords('db-123');
    expect(records).toHaveLength(1);
    expect(records[0].title).toBe('Task One');
    expect(records[0].status).toBe('In Progress');
  });

  it('creates a page and returns the new ID', async () => {
    const pageId = await repo.create('db-123', {
      Name: { title: [{ text: { content: 'New Task' } }] },
    });
    expect(pageId).toBe('new-page-id');
  });
});
```

**Live integration tests (run against real Notion API):**

```typescript
// tests/integration/notion-live.test.ts
import { describe, it, expect } from 'vitest';
import { NotionService } from '../../src/services/notion.service';

// Only runs when NOTION_TOKEN and TEST_DATABASE_ID are set
const SKIP = !process.env.NOTION_TOKEN || !process.env.TEST_DATABASE_ID;

describe.skipIf(SKIP)('Notion Live Integration', () => {
  const service = new NotionService();
  const dbId = process.env.TEST_DATABASE_ID!;

  it('validates database schema', async () => {
    const result = await service.validateSchema(dbId, ['Name', 'Status']);
    expect(result.valid).toBe(true);
  });

  it('creates and retrieves a task', async () => {
    const pageId = await service.createTask(dbId, `Test ${Date.now()}`, {
      status: 'Not Started',
    });
    expect(pageId).toBeTruthy();
  });
});
```

## Output

After applying this architecture you will have:

- **Client singleton** with separate reader/writer integrations, rate limiting (3 req/s), and exponential backoff retry
- **Repository layer** (`NotionDatabaseRepo`) encapsulating all Notion API calls with automatic pagination
- **Service layer** (`NotionService`) with business logic, schema validation, and cache-aware operations
- **TTL cache** between your application and the Notion API, reducing redundant reads
- **Event-driven processing** with polling-based change detection and typed event handlers
- **Test suite** with mocked `@notionhq/client` for fast unit tests and conditional live integration tests

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired integration token | Verify `NOTION_TOKEN` at https://www.notion.so/my-integrations; tokens do not expire but can be regenerated |
| `404 object_not_found` | Page/database not shared with integration | In Notion, click "..." on the page, select "Add connections", and add your integration |
| `400 validation_error: property not found` | Property name mismatch (case-sensitive) | Call `databases.retrieve()` first to get exact property names; use schema validation before bulk ops |
| `429 rate_limited` | Exceeded 3 req/s per integration | The `withRetry` wrapper handles this automatically; for sustained throughput, use separate reader/writer integrations to double capacity |
| `502/503 server errors` | Notion service degradation | Check https://status.notion.so; the retry wrapper auto-recovers with backoff |
| Stale cache data | Cache TTL too long for write-heavy workloads | Invalidate on writes (shown in `NotionService.createTask`); reduce TTL for volatile databases |
| Polling misses changes | Poll interval too wide or clock skew | Use 10s intervals; store `last_edited_time` from the most recent page, not system clock |

## Examples

### Notion as Headless CMS

Use Notion databases as a content management system, fetching published content through the API for rendering in your application:

```typescript
// src/services/cms.service.ts
import { NotionDatabaseRepo } from '../repositories/database.repo';
import { NotionCache } from '../cache/notion-cache';
import { getReaderClient, withRetry } from '../notion/client';
import type { BlockObjectResponse } from '@notionhq/client/build/src/api-endpoints';

export class NotionCmsService {
  private dbRepo = new NotionDatabaseRepo();
  private cache = new NotionCache();
  private reader = getReaderClient();

  // Fetch published articles from a "Content" database
  async getPublishedArticles(contentDbId: string) {
    const cacheKey = `cms:published:${contentDbId}`;
    const cached = this.cache.get(cacheKey);
    if (cached) return cached;

    const pages = await this.dbRepo.queryAll(contentDbId, {
      property: 'Status',
      select: { equals: 'Published' },
    });

    const articles = pages.map(page => ({
      id: page.id,
      slug: page.url.split('-').pop(),
      lastUpdated: page.last_edited_time,
    }));

    this.cache.set(cacheKey, articles, 300_000); // 5min TTL for CMS content
    return articles;
  }

  // Fetch all blocks (content) of a page for rendering
  async getPageBlocks(pageId: string): Promise<BlockObjectResponse[]> {
    const blocks: BlockObjectResponse[] = [];
    let cursor: string | undefined;

    do {
      const response = await withRetry(() =>
        this.reader.blocks.children.list({
          block_id: pageId,
          page_size: 100,
          start_cursor: cursor,
        })
      );
      for (const block of response.results) {
        if ('type' in block) blocks.push(block as BlockObjectResponse);
      }
      cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
    } while (cursor);

    return blocks;
  }
}
```

### Notion as Project/Task Tracker

```typescript
// Project management integration example
import { NotionService } from './services/notion.service';

const service = new NotionService();
const TASKS_DB = process.env.NOTION_TASKS_DB_ID!;

// Validate the database has required fields before starting
const { valid, missing } = await service.validateSchema(TASKS_DB, [
  'Name', 'Status', 'Due Date', 'Priority', 'Assignee',
]);
if (!valid) {
  console.error('Missing required properties:', missing);
  process.exit(1);
}

// Create a sprint's worth of tasks
const tasks = [
  { title: 'API endpoint for user profile', status: 'Not Started', dueDate: '2025-04-01' },
  { title: 'Write integration tests', status: 'Not Started', dueDate: '2025-04-03' },
  { title: 'Deploy to staging', status: 'Not Started', dueDate: '2025-04-05' },
];

for (const task of tasks) {
  const id = await service.createTask(TASKS_DB, task.title, {
    status: task.status,
    dueDate: task.dueDate,
  });
  console.log(`Created: ${task.title} → ${id}`);
}

// Fetch active work
const active = await service.getActiveTasks(TASKS_DB);
console.log(`${active.length} tasks in progress`);
```

### Multi-Integration Architecture

When a single integration's 3 req/s rate limit is insufficient, split read and write operations across separate integrations:

```bash
# .env.example
# Reader integration — shared with all databases (read-only capabilities)
NOTION_READER_TOKEN=ntn_reader_xxxxxxxxxxxx

# Writer integration — shared with databases that need writes
NOTION_WRITER_TOKEN=ntn_writer_xxxxxxxxxxxx

# Fallback: single integration for simple setups
# NOTION_TOKEN=ntn_xxxxxxxxxxxx
```

This doubles your effective rate limit to 6 req/s (3 for reads + 3 for writes). The `getReaderClient()` and `getWriterClient()` functions in the client layer handle this automatically, falling back to `NOTION_TOKEN` if separate tokens are not configured.

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro) — complete endpoint documentation
- [@notionhq/client SDK](https://github.com/makenotion/notion-sdk-js) — official TypeScript/JavaScript SDK
- [Working with Databases](https://developers.notion.com/docs/working-with-databases) — filtering, sorting, pagination
- [Block Types Reference](https://developers.notion.com/reference/block) — all supported content block types
- [Authorization Guide](https://developers.notion.com/docs/authorization) — internal integrations and OAuth
- [Status Page](https://status.notion.so) — check for Notion service degradation
- [API Changelog](https://developers.notion.com/changelog) — breaking changes and new features

## Next Steps

- For environment-specific configuration, see `notion-multi-env-setup`
- For webhook and polling patterns in depth, see `notion-webhooks-events`
- For performance optimization, see `notion-performance-tuning`
- For error troubleshooting, see `notion-common-errors` and `notion-advanced-troubleshooting`
