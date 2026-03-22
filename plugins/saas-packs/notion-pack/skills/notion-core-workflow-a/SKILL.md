---
name: notion-core-workflow-a
description: |
  Query, filter, and manage Notion databases and pages.
  Use when building database queries with filters and sorts,
  creating/updating pages with typed properties, or reading page content.
  Trigger with phrases like "notion database query", "notion filter",
  "notion create page", "notion update properties", "notion CRUD".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Core Workflow A — Databases & Pages

## Overview
Primary workflow for Notion integrations: querying databases with filters/sorts, creating pages with typed properties, updating page properties, and retrieving page content.

## Prerequisites
- Completed `notion-install-auth` setup
- A Notion database shared with your integration
- Understanding of your database's property schema

## Instructions

### Step 1: Retrieve Database Schema
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function getDatabaseSchema(databaseId: string) {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  // db.properties contains the schema
  for (const [name, prop] of Object.entries(db.properties)) {
    console.log(`${name}: ${prop.type}`);
    // For select/multi_select, show options:
    if (prop.type === 'select') {
      console.log('  Options:', prop.select.options.map(o => o.name));
    }
  }
  return db.properties;
}
```

### Step 2: Query with Filters
Notion filters use a unique nested structure based on property type:

```typescript
async function queryWithFilters(databaseId: string) {
  const response = await notion.databases.query({
    database_id: databaseId,
    filter: {
      and: [
        {
          property: 'Status',
          select: { equals: 'In Progress' },
        },
        {
          property: 'Priority',
          select: { does_not_equal: 'Low' },
        },
        {
          or: [
            {
              property: 'Assignee',
              people: { contains: 'user-uuid-here' },
            },
            {
              property: 'Tags',
              multi_select: { contains: 'Urgent' },
            },
          ],
        },
      ],
    },
    sorts: [
      { property: 'Priority', direction: 'ascending' },
      { property: 'Created', direction: 'descending' },
    ],
    page_size: 50,
  });

  return response.results;
}
```

### Step 3: Filter Syntax by Property Type
```typescript
// Text (title, rich_text, url, email, phone_number)
{ property: 'Name', title: { contains: 'search term' } }
{ property: 'Description', rich_text: { starts_with: 'Draft' } }
{ property: 'Email', email: { equals: 'user@example.com' } }

// Number
{ property: 'Score', number: { greater_than: 80 } }
{ property: 'Price', number: { less_than_or_equal_to: 100 } }

// Select / Multi-select
{ property: 'Status', select: { equals: 'Done' } }
{ property: 'Tags', multi_select: { contains: 'Bug' } }

// Date
{ property: 'Due Date', date: { before: '2026-04-01' } }
{ property: 'Created', date: { past_week: {} } }
{ property: 'Updated', date: { on_or_after: '2026-01-01' } }

// Checkbox
{ property: 'Archived', checkbox: { equals: false } }

// People
{ property: 'Assignee', people: { contains: 'user-uuid' } }

// Relation
{ property: 'Project', relation: { contains: 'page-uuid' } }

// Formula (filter on the result type)
{ property: 'Computed', formula: { number: { greater_than: 0 } } }

// Rollup (filter on the aggregated result)
{ property: 'Total', rollup: { number: { greater_than: 100 } } }

// Timestamp (no property name needed)
{ timestamp: 'last_edited_time', last_edited_time: { after: '2026-03-01' } }
```

### Step 4: Create a Page with All Property Types
```typescript
async function createFullPage(databaseId: string) {
  return notion.pages.create({
    parent: { database_id: databaseId },
    icon: { emoji: '📋' },
    properties: {
      // Title (required — every database has exactly one)
      Name: {
        title: [{ text: { content: 'New Task' } }],
      },
      // Rich text
      Description: {
        rich_text: [
          { text: { content: 'This is ' } },
          { text: { content: 'important' }, annotations: { bold: true, color: 'red' } },
        ],
      },
      // Number
      Score: { number: 95 },
      // Select
      Status: { select: { name: 'In Progress' } },
      // Multi-select
      Tags: {
        multi_select: [{ name: 'API' }, { name: 'Backend' }],
      },
      // Date (with optional end and timezone)
      'Due Date': {
        date: { start: '2026-04-15', end: '2026-04-20' },
      },
      // Checkbox
      Urgent: { checkbox: true },
      // URL
      Link: { url: 'https://developers.notion.com' },
      // Email
      Contact: { email: 'team@example.com' },
      // People (array of user objects)
      Assignee: {
        people: [{ id: 'user-uuid-here' }],
      },
      // Relation (array of page references)
      Project: {
        relation: [{ id: 'related-page-uuid' }],
      },
    },
  });
}
```

### Step 5: Update Page Properties
```typescript
async function updatePage(pageId: string) {
  return notion.pages.update({
    page_id: pageId,
    properties: {
      Status: { select: { name: 'Done' } },
      Score: { number: 100 },
      Urgent: { checkbox: false },
    },
  });
}

// Archive (soft delete) a page
async function archivePage(pageId: string) {
  return notion.pages.update({
    page_id: pageId,
    archived: true,
  });
}
```

### Step 6: Paginate Through All Results
```typescript
async function getAllPages(databaseId: string) {
  const allPages = [];
  let cursor: string | undefined = undefined;

  do {
    const response = await notion.databases.query({
      database_id: databaseId,
      start_cursor: cursor,
      page_size: 100, // max is 100
    });
    allPages.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return allPages;
}
```

## Output
- Database schema retrieved with property types and options
- Filtered and sorted query results
- Pages created with typed properties
- Pages updated and archived

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `validation_error` | Property name mismatch or wrong type | Use `databases.retrieve` to check schema |
| `object_not_found` | Database not shared with integration | Add integration via Connections |
| `rate_limited` (429) | >3 requests/second average | Respect `Retry-After` header |
| Empty `results` | Filter too restrictive or no data | Test with no filter first |

## Examples

### Extract Property Values Helper
```typescript
function getPropertyValue(property: any): string | number | boolean | null {
  switch (property.type) {
    case 'title':
      return property.title.map((t: any) => t.plain_text).join('');
    case 'rich_text':
      return property.rich_text.map((t: any) => t.plain_text).join('');
    case 'number':
      return property.number;
    case 'select':
      return property.select?.name ?? null;
    case 'multi_select':
      return property.multi_select.map((s: any) => s.name).join(', ');
    case 'date':
      return property.date?.start ?? null;
    case 'checkbox':
      return property.checkbox;
    case 'url':
      return property.url;
    case 'email':
      return property.email;
    case 'formula':
      return property.formula?.[property.formula.type] ?? null;
    default:
      return null;
  }
}
```

## Resources
- [Query a Database](https://developers.notion.com/reference/post-database-query)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Create a Page](https://developers.notion.com/reference/post-page)
- [Page Property Values](https://developers.notion.com/reference/page-property-values)
- [Database Object](https://developers.notion.com/reference/database)

## Next Steps
For block-level content operations, see `notion-core-workflow-b`.
