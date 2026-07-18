# Notion Reference Architecture — Full Implementation

This reference carries the complete, copy-ready code for the four-layer Notion
architecture summarized in `SKILL.md`. Follow it in order: project layout →
client singleton → repository layer → service layer → cache layer.

## Project layout

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

## Step 1: Client singleton with retry and rate limiting

The client layer wraps `@notionhq/client` in a singleton pattern with built-in retry logic. Notion's SDK handles basic retries, but you need explicit rate limiting and configurable timeouts for production use.

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

## Step 2: Repository and service layers

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

## Step 3: Caching layer between app and Notion API

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

## Step 4: Event-driven processing and testing

Continue to [event-driven processing and testing patterns](event-driven-and-testing.md)
for the event queue, polling-based change detection, unit tests with a mocked
`@notionhq/client`, live integration tests, the headless CMS pattern, the
project tracker example, and the multi-integration architecture.
