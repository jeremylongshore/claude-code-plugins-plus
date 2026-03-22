---
name: notion-hello-world
description: |
  Create a minimal working Notion API example.
  Use when starting a new Notion integration, testing your setup,
  or learning basic Notion API patterns (databases, pages, blocks).
  Trigger with phrases like "notion hello world", "notion example",
  "notion quick start", "simple notion code", "first notion API call".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Hello World

## Overview
Minimal working examples demonstrating core Notion API operations: listing users, querying databases, creating pages, and appending block content.

## Prerequisites
- Completed `notion-install-auth` setup
- `NOTION_TOKEN` environment variable set
- At least one page/database shared with your integration

## Instructions

### Step 1: Initialize Client and List Users
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function listUsers() {
  const { results } = await notion.users.list({});
  for (const user of results) {
    console.log(`${user.type}: ${user.name} (${user.id})`);
  }
}
```

### Step 2: Search for Pages and Databases
```typescript
async function searchNotion(query: string) {
  const response = await notion.search({
    query,
    filter: { value: 'database', property: 'object' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
  });

  for (const result of response.results) {
    if (result.object === 'database') {
      const title = result.title.map(t => t.plain_text).join('');
      console.log(`Database: ${title} (${result.id})`);
    }
  }
}
```

### Step 3: Query a Database
```typescript
async function queryDatabase(databaseId: string) {
  const response = await notion.databases.query({
    database_id: databaseId,
    filter: {
      property: 'Status',
      select: { equals: 'Done' },
    },
    sorts: [{ property: 'Created', direction: 'descending' }],
    page_size: 10,
  });

  for (const page of response.results) {
    if ('properties' in page) {
      const title = page.properties['Name'];
      if (title?.type === 'title') {
        console.log(title.title.map(t => t.plain_text).join(''));
      }
    }
  }
}
```

### Step 4: Create a Page in a Database
```typescript
async function createPage(databaseId: string) {
  const response = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: {
        title: [{ text: { content: 'Hello from the API!' } }],
      },
      Status: {
        select: { name: 'In Progress' },
      },
      Tags: {
        multi_select: [{ name: 'API' }, { name: 'Test' }],
      },
    },
  });
  console.log('Created page:', response.id);
  return response;
}
```

### Step 5: Add Content Blocks to a Page
```typescript
async function addContent(pageId: string) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [
      {
        heading_2: {
          rich_text: [{ text: { content: 'Getting Started' } }],
        },
      },
      {
        paragraph: {
          rich_text: [
            { text: { content: 'This page was created via the ' } },
            { text: { content: 'Notion API' }, annotations: { bold: true } },
            { text: { content: '.' } },
          ],
        },
      },
      {
        to_do: {
          rich_text: [{ text: { content: 'Read the API docs' } }],
          checked: false,
        },
      },
    ],
  });
  console.log('Content added!');
}
```

## Output
- Successful user listing confirming API connectivity
- Search results from your workspace
- Database query results with filtered/sorted pages
- Newly created page with properties and block content

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `unauthorized` | Invalid token | Verify NOTION_TOKEN value |
| `object_not_found` | Page not shared | Add integration via page Connections menu |
| `validation_error` | Wrong property type/name | Check database schema with `databases.retrieve` |
| `rate_limited` (429) | Too many requests | Wait for `Retry-After` header value |

## Examples

### Complete Script
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function main() {
  // 1. Verify connection
  const { results: users } = await notion.users.list({});
  console.log(`Connected! ${users.length} users in workspace.`);

  // 2. Find a database
  const search = await notion.search({
    filter: { value: 'database', property: 'object' },
  });
  const db = search.results[0];
  if (!db) { console.log('No databases found.'); return; }
  console.log('Using database:', db.id);

  // 3. Create a page
  const page = await notion.pages.create({
    parent: { database_id: db.id },
    properties: {
      Name: { title: [{ text: { content: 'Hello World!' } }] },
    },
  });
  console.log('Created page:', page.id);

  // 4. Add a paragraph
  await notion.blocks.children.append({
    block_id: page.id,
    children: [{
      paragraph: {
        rich_text: [{ text: { content: 'Created at ' + new Date().toISOString() } }],
      },
    }],
  });
  console.log('Done!');
}

main().catch(console.error);
```

### Python Example
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Search for databases
results = notion.search(filter={"value": "database", "property": "object"})
db_id = results["results"][0]["id"]

# Create a page
page = notion.pages.create(
    parent={"database_id": db_id},
    properties={"Name": {"title": [{"text": {"content": "Hello from Python!"}}]}},
)
print(f"Created page: {page['id']}")
```

## Resources
- [Notion API Getting Started](https://developers.notion.com/docs/create-a-notion-integration)
- [Working with Databases](https://developers.notion.com/docs/working-with-databases)
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)
- [Search Endpoint](https://developers.notion.com/reference/post-search)

## Next Steps
Proceed to `notion-local-dev-loop` for development workflow setup.
