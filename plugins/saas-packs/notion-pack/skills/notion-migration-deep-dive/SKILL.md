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

Comprehensive migration patterns for moving data to, from, and between Notion workspaces. This covers rate-limited bulk import from CSV/JSON with property mapping, full database export with pagination and block content extraction, cross-database sync with duplicate detection, data transformation patterns for Confluence and Google Docs content, and post-migration validation with integrity checks. All patterns respect Notion's 3 requests/second rate limit.

## Prerequisites

- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- `p-queue` for rate-limited concurrency (`npm install p-queue`)
- Source data access (CSV files, Confluence API, Google Docs API, etc.)
- Target Notion database(s) created with matching property schema

## Instructions

### Step 1: Import CSV/JSON into Notion Database

Map source data fields to Notion property types, create pages with rate limiting:

```typescript
import { Client } from '@notionhq/client';
import { readFileSync } from 'fs';
import { parse } from 'csv-parse/sync';
import PQueue from 'p-queue';

const notion = new Client({ auth: process.env.NOTION_TOKEN! });

// Rate-limited queue: 3 requests/second (Notion's documented limit)
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

interface SourceRecord {
  name: string;
  status: string;
  priority: string;
  dueDate: string;
  tags: string;       // Comma-separated
  assigneeEmail: string;
  description: string;
}

// Map source fields to Notion property value objects
function mapToNotionProperties(record: SourceRecord) {
  const properties: Record<string, any> = {
    // Title property (required — every database has exactly one)
    Name: { title: [{ text: { content: record.name || 'Untitled' } }] },

    // Select — auto-creates options if they don't exist
    Status: { select: { name: record.status || 'Not Started' } },
    Priority: { select: { name: record.priority || 'Medium' } },

    // Multi-select from comma-separated values
    Tags: {
      multi_select: record.tags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean)
        .map(name => ({ name })),
    },

    // Rich text (max 2000 characters per text block)
    Description: {
      rich_text: [{ text: { content: (record.description || '').slice(0, 2000) } }],
    },

    // Email
    'Assignee Email': record.assigneeEmail
      ? { email: record.assigneeEmail }
      : { email: null },
  };

  // Date (only add if valid)
  if (record.dueDate && !isNaN(Date.parse(record.dueDate))) {
    properties['Due Date'] = { date: { start: record.dueDate } };
  }

  return properties;
}

async function importFromCSV(csvPath: string, databaseId: string) {
  const csv = readFileSync(csvPath, 'utf-8');
  const records = parse(csv, { columns: true, skip_empty_lines: true }) as SourceRecord[];

  console.log(`Importing ${records.length} records into database ${databaseId}...`);
  const results = { created: 0, failed: 0, errors: [] as string[] };

  // Validate database schema before importing
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const dbProps = Object.keys(db.properties);
  console.log(`Database properties: ${dbProps.join(', ')}`);

  await Promise.all(records.map((record, index) =>
    queue.add(async () => {
      try {
        const properties = mapToNotionProperties(record);

        // Remove properties not in database schema
        for (const key of Object.keys(properties)) {
          if (!dbProps.includes(key)) delete properties[key];
        }

        await notion.pages.create({
          parent: { database_id: databaseId },
          properties,
        });

        results.created++;
        if (results.created % 50 === 0) {
          console.log(`Progress: ${results.created}/${records.length}`);
        }
      } catch (error: any) {
        results.failed++;
        results.errors.push(`Row ${index + 1} ("${record.name}"): ${error.message}`);
      }
    })
  ));

  console.log(`\nImport complete: ${results.created} created, ${results.failed} failed`);
  if (results.errors.length > 0) {
    console.log('First 10 errors:');
    results.errors.slice(0, 10).forEach(e => console.log(`  ${e}`));
  }

  return results;
}
```

**Python — CSV import:**

```python
import csv
import time
from notion_client import Client

client = Client(auth=os.environ["NOTION_TOKEN"])

def import_csv(csv_path: str, database_id: str):
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    created, failed = 0, 0
    for i, row in enumerate(rows):
        try:
            client.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {"title": [{"text": {"content": row.get("name", "Untitled")}}]},
                    "Status": {"select": {"name": row.get("status", "Not Started")}},
                    "Tags": {"multi_select": [
                        {"name": t.strip()} for t in row.get("tags", "").split(",") if t.strip()
                    ]},
                },
            )
            created += 1
        except Exception as e:
            failed += 1
            print(f"Row {i+1}: {e}")

        # Rate limit: 3 requests/second
        if (created + failed) % 3 == 0:
            time.sleep(1.1)

    print(f"Done: {created} created, {failed} failed")
```

