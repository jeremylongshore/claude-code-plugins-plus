---
name: notion-known-pitfalls
description: |
  Common Notion API mistakes: wrong page ID format (dashes), rich text
  array structure, block children not returned with page, pagination
  required for all lists, 3 req/sec shared across endpoints, not sharing
  pages with integration. Use when debugging or reviewing Notion code.
  Trigger with phrases like "notion mistakes", "notion pitfalls",
  "notion common errors", "notion gotchas", "notion debugging".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Known Pitfalls

## Overview

The twelve most common mistakes when building Notion API integrations, each with the wrong pattern, why it fails, and the correct fix using real `Client` from `@notionhq/client` code. These pitfalls account for the majority of developer support questions. Covers page ID format issues, rich text structure, missing block children, pagination requirements, rate limit sharing, and integration sharing.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set
- Familiarity with Notion API concepts (databases, pages, blocks, properties)

## Instructions

### Step 1: Not Sharing Pages with the Integration (Pitfall #1)

The single most common Notion API error. Every page/database must be explicitly shared with your integration.

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// This returns 404 even though the page EXISTS in your workspace
try {
  const page = await notion.pages.retrieve({ page_id: 'some-page-id' });
} catch (error) {
  if (isNotionClientError(error) && error.code === APIErrorCode.ObjectNotFound) {
    // "object_not_found" does NOT mean the page doesn't exist
    // It means your integration doesn't have access
    console.error('Page exists but integration lacks access.');
    console.error('Fix: In Notion UI, open page -> ... menu -> Connections -> Add your integration');
    console.error('Tip: Share a parent page to grant access to ALL child pages');
  }
}

// Always verify access at startup
async function verifyAccess(databaseId: string): Promise<boolean> {
  try {
    await notion.databases.retrieve({ database_id: databaseId });
    return true;
  } catch {
    console.error(`Cannot access database ${databaseId}. Share it with your integration.`);
    return false;
  }
}
```

### Step 2: Page ID Format Issues and Rich Text Array Structure (Pitfalls #2-3)

Notion IDs work with or without dashes, but URLs contain dashes while the API often returns them without.

```typescript
// PITFALL #2: Page ID format confusion
// Notion URLs: https://notion.so/Page-Title-a1b2c3d4e5f67890abcdef1234567890
// The ID is the last 32 hex chars: a1b2c3d4e5f67890abcdef1234567890
// API accepts both formats:
//   a1b2c3d4-e5f6-7890-abcd-ef1234567890  (with dashes)
//   a1b2c3d4e5f67890abcdef1234567890        (without dashes)

function extractPageId(urlOrId: string): string {
  // Handle full Notion URL
  const urlMatch = urlOrId.match(/([a-f0-9]{32})(?:\?|$)/);
  if (urlMatch) return urlMatch[1];

  // Handle URL with dashes in page title (ID is always last 32 hex chars)
  const cleanId = urlOrId.replace(/-/g, '');
  const idMatch = cleanId.match(/([a-f0-9]{32})$/);
  if (idMatch) return idMatch[1];

  // Already a clean ID
  return urlOrId;
}

// PITFALL #3: Rich text is ALWAYS an array, even for single values
// WRONG: treating rich_text as a string
// const text = page.properties.Description.rich_text; // This is an ARRAY

// WRONG: accessing without checking length
// const text = page.properties.Description.rich_text[0].plain_text; // TypeError if empty!

// RIGHT: safe extraction helper
function extractRichText(page: any, propertyName: string): string {
  const prop = page.properties[propertyName];
  if (!prop) return '';

  if (prop.type === 'title') {
    return prop.title?.map((t: any) => t.plain_text).join('') ?? '';
  }
  if (prop.type === 'rich_text') {
    return prop.rich_text?.map((t: any) => t.plain_text).join('') ?? '';
  }
  return '';
}

// RIGHT: safe property extraction for all types
function extractProperty(page: any, name: string): any {
  const prop = page.properties[name];
  if (!prop) return null;

  switch (prop.type) {
    case 'title':
      return prop.title?.map((t: any) => t.plain_text).join('') ?? '';
    case 'rich_text':
      return prop.rich_text?.map((t: any) => t.plain_text).join('') ?? '';
    case 'number':
      return prop.number;
    case 'select':
      return prop.select?.name ?? null;
    case 'multi_select':
      return prop.multi_select?.map((s: any) => s.name) ?? [];
    case 'date':
      return prop.date?.start ?? null;
    case 'checkbox':
      return prop.checkbox;
    case 'url':
      return prop.url;
    case 'email':
      return prop.email;
    case 'phone_number':
      return prop.phone_number;
    case 'people':
      return prop.people?.map((p: any) => p.name) ?? [];
    default:
      return null;
  }
}
```

### Step 3: Block Children, Pagination, Rate Limits, and More (Pitfalls #4-12)

```typescript
// PITFALL #4: Block children are NOT returned with page retrieval
// pages.retrieve() returns properties, NOT content blocks
// You need a SEPARATE call to get page content

