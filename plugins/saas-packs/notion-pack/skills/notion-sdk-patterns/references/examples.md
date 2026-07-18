# Notion SDK Patterns — Worked Examples

Copy-paste snippets for common Notion integration tasks. Pairs with the deep reference in
`patterns.md`.

## Property Value Extractors

Type-safe accessors that narrow the discriminated union on each property type:

```typescript
import type { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

function getTitle(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'title' ? p.title.map(t => t.plain_text).join('') : '';
}

function getRichText(page: PageObjectResponse, prop: string): string {
  const p = page.properties[prop];
  return p?.type === 'rich_text' ? p.rich_text.map(t => t.plain_text).join('') : '';
}

function getSelect(page: PageObjectResponse, prop: string): string | null {
  const p = page.properties[prop];
  return p?.type === 'select' ? (p.select?.name ?? null) : null;
}

function getNumber(page: PageObjectResponse, prop: string): number | null {
  const p = page.properties[prop];
  return p?.type === 'number' ? p.number : null;
}

function getCheckbox(page: PageObjectResponse, prop: string): boolean {
  const p = page.properties[prop];
  return p?.type === 'checkbox' ? p.checkbox : false;
}
```

## Multi-Workspace Factory

Cache one client per workspace token so multi-tenant integrations reuse connections:

```typescript
const clients = new Map<string, Client>();

function getClient(workspaceId: string, token: string): Client {
  if (!clients.has(workspaceId)) {
    clients.set(workspaceId, new Client({ auth: token }));
  }
  return clients.get(workspaceId)!;
}
```

## Create a Page with Properties

```typescript
await notion.pages.create({
  parent: { database_id },
  properties: {
    Name: { title: [{ text: { content: 'New Task' } }] },
    Status: { select: { name: 'To Do' } },
    Priority: { select: { name: 'High' } },
    'Due Date': { date: { start: '2026-04-01' } },
    Tags: { multi_select: [{ name: 'backend' }, { name: 'api' }] },
  },
});
```

## Python Pagination

```python
cursor = None
all_results = []
while True:
    response = notion.databases.query(
        database_id=db_id,
        start_cursor=cursor,
    )
    all_results.extend(response["results"])
    if not response["has_more"]:
        break
    cursor = response["next_cursor"]
```