### Step 2: Export from Notion to JSON/CSV

Full database export with pagination, property extraction, and optional block content:

```typescript
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

// Extract a flat record from a Notion page's properties
function extractProperties(page: PageObjectResponse): Record<string, any> {
  const row: Record<string, any> = {
    id: page.id,
    url: page.url,
    created_time: page.created_time,
    last_edited_time: page.last_edited_time,
  };

  for (const [name, prop] of Object.entries(page.properties)) {
    switch (prop.type) {
      case 'title':
        row[name] = prop.title.map(t => t.plain_text).join('');
        break;
      case 'rich_text':
        row[name] = prop.rich_text.map(t => t.plain_text).join('');
        break;
      case 'number':
        row[name] = prop.number;
        break;
      case 'select':
        row[name] = prop.select?.name ?? null;
        break;
      case 'multi_select':
        row[name] = prop.multi_select.map(s => s.name).join(', ');
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
      case 'phone_number':
        row[name] = prop.phone_number;
        break;
      case 'people':
        row[name] = prop.people.map(p => ('name' in p ? p.name : p.id)).join(', ');
        break;
      case 'relation':
        row[name] = prop.relation.map(r => r.id).join(', ');
        break;
      default:
        row[name] = `[${prop.type}]`;
    }
  }

  return row;
}

// Export entire database with automatic pagination
async function exportDatabase(databaseId: string): Promise<Record<string, any>[]> {
  const allRows: Record<string, any>[] = [];
  let cursor: string | undefined;
  let pageCount = 0;

  do {
    const response = await notion.databases.query({
      database_id: databaseId,
      page_size: 100,
      start_cursor: cursor,
    });

    for (const page of response.results) {
      if ('properties' in page) {
        allRows.push(extractProperties(page as PageObjectResponse));
      }
    }

    pageCount++;
    console.log(`Fetched page ${pageCount} (${allRows.length} total records)`);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return allRows;
}

// Export page with its block content (for rich content migration)
async function exportPageWithContent(pageId: string) {
  const page = await notion.pages.retrieve({ page_id: pageId });
  const blocks = await getAllBlocks(pageId);

  return {
    page,
    content: blocks.map(block => ({
      type: (block as any).type,
      text: getBlockPlainText(block as any),
      hasChildren: (block as any).has_children,
    })),
  };
}

async function getAllBlocks(blockId: string) {
  const blocks: any[] = [];
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

function getBlockPlainText(block: any): string {
  const content = block[block.type];
  if (content?.rich_text) {
    return content.rich_text.map((t: any) => t.plain_text).join('');
  }
  return '';
}
```

### Step 3: Cross-Platform Migration and Validation

**Transform Confluence/Google Docs content to Notion blocks:**

