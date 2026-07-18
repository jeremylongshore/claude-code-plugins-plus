# Notion Core Workflow A — Full Implementation Walkthrough

Complete, copy-paste-ready code for the six-step database and page CRUD
workflow. SKILL.md carries the lean skeleton (Steps 1–2); this file holds the
full detail for Steps 3–6 plus the complete versions of every step.

## Step 1: Retrieve Database Schema

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

## Step 2: Query with Filters

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

## Step 3: Filter Syntax by Property Type

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

## Step 4: Create a Page with All Property Types

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

## Step 5: Update Page Properties

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

## Step 6: Paginate Through All Results

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
