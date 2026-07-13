# Changelog Sync Script

Node.js script that parses `CHANGELOG.md` and replaces a Notion page's content with structured blocks (headings, bullet lists, paragraphs). Runs in CI after pushes to `main` that modify `CHANGELOG.md`.

## Script

```typescript
// scripts/notion-changelog-sync.js
import { Client } from '@notionhq/client';
import { readFileSync } from 'fs';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const pageId = process.env.NOTION_CHANGELOG_PAGE;

async function syncChangelog() {
  const changelog = readFileSync('CHANGELOG.md', 'utf-8');

  // Clear existing content
  const existing = await notion.blocks.children.list({ block_id: pageId });
  for (const block of existing.results) {
    await notion.blocks.delete({ block_id: block.id });
    await new Promise((r) => setTimeout(r, 350)); // Rate limit: 3 req/sec
  }

  // Parse changelog sections and append as Notion blocks
  const lines = changelog.split('\n');
  const blocks = [];

  for (const line of lines) {
    if (line.startsWith('## ')) {
      blocks.push({
        heading_2: {
          rich_text: [{ text: { content: line.replace('## ', '') } }],
        },
      });
    } else if (line.startsWith('### ')) {
      blocks.push({
        heading_3: {
          rich_text: [{ text: { content: line.replace('### ', '') } }],
        },
      });
    } else if (line.startsWith('- ')) {
      blocks.push({
        bulleted_list_item: {
          rich_text: [{ text: { content: line.replace('- ', '') } }],
        },
      });
    } else if (line.trim()) {
      blocks.push({
        paragraph: {
          rich_text: [{ text: { content: line } }],
        },
      });
    }
  }

  // Append in chunks of 100 (Notion API block append limit)
  for (let i = 0; i < blocks.length; i += 100) {
    await notion.blocks.children.append({
      block_id: pageId,
      children: blocks.slice(i, i + 100),
    });
    if (i + 100 < blocks.length) {
      await new Promise((r) => setTimeout(r, 350));
    }
  }

  console.log(`Synced ${blocks.length} blocks to Notion changelog page`);
}

syncChangelog().catch((err) => {
  console.error('Changelog sync failed:', err.message);
  process.exit(1);
});
```

## GitHub Actions Step

```yaml
- name: Sync CHANGELOG to Notion page
  run: node scripts/notion-changelog-sync.js
  env:
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    NOTION_CHANGELOG_PAGE: ${{ secrets.NOTION_CHANGELOG_PAGE }}
```

## Notes

- The script clears all existing blocks before writing — this is a full replace, not a diff
- Large changelogs (1000+ lines) may take 30+ seconds due to rate limiting
- Set `timeout-minutes: 5` on the job for safety
