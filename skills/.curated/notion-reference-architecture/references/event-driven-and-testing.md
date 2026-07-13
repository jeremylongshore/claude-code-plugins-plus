# Event-Driven Processing and Testing

## Event Queue for Webhook/Polling Events

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

## Polling-Based Change Detection

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

## Testing: Mock `@notionhq/client` for Unit Tests

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

## Live Integration Tests

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

## Headless CMS Pattern

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

## Project/Task Tracker Pattern

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

## Multi-Integration Architecture

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
