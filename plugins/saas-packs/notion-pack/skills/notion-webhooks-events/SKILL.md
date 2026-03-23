---
name: notion-webhooks-events
description: |
  Build change detection and event handling for Notion workspaces using
  polling, native webhooks, and third-party connectors.
  Use when implementing real-time sync, change feeds, incremental backup,
  or event-driven workflows with Notion data.
  Trigger with phrases like "notion webhook", "notion events",
  "notion change detection", "notion polling", "notion sync changes",
  "notion real-time", "notion watch for changes".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npx:*), Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Webhooks & Event Handling

## Overview

Notion offers three approaches to change detection, each with different trade-offs:

| Approach | Latency | Complexity | Reliability |
|----------|---------|------------|-------------|
| **Polling with `search` / `databases.query`** | 30s-5min (your poll interval) | Low | High — you control timing |
| **Native webhooks** (API 2025-02+) | Near real-time | Medium | Good — requires HTTPS endpoint, retry handling |
| **Third-party connectors** (Zapier, Make) | 1-15 min | Low (no-code) | Vendor-dependent |

**Honest assessment:** Notion's native webhook support arrived in mid-2025 and covers page, database, comment, and data source events. It works well for event notification but does not deliver full payloads — you still need API calls to fetch the changed data. For many use cases, especially incremental sync and backup, polling with `last_edited_time` filters remains the most battle-tested pattern.

## Prerequisites

- `@notionhq/client` v2.3+ installed (`npm install @notionhq/client`)
- Notion integration created at https://www.notion.so/my-integrations
- Integration shared with target pages/databases (Connections menu in Notion)
- `NOTION_TOKEN` environment variable set to the integration's Internal Integration Secret
- For native webhooks: HTTPS endpoint accessible from the internet

## Instructions

### Step 1: Polling-Based Change Detection

Polling is the most reliable approach and works with every Notion API version. Use `notion.search()` to discover recently edited content across the entire workspace, or `notion.databases.query()` with timestamp filters for targeted change detection on a specific database.

#### Workspace-Wide Change Feed

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

#### Database-Specific Incremental Sync

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

#### Content-Level Change Tracking

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

### Step 2: Native Webhooks (API 2025-02+)

Notion's native webhooks deliver HTTP POST notifications when pages, databases, comments, or data sources change. They notify you that something changed — you then call the API to fetch the actual data.

#### Register and Verify a Webhook Endpoint

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json());

// Step A: Handle the verification challenge during webhook registration
// Notion sends { type: "url_verification", challenge: "..." }
app.post('/webhooks/notion', (req, res) => {
  if (req.body.type === 'url_verification') {
    console.log('Webhook verification received');
    return res.status(200).json({ challenge: req.body.challenge });
  }

  // Step B: Process real events
  handleWebhookEvent(req.body);
  // Always respond 200 quickly — do heavy processing async
  res.status(200).json({ ok: true });
});

app.listen(3000, () => console.log('Webhook receiver on :3000'));
```

#### Handle Webhook Events

```typescript
interface NotionWebhookEvent {
  type: string;
  data: {
    id: string;
    object: 'page' | 'database' | 'data_source' | 'comment';
    parent?: { type: string; page_id?: string; database_id?: string };
  };
  integration_id: string;
  authors: Array<{ id: string; type: 'person' | 'bot' }>;
  attempt_number: number;
  timestamp: string;
}

// Supported event types:
//   page.created, page.deleted, page.moved, page.undeleted
//   page.content_updated, page.properties_updated
//   page.locked, page.unlocked
//   database.created, database.deleted, database.moved
//   database.schema_updated, database.content_updated
//   comment.created, comment.updated, comment.deleted
//   data_source.schema_updated