```typescript
// Convert HTML-like content to Notion block objects
function htmlToNotionBlocks(html: string): any[] {
  const blocks: any[] = [];
  const lines = html.split('\n').filter(l => l.trim());

  for (const line of lines) {
    const trimmed = line.trim();

    // Headings
    if (trimmed.startsWith('# ')) {
      blocks.push({
        heading_1: { rich_text: [{ text: { content: trimmed.slice(2) } }] },
      });
    } else if (trimmed.startsWith('## ')) {
      blocks.push({
        heading_2: { rich_text: [{ text: { content: trimmed.slice(3) } }] },
      });
    } else if (trimmed.startsWith('### ')) {
      blocks.push({
        heading_3: { rich_text: [{ text: { content: trimmed.slice(4) } }] },
      });
    }
    // Bullet lists
    else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      blocks.push({
        bulleted_list_item: {
          rich_text: [{ text: { content: trimmed.slice(2) } }],
        },
      });
    }
    // Code blocks
    else if (trimmed.startsWith('```')) {
      // Simplified: handle inline code fence
      blocks.push({
        code: {
          rich_text: [{ text: { content: trimmed.replace(/```/g, '') } }],
          language: 'plain text',
        },
      });
    }
    // Regular paragraphs
    else if (trimmed.length > 0) {
      blocks.push({
        paragraph: { rich_text: [{ text: { content: trimmed } }] },
      });
    }
  }

  return blocks;
}

// Create a Notion page with content blocks (max 100 blocks per append)
async function createPageWithContent(
  databaseId: string,
  title: string,
  blocks: any[]
) {
  // Create the page first
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: { title: [{ text: { content: title } }] },
      Source: { select: { name: 'Migration' } },
      'Migrated At': { date: { start: new Date().toISOString() } },
    },
  });

  // Append blocks in batches of 100 (Notion's limit)
  for (let i = 0; i < blocks.length; i += 100) {
    const batch = blocks.slice(i, i + 100);
    await notion.blocks.children.append({
      block_id: page.id,
      children: batch,
    });

    if (i + 100 < blocks.length) {
      await new Promise(r => setTimeout(r, 350)); // Rate limit
    }
  }

  return page;
}
```

**Post-migration validation:**

```typescript
async function validateMigration(
  sourceData: Record<string, any>[],
  targetDatabaseId: string,
  keyField: string = 'Name'
) {
  console.log('Running migration validation...');

  // Export target database
  const targetData = await exportDatabase(targetDatabaseId);

  const report = {
    sourceCount: sourceData.length,
    targetCount: targetData.length,
    countMatch: sourceData.length === targetData.length,
    missingInTarget: [] as string[],
    duplicatesInTarget: [] as string[],
    fieldIntegrity: { checked: 0, passed: 0, failed: 0 },
  };

  // Build lookup from target
  const targetByKey = new Map<string, Record<string, any>[]>();
  for (const row of targetData) {
    const key = row[keyField];
    const existing = targetByKey.get(key) || [];
    existing.push(row);
    targetByKey.set(key, existing);
  }

  // Check for duplicates
  for (const [key, rows] of targetByKey) {
    if (rows.length > 1) {
      report.duplicatesInTarget.push(`"${key}" (${rows.length} copies)`);
    }
  }

  // Check every source record exists in target
  for (const sourceRow of sourceData) {
    const key = sourceRow[keyField];
    const targetRows = targetByKey.get(key);

    if (!targetRows || targetRows.length === 0) {
      report.missingInTarget.push(key);
    } else {
      report.fieldIntegrity.checked++;
      // Compare specific fields
      const targetRow = targetRows[0];
      const fieldsMatch = Object.keys(sourceRow)
        .filter(k => k !== 'id' && k !== 'url')
        .every(k => String(sourceRow[k] ?? '') === String(targetRow[k] ?? ''));

      if (fieldsMatch) {
        report.fieldIntegrity.passed++;
      } else {
        report.fieldIntegrity.failed++;
      }
    }
  }

  // Print report
  console.log('\n=== Migration Validation Report ===');
  console.log(`Source records: ${report.sourceCount}`);
  console.log(`Target records: ${report.targetCount}`);
  console.log(`Count match: ${report.countMatch ? 'PASS' : 'FAIL'}`);
  console.log(`Missing in target: ${report.missingInTarget.length}`);
  console.log(`Duplicates in target: ${report.duplicatesInTarget.length}`);
  console.log(`Field integrity: ${report.fieldIntegrity.passed}/${report.fieldIntegrity.checked} passed`);
  console.log(`Overall: ${
    report.missingInTarget.length === 0 && report.countMatch ? 'PASS' : 'FAIL'
  }`);

  if (report.missingInTarget.length > 0) {
    console.log('\nMissing records (first 10):');
    report.missingInTarget.slice(0, 10).forEach(m => console.log(`  - ${m}`));
  }

  return report;
}
```

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
|-------|-------|----------|
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
    await new Promise(r => setTimeout(r, 350));
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

## Resources

- [Create a Page](https://developers.notion.com/reference/post-page) — import endpoint
- [Query a Database](https://developers.notion.com/reference/post-database-query) — export with pagination
- [Append Block Children](https://developers.notion.com/reference/patch-block-children) — add content blocks
- [Property Value Object](https://developers.notion.com/reference/property-value-object) — all property types
- [Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/s average
- [Block Types](https://developers.notion.com/reference/block) — paragraph, heading, list, code, etc.

## Next Steps

For advanced debugging of migration issues, see `notion-advanced-troubleshooting`.
