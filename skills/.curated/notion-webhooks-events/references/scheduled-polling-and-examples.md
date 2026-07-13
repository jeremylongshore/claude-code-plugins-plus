# Scheduled Polling with Cron / GitHub Actions

For background sync that does not require a persistent server, run a polling script on a schedule.

## Node.js Script for Cron

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

## GitHub Actions Schedule

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

## Third-Party Connector Pattern (Zapier / Make)

If you do not want to manage infrastructure, use a connector as the event source and your API as the handler:

```
Notion page updated (Zapier trigger)
  -> Webhook POST to your endpoint
    -> Your handler fetches full data via @notionhq/client
```

This gives you near real-time updates without running a server, but adds a vendor dependency and typically has 1-15 minute latency depending on the plan.

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