async function handleWebhookEvent(event: NotionWebhookEvent) {
  console.log(`[webhook] ${event.type} → ${event.data.object} ${event.data.id}`);

  switch (event.type) {
    case 'page.content_updated':
    case 'page.properties_updated':
      // Fetch the page to see what actually changed
      const page = await notion.pages.retrieve({ page_id: event.data.id });
      await processPageUpdate(page, event.type);
      break;

    case 'page.created':
      const newPage = await notion.pages.retrieve({ page_id: event.data.id });
      await processNewPage(newPage);
      break;

    case 'page.deleted':
      await handlePageDeletion(event.data.id);
      break;

    case 'database.schema_updated':
      const db = await notion.databases.retrieve({ database_id: event.data.id });
      console.log('Schema changed. Properties:', Object.keys(db.properties));
      break;

    case 'comment.created':
      await handleNewComment(event.data.id);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}
```

#### Debouncing and Deduplication

Notion may deliver events more than once (retries on non-200 responses). Rapid edits can also produce a burst of events for the same resource. Handle both:

```typescript
// Deduplication: skip events we have already processed
const processedEvents = new Map<string, number>(); // key → timestamp

function isDuplicate(event: NotionWebhookEvent): boolean {
  const key = `${event.type}:${event.data.id}:${event.timestamp}`;
  if (processedEvents.has(key)) return true;

  processedEvents.set(key, Date.now());
  // Prune entries older than 10 minutes
  const cutoff = Date.now() - 10 * 60 * 1000;
  for (const [k, ts] of processedEvents) {
    if (ts < cutoff) processedEvents.delete(k);
  }
  return false;
}

// Debouncing: collapse rapid edits into one processing call
const pendingDebounce = new Map<string, NodeJS.Timeout>();
const DEBOUNCE_MS = 2000;

function debounceEvent(
  event: NotionWebhookEvent,
  handler: (event: NotionWebhookEvent) => Promise<void>
) {
  const resourceKey = `${event.data.object}:${event.data.id}`;

  const existing = pendingDebounce.get(resourceKey);
  if (existing) clearTimeout(existing);

  pendingDebounce.set(
    resourceKey,
    setTimeout(async () => {
      pendingDebounce.delete(resourceKey);
      await handler(event);
    }, DEBOUNCE_MS)
  );
}

// Combined entry point
async function onWebhookReceived(event: NotionWebhookEvent) {
  if (isDuplicate(event)) {
    console.log(`Skipping duplicate: ${event.type} ${event.data.id}`);
    return;
  }
  debounceEvent(event, handleWebhookEvent);
}
```

### Step 3: Scheduled Polling with Cron / GitHub Actions

For background sync that does not require a persistent server, run a polling script on a schedule:

#### Node.js Script for Cron

```typescript
// scripts/notion-sync.ts
import { Client } from '@notionhq/client';
import { readFileSync, writeFileSync, existsSync } from 'fs';

const STATE_FILE = './notion-sync-state.json';
const notion = new Client({ auth: process.env.NOTION_TOKEN! });
const DATABASE_ID = process.env.NOTION_DATABASE_ID!;

interface SyncState {
  lastSync: string;
  processedCount: number;
}

function loadState(): SyncState {
  if (existsSync(STATE_FILE)) {
    return JSON.parse(readFileSync(STATE_FILE, 'utf-8'));
  }
  // First run: look back 24 hours
  return {
    lastSync: new Date(Date.now() - 86400_000).toISOString(),
    processedCount: 0,
  };
}

function saveState(state: SyncState) {
  writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

async function syncChanges() {
  const state = loadState();
  console.log(`Syncing changes since ${state.lastSync}`);

  const changed: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: DATABASE_ID,
      filter: {
        timestamp: 'last_edited_time',
        last_edited_time: { after: state.lastSync },
      },
      sorts: [{ timestamp: 'last_edited_time', direction: 'ascending' }],
      start_cursor: cursor,
      page_size: 100,
    });
    changed.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  console.log(`Found ${changed.length} changed page(s)`);

  for (const page of changed) {
    await processChangedPage(page);
  }

  saveState({
    lastSync: new Date().toISOString(),
    processedCount: state.processedCount + changed.length,
  });
}

async function processChangedPage(page: any) {
  // Your sync logic: update database, push to webhook, etc.
  console.log(`Processing: ${page.id} (edited ${page.last_edited_time})`);
}

syncChanges().catch(err => {
  console.error('Sync failed:', err);
  process.exit(1);
});
```

#### GitHub Actions Schedule

```yaml
# .github/workflows/notion-sync.yml
name: Notion Sync
on:
  schedule:
    - cron: '*/5 * * * *'   # Every 5 minutes
  workflow_dispatch:          # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: npm ci

      - name: Restore sync state
        uses: actions/cache@v4
        with:
          path: notion-sync-state.json
          key: notion-sync-${{ github.run_id }}
          restore-keys: notion-sync-

      - run: npx tsx scripts/notion-sync.ts
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
```

#### Third-Party Connector Pattern (Zapier / Make)

If you do not want to manage infrastructure, use a connector as the event source and your API as the handler:

```
Notion page updated (Zapier trigger)
  → Webhook POST to your endpoint
    → Your handler fetches full data via @notionhq/client
