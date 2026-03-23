---
name: notion-content-management
description: |
  Create, update, archive, and compose Notion pages and block content.
  Use when building pages programmatically, appending rich content blocks,
  updating page properties, or managing page lifecycle (archive/restore).
  Trigger with phrases like "notion create page", "notion add blocks",
  "notion update page", "notion archive page", "notion content",
  "notion block types", "notion rich text".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Content Management

## Overview
Complete guide to creating, updating, archiving, and composing Notion pages and block content using the `@notionhq/client` SDK. Covers page lifecycle, all common block types, rich text formatting, and bulk content operations.

## Prerequisites
- Completed `notion-install-auth` setup
- `NOTION_TOKEN` environment variable set
- Target database or page shared with your integration (via Connections menu)
- `@notionhq/client` v2+ installed (TypeScript) or `notion-client` (Python)

## Instructions

### Step 1: Create, Update, and Archive Pages

Create a page in a database with typed properties and initial block content:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Create a page with properties and inline content
async function createPage(databaseId: string) {
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    icon: { emoji: '📄' },
    cover: {
      external: { url: 'https://images.unsplash.com/photo-cover-id' },
    },
    properties: {
      // Title property (required for database pages)
      Name: {
        title: [{ text: { content: 'Q1 Sprint Retrospective' } }],
      },
      Status: {
        select: { name: 'In Progress' },
      },
      Priority: {
        select: { name: 'High' },
      },
      Tags: {
        multi_select: [{ name: 'Engineering' }, { name: 'Sprint' }],
      },
      'Due Date': {
        date: { start: '2026-04-01', end: '2026-04-05' },
      },
      Assignee: {
        people: [{ id: 'user-uuid-here' }],
      },
      Effort: {
        number: 8,
      },
      Done: {
        checkbox: false,
      },
      URL: {
        url: 'https://example.com/sprint-board',
      },
    },
    // Initial page body (block children)
    children: [
      {
        heading_2: {
          rich_text: [{ text: { content: 'Summary' } }],
        },
      },
      {
        paragraph: {
          rich_text: [{ text: { content: 'This page tracks the Q1 sprint retrospective.' } }],
        },
      },
    ],
  });

  console.log('Created page:', page.id);
  return page;
}
```

Update page properties after creation:

```typescript
async function updatePageProperties(pageId: string) {
  const updated = await notion.pages.update({
    page_id: pageId,
    properties: {
      Status: { select: { name: 'Done' } },
      Done: { checkbox: true },
      // Clear a property by setting to null
      'Due Date': { date: null },
    },
    // Update icon/cover
    icon: { emoji: '✅' },
  });

  console.log('Updated page:', updated.id);
  return updated;
}
```

Archive and restore pages:

```typescript
// Archive (soft-delete)
async function archivePage(pageId: string) {
  await notion.pages.update({ page_id: pageId, archived: true });
  console.log('Archived page:', pageId);
}

