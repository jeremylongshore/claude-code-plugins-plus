---
name: notion-core-workflow-b
description: |
  Work with Notion blocks, rich text, comments, and page content.
  Use when reading/writing page content blocks, building rich text,
  managing comments, or working with nested block trees.
  Trigger with phrases like "notion blocks", "notion page content",
  "notion rich text", "notion comments", "notion append blocks".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Core Workflow B — Blocks, Content & Comments

## Overview
Secondary workflow for content operations: reading block trees, appending content, building rich text with annotations, and managing comments.

## Prerequisites
- Completed `notion-install-auth` setup
- A Notion page shared with your integration
- Familiarity with `notion-core-workflow-a` (databases/pages)

## Instructions

### Step 1: Retrieve Block Children
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function getPageContent(pageId: string) {
  const blocks = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      start_cursor: cursor,
      page_size: 100,
    });
    blocks.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return blocks;
}
```

### Step 2: Read Blocks Recursively (Nested Content)
```typescript
async function getBlockTree(blockId: string, depth = 0): Promise<any[]> {
  const blocks = await getPageContent(blockId);
  const tree = [];

  for (const block of blocks) {
    const node: any = { ...block, children: [] };
    // Recursively fetch children if block has them
    if ('has_children' in block && block.has_children) {
      node.children = await getBlockTree(block.id, depth + 1);
    }
    tree.push(node);
  }

  return tree;
}

// Extract plain text from a block tree
function blockToText(block: any): string {
  const type = block.type;
  if (block[type]?.rich_text) {
    return block[type].rich_text.map((t: any) => t.plain_text).join('');
  }
  return '';
}
```

### Step 3: Append Content Blocks
```typescript
async function appendContent(pageId: string) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [
      // Heading
      {
        heading_1: {
          rich_text: [{ text: { content: 'Section Title' } }],
        },
      },
      // Paragraph with formatting
      {
        paragraph: {
          rich_text: [
            { text: { content: 'Regular text, ' } },
            { text: { content: 'bold' }, annotations: { bold: true } },
            { text: { content: ', ' } },
            { text: { content: 'italic' }, annotations: { italic: true } },
            { text: { content: ', ' } },
            { text: { content: 'code' }, annotations: { code: true } },
            { text: { content: ', and ' } },
            {
              text: { content: 'a link', link: { url: 'https://notion.so' } },
              annotations: { underline: true },
            },
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
      // Numbered list
      {
        numbered_list_item: {
          rich_text: [{ text: { content: 'Step one' } }],
        },
      },
      // To-do items
      {
        to_do: {
          rich_text: [{ text: { content: 'Task to complete' } }],
          checked: false,
        },
      },
      {
        to_do: {
          rich_text: [{ text: { content: 'Already done' } }],
          checked: true,
        },
      },
      // Code block
      {
        code: {
          rich_text: [{ text: { content: 'console.log("Hello Notion!");' } }],
          language: 'typescript',
        },
      },
      // Callout
      {
        callout: {
          rich_text: [{ text: { content: 'Important note here' } }],
          icon: { emoji: '💡' },
        },
      },
      // Quote
      {
        quote: {
          rich_text: [{ text: { content: 'A meaningful quote' } }],
        },
      },
      // Divider
      { divider: {} },
      // Toggle block (with children added separately)
      {
        toggle: {
          rich_text: [{ text: { content: 'Click to expand' } }],
        },
      },
    ],
  });
}
```

### Step 4: Rich Text Annotations Reference
```typescript
// All annotation options
interface Annotations {
  bold: boolean;
  italic: boolean;
  strikethrough: boolean;
  underline: boolean;
  code: boolean;
  color: 'default' | 'gray' | 'brown' | 'orange' | 'yellow' |
         'green' | 'blue' | 'purple' | 'pink' | 'red' |
         'gray_background' | 'brown_background' | 'orange_background' |
         'yellow_background' | 'green_background' | 'blue_background' |
         'purple_background' | 'pink_background' | 'red_background';
}

// Rich text types: text, mention, equation
const richTextExamples = [
  // Plain text
  { text: { content: 'Hello' } },

  // Text with link
  { text: { content: 'Click here', link: { url: 'https://notion.so' } } },

  // Mention a user
  { mention: { user: { id: 'user-uuid' } } },

  // Mention a page
  { mention: { page: { id: 'page-uuid' } } },

  // Mention a date
  { mention: { date: { start: '2026-04-01' } } },

  // Inline equation (LaTeX)
  { equation: { expression: 'E = mc^2' } },
];
```

### Step 5: Update and Delete Blocks
```typescript
// Update a block's content
async function updateBlock(blockId: string) {
  await notion.blocks.update({
    block_id: blockId,
    paragraph: {
      rich_text: [{ text: { content: 'Updated content' } }],
    },
  });
}

// Delete (archive) a block
async function deleteBlock(blockId: string) {
  await notion.blocks.delete({ block_id: blockId });
}
```

### Step 6: Work with Comments
```typescript
// Add a comment to a page
async function addComment(pageId: string, text: string) {
  await notion.comments.create({
    parent: { page_id: pageId },
    rich_text: [{ text: { content: text } }],
  });
}

// Add a comment to a specific block (discussion thread)
async function addBlockComment(discussionId: string, text: string) {
  await notion.comments.create({
    discussion_id: discussionId,
    rich_text: [{ text: { content: text } }],
  });
}

// List comments on a block or page
async function listComments(blockId: string) {
  const response = await notion.comments.list({ block_id: blockId });
  for (const comment of response.results) {
    const text = comment.rich_text.map(t => t.plain_text).join('');
    console.log(`${comment.created_by.id}: ${text}`);
  }
}
```

## Output
- Page content blocks retrieved (flat or recursive tree)
- Rich content appended with formatting, lists, code, callouts
- Blocks updated and deleted
- Comments created and listed

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `validation_error` on append | Invalid block type structure | Check block type object shape |
| `object_not_found` | Block deleted or page not shared | Verify block ID and permissions |
| `rate_limited` (429) | Rapid block operations | Add delays between batch operations |
| Empty `rich_text` array | Block has no text content | Check block type before accessing |

## Examples

### Build a Report Page
```typescript
async function buildReport(pageId: string, data: { title: string; items: string[] }) {
  const blocks: any[] = [
    { heading_1: { rich_text: [{ text: { content: data.title } }] } },
    { paragraph: { rich_text: [{ text: { content: `Generated ${new Date().toISOString()}` } }] } },
    { divider: {} },
  ];

  for (const item of data.items) {
    blocks.push({
      bulleted_list_item: { rich_text: [{ text: { content: item } }] },
    });
  }

  await notion.blocks.children.append({ block_id: pageId, children: blocks });
}
```

## Resources
- [Block Object Reference](https://developers.notion.com/reference/block)
- [Rich Text Reference](https://developers.notion.com/reference/rich-text)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)
- [Working with Comments](https://developers.notion.com/docs/working-with-comments)

## Next Steps
For common errors, see `notion-common-errors`.
