---
name: notion-known-pitfalls
description: |
  Identify and avoid Notion API anti-patterns and common integration mistakes.
  Use when reviewing Notion code for issues, onboarding new developers,
  or auditing existing Notion integrations.
  Trigger with phrases like "notion mistakes", "notion anti-patterns",
  "notion pitfalls", "notion what not to do", "notion code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Known Pitfalls

## Overview
Ten common mistakes when building Notion API integrations, with correct patterns using real `@notionhq/client` code.

## Prerequisites
- `@notionhq/client` installed
- Familiarity with Notion API concepts (databases, pages, blocks, properties)

## Instructions

### Pitfall #1: Forgetting to Share Pages with Integration

**The most common Notion API error.** The API returns `object_not_found` for pages that exist but are not shared with your integration.

```typescript
// This will return 404 even if the page exists!
const page = await notion.pages.retrieve({ page_id: 'unshared-page-id' });

// Fix: In Notion UI, open page → ... menu → Connections → Add your integration
// Or share a parent page to grant access to all children
```

---

### Pitfall #2: Wrong Property Names

Property names are case-sensitive and must match exactly:

```typescript
// WRONG: property name doesn't match Notion database
await notion.databases.query({
  database_id: dbId,
  filter: { property: 'status', select: { equals: 'Done' } }, // lowercase 's'!
});

// RIGHT: match the exact property name from the database
await notion.databases.query({
  database_id: dbId,
  filter: { property: 'Status', select: { equals: 'Done' } }, // capital 'S'
});

// PRO TIP: Always verify property names first
const db = await notion.databases.retrieve({ database_id: dbId });
console.log('Properties:', Object.keys(db.properties));
```

---

### Pitfall #3: Missing Title Property on Page Creation

Every database page requires the title property:

```typescript
// WRONG: missing title property
await notion.pages.create({
  parent: { database_id: dbId },
  properties: {
    Status: { select: { name: 'New' } }, // No title! → validation_error
  },
});

// RIGHT: always include the title property
await notion.pages.create({
  parent: { database_id: dbId },
  properties: {
    Name: { title: [{ text: { content: 'New Item' } }] }, // Title required
    Status: { select: { name: 'New' } },
  },
});
```

---

### Pitfall #4: Unthrottled Bulk Operations

```typescript
// WRONG: blasts through rate limit (3 req/s)
const pages = await notion.databases.query({ database_id: dbId });
await Promise.all(pages.results.map(page =>
  notion.pages.update({
    page_id: page.id,
    properties: { Status: { select: { name: 'Processed' } } },
  })
)); // 100 concurrent requests → 429 errors!

// RIGHT: throttle with p-queue
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

const pages = await notion.databases.query({ database_id: dbId });
await Promise.all(pages.results.map(page =>
  queue.add(() =>
    notion.pages.update({
      page_id: page.id,
      properties: { Status: { select: { name: 'Processed' } } },
    })
  )
));
```

---

### Pitfall #5: Not Handling Pagination

Notion returns max 100 results per request. Ignoring `has_more` means missing data:

```typescript
// WRONG: only gets first 100 results
const response = await notion.databases.query({ database_id: dbId });
const pages = response.results; // Missing pages 101+!

// RIGHT: paginate through all results
const allPages = [];
let cursor: string | undefined;
do {
  const response = await notion.databases.query({
    database_id: dbId,
    page_size: 100,
    start_cursor: cursor,
  });
  allPages.push(...response.results);
  cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
} while (cursor);
```

---

### Pitfall #6: Wrong Filter Type for Property

Each property type requires its own filter syntax:

```typescript
// WRONG: using 'text' filter on a 'select' property
{ property: 'Status', text: { equals: 'Done' } }

// WRONG: using 'equals' directly (no property type wrapper)
{ property: 'Status', equals: 'Done' }

// RIGHT: wrap in the property type
{ property: 'Status', select: { equals: 'Done' } }

// Reference:
// title:        { property: 'X', title: { contains: 'y' } }
// rich_text:    { property: 'X', rich_text: { contains: 'y' } }
// number:       { property: 'X', number: { greater_than: 5 } }
// select:       { property: 'X', select: { equals: 'y' } }
// multi_select: { property: 'X', multi_select: { contains: 'y' } }
// date:         { property: 'X', date: { before: '2026-01-01' } }
// checkbox:     { property: 'X', checkbox: { equals: true } }
// people:       { property: 'X', people: { contains: 'user-id' } }
// relation:     { property: 'X', relation: { contains: 'page-id' } }
```

---

### Pitfall #7: Appending Blocks One at a Time

```typescript
// WRONG: N API calls for N blocks
for (const item of items) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [{ paragraph: { rich_text: [{ text: { content: item } }] } }],
  });
} // 100 items = 100 API calls

// RIGHT: batch into one call (max 100 blocks)
await notion.blocks.children.append({
  block_id: pageId,
  children: items.map(item => ({
    paragraph: { rich_text: [{ text: { content: item } }] },
  })),
}); // 100 items = 1 API call
```

---

### Pitfall #8: Using Wrong Import

```typescript
// WRONG: this package doesn't exist
import { NotionClient } from '@notion/sdk';
import { NotionClient } from 'notion';

// RIGHT: official package
import { Client } from '@notionhq/client';

// Also useful imports:
import {
  isNotionClientError,
  APIErrorCode,
  ClientErrorCode,
  LogLevel,
} from '@notionhq/client';
```

---

### Pitfall #9: Not Handling Empty Rich Text

```typescript
// WRONG: crashes if rich_text is empty
const text = page.properties.Description.rich_text[0].plain_text; // TypeError!

// RIGHT: handle empty arrays
const text = page.properties.Description?.type === 'rich_text'
  ? page.properties.Description.rich_text.map(t => t.plain_text).join('')
  : '';
```

---

### Pitfall #10: Hardcoded Database IDs in Source

```typescript
// WRONG: hardcoded IDs change between environments
const DB_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

// RIGHT: use environment variables
const DB_ID = process.env.NOTION_TASKS_DB_ID;
if (!DB_ID) throw new Error('NOTION_TASKS_DB_ID required');
```

## Output
- Anti-patterns identified in codebase
- Correct patterns applied
- Code quality improved

## Error Handling
| Pitfall | Detection | Prevention |
|---------|-----------|------------|
| #1 Not shared | 404 on valid pages | Document sharing requirements |
| #2 Wrong names | 400 validation error | Retrieve schema first |
| #3 No title | 400 validation error | Always include title |
| #4 No throttle | 429 rate limits | Use p-queue |
| #5 No pagination | Missing data | Always check `has_more` |
| #6 Wrong filter | 400 validation error | Match filter to property type |
| #7 Single append | Slow operations | Batch up to 100 blocks |
| #8 Wrong import | Module not found | Use `@notionhq/client` |
| #9 Empty text | TypeError crash | Check array length |
| #10 Hardcoded IDs | Works locally, fails elsewhere | Use env vars |

## Examples

### Quick Codebase Scan
```bash
# Check for common pitfalls
grep -rn "@notion/sdk\|from 'notion'" --include="*.ts" src/   # Wrong import
grep -rn "rich_text\[0\]" --include="*.ts" src/               # Unsafe array access
grep -rn "[a-f0-9-]\{36\}" --include="*.ts" src/              # Hardcoded UUIDs
```

## Resources
- [Notion API Reference](https://developers.notion.com/reference/intro)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Property Value Types](https://developers.notion.com/reference/property-value-object)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Request Limits](https://developers.notion.com/reference/request-limits)
