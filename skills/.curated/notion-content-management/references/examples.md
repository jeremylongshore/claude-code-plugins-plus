# Worked Examples

Full end-to-end examples for the workflow summarized in the skill's Examples section.

## Complete Page Builder

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

## Python Example

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

## Batch Block Append (Chunked for >100 Blocks)

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
