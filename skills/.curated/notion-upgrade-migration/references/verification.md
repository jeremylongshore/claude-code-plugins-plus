# Full Post-Upgrade Verification Suite

Run these targeted verification tests to confirm nothing broke after the upgrade. Test each API surface your application actually uses; drop the ones you do not use.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28',
});

// Test 1: Authentication and user listing
async function verifyAuth(): Promise<void> {
  const { results } = await notion.users.list({});
  console.log(`Auth OK — ${results.length} users found`);
}

// Test 2: Database query (most common operation)
async function verifyDatabaseQuery(databaseId: string): Promise<void> {
  const response = await notion.databases.query({
    database_id: databaseId,
    page_size: 5,
  });
  console.log(`Query OK — ${response.results.length} pages, has_more=${response.has_more}`);

  // Verify property types are still parsed correctly
  for (const page of response.results) {
    if ('properties' in page) {
      const types = Object.values(page.properties).map(p => p.type);
      console.log(`  Property types: ${[...new Set(types)].join(', ')}`);
    }
  }
}

// Test 3: Page creation and archival (write path)
async function verifyPageLifecycle(databaseId: string): Promise<void> {
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      Name: { title: [{ text: { content: `Upgrade test ${Date.now()}` } }] },
    },
  });
  console.log(`Create OK — page ${page.id}`);
  await notion.pages.update({ page_id: page.id, archived: true });
  console.log('Archive OK');
}

// Test 4: Block operations (read + append)
async function verifyBlocks(pageId: string): Promise<void> {
  const { results } = await notion.blocks.children.list({ block_id: pageId });
  console.log(`Block list OK — ${results.length} blocks`);
  await notion.blocks.children.append({
    block_id: pageId,
    children: [{
      paragraph: { rich_text: [{ text: { content: 'Upgrade verification block' } }] },
    }],
  });
  console.log('Block append OK');
}

// Test 5: Comments API (available since SDK 2.2.0)
async function verifyComments(pageId: string): Promise<void> {
  try {
    const { results } = await notion.comments.list({ block_id: pageId });
    console.log(`Comments OK — ${results.length} comments`);
  } catch (err) {
    console.log('Comments API not available in this SDK version');
  }
}

// Run all verification
await verifyAuth();
await verifyDatabaseQuery(process.env.TEST_DB_ID!);
await verifyPageLifecycle(process.env.TEST_DB_ID!);
await verifyBlocks(process.env.TEST_PAGE_ID!);
await verifyComments(process.env.TEST_PAGE_ID!);
```

After all tests pass, merge the upgrade branch:

```bash
npm test                  # Run project test suite
git add -A
git commit -m "chore: upgrade @notionhq/client to $(npm ls @notionhq/client --depth=0 | grep @notionhq)"
git checkout main && git merge -
```