// WRONG: expecting blocks from page retrieval
const page = await notion.pages.retrieve({ page_id: pageId });
// page.content — DOES NOT EXIST

// RIGHT: separate call for blocks
const blocks = await notion.blocks.children.list({ block_id: pageId });
// blocks.results contains the actual page content

// Also: nested blocks require recursive fetching (max 3 levels via API)
async function getAllBlocks(blockId: string): Promise<any[]> {
  const blocks: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: blockId,
      page_size: 100,
      start_cursor: cursor,
    });
    blocks.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  // Fetch nested children (API max depth: 3)
  for (const block of blocks) {
    if ((block as any).has_children) {
      (block as any)._children = await getAllBlocks((block as any).id);
    }
  }

  return blocks;
}

// ---

// PITFALL #5: Pagination required for ALL list endpoints
// Every list endpoint returns max 100 results. ALWAYS check has_more.

// WRONG: only gets first 100 results
const response = await notion.databases.query({ database_id: dbId });
const allPages = response.results; // Missing results 101+!

// RIGHT: paginate through all results
async function queryAll(dbId: string, filter?: any): Promise<any[]> {
  const allResults: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter,
      page_size: 100,
      start_cursor: cursor,
    });
    allResults.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return allResults;
}

// ---

// PITFALL #6: Rate limit is SHARED across all endpoints
// 3 req/s applies to ALL calls combined (queries + creates + updates + blocks)
// NOT 3/s per endpoint

// WRONG: separate throttles per operation type
// This uses 6 req/s total and will get 429 errors:
const readQueue = new PQueue({ interval: 333, intervalCap: 1 });   // 3/s
const writeQueue = new PQueue({ interval: 333, intervalCap: 1 });  // 3/s

// RIGHT: single shared queue for all operations
import PQueue from 'p-queue';
const notionQueue = new PQueue({
  concurrency: 1,
  interval: 340,      // ~3/s with margin
  intervalCap: 1,
});

// ALL calls go through this one queue
const queryResult = await notionQueue.add(() =>
  notion.databases.query({ database_id: dbId })
);
const createResult = await notionQueue.add(() =>
  notion.pages.create({ parent: { database_id: dbId }, properties: { /* ... */ } })
);

// ---

// PITFALL #7: Wrong property type in filter
// Each property type has its own filter syntax

// WRONG: using text filter on a select property
// { property: 'Status', text: { equals: 'Done' } }

// WRONG: missing the property type wrapper
// { property: 'Status', equals: 'Done' }

// RIGHT: match the filter type to the property type
const filterExamples = {
  title:        { property: 'Name', title: { contains: 'search' } },
  rich_text:    { property: 'Notes', rich_text: { contains: 'keyword' } },
  number:       { property: 'Score', number: { greater_than: 90 } },
  select:       { property: 'Status', select: { equals: 'Done' } },
  multi_select: { property: 'Tags', multi_select: { contains: 'urgent' } },
  date:         { property: 'Due', date: { before: '2026-04-01' } },
  checkbox:     { property: 'Active', checkbox: { equals: true } },
  people:       { property: 'Owner', people: { contains: 'user-id' } },
  relation:     { property: 'Project', relation: { contains: 'page-id' } },
};

// ---

// PITFALL #8: Property names are CASE-SENSITIVE

// WRONG: lowercase property name
// { property: 'status', select: { equals: 'Done' } }  // 400 error

// RIGHT: exact case match
// { property: 'Status', select: { equals: 'Done' } }

// Always verify property names first:
async function getPropertyNames(dbId: string): Promise<string[]> {
  const db = await notion.databases.retrieve({ database_id: dbId });
  return Object.keys(db.properties);
}

// ---

// PITFALL #9: Appending blocks one at a time
// Batch blocks into a single call (max 100 per request)

// WRONG: N API calls for N blocks
for (const item of items) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [{ paragraph: { rich_text: [{ text: { content: item } }] } }],
  }); // 100 items = 100 API calls (33 seconds)
}

// RIGHT: one API call for all blocks
await notion.blocks.children.append({
  block_id: pageId,
  children: items.slice(0, 100).map(item => ({
    paragraph: { rich_text: [{ text: { content: item } }] },
  })),
}); // 100 items = 1 API call

// For >100 blocks, chunk into batches of 100
for (let i = 0; i < items.length; i += 100) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: items.slice(i, i + 100).map(item => ({
      paragraph: { rich_text: [{ text: { content: item } }] },
    })),
  });
  await new Promise(r => setTimeout(r, 350)); // Rate limit
}

// ---

// PITFALL #10: Using the wrong import
// WRONG: these packages don't exist
// import { NotionClient } from '@notion/sdk';
// import { NotionClient } from 'notion';
// import Notion from 'notion-api';

// RIGHT: official package
import { Client } from '@notionhq/client';
// Also available:
import {
  isNotionClientError,  // Type guard for error handling
  APIErrorCode,         // Error code enum
  ClientErrorCode,      // Client-side error codes
  LogLevel,            // DEBUG, WARN, ERROR
} from '@notionhq/client';

