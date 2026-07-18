---
name: notion-webhooks-events
description: 'Build change detection and event handling for Notion workspaces using

  polling, native webhooks, and third-party connectors.

  Use when implementing real-time sync, change feeds, incremental backup,

  or event-driven workflows with Notion data.

  Trigger with phrases like "notion webhook", "notion events",

  "notion change detection", "notion polling", "notion sync changes",

  "notion real-time", "notion watch for changes".

  '
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npx:*), Bash(npm:*), Bash(curl:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Webhooks & Event Handling

## Overview

Notion offers three approaches to change detection, each with different trade-offs:

| Approach | Latency | Complexity | Reliability |
| ---------- | --------- | ------------ | ------------- |
| **Polling with `search` / `databases.query`** | 30s-5min (your poll interval) | Low | High — you control timing |
| **Native webhooks** (API 2025-02+) | Near real-time | Medium | Good — requires HTTPS endpoint, retry handling |
| **Third-party connectors** (Zapier, Make) | 1-15 min | Low (no-code) | Vendor-dependent |

**Honest assessment:** Notion's native webhook support arrived in mid-2025 and covers page, database, comment, and data source events. It works well for event notification but does not deliver full payloads — you still need API calls to fetch the changed data. For many use cases, especially incremental sync and backup, polling with `last_edited_time` filters remains the most battle-tested pattern.

## Prerequisites

- `@notionhq/client` v2.3+ installed (`npm install @notionhq/client`)
- Notion integration created at <https://www.notion.so/my-integrations>
- Integration shared with target pages/databases (Connections menu in Notion)
- `NOTION_TOKEN` environment variable set to the integration's Internal Integration Secret
- For native webhooks: HTTPS endpoint accessible from the internet

## Authentication

All API calls authenticate with the integration's Internal Integration Secret, passed as a bearer token. The `@notionhq/client` handles the header when you construct the client — never hardcode the secret:

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

Store `NOTION_TOKEN` in your environment (`.env`, a GitHub Actions secret, or a secrets manager) and grant the integration access to each target page/database via the Connections menu.

Webhook deliveries themselves carry no bearer token — verify them with the `url_verification` handshake and treat the payload as untrusted, fetching the real data through the authenticated client rather than trusting the event body.

## Instructions

Pick an approach from the Overview table, then follow the matching step. Steps 1 and 2 keep a runnable skeleton here and link to the full implementation in `references/`.

### Step 1: Polling-Based Change Detection

Polling is the most reliable approach and works with every Notion API version. Use `notion.search()` to discover recently edited content across the entire workspace, or `notion.databases.query()` with a `last_edited_time` filter for targeted change detection on a single database. The database-scoped query below is the efficient default — it stays within rate limits and returns only what changed since your last poll:

```typescript
import { Client } from '@notionhq/client';
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Return pages edited since the given ISO 8601 timestamp
async function pollDatabaseChanges(databaseId: string, since: string) {
  const { results } = await notion.databases.query({
    database_id: databaseId,
    filter: { timestamp: 'last_edited_time', last_edited_time: { after: since } },
    sorts: [{ timestamp: 'last_edited_time', direction: 'descending' }],
  });
  return results; // paginate on response.has_more for large result sets
}
```

`references/polling.md` covers the full implementation: a paginated workspace-wide change feed with a high-water-mark cursor, a property-level `diffChanges` that reports exactly which fields changed against a cache, and block-level content fingerprinting to catch edits inside a page body (not just property edits). See [full polling implementation](references/polling.md).

### Step 2: Native Webhooks (API 2025-02+)

Notion's native webhooks deliver HTTP POST notifications when pages, databases, comments, or data sources change. They notify you that something changed — you then call the API to fetch the actual data. The receiver must first answer the one-time registration handshake, then acknowledge every event fast and process it asynchronously:

```typescript
import express from 'express';
const app = express();
app.use(express.json());

app.post('/webhooks/notion', (req, res) => {
  // Registration handshake: echo the challenge back
  if (req.body.type === 'url_verification') {
    return res.status(200).json({ challenge: req.body.challenge });
  }
  res.status(200).json({ ok: true }); // ack fast — process async
  handleWebhookEvent(req.body);
});

app.listen(3000, () => console.log('Webhook receiver on :3000'));
```

`references/webhooks.md` covers the full implementation: the `NotionWebhookEvent` type, the complete list of supported event types (`page.*`, `database.*`, `comment.*`, `data_source.*`), a `switch`-based `handleWebhookEvent` router that fetches the changed resource, and the deduplication + debouncing layer that absorbs Notion's delivery retries and rapid-edit bursts. See [full webhook implementation](references/webhooks.md).

### Step 3: Scheduled Polling with Cron / GitHub Actions

See [scheduled polling and examples](references/scheduled-polling-and-examples.md) for Node.js cron scripts, GitHub Actions scheduled sync with persistent state, third-party connector patterns, and additional examples including minimal change watchers and hybrid webhook+polling fallback.

## Output

- Polling-based change detection for workspace-wide or per-database monitoring
- Property-level diff detection comparing current state against cached snapshots
- Block-level content fingerprinting for page body change tracking
- Native webhook receiver with verification handshake and event routing
- Deduplication and debouncing for reliable event processing
- Cron/GitHub Actions scheduled sync with persistent state

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `search` returns stale results | Notion indexing delay (up to 30s) | Accept eventual consistency; do not poll faster than 30s |
| Rate limited during polling | Too many API calls per second | Add 350ms delay between paginated requests; use `databases.query` over `search` when possible |
| Webhook verification fails | Endpoint not returning `{ challenge }` | Respond with `res.json({ challenge: req.body.challenge })` for `url_verification` type |
| Duplicate webhook events | Network retries from Notion | Deduplicate on `type + data.id + timestamp` composite key |
| Missed changes between polls | Poll interval too wide | Persist `lastPollTimestamp` to disk; use overlapping windows (poll since `lastSync - 60s`) |
| Content changes not detected | `last_edited_time` only covers properties | Use `blocks.children.list` fingerprinting for page body changes |
| `databases.query` filter ignored | Wrong filter structure | Use `{ timestamp: 'last_edited_time', last_edited_time: { after: isoString } }` — not a property filter |

## Examples

### Minimal Webhook Receiver (verification + fetch on change)

```typescript
import express from 'express';
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const app = express();
app.use(express.json());

app.post('/webhooks/notion', async (req, res) => {
  // Registration handshake: echo the challenge back
  if (req.body.type === 'url_verification') {
    return res.status(200).json({ challenge: req.body.challenge });
  }
  res.status(200).json({ ok: true }); // ack fast, process async

  // Webhooks carry no payload — fetch the changed resource
  if (req.body.type === 'page.properties_updated') {
    const page = await notion.pages.retrieve({ page_id: req.body.data.id });
    console.log('Page changed:', 'url' in page ? page.url : page.id);
  }
});

app.listen(3000);
```

### One-Database Change Watcher (polling)

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
let since = new Date().toISOString();

setInterval(async () => {
  const response = await notion.databases.query({
    database_id: process.env.NOTION_DATABASE_ID!,
    filter: { timestamp: 'last_edited_time', last_edited_time: { after: since } },
    sorts: [{ timestamp: 'last_edited_time', direction: 'descending' }],
  });
  if (response.results.length > 0) {
    since = (response.results[0] as any).last_edited_time;
    console.log(`${response.results.length} row(s) changed since last poll`);
  }
}, 60_000); // 60s interval respects the 3 req/s rate limit
```

## Resources

- [Notion API Search endpoint](https://developers.notion.com/reference/post-search)
- [Database query filters](https://developers.notion.com/reference/post-database-query-filter)
- [Notion Webhooks Reference](https://developers.notion.com/reference/webhooks)
- [Webhook Actions (database automations)](https://www.notion.com/help/webhook-actions)
- [@notionhq/client on npm](https://www.npmjs.com/package/@notionhq/client)
- [Rate limits](https://developers.notion.com/reference/request-limits)

## Next Steps

Once change detection is working, tune it for scale. For sizing poll intervals against Notion's 3 requests/second limit and avoiding 429s during bursts, see the `notion-rate-limits` skill. For caching, batching, and reducing per-poll API calls on large workspaces, see `notion-performance-tuning`. For scheduled background sync without a persistent server, follow [scheduled polling and examples](references/scheduled-polling-and-examples.md).
