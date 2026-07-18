---
name: notion-cost-tuning
description: 'Optimize Notion API usage to minimize rate-limit pressure, reduce engineering
  overhead, and maximize throughput. Use when auditing request volume, eliminating
  redundant API calls, implementing caching, or restructuring queries for efficiency.
  Trigger with "notion cost", "notion optimize", "notion API usage", "reduce notion
  requests", "notion rate limit budget", "notion efficient", "notion caching".'
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob, Grep
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- optimization
- caching
- cost
compatibility: Designed for Claude Code
---
# Notion Cost Tuning

## Overview

The Notion API is **free with every workspace plan** — there is no per-call pricing. The real "cost" is the **3 requests/second rate limit** (per integration token) plus the engineering time wasted on inefficient patterns. Apply the six strategies below to reduce request volume by 80-95%.

**Notion workspace pricing (for context — API access is included at every tier):**

| Plan | Price | API Access | Rate Limit |
| ------ | ------- | ------------ | ------------ |
| Free | $0 | Full API | 3 req/sec |
| Plus | $12/user/mo | Full API | 3 req/sec |
| Business | $28/user/mo | Full API | 3 req/sec |
| Enterprise | Custom | Full API | 3 req/sec |

The rate limit is identical across all plans. Optimization is about staying within 3 req/sec, not reducing a bill.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Token shared with target pages/databases via the **Connections** menu in Notion
- For queue patterns: `p-queue` v8+ (`npm install p-queue`)
- For caching: `node-cache` or `lru-cache` (`npm install lru-cache`)

## Authentication

Every technique here uses the same auth as any Notion integration: a single bearer token passed to the client constructor. Store it in an environment variable (`NOTION_TOKEN`) — never hardcode it — and share it with each target page/database through the **Connections** menu. One token = one 3 req/sec budget; provision a separate integration token per service when you need independent budgets.

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN });
```

## Instructions

Work the three steps in order. Each links to the full, copy-paste-ready code in [references/implementation.md](references/implementation.md); the essentials are inlined below so you can follow the flow from here.

### Step 1: Audit current request volume

Measure before optimizing. Wrap every Notion call in a tracker that records method, endpoint, timestamp, and duration, then print a per-minute report to find the operations eating > 50% of your budget (usually polling loops, redundant retrieves, and full-table scans).

```typescript
async function tracked<T>(method: string, fn: () => Promise<T>): Promise<T> {
  const start = Date.now();
  try {
    return await fn();
  } finally {
    requestLog.push({ method, timestamp: start, durationMs: Date.now() - start });
  }
}
```

Full tracker + `auditReport()`: [references/implementation.md](references/implementation.md), § Step 1.

### Step 2: Eliminate redundant reads and shrink payloads

Three patterns cut reads immediately: (A) stop calling `pages.retrieve` on pages you already got from `databases.query` — the properties are already there; (B) pass `filter_properties` (property IDs, not names) to shrink responses 60-90%; (C) filter on `last_edited_time` to fetch only what changed since the last sync instead of re-scanning the whole database.

```typescript
// Redundant: query already returned every property — skip the retrieve
const { results } = await notion.databases.query({ database_id: dbId });
for (const page of results) processPage(page); // 1 request total, not 1 + N
```

All three patterns with runnable code: [references/implementation.md](references/implementation.md), § Step 2.

### Step 3: Cache, batch, and replace polling

Cache read-heavy data with a TTL'd LRU; throttle writes through a `p-queue` sized to the 3 req/sec limit; batch up to 100 blocks per `blocks.children.append`; and replace polling loops with webhooks (a 10-second poll costs 360 requests/hour per database — webhooks cost zero).

```typescript
// Rate-limited write queue — never exceeds 3 req/sec
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
```

Caching, batching, and the webhook handler: [references/implementation.md](references/implementation.md), § Step 3.

## Output

After applying these optimizations:

- **Audit report** showing request volume baseline and hotspots
- **Redundant reads eliminated** — no duplicate `pages.retrieve` after `databases.query`
- **Payload sizes reduced** 60-90% via `filter_properties`
- **Incremental sync** via `last_edited_time` filter replacing full-table scans
- **Cache layer** with TTL-based invalidation for reads
- **Write throughput maximized** via queue-based throttling and block batching
- **Polling eliminated** where webhooks are available (360 req/hr per database saved)

**Typical impact:** integrations drop from 500+ requests/hour to under 200 requests/hour (80-95% reduction), staying well within the 3 req/sec limit even with multiple databases.

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| 429 Too Many Requests despite optimization | Shared token across multiple services | Use separate integration tokens per service; each gets its own 3 req/sec budget |
| Stale cached data causing bugs | Cache TTL too long for the use case | Shorten TTL to 30-60s for volatile data, or use webhook-based cache invalidation |
| Webhook not triggering | Integration not connected to the page/database | Share via **Connections** menu in Notion; verify webhook URL is publicly accessible |
| `filter_properties` returning empty results | Using property names instead of IDs | Run `databases.retrieve` to get property IDs (short strings like `abc1`), not display names |
| Incremental sync missing updates | Clock skew between client and Notion server | Subtract 5-second buffer from `lastSync` timestamp to create overlap window |
| `blocks.children.append` failing with 400 | More than 100 children in single call | Chunk arrays into groups of 100 before appending |

## Examples

Two complete worked examples live in [references/examples.md](references/examples.md):

- **Request Reduction Calculator** — estimate before/after request volume and rate-limit headroom for your own database count, page count, and poll interval before you commit to changes.
- **Full Optimization Wrapper** — a drop-in `createOptimizedClient(token)` that bundles caching, request tracking, and a rate-limited write queue into one client.

Skeleton of the wrapper (full body in the reference):

```typescript
export function createOptimizedClient(token: string) {
  const notion = new Client({ auth: token });
  const cache = new LRUCache<string, any>({ max: 1000, ttl: 5 * 60 * 1000 });
  const writeQueue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
  // getPage / queryDatabase / createPage / invalidate / stats — see references/examples.md
}
```

## Resources

- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per token, `Retry-After` header on 429
- [Database Query Filter](https://developers.notion.com/reference/post-database-query-filter) — push filtering server-side
- [Filter Properties Parameter](https://developers.notion.com/reference/retrieve-a-page#filter-properties) — reduce response payload size
- [Notion Webhooks](https://developers.notion.com/reference/webhooks) — event-driven updates replacing polling
- [Block Children Append](https://developers.notion.com/reference/patch-block-children) — batch up to 100 blocks per call
- [Notion Pricing](https://www.notion.so/pricing) — API included at all tiers, no per-call charges
- [references/implementation.md](references/implementation.md) — full three-step walkthrough with complete code
- [references/examples.md](references/examples.md) — request calculator and drop-in optimized client

## Next Steps

For rate-limit retry patterns, see `notion-rate-limits`. For query and search patterns, see `notion-search-retrieve`. For overall architecture guidance, see `notion-reference-architecture`.
