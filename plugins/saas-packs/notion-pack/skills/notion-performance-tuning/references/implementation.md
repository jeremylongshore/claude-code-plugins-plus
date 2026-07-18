# Implementation: Minimizing Calls and Caching

Full working code for Step 1 (minimize API calls and reduce payload) and Step 2
(TTL-based caching with write-through invalidation).

## Step 1: Minimize API Calls and Reduce Payload

Avoid N+1 query patterns. Use `page_size: 100` (the maximum) to reduce pagination requests. Select only the properties you need in database queries to shrink response payloads.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// BAD: N+1 pattern — fetching content for every page individually
async function fetchAllBad(dbId: string) {
  const pages = await notion.databases.query({ database_id: dbId });
  for (const page of pages.results) {
    // Each iteration is a separate API call — O(n) requests
    const content = await notion.blocks.children.list({ block_id: page.id });
  }
}

// GOOD: Use filter_properties to select only needed fields
async function fetchAllGood(dbId: string) {
  const pages = await notion.databases.query({
    database_id: dbId,
    page_size: 100, // Maximum — reduces total pagination requests
    filter: {
      property: 'Status',
      select: { equals: 'Active' },
    },
    // Select only the properties you need by property ID
    // Find IDs via: notion.databases.retrieve({ database_id: dbId })
    filter_properties: ['title', 'Status', 'Priority'],
  });

  // Properties are already in the response — no extra retrieve calls
  for (const page of pages.results) {
    if ('properties' in page) {
      const title = page.properties.Name?.type === 'title'
        ? page.properties.Name.title.map(t => t.plain_text).join('')
        : '';
      const status = page.properties.Status?.type === 'select'
        ? page.properties.Status.select?.name
        : undefined;
      // Use properties directly — zero additional API calls
    }
  }
  return pages;
}

// Batch block appends — up to 100 blocks per request
async function appendBlocks(pageId: string, items: string[]) {
  const blocks = items.map(item => ({
    object: 'block' as const,
    type: 'paragraph' as const,
    paragraph: {
      rich_text: [{ type: 'text' as const, text: { content: item } }],
    },
  }));

  // BAD: one call per block = N API calls
  // for (const block of blocks) {
  //   await notion.blocks.children.append({ block_id: pageId, children: [block] });
  // }

  // GOOD: batch in chunks of 100 (API maximum)
  for (let i = 0; i < blocks.length; i += 100) {
    await notion.blocks.children.append({
      block_id: pageId,
      children: blocks.slice(i, i + 100),
    });
  }
}

// Avoid recursive block fetching unless you actually need nested content
async function getTopLevelBlocks(pageId: string) {
  const blocks = await notion.blocks.children.list({
    block_id: pageId,
    page_size: 100,
  });
  // Only recurse into blocks that have children AND you need them
  const expandable = blocks.results.filter(
    (b) => 'has_children' in b && b.has_children && needsExpansion(b)
  );
  // Fetch children only for blocks that matter
  return { topLevel: blocks.results, expandable };
}

function needsExpansion(block: any): boolean {
  // Only expand toggles and nested content — skip paragraphs, headings, etc.
  return ['toggle', 'child_page', 'child_database', 'column_list'].includes(block.type);
}
```

## Step 2: Cache Responses with TTL-Based Invalidation

Implement in-memory caching with LRU eviction and TTL expiration. Invalidate cache entries on writes to maintain consistency.

```typescript
import { LRUCache } from 'lru-cache';
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Tiered TTL cache — different durations for different data volatility
const cache = new LRUCache<string, any>({
  max: 1000,             // max entries
  ttl: 60_000,           // default 1-minute TTL
  updateAgeOnGet: false, // don't extend TTL on reads (ensures freshness)
  allowStale: false,     // never return expired entries
});

// Cache configuration per operation type
const TTL = {
  DATABASE_SCHEMA: 300_000,  // 5 min — schemas rarely change
  DATABASE_QUERY:  60_000,   // 1 min — data changes frequently
  PAGE_RETRIEVE:   120_000,  // 2 min — pages change occasionally
  SEARCH:          30_000,   // 30s — search results are volatile
  BLOCK_CHILDREN:  60_000,   // 1 min — content updates moderately
} as const;

async function cachedDatabaseQuery(dbId: string, filter?: any, sorts?: any) {
  const cacheKey = `db:${dbId}:${JSON.stringify({ filter, sorts })}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const allPages: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter,
      sorts,
      page_size: 100,
      start_cursor: cursor,
    });
    allPages.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  const result = { results: allPages, count: allPages.length };
  cache.set(cacheKey, result, { ttl: TTL.DATABASE_QUERY });
  return result;
}

async function cachedPageRetrieve(pageId: string) {
  const cacheKey = `page:${pageId}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const page = await notion.pages.retrieve({ page_id: pageId });
  cache.set(cacheKey, page, { ttl: TTL.PAGE_RETRIEVE });
  return page;
}

// Invalidate on writes — consistency over speed
async function createPageInvalidating(dbId: string, properties: any) {
  const page = await notion.pages.create({
    parent: { database_id: dbId },
    properties,
  });

  // Invalidate all cached queries for this database
  for (const key of cache.keys()) {
    if (key.startsWith(`db:${dbId}:`)) cache.delete(key);
  }

  return page;
}

async function updatePageInvalidating(pageId: string, properties: any) {
  const page = await notion.pages.update({ page_id: pageId, properties });

  // Invalidate specific page cache and parent database queries
  cache.delete(`page:${pageId}`);
  // If you know the parent DB, invalidate its queries too:
  // for (const key of cache.keys()) {
  //   if (key.startsWith(`db:${parentDbId}:`)) cache.delete(key);
  // }

  return page;
}

// Cache stats for monitoring
function getCacheStats() {
  return {
    size: cache.size,
    maxSize: cache.max,
    hitRate: cache.size > 0 ? 'check cache.get return values' : 'empty',
  };
}
```
