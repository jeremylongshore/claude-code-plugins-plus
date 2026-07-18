# Notion Core Workflow B — Full Implementation

Complete, copy-paste implementations for every content operation the skill
summarizes. All snippets assume the client from Step 1:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

## Step 1: Retrieve Block Children (paginated)

```typescript
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

## Step 2: Read Blocks Recursively (Nested Content)

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

## Step 3: Append Content Blocks

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

## Step 4: Rich Text Annotations Reference

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

## Step 5: Update and Delete Blocks

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

## Step 6: Work with Comments

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
