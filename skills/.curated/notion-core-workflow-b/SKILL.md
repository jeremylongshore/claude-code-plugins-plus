---
name: notion-core-workflow-b
description: |
  Work with Notion blocks, rich text, comments, and page content.

  Use when you need to read a page's block tree, append formatted content
  (headings, lists, callouts, code), edit or delete blocks, build rich text
  with annotations, or manage page and block comments through the Notion API.

  Trigger with phrases like "notion blocks", "notion page content",
  "notion rich text", "notion comments", "notion append blocks".
allowed-tools: Read, Write, Bash(npm:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Core Workflow B — Blocks, Content & Comments

## Overview

Secondary workflow for content operations: reading block trees, appending content, building rich text with annotations, and managing comments. SKILL.md keeps the flow at a high level; every full implementation lives in [references/implementation.md](references/implementation.md).

## Prerequisites

- Completed `notion-install-auth` setup
- A Notion page shared with your integration
- Familiarity with `notion-core-workflow-a` (databases/pages)

## Authentication

All calls use the `@notionhq/client` SDK authenticated with an integration token read from `process.env.NOTION_TOKEN`. The token is provisioned by the `notion-install-auth` skill (internal integration secret) — do not hard-code it. The page or block being edited must be explicitly shared with that integration, or calls return `object_not_found`.

## Instructions

The workflow has six steps. The client is created once and reused:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

1. **Retrieve block children** — page through `notion.blocks.children.list` with a `start_cursor` loop (100 blocks/page) until `has_more` is false.
2. **Read blocks recursively** — walk each block, and when `has_children` is true recurse to build a nested tree; `blockToText` flattens a block's `rich_text` to a plain string.
3. **Append content blocks** — one `notion.blocks.children.append` call adds headings, formatted paragraphs, bulleted/numbered lists, to-dos, code, callouts, quotes, dividers, and toggles.
4. **Rich text annotations** — each rich-text span carries `annotations` (`bold`, `italic`, `strikethrough`, `underline`, `code`, `color`); spans can be plain text, links, user/page/date mentions, or LaTeX equations.
5. **Update and delete blocks** — `notion.blocks.update` replaces a block's content; `notion.blocks.delete` archives it.
6. **Work with comments** — `notion.comments.create` adds page or discussion-thread comments; `notion.comments.list` reads them back.

Each step's complete, copy-paste code is in [references/implementation.md](references/implementation.md).

## Output

- Page content blocks retrieved (flat or recursive tree)
- Rich content appended with formatting, lists, code, callouts
- Blocks updated and deleted
- Comments created and listed

## Error Handling

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `validation_error` on append | Invalid block type structure | Check block type object shape |
| `object_not_found` | Block deleted or page not shared | Verify block ID and permissions |
| `rate_limited` (429) | Rapid block operations | Add delays between batch operations |
| Empty `rich_text` array | Block has no text content | Check block type before accessing |

## Examples

The building blocks above compose into full tasks. For instance, `buildReport`
assembles a heading, timestamp, divider, and a bulleted list, then appends them
in a single call:

```typescript
async function buildReport(pageId: string, data: { title: string; items: string[] }) {
  const blocks: any[] = [
    { heading_1: { rich_text: [{ text: { content: data.title } }] } },
    { paragraph: { rich_text: [{ text: { content: `Generated ${new Date().toISOString()}` } }] } },
    { divider: {} },
  ];
  for (const item of data.items) {
    blocks.push({ bulleted_list_item: { rich_text: [{ text: { content: item } }] } });
  }
  await notion.blocks.children.append({ block_id: pageId, children: blocks });
}
```

See [references/examples.md](references/examples.md) for the annotated version and additional worked examples.

## Resources

- [Block Object Reference](https://developers.notion.com/reference/block)
- [Rich Text Reference](https://developers.notion.com/reference/rich-text)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)
- [Working with Comments](https://developers.notion.com/docs/working-with-comments)
- Full implementation: [references/implementation.md](references/implementation.md); worked examples: [references/examples.md](references/examples.md)
- For common errors, see the `notion-common-errors` skill.
