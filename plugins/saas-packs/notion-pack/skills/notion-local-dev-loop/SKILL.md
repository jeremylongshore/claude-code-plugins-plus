---
name: notion-local-dev-loop
description: |
  Configure Notion local development with hot reload, testing, and mocks.
  Use when setting up a development environment, writing tests for Notion code,
  or establishing a fast iteration cycle with the Notion API.
  Trigger with phrases like "notion dev setup", "notion local development",
  "notion test", "develop with notion", "mock notion".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Notion integrations with type-safe client, test mocking, and hot reload.

## Prerequisites
- Completed `notion-install-auth` setup
- Node.js 18+ with npm/pnpm
- TypeScript configured

## Instructions

### Step 1: Project Structure
```
my-notion-project/
├── src/
│   ├── notion/
│   │   ├── client.ts       # Singleton client
│   │   ├── queries.ts      # Database query functions
│   │   └── helpers.ts      # Property extractors, rich text builders
│   └── index.ts
├── tests/
│   ├── notion.test.ts      # Unit tests with mocks
│   └── integration.test.ts # Live API tests (uses real token)
├── .env                    # NOTION_TOKEN (git-ignored)
├── .env.example            # Template for team
├── .gitignore
├── package.json
└── tsconfig.json
```

### Step 2: Package Setup
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "INTEGRATION=true vitest run tests/integration.test.ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@notionhq/client": "^2.2.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^2.0.0",
    "dotenv": "^16.0.0"
  }
}
```

### Step 3: Environment Setup
```bash
# Copy template
cp .env.example .env

# .env.example contents:
# NOTION_TOKEN=ntn_your_token_here
# NOTION_TEST_DATABASE_ID=your_test_db_id
# NOTION_TEST_PAGE_ID=your_test_page_id

# Install and run
npm install
npm run dev
```

### Step 4: Unit Tests with Mocked Client
```typescript
// tests/notion.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Client } from '@notionhq/client';

// Mock the entire @notionhq/client module
vi.mock('@notionhq/client', () => ({
  Client: vi.fn().mockImplementation(() => ({
    databases: {
      query: vi.fn(),
      retrieve: vi.fn(),
    },
    pages: {
      create: vi.fn(),
      update: vi.fn(),
      retrieve: vi.fn(),
    },
    blocks: {
      children: {
        list: vi.fn(),
        append: vi.fn(),
      },
    },
    search: vi.fn(),
    users: { list: vi.fn() },
  })),
  isNotionClientError: vi.fn(),
}));

describe('Database Queries', () => {
  let notion: any;

  beforeEach(() => {
    notion = new Client({ auth: 'test-token' });
  });

  it('should query database with status filter', async () => {
    notion.databases.query.mockResolvedValue({
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
    });

    const result = await notion.databases.query({
      database_id: 'test-db',
      filter: { property: 'Status', select: { equals: 'Done' } },
    });

    expect(result.results).toHaveLength(1);
    expect(notion.databases.query).toHaveBeenCalledWith(
      expect.objectContaining({
        filter: { property: 'Status', select: { equals: 'Done' } },
      })
    );
  });

  it('should handle pagination', async () => {
    notion.databases.query
      .mockResolvedValueOnce({
        results: [{ id: '1' }],
        has_more: true,
        next_cursor: 'cursor-1',
      })
      .mockResolvedValueOnce({
        results: [{ id: '2' }],
        has_more: false,
        next_cursor: null,
      });

    // First call
    const page1 = await notion.databases.query({ database_id: 'db' });
    expect(page1.has_more).toBe(true);

    // Second call with cursor
    const page2 = await notion.databases.query({
      database_id: 'db',
      start_cursor: page1.next_cursor,
    });
    expect(page2.has_more).toBe(false);
  });
});
```

### Step 5: Integration Tests (Live API)
```typescript
// tests/integration.test.ts
import { describe, it, expect } from 'vitest';
import { Client } from '@notionhq/client';

const SKIP = !process.env.INTEGRATION;

describe.skipIf(SKIP)('Notion Integration', () => {
  const notion = new Client({ auth: process.env.NOTION_TOKEN! });
  const testDbId = process.env.NOTION_TEST_DATABASE_ID!;

  it('should connect and list users', async () => {
    const { results } = await notion.users.list({});
    expect(results.length).toBeGreaterThan(0);
  });

  it('should query test database', async () => {
    const response = await notion.databases.query({
      database_id: testDbId,
      page_size: 1,
    });
    expect(response.results).toBeDefined();
  });

  it('should create and archive a test page', async () => {
    const page = await notion.pages.create({
      parent: { database_id: testDbId },
      properties: {
        Name: { title: [{ text: { content: `Test ${Date.now()}` } }] },
      },
    });
    expect(page.id).toBeTruthy();

    // Clean up
    await notion.pages.update({ page_id: page.id, archived: true });
  });
});
```

### Step 6: Vitest Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    setupFiles: ['dotenv/config'],
    testTimeout: 30_000, // Notion API can be slow
  },
});
```

## Output
- Working development environment with hot reload via `tsx watch`
- Unit tests with fully mocked Notion client
- Integration tests gated behind `INTEGRATION=true`
- Type checking with `tsc --noEmit`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `NOTION_TOKEN undefined` | Missing .env file | Copy from .env.example |
| Mock not working | Import order | Ensure `vi.mock` is at top of test file |
| Integration test 404 | Test DB not shared | Add integration to test database |
| Timeout in tests | Slow API | Increase `testTimeout` in vitest config |

## Examples

### Quick Smoke Test
```bash
# One-line connection test
NOTION_TOKEN=ntn_xxx npx tsx -e "
  const { Client } = require('@notionhq/client');
  new Client({ auth: process.env.NOTION_TOKEN })
    .users.list({}).then(r => console.log('OK:', r.results.length, 'users'));
"
```

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)

## Next Steps
See `notion-sdk-patterns` for production-ready code patterns.
