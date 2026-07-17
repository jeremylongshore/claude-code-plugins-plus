---
name: notion-core-workflow-a
description: 'Query, filter, and manage Notion databases and pages.

  Use when building database queries with filters and sorts,

  creating/updating pages with typed properties, or reading page content.

  Trigger with phrases like "notion database query", "notion filter",

  "notion create page", "notion update properties", "notion CRUD".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Core Workflow A — Databases & Pages

## Overview

Primary workflow for Notion integrations: querying databases with filters/sorts, creating pages with typed properties, updating page properties, and retrieving page content.

## Prerequisites

- Completed `notion-install-auth` setup
- A Notion database shared with your integration
- Understanding of your database's property schema

## Authentication

Every call below uses a `Client` authenticated with an integration token
(`process.env.NOTION_TOKEN`). Token creation, secret storage, and sharing a
database with the integration are covered end-to-end in the `notion-install-auth`
skill — complete it first. Never hardcode the token; read it from the environment.

## Instructions

The workflow is six steps. Steps 1–2 (schema + filtered query) are the skeleton
you almost always start with, shown here in full. Steps 3–6 (filter syntax by
type, page creation, updates/archive, pagination) live in
[the full walkthrough](references/implementation.md) so this file stays scannable.

### Step 1: Retrieve Database Schema

Always inspect the schema first — property names and types drive every filter
and write. `databases.retrieve` returns `db.properties` keyed by property name.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function getDatabaseSchema(databaseId: string) {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  for (const [name, prop] of Object.entries(db.properties)) {
    console.log(`${name}: ${prop.type}`);
    if (prop.type === 'select') {
      console.log('  Options:', prop.select.options.map(o => o.name));
    }
  }
  return db.properties;
}
```

### Step 2: Query with Filters

Notion filters use a nested structure keyed by property type, and combine with
`and` / `or`. `sorts` and `page_size` (max 100) tune the result set.

```typescript
async function queryWithFilters(databaseId: string) {
  const response = await notion.databases.query({
    database_id: databaseId,
    filter: {
      and: [
        { property: 'Status', select: { equals: 'In Progress' } },
        { property: 'Priority', select: { does_not_equal: 'Low' } },
      ],
    },
    sorts: [{ property: 'Priority', direction: 'ascending' }],
    page_size: 50,
  });
  return response.results;
}
```

### Steps 3–6: Filter syntax, create, update, paginate

See [the full walkthrough](references/implementation.md) for copy-paste code:

- **Step 3 — Filter syntax by property type.** Every property type (text,
  number, select, date, checkbox, people, relation, formula, rollup, timestamp)
  has its own filter shape.
- **Step 4 — Create a page with all property types.** One `pages.create` call
  showing the correct payload for each typed property.
- **Step 5 — Update & archive.** `pages.update` to change properties, or set
  `archived: true` to soft-delete.
- **Step 6 — Paginate all results.** Loop on `has_more` / `next_cursor` to pull
  a full database beyond the 100-row page limit.

## Output

- Database schema retrieved with property types and options
- Filtered and sorted query results
- Pages created with typed properties
- Pages updated and archived

## Error Handling

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `validation_error` | Property name mismatch or wrong type | Use `databases.retrieve` to check schema |
| `object_not_found` | Database not shared with integration | Add integration via Connections |
| `rate_limited` (429) | >3 requests/second average | Respect `Retry-After` header |
| Empty `results` | Filter too restrictive or no data | Test with no filter first |

## Examples

Reading queried pages back into plain values requires switching on each
property's `type`. A reusable `getPropertyValue` helper plus a full
"flatten a database into an array of objects" example live in
[examples & helpers](references/examples.md):

```typescript
// Excerpt — full helper in references/examples.md
function getPropertyValue(property: any) {
  switch (property.type) {
    case 'title':  return property.title.map((t: any) => t.plain_text).join('');
    case 'number': return property.number;
    case 'select': return property.select?.name ?? null;
    // ...rich_text, multi_select, date, checkbox, url, email, formula
    default:       return null;
  }
}
```

## Resources

- [Query a Database](https://developers.notion.com/reference/post-database-query)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Create a Page](https://developers.notion.com/reference/post-page)
- [Page Property Values](https://developers.notion.com/reference/page-property-values)
- [Database Object](https://developers.notion.com/reference/database)
- [Full CRUD walkthrough (Steps 1–6)](references/implementation.md)
- [Examples & helpers](references/examples.md)
- For block-level content operations, see the `notion-core-workflow-b` skill.
