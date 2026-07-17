---
name: notion-content-management
description: 'Create, update, archive, and compose Notion pages and block content.

  Use when building pages programmatically, appending rich content blocks,

  updating page properties, or managing page lifecycle (archive/restore).

  Trigger with phrases like "notion create page", "notion add blocks",

  "notion update page", "notion archive page", "notion content",

  "notion block types", "notion rich text".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Content Management

## Overview

Complete guide to creating, updating, archiving, and composing Notion pages and block content using the `@notionhq/client` SDK. Covers page lifecycle, all common block types, rich text formatting, and bulk content operations. The core workflow lives here at a high level; deep code walkthroughs are extracted into `references/` so this file stays scannable.

## Prerequisites

- Completed `notion-install-auth` setup
- `NOTION_TOKEN` environment variable set
- Target database or page shared with the integration (via Connections menu)
- `@notionhq/client` v2+ installed (TypeScript) or `notion-client` (Python)

## Instructions

### Step 1: Create, Update, and Archive Pages

Create a page in a database with typed properties (`title`, `select`, `multi_select`, `date`, `people`, `number`, `checkbox`, `url`), an optional `icon`/`cover`, and initial `children` block content. Update properties with `pages.update` (set a property to `null` to clear it). Archive is a soft-delete via `archived: true`, and restore flips it back to `false`.

Minimal skeleton:

```typescript
import { Client } from '@notionhq/client';
const notion = new Client({ auth: process.env.NOTION_TOKEN });

const page = await notion.pages.create({
  parent: { database_id: databaseId },
  properties: { Name: { title: [{ text: { content: 'Q1 Retro' } }] } },
});
await notion.pages.update({ page_id: page.id, properties: { Status: { select: { name: 'Done' } } } });
await notion.pages.update({ page_id: page.id, archived: true });  // archive
```

Full typed-property create, update-with-clear, and archive/restore functions: [page lifecycle walkthrough](references/page-lifecycle.md).

### Step 2: Compose Content with Block Types

Append blocks to an existing page with `blocks.children.append`. Each block type has its own payload shape — headings, paragraphs (with rich text annotations), bulleted/numbered lists, to-dos, toggles, code blocks, callouts, quotes, dividers, images, and tables are all supported. The full catalog with the exact shape for every block type is in [the block type catalog](references/block-type-catalog.md).

The minimal pattern:

```typescript
await notion.blocks.children.append({
  block_id: pageId,
  children: [
    { heading_2: { rich_text: [{ text: { content: 'Notes' } }] } },
    {
      paragraph: {
        rich_text: [
          { text: { content: 'Plain and ' } },
          { text: { content: 'bold' }, annotations: { bold: true } },
        ],
      },
    },
    { to_do: { rich_text: [{ text: { content: 'Review PRs' } }], checked: false } },
  ],
});
```

### Step 3: Update and Delete Individual Blocks

Retrieve, modify, and remove specific blocks: `blocks.children.list` (paginate with `start_cursor`), `blocks.update` to change content or toggle a to-do's `checked` state, `blocks.delete` to trash a block (recoverable for 30 days), and `blocks.retrieve` to fetch one block.

Minimal skeleton:

```typescript
await notion.blocks.update({ block_id: blockId, to_do: { checked: true } });
await notion.blocks.delete({ block_id: blockId });
```

Full paginated list, rich-text update, to-do toggle, delete, and retrieve helpers: [block editing walkthrough](references/block-editing.md).

## Output

- Created pages with typed properties, icons, covers, and initial block content
- Updated page properties and metadata
- Archived and restored pages
- Appended all common block types: headings, paragraphs, lists, to-dos, toggles, code, callouts, quotes, dividers, images, and tables
- Retrieved, updated, and deleted individual blocks

## Error Handling

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `validation_error` (400) | Wrong property type or name | Retrieve database schema with `databases.retrieve()` to confirm property names and types |
| `object_not_found` (404) | Page/block not shared with integration | Open the page in Notion, click `...` > Connections > add the integration |
| `unauthorized` (401) | Invalid or expired token | Regenerate at `notion.so/my-integrations` and update `NOTION_TOKEN` |
| `rate_limited` (429) | Over 3 requests/second | Implement exponential backoff; read `Retry-After` header |
| `conflict_error` (409) | Concurrent edit to same block | Retry with fresh block data from `blocks.retrieve()` |
| `body too large` (413) | Over 100 blocks in one append | Batch into chunks of 100 blocks per `blocks.children.append` call |

## Examples

A page builder composes a create call plus a structured `blocks.children.append` in sequence — for example, a standup note with `heading_2` sections, `bulleted_list_item` history, `to_do` tasks, and a `callout` for blockers:

```typescript
const page = await notion.pages.create({
  parent: { database_id: databaseId },
  properties: { Name: { title: [{ text: { content: `Standup ${new Date().toISOString().slice(0, 10)}` } }] } },
});
await notion.blocks.children.append({
  block_id: page.id,
  children: [
    { heading_2: { rich_text: [{ text: { content: 'Today' } }] } },
    { to_do: { rich_text: [{ text: { content: 'Build content module' } }], checked: false } },
  ],
});
```

Full worked examples — the complete page builder, a Python (`notion-client`) equivalent, and a chunked batch-append helper for payloads over 100 blocks — are in [the worked examples reference](references/examples.md).

## Resources

- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)
- [Create a Page](https://developers.notion.com/reference/post-page)
- [Update Page Properties](https://developers.notion.com/reference/patch-page)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Block Type Reference](https://developers.notion.com/reference/block)
- [Rich Text Object](https://developers.notion.com/reference/rich-text)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)
- [notion-sdk-py GitHub](https://github.com/ramnes/notion-sdk-py)

Next, proceed to `notion-data-handling` for database queries, filtering, sorting, and pagination patterns.
