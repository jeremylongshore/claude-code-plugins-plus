---
name: notion-hello-world
description: |
  Create a minimal working Notion API example.
  Use when starting a new Notion integration, testing your setup,
  or learning basic Notion API patterns (search, pages, users).
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

Three minimal examples covering the Notion API core surfaces: searching for pages, creating a test page in a database, and verifying the created page by retrieving it back.

## Prerequisites

- Completed `notion-install-auth` setup
- `NOTION_TOKEN` environment variable set (internal integration token from https://www.notion.so/my-integrations)
- At least one database shared with your integration via the Connections menu
- Node.js 18+ with `@notionhq/client` or Python 3.8+ with `notion-client`

## Instructions

### Step 1: Search for Pages in Your Workspace

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function searchPages(query: string) {
  const { results } = await notion.search({
    query,
    filter: { property: 'object', value: 'page' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
    page_size: 5,
  });

  for (const page of results) {
    if (page.object === 'page' && 'properties' in page) {
      // Title lives under a property with type "title"
      const titleProp = Object.values(page.properties).find(
        (p) => p.type === 'title'
      );
      const title = titleProp?.type === 'title'
        ? titleProp.title.map((t) => t.plain_text).join('')
        : '(untitled)';
      console.log(`Page: ${title} (${page.id})`);
    }
  }

  return results;
}

// Usage: searchPages('meeting notes');
```

**What this does:** The `search` endpoint queries across all pages and databases your integration can access. The `filter` narrows results to pages only (use `value: 'database'` for databases). Results come back as partial page objects with properties included.

### Step 2: Create a Test Page in a Database

```typescript
async function createTestPage(databaseId: string) {
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: {
        title: [{ text: { content: 'Hello from the API!' } }],
      },
    },
    // Optional: add inline content blocks
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
            { text: { content: ' at ' + new Date().toISOString() + '.' } },
          ],
        },
      },
    ],
  });

  console.log(`Created page: ${page.id}`);
  console.log(`URL: ${page.url}`);
  return page;
}
```

**What this does:** `pages.create` adds a new row to the target database. The `properties` object must match the database schema — `Name` with type `title` is the only universally required property. The optional `children` array appends block content (headings, paragraphs, to-dos, etc.) directly at creation time instead of requiring a separate `blocks.children.append` call.

### Step 3: Verify by Retrieving the Created Page

```typescript
async function verifyPage(pageId: string) {
  const page = await notion.pages.retrieve({ page_id: pageId });

  // Extract title
  if ('properties' in page) {
    const titleProp = Object.values(page.properties).find(
      (p) => p.type === 'title'
    );
    const title = titleProp?.type === 'title'
      ? titleProp.title.map((t) => t.plain_text).join('')
      : '(untitled)';

    console.log(`Verified: "${title}"`);
    console.log(`Created: ${page.created_time}`);
    console.log(`Last edited: ${page.last_edited_time}`);
    console.log(`URL: ${page.url}`);
  }

  return page;
}
```

**What this does:** `pages.retrieve` fetches the full page object including all properties. This confirms the page was created correctly and lets you inspect its metadata. The response includes `created_time`, `last_edited_time`, `url`, and the full `properties` object matching the parent database schema.

## Output

- Search results listing pages your integration can access
- Newly created page in the target database with title and block content
- Verification output confirming the page exists with correct metadata

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `unauthorized` | 401 | Invalid or expired token | Verify `NOTION_TOKEN` value at notion.so/my-integrations |
| `object_not_found` | 404 | Page/database not shared with integration | Add your integration via the page's Connections menu (... > Connect to) |
| `validation_error` | 400 | Property name/type mismatch | Retrieve the database schema with `databases.retrieve` first |
| `rate_limited` | 429 | Exceeded 3 requests/second | Wait for `Retry-After` header value, then retry |
| `conflict_error` | 409 | Transaction conflict | Retry the request after a brief delay |

## Examples

### Complete TypeScript Script

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function main() {
  // 1. List users to verify connectivity
  const { results: users } = await notion.users.list({});
  console.log(`Connected! ${users.length} user(s) in workspace.\n`);

  // 2. Search for a database to use as the target
  const { results } = await notion.search({
    query: 'test',
    filter: { property: 'object', value: 'page' },
  });
  console.log(`Found ${results.length} page(s) matching "test".\n`);

  // 3. Find a database for page creation
  const dbSearch = await notion.search({
    filter: { property: 'object', value: 'database' },
  });
  const db = dbSearch.results[0];
  if (!db) {
    console.log('No databases found. Share a database with your integration first.');
    return;
  }
  console.log(`Using database: ${db.id}\n`);

  // 4. Create a test page
  const page = await notion.pages.create({
    parent: { database_id: db.id },
    properties: {
      Name: { title: [{ text: { content: 'Hello World!' } }] },
    },
  });
  console.log(`Created page: ${page.id}`);
  console.log(`URL: ${page.url}\n`);

  // 5. Verify it exists
  const verified = await notion.pages.retrieve({ page_id: page.id });
  console.log(`Verified: created at ${verified.created_time}`);
}

main().catch(console.error);
```

### Python Example

```python
import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# 1. Search for pages
results = notion.search(
    query="test",
    filter={"property": "object", "value": "page"},
)
print(f"Found {len(results['results'])} page(s)")

# 2. Find a database
db_results = notion.search(
    filter={"property": "object", "value": "database"},
)
db_id = db_results["results"][0]["id"]
print(f"Using database: {db_id}")

# 3. Create a test page
page = notion.pages.create(
    parent={"database_id": db_id},
    properties={
        "Name": {"title": [{"text": {"content": "Hello from Python!"}}]},
    },
)
print(f"Created page: {page['id']}")
print(f"URL: {page['url']}")

# 4. Verify
verified = notion.pages.retrieve(page_id=page["id"])
print(f"Verified: created at {verified['created_time']}")
```

## Resources

- [Notion API Getting Started](https://developers.notion.com/docs/create-a-notion-integration)
- [Search Endpoint Reference](https://developers.notion.com/reference/post-search)
- [Create a Page Reference](https://developers.notion.com/reference/post-page)
- [Retrieve a Page Reference](https://developers.notion.com/reference/retrieve-a-page)
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)

## Next Steps

Proceed to `notion-local-dev-loop` for development workflow setup.
