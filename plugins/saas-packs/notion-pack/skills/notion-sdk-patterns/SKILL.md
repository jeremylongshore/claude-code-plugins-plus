---
name: notion-sdk-patterns
description: |
  Apply production-ready @notionhq/client SDK patterns for TypeScript and Python.
  Use when implementing Notion integrations, building database queries with filters
  and sorts, handling pagination, constructing rich text blocks, or establishing
  team coding standards for Notion API usage.
  Trigger with "notion SDK patterns", "notion best practices", "notion code patterns",
  "idiomatic notion", "notion typescript", "notion python SDK".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, sdk, typescript, python]
compatible-with: claude-code
---

# Notion SDK Patterns

## Overview

Production-ready patterns for the official Notion SDK (`@notionhq/client` for TypeScript, `notion-client` for Python) covering client initialization, database queries with filters and sorts, cursor-based pagination, rich text construction, block manipulation, and type-safe error handling using SDK error codes.

## Prerequisites

- **Node.js 18+** with `@notionhq/client` v2.x installed, or **Python 3.9+** with `notion-client`
- A Notion integration token (`NOTION_TOKEN`) from [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Target databases/pages shared with the integration (Share > Invite > select your integration)
- TypeScript 5+ with strict mode enabled (for TypeScript patterns)

## Instructions

### Step 1 — Initialize the Client and Query Databases

Set up the SDK client and execute filtered, sorted database queries.

**TypeScript — Client initialization:**
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

**Database query with filter and sort:**
```typescript
const response = await notion.databases.query({
  database_id,
  filter: {
    property: 'Status',
    select: {
      equals: 'Active',
    },
  },
  sorts: [
    {
      property: 'Created',
      direction: 'descending',
    },
  ],
});
```

**Compound filters** combine conditions with `and`/`or`:
```typescript
const response = await notion.databases.query({
  database_id,
  filter: {
    and: [
      { property: 'Status', select: { equals: 'Active' } },
      { property: 'Priority', select: { does_not_equal: 'Low' } },
      { property: 'Assignee', people: { is_not_empty: true } },
    ],
  },
  sorts: [
    { property: 'Priority', direction: 'ascending' },
    { property: 'Created', direction: 'descending' },
  ],
});
```

**Python — Client initialization and query:**
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

results = notion.databases.query(
    database_id=db_id,
    filter={
        "property": "Status",
        "select": {"equals": "Active"},
    },
    sorts=[{"property": "Created", "direction": "descending"}],
)
```

### Step 2 — Paginate Results and Manipulate Blocks

The Notion API returns at most 100 results per request. Use cursor-based pagination to retrieve all records.

**Cursor-based pagination:**
```typescript
let cursor: string | undefined;
do {
  const { results, next_cursor, has_more } = await notion.databases.query({
    database_id,
    start_cursor: cursor,
  });

  // Process each page of results
  for (const page of results) {
    console.log(page.id);
  }

  cursor = has_more && next_cursor ? next_cursor : undefined;
} while (cursor);
```

**Reusable pagination helper (generic):**
```typescript
type PaginatedFn<T> = (args: { start_cursor?: string }) => Promise<{
  results: T[];
  has_more: boolean;
  next_cursor: string | null;
}>;

async function collectPaginated<T>(fn: PaginatedFn<T>): Promise<T[]> {
  const all: T[] = [];
  let cursor: string | undefined;

  do {
    const response = await fn({ start_cursor: cursor });
    all.push(...response.results);
    cursor = response.has_more && response.next_cursor
      ? response.next_cursor
      : undefined;
  } while (cursor);

  return all;
}

// Usage — collect all pages from a database
const allPages = await collectPaginated((args) =>
  notion.databases.query({ database_id: 'db-id', ...args })
);
```

**Read block children (page content):**
```typescript
const blocks = await notion.blocks.children.list({
  block_id: pageId,
});

for (const block of blocks.results) {
  if ('type' in block) {
    console.log(block.type, block.id);
  }
}
```

**Append blocks to a page:**
```typescript
await notion.blocks.children.append({
  block_id: pageId,
  children: [
    {
      type: 'paragraph',
      paragraph: {
        rich_text: [{ text: { content: 'Hello from the SDK' } }],
      },
    },
    {
      type: 'heading_2',
      heading_2: {
        rich_text: [{ text: { content: 'Section Title' } }],
      },
    },
    {
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ text: { content: 'First item' } }],
      },
    },
  ],
});
```

**Rich text with annotations and links:**
```typescript
const richTextBlock = {
  type: 'text' as const,
  text: {
    content: 'Hello',
    link: { url: 'https://developers.notion.com' },
  },
  annotations: {
    bold: true,
    italic: false,
    strikethrough: false,
    underline: false,
    code: false,
    color: 'default' as const,
  },
};
```

**Python — block manipulation:**
```python
# List block children
blocks = notion.blocks.children.list(block_id=page_id)

# Append blocks
notion.blocks.children.append(
    block_id=page_id,
    children=[
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "Added via Python SDK"}}]
            },
        }
    ],
)
```

### Step 3 — Handle Errors with SDK Error Codes

Use the SDK's built-in error type guards instead of catching generic exceptions.

**TypeScript — type-safe error handling:**
```typescript
import {
  isNotionClientError,
  APIErrorCode,
  ClientErrorCode,
} from '@notionhq/client';

