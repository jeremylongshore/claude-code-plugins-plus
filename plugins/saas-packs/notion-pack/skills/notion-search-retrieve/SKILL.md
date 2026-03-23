---
name: notion-search-retrieve
description: |
  Search Notion workspaces and retrieve pages, databases, and block content
  using the Notion API. Use when querying databases with filters, searching
  across a workspace, paginating large result sets, or extracting page content.
  Trigger with phrases like "notion search", "query notion database",
  "notion retrieve page", "notion pagination", "notion filter",
  "notion blocks", "notion get content".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Search & Data Retrieval

## Overview

Search across a Notion workspace, query databases with compound filters, retrieve individual pages, and extract nested block content. Covers the full read path: workspace-level search, database queries with filter/sort/pagination, page retrieval, and recursive block tree traversal.

## Prerequisites

- `@notionhq/client` installed (`npm install @notionhq/client`)
- Notion integration token with read access to target pages/databases
- Integration added to target pages via the Share menu in Notion
- Completed `notion-install-auth` setup

## Instructions

### Step 1: Search the Workspace

Call `notion.search()` to find pages and databases. The integration only sees content explicitly shared with it.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Search for pages matching a query
const searchResults = await notion.search({
  query: 'meeting notes',
  filter: {
    property: 'object',
    value: 'page',        // 'page' or 'database'
  },
  sort: {
    direction: 'descending',
    timestamp: 'last_edited_time',
  },
  page_size: 20,
});

for (const result of searchResults.results) {
  if (result.object === 'page' && 'properties' in result) {
    const titleProp = Object.values(result.properties)
      .find(p => p.type === 'title');
    const title = titleProp?.type === 'title'
      ? titleProp.title.map(t => t.plain_text).join('')
      : 'Untitled';
    console.log(`${title} (${result.id})`);
  }
}
```

An empty `query` string returns all shared content. Results are eventually consistent — newly shared pages may take a few seconds to appear in the index.

### Step 2: Query Databases with Filters

Call `notion.databases.query()` for structured queries. Filters support compound `and`/`or` logic. See [filter-operators.md](references/filter-operators.md) for every property type and operator.

```typescript
// Single filter
const activeItems = await notion.databases.query({
  database_id: 'your-database-id',
  filter: {
    property: 'Status',
    select: { equals: 'Active' },
  },
  sorts: [
    { property: 'Priority', direction: 'descending' },
  ],
  page_size: 50,
});

// Compound filter with AND
const highPriorityActive = await notion.databases.query({
  database_id: 'your-database-id',
  filter: {
    and: [
      { property: 'Status', select: { equals: 'Active' } },
      { property: 'Priority', number: { greater_than: 3 } },
    ],
  },
});
```

### Step 3: Paginate, Retrieve Pages, and Extract Content

Notion uses cursor-based pagination. All list endpoints return `has_more` and `next_cursor`. Call `notion.pages.retrieve()` for a single page, then `notion.blocks.children.list()` to read its content recursively.

```typescript
import type {
  PageObjectResponse,
  BlockObjectResponse,
} from '@notionhq/client/build/src/api-endpoints';

// Paginate through all database results
async function queryAllPages(databaseId: string): Promise<PageObjectResponse[]> {
  const pages: PageObjectResponse[] = [];
  let cursor: string | undefined = undefined;

  do {
    const response = await notion.databases.query({
      database_id: databaseId,
      start_cursor: cursor,
      page_size: 100,
    });

    for (const page of response.results) {
      if ('properties' in page) {
        pages.push(page as PageObjectResponse);
      }
    }
    cursor = response.has_more ? response.next_cursor! : undefined;
  } while (cursor);

  return pages;
}

// Retrieve a single page and extract typed property values
async function getPage(pageId: string) {
  const page = await notion.pages.retrieve({ page_id: pageId });
  if (!('properties' in page)) throw new Error('Partial page object');
  return page as PageObjectResponse;
}

