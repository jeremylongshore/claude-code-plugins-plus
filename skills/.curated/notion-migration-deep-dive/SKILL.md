---
name: notion-migration-deep-dive
description: 'Migrate data to/from Notion or between Notion workspaces with data mapping
  and validation.

  Use when migrating data into Notion databases, exporting from Notion, syncing between
  workspaces, or building ETL pipelines with Notion as source or destination.

  Trigger with phrases like "migrate notion", "notion migration", "import to notion",
  "export from notion", "notion data migration", "notion ETL".

  '
allowed-tools: Read, Bash(npm:*), Bash(node:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Migration Deep Dive

## Overview

Production migration patterns for moving data to, from, and between Notion workspaces — rate-limited bulk import, paginated export, cross-platform conversion, and post-migration validation. Every bulk-write path respects Notion's 3 requests/second average rate limit.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- `p-queue` for rate-limited concurrency (`npm install p-queue`)
- Source data access (CSV files, Confluence API, Google Docs API, etc.)
- Target Notion database(s) created with matching property schema

**Authentication:** create a Notion internal integration at
[notion.so/my-integrations](https://www.notion.so/my-integrations), share the
target database(s) with it, and export the secret as `NOTION_TOKEN`. Every code
sample reads `process.env.NOTION_TOKEN` — the client never takes an inline
credential.

## Instructions

The workflow has three directions. Each step below gives the essential shape;
the full runnable code lives in the reference files so this page stays scannable.

### Step 1: Import CSV/JSON into a Notion database

Map each source field to a Notion property value object, strip properties the
target schema does not have, and create pages through a rate-limited queue:

```typescript
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 }); // ≤3 req/s

await notion.pages.create({
  parent: { database_id: databaseId },
  properties: {
    Name: { title: [{ text: { content: record.name || 'Untitled' } }] },
    Status: { select: { name: record.status || 'Not Started' } },
  },
});
```

Validate the database schema with `databases.retrieve` **before** the loop so
mismatched columns are dropped instead of failing every row. Full TypeScript +
Python importers (property mapping, schema filtering, error collection):
[full walkthrough](references/implementation.md).

### Step 2: Export from Notion to JSON/CSV

Page through `databases.query` (100 rows per page) and flatten each page's
properties by type. Optionally pull block content for rich-content migrations:

```typescript
do {
  const response = await notion.databases.query({
    database_id: databaseId, page_size: 100, start_cursor: cursor,
  });
  // extractProperties() maps title/select/multi_select/date/relation/... to flat values
  cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
} while (cursor);
```

Full exporter with the per-property-type extractor and block-content reader:
[full walkthrough](references/implementation.md).

### Step 3: Cross-platform migration and validation

See [cross-platform migration patterns](references/cross-platform-migration.md)
for HTML/Markdown to Notion block conversion, batch content appending (100-block
batches), cross-database sync with duplicate detection, and post-migration
validation with integrity checks.

## Output

- Rate-limited CSV/JSON import with property mapping and schema validation
- Full database export with pagination and property extraction (all property types)
- Page content export (block-level) for rich content migration
- HTML/Markdown to Notion block conversion for Confluence/Google Docs content
- Cross-database sync with duplicate detection
- Post-migration validation comparing source and target with integrity checks
- Dual language support (TypeScript and Python)

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `validation_error` on import | Property name mismatch | Retrieve database schema first with `databases.retrieve` |
| Rate limited during bulk import | Exceeding 3 req/s | Use PQueue with `intervalCap: 3, interval: 1000` |
| Empty title error | Missing required title field | Default to `'Untitled'` for empty names |
| Select option not found | New option value | Notion auto-creates new select options (not an error) |
| Relation import fails | Target pages don't exist yet | Import referenced pages first, then create relations |
| Rich text truncated | Text exceeds 2000 char limit | Split into multiple text blocks |
| Block append fails | More than 100 blocks | Batch blocks in groups of 100 |

## Examples

### One-Line CSV Import

```bash
# Quick import with Node.js script
node -e "
const { Client } = require('@notionhq/client');
const { parse } = require('csv-parse/sync');
const fs = require('fs');
const notion = new Client({ auth: process.env.NOTION_TOKEN });
const rows = parse(fs.readFileSync('data.csv', 'utf-8'), { columns: true });
(async () => {
  for (const row of rows) {
    await notion.pages.create({
      parent: { database_id: process.env.NOTION_DB_ID },
      properties: { Name: { title: [{ text: { content: row.name } }] } }
    });
    await new Promise(r => setTimeout(r, 350)); // ~3 req/s throttle
  }
  console.log('Done:', rows.length, 'imported');
})();
"
```

### Export to JSON File

```typescript
const data = await exportDatabase(process.env.NOTION_DB_ID!);
writeFileSync('export.json', JSON.stringify(data, null, 2));
console.log(`Exported ${data.length} records to export.json`);
```

The `exportDatabase` and `importFromCSV` helpers referenced here are defined in
full in [references/implementation.md](references/implementation.md).

## Resources

- [Create a Page](https://developers.notion.com/reference/post-page) — import endpoint
- [Query a Database](https://developers.notion.com/reference/post-database-query) — export with pagination
- [Append Block Children](https://developers.notion.com/reference/patch-block-children) — add content blocks
- [Property Value Object](https://developers.notion.com/reference/property-value-object) — all property types
- [Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/s average
- [Block Types](https://developers.notion.com/reference/block) — paragraph, heading, list, code, etc.
- **Related skill:** for advanced debugging of migration issues, see `notion-advanced-troubleshooting`.
