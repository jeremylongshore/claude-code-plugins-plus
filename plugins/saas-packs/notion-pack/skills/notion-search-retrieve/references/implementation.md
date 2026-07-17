# Pagination, Page Retrieval, and Block Extraction — Full Implementation

Notion uses cursor-based pagination. All list endpoints return `has_more` and
`next_cursor`. Call `notion.pages.retrieve()` for a single page, then
`notion.blocks.children.list()` to read its content recursively.

## Paginate through all database results

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
```

## Retrieve a single page and extract typed property values

```typescript
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
```

## Recursively fetch all blocks (page content)

```typescript
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

## Tuning notes

- **`page_size`**: max is 100. Use it for bulk pulls to minimize round trips; use a
  smaller value only when you want to surface a first page quickly to the user.
- **`maxDepth`**: the recursion depth guard defaults to 3. Deeply nested pages
  (toggles inside toggles) may need a higher value; raising it increases API calls
  linearly with nested block count.
- **Eventual consistency**: newly shared or edited content may lag the index by a
  few seconds — retry a search that unexpectedly returns empty.
