# Notion Search & Retrieval — Examples

## Search and Summarize Recent Pages

```typescript
async function getRecentPages(query: string, limit: number = 10) {
  const response = await notion.search({
    query,
    filter: { property: 'object', value: 'page' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
    page_size: limit,
  });

  return response.results
    .filter((r): r is PageObjectResponse => 'properties' in r)
    .map(page => ({
      id: page.id,
      lastEdited: page.last_edited_time,
      title: Object.values(page.properties)
        .find(p => p.type === 'title')
        ?.title?.map(t => t.plain_text).join('') ?? 'Untitled',
    }));
}
```

## Export Database to JSON

```typescript
async function exportDatabase(databaseId: string) {
  const pages = await queryAllPages(databaseId);
  return pages.map(page => ({
    id: page.id,
    created: page.created_time,
    lastEdited: page.last_edited_time,
    ...extractProperties(page),
  }));
}

const data = await exportDatabase('db-id');
await fs.writeFile('export.json', JSON.stringify(data, null, 2));
```

## Full-Text Page Dump

```typescript
async function dumpPage(pageId: string): Promise<string> {
  const page = await getPage(pageId);
  const props = extractProperties(page);
  const blocks = await getPageContent(pageId);
  const body = blocks.map(blockToText).filter(Boolean).join('\n');

  return `# ${props.Name || props.Title || 'Untitled'}\n\n${body}`;
}
```

## Filter by Multiple Property Types

```typescript
// Date-based filter
const recentItems = await notion.databases.query({
  database_id: 'your-database-id',
  filter: {
    property: 'Due Date',
    date: { on_or_after: '2026-01-01' },
  },
});

// Checkbox filter
const completedTasks = await notion.databases.query({
  database_id: 'your-database-id',
  filter: {
    property: 'Done',
    checkbox: { equals: true },
  },
});

// Nested AND/OR compound filter
const complexQuery = await notion.databases.query({
  database_id: 'your-database-id',
  filter: {
    and: [
      { property: 'Status', select: { does_not_equal: 'Archived' } },
      {
        or: [
          { property: 'Assignee', people: { contains: 'user-id' } },
          { property: 'Tags', multi_select: { contains: 'urgent' } },
        ],
      },
    ],
  },
});
```
