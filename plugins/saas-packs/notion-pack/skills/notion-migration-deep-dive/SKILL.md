---
name: notion-migration-deep-dive
description: |
  Migrate data to/from Notion or between Notion workspaces with data mapping and validation.
  Use when migrating data into Notion databases, exporting from Notion, syncing between
  workspaces, or building ETL pipelines with Notion as source or destination.
  Trigger with phrases like "migrate notion", "notion migration", "import to notion",
  "export from notion", "notion data migration", "notion ETL".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Migration Deep Dive

## Overview
Comprehensive guide for migrating data to and from Notion: importing CSV/JSON into databases, exporting Notion content, syncing between workspaces, and handling the unique constraints of Notion's data model.

## Prerequisites
- `@notionhq/client` installed
- Source/target data access
- Understanding of Notion property types (see `notion-core-workflow-a`)

## Instructions

### Step 1: Understand Notion Data Model Constraints
```
Key constraints to plan for:
- Rate limit: 3 requests/second average
- Max page_size: 100 items per query
- Max blocks per append: 100 blocks per request
- One title property per database (required on every page)
- No bulk create endpoint — pages created one at a time
- Select options auto-created if they don't exist
- Relation requires target pages to exist first
```

### Step 2: Import CSV/JSON into Notion Database
```typescript
import { Client } from '@notionhq/client';
import { readFileSync } from 'fs';
import PQueue from 'p-queue';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

interface CsvRow {
  name: string;
  status: string;
  priority: string;
  dueDate: string;
  tags: string; // comma-separated
  description: string;
}

// Map source data to Notion properties
function mapToNotionProperties(row: CsvRow) {
  return {
    Name: { title: [{ text: { content: row.name } }] },
    Status: { select: { name: row.status || 'Not Started' } },
    Priority: { select: { name: row.priority || 'Medium' } },
    'Due Date': row.dueDate ? { date: { start: row.dueDate } } : undefined,
    Tags: {
      multi_select: row.tags.split(',').filter(Boolean).map(t => ({ name: t.trim() })),
    },
    Description: {
      rich_text: [{ text: { content: row.description || '' } }],
    },
  };
}

async function importToNotion(databaseId: string, rows: CsvRow[]) {
  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
  const results = { created: 0, failed: 0, errors: [] as string[] };

  console.log(`Importing ${rows.length} rows...`);

  await Promise.all(rows.map((row, index) =>
    queue.add(async () => {
      try {
        const properties: any = mapToNotionProperties(row);
        // Remove undefined values
        Object.keys(properties).forEach(k => properties[k] === undefined && delete properties[k]);

        await notion.pages.create({
          parent: { database_id: databaseId },
          properties,
        });
        results.created++;

        if (results.created % 10 === 0) {
          console.log(`Progress: ${results.created}/${rows.length}`);
        }
      } catch (error: any) {
        results.failed++;
        results.errors.push(`Row ${index}: ${error.message}`);
      }
    })
  ));

  console.log(`Done: ${results.created} created, ${results.failed} failed`);
  if (results.errors.length > 0) {
    console.log('Errors:', results.errors.slice(0, 10));
  }
  return results;
}
```

### Step 3: Export from Notion to JSON/CSV
```typescript
async function exportDatabase(databaseId: string) {
  const allPages = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: databaseId,
      page_size: 100,
      start_cursor: cursor,
    });
    allPages.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  // Extract properties to flat objects
  const rows = allPages
    .filter((p): p is any => 'properties' in p)
    .map(page => {
      const row: Record<string, any> = {
        id: page.id,
        created_time: page.created_time,
        last_edited_time: page.last_edited_time,
        url: page.url,
      };

      for (const [name, prop] of Object.entries(page.properties) as any[]) {
        switch (prop.type) {
          case 'title':
            row[name] = prop.title.map((t: any) => t.plain_text).join('');
            break;
          case 'rich_text':
            row[name] = prop.rich_text.map((t: any) => t.plain_text).join('');
            break;
          case 'number':
            row[name] = prop.number;
            break;
          case 'select':
            row[name] = prop.select?.name ?? null;
            break;
          case 'multi_select':
            row[name] = prop.multi_select.map((s: any) => s.name).join(', ');
            break;
          case 'date':
            row[name] = prop.date?.start ?? null;
            break;
          case 'checkbox':
            row[name] = prop.checkbox;
            break;
          case 'url':
            row[name] = prop.url;
            break;
          case 'email':
            row[name] = prop.email;
            break;
          default:
            row[name] = `[${prop.type}]`;
        }
      }

      return row;
    });

  return rows;
}

// Export with page content (blocks)
async function exportPageWithContent(pageId: string) {
  const page = await notion.pages.retrieve({ page_id: pageId });
  const blocks = await getAllBlocks(pageId);

  return {
    page,
    content: blocks.map(block => ({
      type: block.type,
      text: getBlockText(block),
      hasChildren: block.has_children,
    })),
  };
}

async function getAllBlocks(blockId: string) {
  const blocks = [];
  let cursor: string | undefined;
  do {
    const response = await notion.blocks.children.list({
      block_id: blockId,
      page_size: 100,
      start_cursor: cursor,
    });
    blocks.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);
  return blocks;
}

function getBlockText(block: any): string {
  const content = block[block.type];
  if (content?.rich_text) {
    return content.rich_text.map((t: any) => t.plain_text).join('');
  }
  return '';
}
```

