# Polling-Based Change Detection

Polling is the most reliable approach and works with every Notion API version. Use `notion.search()` to discover recently edited content across the entire workspace, or `notion.databases.query()` with timestamp filters for targeted change detection on a specific database.

## Workspace-Wide Change Feed

```typescript
import { Client } from '@notionhq/client';
import type {
  PageObjectResponse,
  DatabaseObjectResponse,
} from '@notionhq/client/build/src/api-endpoints';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

interface ChangeRecord {
  id: string;
  object: 'page' | 'database';
  lastEdited: string;
  title: string;
}

// Track the high-water mark for incremental polling
let lastPollTimestamp: string | null = null;

async function pollWorkspaceChanges(): Promise<ChangeRecord[]> {
  const changes: ChangeRecord[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.search({
      sort: {
        direction: 'descending',
        timestamp: 'last_edited_time',
      },
      start_cursor: cursor,
      page_size: 100,
    });

    for (const result of response.results) {
      if (!('last_edited_time' in result)) continue;
      const item = result as PageObjectResponse | DatabaseObjectResponse;

      // Stop when we reach items older than our last poll
      if (lastPollTimestamp && item.last_edited_time <= lastPollTimestamp) {
        // Found our boundary — everything after this is old
        return changes;
      }

      const title = extractTitle(item);
      changes.push({
        id: item.id,
        object: item.object,
        lastEdited: item.last_edited_time,
        title,
      });
    }

    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return changes;
}

function extractTitle(
  item: PageObjectResponse | DatabaseObjectResponse
): string {
  if (item.object === 'database') {
    return (item as DatabaseObjectResponse).title
      .map(t => t.plain_text).join('');
  }
  const page = item as PageObjectResponse;
  for (const prop of Object.values(page.properties)) {
    if (prop.type === 'title') {
      return prop.title.map(t => t.plain_text).join('');
    }
  }
  return 'Untitled';
}

// Run the poller on an interval
async function startPolling(intervalMs: number = 60_000) {
  console.log(`Polling Notion every ${intervalMs / 1000}s`);

  async function tick() {
    try {
      const changes = await pollWorkspaceChanges();
      if (changes.length > 0) {
        console.log(`Detected ${changes.length} change(s):`);
        for (const c of changes) {
          console.log(`  [${c.object}] "${c.title}" edited at ${c.lastEdited}`);
        }
        lastPollTimestamp = changes[0].lastEdited;
        await processChanges(changes);
      } else {
        console.log('No new changes');
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }

  // Initial poll
  await tick();
  setInterval(tick, intervalMs);
}
```

## Database-Specific Incremental Sync

When you only care about one database, `databases.query` with a `last_edited_time` filter is more efficient and stays within rate limits:

```typescript
async function pollDatabaseChanges(
  databaseId: string,
  since: string  // ISO 8601 timestamp
): Promise<PageObjectResponse[]> {
  const changed: PageObjectResponse[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: databaseId,
      filter: {
        timestamp: 'last_edited_time',
        last_edited_time: { after: since },
      },
      sorts: [
        { timestamp: 'last_edited_time', direction: 'descending' },
      ],
      start_cursor: cursor,
      page_size: 100,
    });

    changed.push(...response.results as PageObjectResponse[]);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return changed;
}

// Compare with cached state for fine-grained diff
interface CachedPage {
  id: string;
  lastEdited: string;
  properties: Record<string, unknown>;
}

function diffChanges(
  current: PageObjectResponse[],
  cache: Map<string, CachedPage>
): { added: string[]; modified: string[]; propertyChanges: Map<string, string[]> } {
  const added: string[] = [];
  const modified: string[] = [];
  const propertyChanges = new Map<string, string[]>();

  for (const page of current) {
    const cached = cache.get(page.id);
    if (!cached) {
      added.push(page.id);
      continue;
    }
    if (cached.lastEdited !== page.last_edited_time) {
      modified.push(page.id);
      // Detect which properties changed
      const changedProps: string[] = [];
      for (const [key, value] of Object.entries(page.properties)) {
        if (JSON.stringify(value) !== JSON.stringify(cached.properties[key])) {
          changedProps.push(key);
        }
      }
      if (changedProps.length > 0) {
        propertyChanges.set(page.id, changedProps);
      }
    }
  }

  return { added, modified, propertyChanges };
}
```

## Content-Level Change Tracking

To detect changes inside page content (not just property edits), fetch and compare block children:

```typescript
async function getBlockFingerprint(pageId: string): Promise<string> {
  const blocks: string[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      start_cursor: cursor,
      page_size: 100,
    });

    for (const block of response.results) {
      if ('type' in block && 'last_edited_time' in block) {
        // Use block ID + edit time as a lightweight fingerprint
        blocks.push(`${block.id}:${block.last_edited_time}`);
      }
    }

    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  // Simple hash: join and compare as a string
  return blocks.join('|');
}

// Cache fingerprints and compare on each poll
const contentCache = new Map<string, string>();

async function detectContentChanges(pageId: string): Promise<boolean> {
  const current = await getBlockFingerprint(pageId);
  const previous = contentCache.get(pageId);
  contentCache.set(pageId, current);

  if (previous === undefined) return false; // First seen
  return current !== previous;
}
```
