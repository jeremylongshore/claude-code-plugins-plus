# Notion Core Workflow B — Worked Examples

End-to-end examples that combine the building blocks from
[implementation.md](implementation.md) into complete tasks.

## Build a Report Page

Assembles a heading, a timestamp line, a divider, and a bulleted list of items,
then appends them all in one `append` call.

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
