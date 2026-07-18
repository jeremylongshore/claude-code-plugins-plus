# Notion Hello World — Full Implementation Walkthrough

The three core steps for a minimal Notion integration: search for pages, create a
test page in a database, and verify it by retrieving it back. Each block is
copy-pasteable TypeScript using `@notionhq/client`.

## Step 1: Search for Pages in Your Workspace

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

## Step 2: Create a Test Page in a Database

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

## Step 3: Verify by Retrieving the Created Page

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