// Restore from archive
async function restorePage(pageId: string) {
  await notion.pages.update({ page_id: pageId, archived: false });
  console.log('Restored page:', pageId);
}
```

### Step 2: Compose Content with Block Types

Append blocks to an existing page. Each block type has its own shape:

```typescript
async function appendBlocks(pageId: string) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [
      // Headings (heading_1, heading_2, heading_3)
      {
        heading_1: {
          rich_text: [{ text: { content: 'Project Overview' } }],
          is_toggleable: false,
        },
      },

      // Paragraph with rich text formatting
      {
        paragraph: {
          rich_text: [
            { text: { content: 'This is ' } },
            { text: { content: 'bold text' }, annotations: { bold: true } },
            { text: { content: ' and ' } },
            { text: { content: 'inline code' }, annotations: { code: true } },
            { text: { content: '. Visit ' } },
            {
              text: { content: 'our docs', link: { url: 'https://example.com' } },
              annotations: { italic: true },
            },
            { text: { content: '.' } },
          ],
        },
      },

      // Bulleted list items
      {
        bulleted_list_item: {
          rich_text: [{ text: { content: 'First bullet point' } }],
        },
      },
      {
        bulleted_list_item: {
          rich_text: [{ text: { content: 'Second bullet point' } }],
        },
      },

      // Numbered list items
      {
        numbered_list_item: {
          rich_text: [{ text: { content: 'Step one' } }],
        },
      },
      {
        numbered_list_item: {
          rich_text: [{ text: { content: 'Step two' } }],
        },
      },

      // To-do items
      {
        to_do: {
          rich_text: [{ text: { content: 'Review pull requests' } }],
          checked: false,
        },
      },
      {
        to_do: {
          rich_text: [{ text: { content: 'Update documentation' } }],
          checked: true,
        },
      },

      // Toggle block (collapsible)
      {
        toggle: {
          rich_text: [{ text: { content: 'Click to expand details' } }],
          children: [
            {
              paragraph: {
                rich_text: [{ text: { content: 'Hidden content inside toggle.' } }],
              },
            },
          ],
        },
      },

      // Code block
      {
        code: {
          rich_text: [{ text: { content: 'const x = 42;\nconsole.log(x);' } }],
          language: 'typescript',
          caption: [{ text: { content: 'Example snippet' } }],
        },
      },

      // Callout
      {
        callout: {
          rich_text: [{ text: { content: 'Important: review before merging.' } }],
          icon: { emoji: '⚠️' },
          color: 'yellow_background',
        },
      },

      // Quote
      {
        quote: {
          rich_text: [{ text: { content: 'Ship early, ship often.' } }],
          color: 'gray',
        },
      },

      // Divider
      { divider: {} },

      // Image (external URL)
      {
        image: {
          external: { url: 'https://example.com/diagram.png' },
          caption: [{ text: { content: 'System architecture diagram' } }],
        },
      },

      // Table (3 columns x 2 rows)
      {
        table: {
          table_width: 3,
          has_column_header: true,
          has_row_header: false,
          children: [
            {
              table_row: {
                cells: [
                  [{ text: { content: 'Feature' } }],
                  [{ text: { content: 'Status' } }],
                  [{ text: { content: 'Owner' } }],
                ],
              },
            },
            {
              table_row: {
                cells: [
                  [{ text: { content: 'Auth' } }],
                  [{ text: { content: 'Done' } }],
                  [{ text: { content: 'Alice' } }],
                ],
              },
            },
          ],
        },
      },
    ],
  });

  console.log('Blocks appended to page:', pageId);
}
```

### Step 3: Update and Delete Individual Blocks

Retrieve, modify, and remove specific blocks:

```typescript
// List all child blocks of a page
async function listBlocks(pageId: string) {
  const blocks: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      start_cursor: cursor,
      page_size: 100,
    });
    blocks.push(...response.results);
    cursor = response.has_more ? response.next_cursor! : undefined;
  } while (cursor);

  return blocks;
}

// Update a specific block's content
async function updateBlock(blockId: string) {
  await notion.blocks.update({
    block_id: blockId,
    paragraph: {
      rich_text: [
        { text: { content: 'Updated paragraph content with ' } },
        { text: { content: 'new formatting' }, annotations: { bold: true, color: 'red' } },
      ],
    },
  });
  console.log('Block updated:', blockId);
}

// Update a to-do block's checked state
async function toggleTodo(blockId: string, checked: boolean) {
  await notion.blocks.update({
    block_id: blockId,
    to_do: {
      checked,
    },
  });
}

// Delete a block (moves to trash, recoverable for 30 days)
async function deleteBlock(blockId: string) {
  await notion.blocks.delete({ block_id: blockId });
  console.log('Deleted block:', blockId);
}