function extractProperties(page: PageObjectResponse) {
  const result: Record<string, any> = {};
  for (const [name, prop] of Object.entries(page.properties)) {
    switch (prop.type) {
      case 'title':
        result[name] = prop.title.map(t => t.plain_text).join(''); break;
      case 'rich_text':
        result[name] = prop.rich_text.map(t => t.plain_text).join(''); break;
      case 'number':    result[name] = prop.number; break;
      case 'select':    result[name] = prop.select?.name ?? null; break;
      case 'multi_select':
        result[name] = prop.multi_select.map(s => s.name); break;
      case 'date':
        result[name] = prop.date ? { start: prop.date.start, end: prop.date.end } : null; break;
      case 'people':
        result[name] = prop.people.map(p => ('name' in p ? p.name : p.id)); break;
      case 'checkbox':  result[name] = prop.checkbox; break;
      case 'url':       result[name] = prop.url; break;
      case 'email':     result[name] = prop.email; break;
      case 'phone_number': result[name] = prop.phone_number; break;
      case 'status':    result[name] = prop.status?.name ?? null; break;
      case 'relation':  result[name] = prop.relation.map(r => r.id); break;
      case 'formula':   result[name] = prop.formula; break;
      case 'rollup':    result[name] = prop.rollup; break;
      default:          result[name] = `[${prop.type}]`;
    }
  }
  return result;
}

// Recursively fetch all blocks (page content)
async function getPageContent(
  blockId: string, depth = 0, maxDepth = 3
): Promise<BlockObjectResponse[]> {
  const blocks: BlockObjectResponse[] = [];
  let cursor: string | undefined = undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: blockId,
      start_cursor: cursor,
      page_size: 100,
    });

    for (const block of response.results) {
      if (!('type' in block)) continue;
      const b = block as BlockObjectResponse;
      blocks.push(b);
      if (b.has_children && depth < maxDepth) {
        blocks.push(...await getPageContent(b.id, depth + 1, maxDepth));
      }
    }
    cursor = response.has_more ? response.next_cursor! : undefined;
  } while (cursor);

  return blocks;
}

function blockToText(block: BlockObjectResponse): string {
  const content = (block as any)[block.type];
  if (!content?.rich_text) return '';
  return content.rich_text.map((t: any) => t.plain_text).join('');
}
```

## Output

- Workspace-wide search returning pages and databases sorted by recency
- Database queries with compound filters across all property types
- Full pagination collecting every matching result
- Typed property extraction for all 15 Notion property types
- Recursive block tree traversal yielding full page content

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Could not find database | Database not shared with integration | Open database in Notion, click Share, add the integration |
| Could not find page | Page not shared or deleted | Verify page is shared; check `archived` status |
| Empty search results | Integration not connected | Share parent page/database with integration; wait for indexing |
| validation_error on filter | Wrong operator for property type | Check [filter-operators.md](references/filter-operators.md) |
| HTTP 429 rate_limited | Too many requests | Back off using `Retry-After` header; use `page_size: 100` |
| Missing properties | Partial page object | Check `'properties' in page` before casting to `PageObjectResponse` |
| Incomplete page content | Not recursing child blocks | Check `has_children` and recurse; increase `maxDepth` |

## Examples

See [examples.md](references/examples.md) for complete patterns including database export, full-text page dump, and compound filter variations.

## Resources

- [Notion Search API](https://developers.notion.com/reference/post-search)
- [Query a Database](https://developers.notion.com/reference/post-database-query)
- [Retrieve a Page](https://developers.notion.com/reference/retrieve-a-page)
- [List Block Children](https://developers.notion.com/reference/get-block-children)
- [Filter Reference](https://developers.notion.com/reference/post-database-query-filter)
- [Property Values](https://developers.notion.com/reference/page-property-values)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)

## Next Steps

For creating and updating pages, see `notion-core-workflow-a`. For PII handling and GDPR compliance, see `notion-data-handling`. For real-time sync via webhooks, see `notion-webhooks-events`.
