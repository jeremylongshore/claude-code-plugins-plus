# Import & Export — Full Implementation

Complete, runnable code for the two core migration directions. Every snippet
assumes `process.env.NOTION_TOKEN` holds a Notion integration token with access
to the target database (see the SKILL.md "Prerequisites" section for auth setup).

All bulk-write paths respect Notion's documented **3 requests/second** average
rate limit.

## Step 1: Import CSV/JSON into a Notion database

Map source data fields to Notion property types, then create pages with a
rate-limited queue:

```typescript
import { Client } from '@notionhq/client';
import { readFileSync } from 'fs';
import { parse } from 'csv-parse/sync';
import PQueue from 'p-queue';

const notion = new Client({ auth: process.env.NOTION_TOKEN! });

// Rate-limited queue: at most 3 requests per 1000 ms window.
// interval=1000 is Notion's rate-limit window (1 second); intervalCap=3 is
// its documented average of 3 requests/second — staying under both avoids 429s.
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

    // Rich text — Notion caps a single text block at 2000 characters, so
    // truncate to stay inside the API limit (longer content must be split).
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

## Step 2: Export from Notion to JSON/CSV

Full database export with pagination, property extraction, and optional block
content:

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
