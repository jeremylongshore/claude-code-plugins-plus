# Notion Hello World — Complete Runnable Examples

End-to-end scripts that chain all three operations (connect, search, create,
verify) into a single runnable program. Set `NOTION_TOKEN` in your environment,
share at least one database with your integration, then run either script.

## Complete TypeScript Script

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

## Python Example

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