### Step 4: Sync Between Databases
```typescript
async function syncDatabases(sourceDbId: string, targetDbId: string, keyProperty: string) {
  // Fetch source pages
  const sourcePages = await exportDatabase(sourceDbId);

  // Fetch existing target pages to avoid duplicates
  const targetPages = await exportDatabase(targetDbId);
  const existingKeys = new Set(targetPages.map(p => p[keyProperty]));

  const toCreate = sourcePages.filter(p => !existingKeys.has(p[keyProperty]));
  console.log(`${toCreate.length} new pages to sync (${existingKeys.size} already exist)`);

  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
  let synced = 0;

  await Promise.all(toCreate.map(row =>
    queue.add(async () => {
      const properties: any = {};
      // Map properties (customize based on your schema)
      if (row.Name) properties.Name = { title: [{ text: { content: row.Name } }] };
      if (row.Status) properties.Status = { select: { name: row.Status } };
      // ... add other properties

      await notion.pages.create({
        parent: { database_id: targetDbId },
        properties,
      });
      synced++;
    })
  ));

  console.log(`Synced ${synced} pages`);
}
```

### Step 5: Migration Validation
```typescript
async function validateMigration(sourceDbId: string, targetDbId: string) {
  const source = await exportDatabase(sourceDbId);
  const target = await exportDatabase(targetDbId);

  const report = {
    sourceCount: source.length,
    targetCount: target.length,
    countMatch: source.length === target.length,
    missingInTarget: [] as string[],
    dataIntegrity: true,
  };

  // Check every source page exists in target
  const targetNames = new Set(target.map(p => p.Name));
  for (const page of source) {
    if (!targetNames.has(page.Name)) {
      report.missingInTarget.push(page.Name);
    }
  }

  report.dataIntegrity = report.missingInTarget.length === 0;

  console.log('Migration Validation Report:');
  console.log(`  Source: ${report.sourceCount} pages`);
  console.log(`  Target: ${report.targetCount} pages`);
  console.log(`  Missing: ${report.missingInTarget.length}`);
  console.log(`  Status: ${report.dataIntegrity ? 'PASS' : 'FAIL'}`);

  return report;
}
```

## Output
- Data imported from CSV/JSON into Notion database
- Data exported from Notion to structured format
- Cross-database sync with duplicate detection
- Migration validation report

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `validation_error` on import | Property name mismatch | Retrieve DB schema first |
| Rate limited during import | Too many pages | Use PQueue at 3 req/s |
| Select option not found | Notion auto-creates options | Usually not an error |
| Empty title | Missing required field | Default to fallback title |
| Relation import fails | Target pages don't exist | Import related pages first |

## Examples

### Quick CSV Import
```typescript
import { parse } from 'csv-parse/sync';

const csv = readFileSync('data.csv', 'utf-8');
const rows = parse(csv, { columns: true }) as CsvRow[];
await importToNotion(process.env.NOTION_DB_ID!, rows);
```

## Resources
- [Create a Page](https://developers.notion.com/reference/post-page)
- [Query a Database](https://developers.notion.com/reference/post-database-query)
- [Property Value Object](https://developers.notion.com/reference/property-value-object)
- [Request Limits](https://developers.notion.com/reference/request-limits)

## Next Steps
For advanced troubleshooting, see `notion-advanced-troubleshooting`.
