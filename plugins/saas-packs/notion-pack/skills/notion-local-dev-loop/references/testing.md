# Unit and Integration Tests

**Unit tests** mock the entire `@notionhq/client` module so they run instantly with no network
calls. **Integration tests** hit the real API but are gated behind an environment variable and
target only the dev workspace.

## Unit tests with a mocked SDK

```typescript
// tests/unit/notion.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Client } from '@notionhq/client';

vi.mock('@notionhq/client', () => ({
  Client: vi.fn().mockImplementation(() => ({
    databases: {
      query: vi.fn(),
      retrieve: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    pages: {
      create: vi.fn(),
      update: vi.fn(),
      retrieve: vi.fn(),
    },
    blocks: {
      children: { list: vi.fn(), append: vi.fn() },
      retrieve: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    search: vi.fn(),
    users: { list: vi.fn(), retrieve: vi.fn() },
  })),
  isNotionClientError: vi.fn((err) => err?.code !== undefined),
  LogLevel: { DEBUG: 'debug', WARN: 'warn' },
}));

describe('Database queries', () => {
  let notion: InstanceType<typeof Client>;

  beforeEach(() => {
    notion = new Client({ auth: 'ntn_test_token' });
  });

  it('queries database with a status filter', async () => {
    const mockResponse = {
      results: [
        {
          id: 'page-1',
          properties: {
            Name: { type: 'title', title: [{ plain_text: 'Task 1' }] },
            Status: { type: 'select', select: { name: 'Done' } },
          },
        },
      ],
      has_more: false,
      next_cursor: null,
    };
    (notion.databases.query as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    const result = await notion.databases.query({
      database_id: 'test-db-id',
      filter: { property: 'Status', select: { equals: 'Done' } },
    });

    expect(result.results).toHaveLength(1);
    expect(notion.databases.query).toHaveBeenCalledWith(
      expect.objectContaining({
        filter: { property: 'Status', select: { equals: 'Done' } },
      })
    );
  });

  it('handles pagination across multiple pages', async () => {
    const queryMock = notion.databases.query as ReturnType<typeof vi.fn>;
    queryMock
      .mockResolvedValueOnce({ results: [{ id: '1' }], has_more: true, next_cursor: 'cursor-abc' })
      .mockResolvedValueOnce({ results: [{ id: '2' }], has_more: false, next_cursor: null });

    const page1 = await notion.databases.query({ database_id: 'db' });
    expect(page1.has_more).toBe(true);

    const page2 = await notion.databases.query({
      database_id: 'db',
      start_cursor: page1.next_cursor,
    });
    expect(page2.has_more).toBe(false);
    expect(queryMock).toHaveBeenCalledTimes(2);
  });
});
```

## Integration tests against the dev workspace

```typescript
// tests/integration/notion.test.ts
import { describe, it, expect } from 'vitest';
import { Client } from '@notionhq/client';

const SKIP = !process.env.INTEGRATION;

describe.skipIf(SKIP)('Notion Integration (live API)', () => {
  const notion = new Client({ auth: process.env.NOTION_TOKEN! });
  const testDbId = process.env.NOTION_TEST_DATABASE_ID!;

  it('connects and lists workspace users', async () => {
    const { results } = await notion.users.list({});
    expect(results.length).toBeGreaterThan(0);
  });

  it('queries the test database', async () => {
    const response = await notion.databases.query({
      database_id: testDbId,
      page_size: 1,
    });
    expect(response.results).toBeDefined();
  });

  it('creates and archives a test page (cleanup)', async () => {
    const page = await notion.pages.create({
      parent: { database_id: testDbId },
      properties: {
        Name: { title: [{ text: { content: `DevLoop Test ${Date.now()}` } }] },
      },
    });
    expect(page.id).toBeTruthy();

    // Always clean up
    await notion.pages.update({ page_id: page.id, archived: true });
  });
});
```

## Vitest configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    setupFiles: ['dotenv/config'],
    testTimeout: 30_000,  // Notion API can be slow under rate limits
    include: ['tests/**/*.test.ts'],
  },
});
```