// ---

// PITFALL #11: Missing title property on page creation
// Every page in a database MUST include the title property

// WRONG: no title
await notion.pages.create({
  parent: { database_id: dbId },
  properties: {
    Status: { select: { name: 'New' } }, // validation_error: missing title
  },
});

// RIGHT: always include title (the property name varies by database)
// First, find the title property name:
const db = await notion.databases.retrieve({ database_id: dbId });
const titlePropName = Object.entries(db.properties)
  .find(([, v]) => v.type === 'title')![0];
console.log(`Title property name: "${titlePropName}"`); // Usually "Name" or "Title"

await notion.pages.create({
  parent: { database_id: dbId },
  properties: {
    [titlePropName]: { title: [{ text: { content: 'New Item' } }] },
    Status: { select: { name: 'New' } },
  },
});

// ---

// PITFALL #12: Hardcoded database IDs
// IDs change between environments and when databases are duplicated

// WRONG:
const DB_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

// RIGHT: environment variables
const DB_ID_RIGHT = process.env.NOTION_TASKS_DB;
if (!DB_ID_RIGHT) throw new Error('NOTION_TASKS_DB env var required');
```

```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Safe property extraction (handles empty arrays)
def extract_text(page: dict, prop_name: str) -> str:
    prop = page.get("properties", {}).get(prop_name)
    if not prop:
        return ""
    if prop["type"] == "title":
        return "".join(t["plain_text"] for t in prop.get("title", []))
    if prop["type"] == "rich_text":
        return "".join(t["plain_text"] for t in prop.get("rich_text", []))
    return ""

# Full pagination
def query_all(database_id: str, filter_obj=None) -> list:
    results = []
    cursor = None
    while True:
        kwargs = {"database_id": database_id, "page_size": 100}
        if filter_obj:
            kwargs["filter"] = filter_obj
        if cursor:
            kwargs["start_cursor"] = cursor
        response = notion.databases.query(**kwargs)
        results.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return results

# Block content retrieval (separate from page retrieval)
def get_page_blocks(page_id: str) -> list:
    blocks = []
    cursor = None
    while True:
        kwargs = {"block_id": page_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = notion.blocks.children.list(**kwargs)
        blocks.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return blocks
```

## Output

- 12 pitfalls identified with wrong pattern, explanation, and correct code
- Safe property extraction helpers for all property types
- Full pagination pattern that never misses data
- Block retrieval pattern (separate from page retrieval)
- Rate limit queue shared across all endpoints
- Codebase scanning commands to detect pitfalls

## Error Handling

| Pitfall | Error You See | Real Cause |
|---------|--------------|------------|
| #1 Not shared | `object_not_found` (404) | Page not shared with integration |
| #2 ID format | `validation_error` (400) | Wrong ID extracted from URL |
| #3 Empty rich_text | `TypeError: Cannot read property` | Array is empty, not checked |
| #4 No blocks | Missing page content | Need `blocks.children.list()` |
| #5 No pagination | Incomplete data | Only got first 100 results |
| #6 Split rate limit | `rate_limited` (429) | Separate queues = 2x rate |
| #7 Wrong filter | `validation_error` (400) | Filter type doesn't match property |
| #8 Wrong case | `validation_error` (400) | Property names are case-sensitive |
| #9 Single append | Slow performance | N calls instead of 1 batched call |
| #10 Wrong import | `Module not found` | Use `@notionhq/client` |
| #11 No title | `validation_error` (400) | Title property is required |
| #12 Hardcoded ID | Works locally, fails in CI | Use environment variables |

## Examples

### Quick Codebase Scan for Pitfalls

```bash
# Check for common pitfalls in your codebase
echo "=== Pitfall Scan ==="

# Wrong import
grep -rn "@notion/sdk\|from 'notion'" --include="*.ts" --include="*.js" src/ && \
  echo "FAIL: Wrong import (use @notionhq/client)" || echo "OK: Correct import"

# Unsafe array access on rich_text
grep -rn "rich_text\[0\]\|\.title\[0\]" --include="*.ts" src/ && \
  echo "WARN: Unsafe array access (check length first)" || echo "OK: No unsafe access"

# Hardcoded UUIDs
grep -rn "[a-f0-9]\{8\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{12\}" --include="*.ts" src/ && \
  echo "WARN: Possible hardcoded UUID (use env vars)" || echo "OK: No hardcoded UUIDs"

# Missing pagination
grep -rn "databases.query\|blocks.children.list" --include="*.ts" src/ | \
  grep -v "has_more\|start_cursor\|paginate" && \
  echo "WARN: Query without pagination check" || echo "OK: Pagination handled"
```

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Property Value Types](https://developers.notion.com/reference/property-value-object)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Request Limits](https://developers.notion.com/reference/request-limits)
- [GitHub: notion-sdk-js](https://github.com/makenotion/notion-sdk-js)

## Next Steps

For debugging hard issues, see `notion-advanced-troubleshooting`.
For scaling beyond these basics, see `notion-load-scale`.
