---
name: notion-sdk-patterns
description: |
  Apply production-ready @notionhq/client SDK patterns for TypeScript and Python.
  Use when implementing Notion integrations, building database queries with filters
  and sorts, handling pagination, constructing rich text blocks, or establishing
  team coding standards for Notion API usage.
  Trigger with "notion SDK patterns", "notion best practices", "notion code patterns",
  "idiomatic notion", "notion typescript", "notion python SDK".
allowed-tools: Read, Write, Edit, Grep
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- sdk
- typescript
- python
compatibility: Designed for Claude Code
---
# Notion SDK Patterns

## Overview

Production-ready patterns for the official Notion SDK (`@notionhq/client` for TypeScript, `notion-client` for Python) covering client initialization, database queries with filters and sorts, cursor-based pagination, rich text construction, block manipulation, and type-safe error handling using SDK error codes.

The full workflow lives in three steps below. Each step shows the essential skeleton inline; deep variants (compound filters, generic pagination helpers, block manipulation, exhaustive error switches) are in [references/patterns.md](references/patterns.md), and copy-paste task recipes are in [references/examples.md](references/examples.md).

## Prerequisites

- **Node.js 18+** with `@notionhq/client` v2.x installed, or **Python 3.9+** with `notion-client`
- A Notion integration token (`NOTION_TOKEN`) from [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Target databases/pages shared with the integration (Share > Invite > select your integration)
- TypeScript 5+ with strict mode enabled (for TypeScript patterns)

## Instructions

### Step 1 — Initialize the Client and Query Databases

Set up the SDK client and execute a filtered, sorted database query.

**TypeScript:**

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

const response = await notion.databases.query({
  database_id,
  filter: {
    property: 'Status',
    select: { equals: 'Active' },
  },
  sorts: [{ property: 'Created', direction: 'descending' }],
});
```

**Python:**

```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

results = notion.databases.query(
    database_id=db_id,
    filter={"property": "Status", "select": {"equals": "Active"}},
    sorts=[{"property": "Created", "direction": "descending"}],
)
```

For `and`/`or` compound filters and multi-key sorts, see the Compound Filters section of [references/patterns.md](references/patterns.md).

### Step 2 — Paginate Results and Manipulate Blocks

The Notion API returns at most 100 results per request. Loop on the cursor to retrieve every record:

```typescript
let cursor: string | undefined;
do {
  const { results, next_cursor, has_more } = await notion.databases.query({
    database_id,
    start_cursor: cursor,
  });
  for (const page of results) {
    console.log(page.id);
  }
  cursor = has_more && next_cursor ? next_cursor : undefined;
} while (cursor);
```

A reusable generic `collectPaginated` helper, the Python pagination loop, and block read/append plus rich-text construction are in the Cursor-Based Pagination and Block Manipulation sections of [references/patterns.md](references/patterns.md).

### Step 3 — Handle Errors with SDK Error Codes

Use the SDK's built-in error type guards instead of catching generic exceptions:

```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

try {
  const page = await notion.pages.retrieve({ page_id: pageId });
} catch (error) {
  if (isNotionClientError(error)) {
    if (error.code === APIErrorCode.ObjectNotFound) {
      console.error('Page not found — ensure it is shared with the integration');
    } else {
      console.error(`Notion error [${error.code}]: ${error.message}`);
    }
  } else {
    throw error; // Re-throw non-Notion errors
  }
}
```

The exhaustive TypeScript `switch` over every error code, the Python `APIResponseError` handler, and a `safeNotionCall` Result-type wrapper are in the Error Handling section of [references/patterns.md](references/patterns.md).

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
| --- | --- | --- |
| `ObjectNotFound` | Page/database not shared with integration | Open in Notion > Share > Invite integration |
| `Unauthorized` | Invalid or expired token | Regenerate at notion.so/my-integrations |
| `RateLimited` | >3 requests/second sustained | Respect `retry-after` header; add exponential backoff |
| `ValidationError` | Malformed filter, sort, or property | Check property names match database schema exactly |
| `ConflictError` | Concurrent modification | Retry with fresh read; use optimistic concurrency |
| `RequestTimeout` | Network or payload too large | Increase `timeoutMs` on client; reduce page_size |

The SDK has built-in retry with exponential backoff (defaults: `maxRetries=2`, `initialRetryDelayMs=1000`, `maxRetryDelayMs=60000`). Override via client constructor options. Full type-safe handlers for each code are in the Error Handling section of [references/patterns.md](references/patterns.md).

## Examples

Copy-paste recipes live in [references/examples.md](references/examples.md):

- **Property Value Extractors** — type-safe `getTitle`/`getSelect`/`getNumber`/`getCheckbox` accessors that narrow each property's discriminated union.
- **Multi-Workspace Factory** — cache one `Client` per workspace token for multi-tenant integrations.
- **Create a Page with Properties** — populate title, select, date, and multi-select fields on `pages.create`.
- **Python Pagination** — the equivalent cursor loop for `notion-client`.

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
