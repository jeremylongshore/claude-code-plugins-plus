# Notion SDK Patterns — Deep Reference

Full implementations for the patterns summarized in `SKILL.md`. Every snippet here is drop-in
production code for `@notionhq/client` (TypeScript) and `notion-client` (Python).

## Compound Filters

Combine conditions with `and`/`or` and stack multiple sort keys:

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

## Cursor-Based Pagination

The Notion API returns at most 100 results per request. Loop on the cursor to retrieve everything:

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

### Reusable Pagination Helper (generic)

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

## Block Manipulation

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

## Error Handling with SDK Error Codes

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

The SDK has built-in retry with exponential backoff. Defaults: `maxRetries=2`,
`initialRetryDelayMs=1000` (first retry waits 1 second), `maxRetryDelayMs=60000` (cap of
60 seconds between retries). Override via client constructor options.