try {
  const page = await notion.pages.retrieve({ page_id: pageId });
} catch (error) {
  if (isNotionClientError(error)) {
    switch (error.code) {
      case APIErrorCode.ObjectNotFound:
        console.error('Page not found — ensure it is shared with the integration');
        break;
      case APIErrorCode.Unauthorized:
        console.error('Invalid token — regenerate at notion.so/my-integrations');
        break;
      case APIErrorCode.RateLimited:
        console.error(`Rate limited — retry after ${error.headers?.['retry-after']}s`);
        break;
      case APIErrorCode.ValidationError:
        console.error(`Invalid request: ${error.message}`);
        break;
      case APIErrorCode.ConflictError:
        console.error('Conflict — resource was modified by another request');
        break;
      case ClientErrorCode.RequestTimeout:
        console.error('Request timed out — increase timeoutMs or check network');
        break;
      default:
        console.error(`Notion error [${error.code}]: ${error.message}`);
    }
  } else {
    throw error; // Re-throw non-Notion errors
  }
}
```

**Python — error handling:**
```python
from notion_client import Client, APIResponseError

try:
    results = notion.databases.query(database_id=db_id)
except APIResponseError as e:
    if e.code == "object_not_found":
        print("Database not found or not shared with integration")
    elif e.code == "rate_limited":
        retry_after = e.headers.get("retry-after", "unknown")
        print(f"Rate limited — retry after {retry_after}s")
    elif e.code == "unauthorized":
        print("Invalid token — regenerate at notion.so/my-integrations")
    elif e.code == "validation_error":
        print(f"Validation error: {e.message}")
    else:
        raise
```

**Safe wrapper pattern (Result type):**
```typescript
async function safeNotionCall<T>(
  operation: () => Promise<T>,
): Promise<{ data: T; error: null } | { data: null; error: string }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (error: unknown) {
    if (isNotionClientError(error)) {
      return { data: null, error: `[${error.code}] ${error.message}` };
    }
    return { data: null, error: String(error) };
  }
}

// Usage
const result = await safeNotionCall(() =>
  notion.pages.retrieve({ page_id: pageId })
);
if (result.error) {
  console.error(result.error);
} else {
  console.log(result.data.id);
}
```

## Output

Applying these patterns produces:

- A configured SDK client connected via `NOTION_TOKEN`
- Database queries with filters, sorts, and compound conditions
- Complete result sets through cursor-based pagination (no missed records)
- Block read/write operations with properly structured rich text
- Exhaustive error handling using SDK error codes (not string matching)
- TypeScript and Python implementations for cross-team consistency

## Error Handling

| Error Code | Cause | Resolution |
|---|---|---|
| `ObjectNotFound` | Page/database not shared with integration | Open in Notion > Share > Invite integration |
| `Unauthorized` | Invalid or expired token | Regenerate at notion.so/my-integrations |
| `RateLimited` | >3 requests/second sustained | Respect `retry-after` header; add exponential backoff |
| `ValidationError` | Malformed filter, sort, or property | Check property names match database schema exactly |
| `ConflictError` | Concurrent modification | Retry with fresh read; use optimistic concurrency |
| `RequestTimeout` | Network or payload too large | Increase `timeoutMs` on client; reduce page_size |

The SDK has built-in retry with exponential backoff (defaults: `maxRetries=2`, `initialRetryDelayMs=1000`, `maxRetryDelayMs=60000`). Override via client constructor options.

## Examples

### Property Value Extractors
```typescript
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

function getTitle(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'title' ? p.title.map(t => t.plain_text).join('') : '';
}

function getRichText(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'rich_text' ? p.rich_text.map(t => t.plain_text).join('') : '';
}

function getSelect(page: PageObjectResponse, prop: string): string | null {
  const p = page.properties[prop];
  return p?.type === 'select' ? (p.select?.name ?? null) : null;
}

function getNumber(page: PageObjectResponse, prop: string): number | null {
  const p = page.properties[prop];
  return p?.type === 'number' ? p.number : null;
}

function getCheckbox(page: PageObjectResponse, prop: string): boolean {
  const p = page.properties[prop];
  return p?.type === 'checkbox' ? p.checkbox : false;
}
```

### Multi-Workspace Factory
```typescript
const clients = new Map<string, Client>();

function getClient(workspaceId: string, token: string): Client {
  if (!clients.has(workspaceId)) {
    clients.set(workspaceId, new Client({ auth: token }));
  }
  return clients.get(workspaceId)!;
}
```

### Create a Page with Properties
```typescript
await notion.pages.create({
  parent: { database_id },
  properties: {
    Name: { title: [{ text: { content: 'New Task' } }] },
    Status: { select: { name: 'To Do' } },
    Priority: { select: { name: 'High' } },
    'Due Date': { date: { start: '2026-04-01' } },
    Tags: { multi_select: [{ name: 'backend' }, { name: 'api' }] },
  },
});
```

### Python Pagination
```python
cursor = None
all_results = []
while True:
    response = notion.databases.query(
        database_id=db_id,
        start_cursor=cursor,
    )
    all_results.extend(response["results"])
    if not response["has_more"]:
        break
    cursor = response["next_cursor"]
```

## Resources

- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client) — Official TypeScript/JS SDK
- [notion-sdk-js on GitHub](https://github.com/makenotion/notion-sdk-js) — Source, examples, and changelog
- [notion-sdk-py on GitHub](https://github.com/ramnes/notion-sdk-py) — Official Python SDK
- [Notion API Reference](https://developers.notion.com/reference/intro) — Endpoints, types, and limits
- [API Error Codes](https://developers.notion.com/reference/request-limits) — Rate limits and error responses
- [Working with Databases](https://developers.notion.com/docs/working-with-databases) — Filters, sorts, and pagination

## Next Steps

- Apply patterns in `notion-core-workflow-a` for end-to-end CRUD operations
- See `notion-data-handling` for property type mapping and data transformation
- See `notion-rate-limits` for advanced rate limiting strategies beyond built-in retry
- See `notion-common-errors` for troubleshooting integration sharing and permission issues
