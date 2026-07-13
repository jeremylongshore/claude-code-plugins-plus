# Notion Block Type Catalog

Complete `blocks.children.append` reference covering every common block type
and its exact payload shape. Notion caps append calls at 100 blocks per
request — see the "Batch Block Append" example in SKILL.md for chunking.

## All Common Block Types in One Append Call

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