// Retrieve a single block by ID
async function getBlock(blockId: string) {
  const block = await notion.blocks.retrieve({ block_id: blockId });
  console.log('Block type:', block.type, 'Has children:', block.has_children);
  return block;
}
```

## Output
- Created pages with typed properties, icons, covers, and initial block content
- Updated page properties and metadata
- Archived and restored pages
- Appended all common block types: headings, paragraphs, lists, to-dos, toggles, code, callouts, quotes, dividers, images, and tables
- Retrieved, updated, and deleted individual blocks

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `validation_error` (400) | Wrong property type or name | Retrieve database schema with `databases.retrieve()` to confirm property names and types |
| `object_not_found` (404) | Page/block not shared with integration | Open the page in Notion, click `...` > Connections > add your integration |
| `unauthorized` (401) | Invalid or expired token | Regenerate at `notion.so/my-integrations` and update `NOTION_TOKEN` |
| `rate_limited` (429) | Over 3 requests/second | Implement exponential backoff; read `Retry-After` header |
| `conflict_error` (409) | Concurrent edit to same block | Retry with fresh block data from `blocks.retrieve()` |
| `body too large` (413) | Over 100 blocks in one append | Batch into chunks of 100 blocks per `blocks.children.append` call |

## Examples

### Complete Page Builder
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function buildMeetingNotes(databaseId: string) {
  // 1. Create the page
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    icon: { emoji: '📝' },
    properties: {
      Name: { title: [{ text: { content: `Standup ${new Date().toISOString().slice(0, 10)}` } }] },
      Status: { select: { name: 'In Progress' } },
      Tags: { multi_select: [{ name: 'Standup' }, { name: 'Daily' }] },
    },
  });

  // 2. Append structured content
  await notion.blocks.children.append({
    block_id: page.id,
    children: [
      { heading_2: { rich_text: [{ text: { content: 'Yesterday' } }] } },
      { bulleted_list_item: { rich_text: [{ text: { content: 'Completed auth integration' } }] } },
      { bulleted_list_item: { rich_text: [{ text: { content: 'Fixed rate-limit retry logic' } }] } },
      { heading_2: { rich_text: [{ text: { content: 'Today' } }] } },
      { to_do: { rich_text: [{ text: { content: 'Build content management module' } }], checked: false } },
      { to_do: { rich_text: [{ text: { content: 'Write integration tests' } }], checked: false } },
      { heading_2: { rich_text: [{ text: { content: 'Blockers' } }] } },
      {
        callout: {
          rich_text: [{ text: { content: 'Waiting on API key for staging environment.' } }],
          icon: { emoji: '🚧' },
          color: 'red_background',
        },
      },
    ],
  });

  console.log('Meeting notes page:', `https://notion.so/${page.id.replace(/-/g, '')}`);
  return page;
}
```

### Python Example
```python
import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Create a page
page = notion.pages.create(
    parent={"database_id": "your-database-id"},
    properties={
        "Name": {"title": [{"text": {"content": "Python Page"}}]},
        "Status": {"select": {"name": "Draft"}},
        "Tags": {"multi_select": [{"name": "API"}, {"name": "Python"}]},
    },
)
print(f"Created: {page['id']}")

# Update properties
notion.pages.update(
    page_id=page["id"],
    properties={
        "Status": {"select": {"name": "Done"}},
    },
)

# Append blocks
notion.blocks.children.append(
    block_id=page["id"],
    children=[
        {"heading_2": {"rich_text": [{"text": {"content": "Notes"}}]}},
        {
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "Created via "}},
                    {"text": {"content": "Python SDK"}, "annotations": {"bold": True}},
                ]
            }
        },
        {
            "code": {
                "rich_text": [{"text": {"content": "print('hello notion')"}}],
                "language": "python",
            }
        },
        {"divider": {}},
        {
            "to_do": {
                "rich_text": [{"text": {"content": "Review and publish"}}],
                "checked": False,
            }
        },
    ],
)

# Archive the page
notion.pages.update(page_id=page["id"], archived=True)
```

### Batch Block Append (Chunked for >100 Blocks)
```typescript
async function appendBlocksChunked(
  pageId: string,
  blocks: any[],
  chunkSize = 100,
) {
  for (let i = 0; i < blocks.length; i += chunkSize) {
    const chunk = blocks.slice(i, i + chunkSize);
    await notion.blocks.children.append({
      block_id: pageId,
      children: chunk,
    });
    // Respect rate limits between chunks
    if (i + chunkSize < blocks.length) {
      await new Promise((r) => setTimeout(r, 350));
    }
  }
}
```

## Resources
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)
- [Create a Page](https://developers.notion.com/reference/post-page)
- [Update Page Properties](https://developers.notion.com/reference/patch-page)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Block Type Reference](https://developers.notion.com/reference/block)
- [Rich Text Object](https://developers.notion.com/reference/rich-text)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)
- [notion-sdk-py GitHub](https://github.com/ramnes/notion-sdk-py)

## Next Steps
Proceed to `notion-data-handling` for database queries, filtering, sorting, and pagination patterns.
