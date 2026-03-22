---
name: notion-sdk-patterns
description: |
  Apply production-ready @notionhq/client SDK patterns for TypeScript and Python.
  Use when implementing Notion integrations, refactoring SDK usage,
  or establishing team coding standards for Notion.
  Trigger with phrases like "notion SDK patterns", "notion best practices",
  "notion code patterns", "idiomatic notion", "notion typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion SDK Patterns

## Overview
Production-ready patterns for `@notionhq/client` usage: typed error handling, singleton client, pagination helpers, and response extraction utilities.

## Prerequisites
- `@notionhq/client` installed
- TypeScript 5+ with strict mode
- Familiarity with async/await patterns

## Instructions

### Step 1: Singleton Client with Configuration
```typescript
// src/notion/client.ts
import { Client, LogLevel } from '@notionhq/client';

let instance: Client | null = null;

export function getNotionClient(): Client {
  if (!instance) {
    if (!process.env.NOTION_TOKEN) {
      throw new Error('NOTION_TOKEN environment variable is required');
    }
    instance = new Client({
      auth: process.env.NOTION_TOKEN,
      logLevel: process.env.NODE_ENV === 'development' ? LogLevel.DEBUG : LogLevel.WARN,
      timeoutMs: 60_000,
      // Built-in retry with exponential backoff
      // Defaults: maxRetries=2, initialRetryDelayMs=1000, maxRetryDelayMs=60000
    });
  }
  return instance;
}
```

### Step 2: Type-Safe Error Handling
```typescript
import { Client, isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

async function safeNotionCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: string | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (error: unknown) {
    if (isNotionClientError(error)) {
      switch (error.code) {
        case APIErrorCode.Unauthorized:
          return { data: null, error: 'Invalid API token. Regenerate at notion.so/my-integrations.' };
        case APIErrorCode.ObjectNotFound:
          return { data: null, error: 'Resource not found. Ensure page is shared with integration.' };
        case APIErrorCode.RateLimited:
          return { data: null, error: `Rate limited. Retry after ${error.headers?.['retry-after']}s.` };
        case APIErrorCode.ValidationError:
          return { data: null, error: `Validation error: ${error.message}` };
        case APIErrorCode.ConflictError:
          return { data: null, error: 'Conflict. Resource was modified by another request.' };
        case ClientErrorCode.RequestTimeout:
          return { data: null, error: 'Request timed out. Increase timeoutMs.' };
        default:
          return { data: null, error: `Notion API error [${error.code}]: ${error.message}` };
      }
    }
    return { data: null, error: `Unexpected error: ${String(error)}` };
  }
}
```

### Step 3: Generic Pagination Helper
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

// Usage
const notion = getNotionClient();
const allPages = await collectPaginated((args) =>
  notion.databases.query({ database_id: 'db-id', ...args })
);
```

### Step 4: Property Value Extractors
```typescript
// Type-safe property extraction from page results
import type {
  PageObjectResponse,
  RichTextItemResponse,
} from '@notionhq/client/build/src/api-endpoints';

function getTitle(page: PageObjectResponse, propertyName: string): string {
  const prop = page.properties[propertyName];
  if (prop?.type === 'title') {
    return prop.title.map(t => t.plain_text).join('');
  }
  return '';
}

function getRichText(page: PageObjectResponse, propertyName: string): string {
  const prop = page.properties[propertyName];
  if (prop?.type === 'rich_text') {
    return prop.rich_text.map(t => t.plain_text).join('');
  }
  return '';
}

function getSelect(page: PageObjectResponse, propertyName: string): string | null {
  const prop = page.properties[propertyName];
  return prop?.type === 'select' ? prop.select?.name ?? null : null;
}

function getMultiSelect(page: PageObjectResponse, propertyName: string): string[] {
  const prop = page.properties[propertyName];
  return prop?.type === 'multi_select' ? prop.multi_select.map(s => s.name) : [];
}

function getNumber(page: PageObjectResponse, propertyName: string): number | null {
  const prop = page.properties[propertyName];
  return prop?.type === 'number' ? prop.number : null;
}

function getCheckbox(page: PageObjectResponse, propertyName: string): boolean {
  const prop = page.properties[propertyName];
  return prop?.type === 'checkbox' ? prop.checkbox : false;
}

function getDate(page: PageObjectResponse, propertyName: string): string | null {
  const prop = page.properties[propertyName];
  return prop?.type === 'date' ? prop.date?.start ?? null : null;
}
```

### Step 5: Rich Text Builder
```typescript
type RichTextInput = {
  text: { content: string; link?: { url: string } | null };
  annotations?: Partial<{
    bold: boolean; italic: boolean; strikethrough: boolean;
    underline: boolean; code: boolean;
    color: 'default' | 'red' | 'blue' | 'green' | 'yellow' | 'purple';
  }>;
};

function richText(content: string, opts?: {
  bold?: boolean; italic?: boolean; code?: boolean;
  link?: string; color?: string;
}): RichTextInput {
  return {
    text: {
      content,
      link: opts?.link ? { url: opts.link } : null,
    },
    annotations: {
      bold: opts?.bold ?? false,
      italic: opts?.italic ?? false,
      code: opts?.code ?? false,
      color: (opts?.color as any) ?? 'default',
    },
  };
}

// Usage
await notion.blocks.children.append({
  block_id: pageId,
  children: [{
    paragraph: {
      rich_text: [
        richText('Check out '),
        richText('the docs', { bold: true, link: 'https://developers.notion.com' }),
        richText(' for details.'),
      ],
    },
  }],
});
```

## Output
- Type-safe client singleton with lazy initialization
- Robust error handling using SDK error codes
- Reusable pagination helper for all list endpoints
- Property extractors for every common property type
- Fluent rich text builder

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `isNotionClientError` | All API calls | Type-safe error discrimination |
| `collectPaginated` | Any list endpoint | No missed results |
| Property extractors | Reading pages | No `undefined` crashes |
| Rich text builder | Creating content | Correct annotation structure |

## Examples

### Factory Pattern (Multi-Workspace)
```typescript
const clients = new Map<string, Client>();

function getClientForWorkspace(workspaceId: string, token: string): Client {
  if (!clients.has(workspaceId)) {
    clients.set(workspaceId, new Client({ auth: token }));
  }
  return clients.get(workspaceId)!;
}
```

### Python Equivalent
```python
from notion_client import Client, APIResponseError

notion = Client(auth=os.environ["NOTION_TOKEN"])

try:
    results = notion.databases.query(database_id=db_id)
except APIResponseError as e:
    if e.code == "object_not_found":
        print("Database not found or not shared with integration")
    elif e.code == "rate_limited":
        print(f"Rate limited. Retry after {e.headers.get('retry-after')}s")
    else:
        raise
```

## Resources
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)
- [GitHub: notion-sdk-js](https://github.com/makenotion/notion-sdk-js)
- [API Error Codes](https://developers.notion.com/reference/request-limits)
- [Notion API Types](https://developers.notion.com/reference/intro)

## Next Steps
Apply patterns in `notion-core-workflow-a` for real-world usage.
