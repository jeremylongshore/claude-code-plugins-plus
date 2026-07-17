# Block Editing — List, Update, Toggle, Delete, Retrieve

Full walkthrough for the individual-block operations summarized in Step 3 of the skill.
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