```

This gives you near real-time updates without running a server, but adds a vendor dependency and typically has 1-15 minute latency depending on the plan.

## Output

- Polling-based change detection for workspace-wide or per-database monitoring
- Property-level diff detection comparing current state against cached snapshots
- Block-level content fingerprinting for page body change tracking
- Native webhook receiver with verification handshake and event routing
- Deduplication and debouncing for reliable event processing
- Cron/GitHub Actions scheduled sync with persistent state

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `search` returns stale results | Notion indexing delay (up to 30s) | Accept eventual consistency; do not poll faster than 30s |
| Rate limited during polling | Too many API calls per second | Add 350ms delay between paginated requests; use `databases.query` over `search` when possible |
| Webhook verification fails | Endpoint not returning `{ challenge }` | Respond with `res.json({ challenge: req.body.challenge })` for `url_verification` type |
| Duplicate webhook events | Network retries from Notion | Deduplicate on `type + data.id + timestamp` composite key |
| Missed changes between polls | Poll interval too wide | Persist `lastPollTimestamp` to disk; use overlapping windows (poll since `lastSync - 60s`) |
| Content changes not detected | `last_edited_time` only covers properties | Use `blocks.children.list` fingerprinting for page body changes |
| `databases.query` filter ignored | Wrong filter structure | Use `{ timestamp: 'last_edited_time', last_edited_time: { after: isoString } }` — not a property filter |

## Examples

### Minimal Change Watcher (One File)

```typescript
// watch-notion.ts — run with: npx tsx watch-notion.ts
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN! });
const DB = process.env.NOTION_DATABASE_ID!;
let since = new Date(Date.now() - 3600_000).toISOString(); // Last hour

setInterval(async () => {
  const { results } = await notion.databases.query({
    database_id: DB,
    filter: { timestamp: 'last_edited_time', last_edited_time: { after: since } },
    sorts: [{ timestamp: 'last_edited_time', direction: 'descending' }],
  });

  if (results.length > 0) {
    console.log(`${new Date().toISOString()} — ${results.length} change(s)`);
    since = new Date().toISOString();
  }
}, 60_000);

console.log('Watching for changes...');
```

### Local Webhook Development with ngrok

```bash
# Terminal 1: Start your webhook server
npx tsx webhook-server.ts

# Terminal 2: Expose via ngrok
ngrok http 3000

# Copy the https://*.ngrok-free.app URL to your Notion integration's
# webhook settings at https://www.notion.so/my-integrations
```

### Hybrid: Webhooks + Polling Fallback

```typescript
// Use webhooks for real-time, polling as a safety net
class HybridChangeDetector {
  private lastWebhookTime = Date.now();
  private readonly STALE_THRESHOLD = 5 * 60 * 1000; // 5 min

  onWebhookReceived(event: NotionWebhookEvent) {
    this.lastWebhookTime = Date.now();
    this.processChange(event.data.id, 'webhook');
  }

  startFallbackPolling(intervalMs = 120_000) {
    setInterval(async () => {
      const timeSinceWebhook = Date.now() - this.lastWebhookTime;
      if (timeSinceWebhook > this.STALE_THRESHOLD) {
        console.log('No webhooks received recently — running poll fallback');
        const changes = await pollWorkspaceChanges();
        for (const c of changes) {
          this.processChange(c.id, 'poll-fallback');
        }
      }
    }, intervalMs);
  }

  private processChange(id: string, source: string) {
    console.log(`[${source}] Change detected: ${id}`);
  }
}
```

## Resources

- [Notion API Search endpoint](https://developers.notion.com/reference/post-search)
- [Database query filters](https://developers.notion.com/reference/post-database-query-filter)
- [Notion Webhooks Reference](https://developers.notion.com/reference/webhooks)
- [Webhook Actions (database automations)](https://www.notion.com/help/webhook-actions)
- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client)
- [Rate limits](https://developers.notion.com/reference/request-limits)

## Next Steps

For tuning poll intervals and managing API usage, see `notion-rate-limits` and `notion-performance-tuning`.
