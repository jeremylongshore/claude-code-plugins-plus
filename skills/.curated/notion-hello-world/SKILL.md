---
name: notion-hello-world
description: 'Create a minimal working Notion API example.

  Use when starting a new Notion integration, testing your setup,

  or learning basic Notion API patterns (search, pages, users).

  Trigger with phrases like "notion hello world", "notion example",

  "notion quick start", "simple notion code", "first notion API call".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Hello World

## Overview

Three minimal examples covering the Notion API core surfaces: searching for pages, creating a test page in a database, and verifying the created page by retrieving it back.

## Prerequisites

- Completed `notion-install-auth` setup
- `NOTION_TOKEN` environment variable set (internal integration token from <https://www.notion.so/my-integrations>)
- At least one database shared with your integration via the Connections menu
- Node.js 18+ with `@notionhq/client` or Python 3.8+ with `notion-client`

## Authentication

Every request authenticates with your internal integration token via the
`NOTION_TOKEN` environment variable — the client reads it as
`new Client({ auth: process.env.NOTION_TOKEN })` (or Python's
`Client(auth=os.environ["NOTION_TOKEN"])`). Generate the token at
[notion.so/my-integrations](https://www.notion.so/my-integrations), then share each
target database with the integration through its Connections menu. Never hardcode
the token — keep it in the environment. See `notion-install-auth` for the full setup.

## Instructions

The workflow is three steps against the Notion API core surfaces. Instantiate the
client once, then search, create, and verify. Step 1's skeleton is below; the full
create + verify code (with block content, title extraction, and metadata) is in
[the implementation walkthrough](references/implementation.md).

### Step 1: Search for pages

The `search` endpoint queries across everything your integration can access;
`filter` narrows to pages (use `value: 'database'` for databases).

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

const { results } = await notion.search({
  query: 'meeting notes',
  filter: { property: 'object', value: 'page' },
  page_size: 5,
});
```

### Step 2: Create a test page

`pages.create` adds a row to a target database. The `properties` object must match
the database schema — `Name` with type `title` is the only universally required
property. An optional `children` array appends block content (headings, paragraphs,
to-dos) at creation time. Full code is in the
[implementation walkthrough](references/implementation.md).

### Step 3: Verify by retrieving the page

`pages.retrieve` fetches the full page object, confirming creation and exposing
`created_time`, `last_edited_time`, `url`, and the complete `properties` map. Full
code is in the [implementation walkthrough](references/implementation.md).

## Output

- Search results listing pages your integration can access
- Newly created page in the target database with title and block content
- Verification output confirming the page exists with correct metadata

## Error Handling

| Error | HTTP Code | Cause | Solution |
| ------- | ----------- | ------- | ---------- |
| `unauthorized` | 401 | Invalid or expired token | Verify `NOTION_TOKEN` value at notion.so/my-integrations |
| `object_not_found` | 404 | Page/database not shared with integration | Add your integration via the page's Connections menu (... > Connect to) |
| `validation_error` | 400 | Property name/type mismatch | Retrieve the database schema with `databases.retrieve` first |
| `rate_limited` | 429 | Exceeded 3 requests/second | Wait for `Retry-After` header value, then retry |
| `conflict_error` | 409 | Transaction conflict | Retry the request after a brief delay |

## Examples

Two complete, runnable scripts chain all three operations end to end — connect,
search, find a database, create a page, and verify it. Here is the shape of the
TypeScript version:

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN });
await notion.users.list({});                 // 1. verify connectivity
await notion.search({ query: 'test' });      // 2. search
const page = await notion.pages.create({ /* ... */ });  // 3. create
await notion.pages.retrieve({ page_id: page.id });      // 4. verify
```

Full copy-paste scripts for both languages — the complete TypeScript `main()` and
the equivalent Python program — live in [runnable examples](references/examples.md).

## Resources

- [Notion API Getting Started](https://developers.notion.com/docs/create-a-notion-integration)
- [Search Endpoint Reference](https://developers.notion.com/reference/post-search)
- [Create a Page Reference](https://developers.notion.com/reference/post-page)
- [Retrieve a Page Reference](https://developers.notion.com/reference/retrieve-a-page)
- [Working with Page Content](https://developers.notion.com/docs/working-with-page-content)

## Next Steps

Once these three calls succeed, proceed to `notion-local-dev-loop` to set up a
development workflow with live reload and environment management. From there,
`notion-database-query` covers filtering and sorting rows, and `notion-block-content`
covers appending richer block structures to pages you create.
