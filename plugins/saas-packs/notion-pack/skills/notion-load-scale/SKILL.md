---
name: notion-load-scale
description: |
  Use when you must move high volumes through the Notion API without tripping
  its 3 req/sec limit — bulk-creating pages, syncing 100K+ record databases, or
  running background jobs. Covers parallel requests within 3 req/sec, worker
  queues, database pagination at scale, incremental sync for large workspaces,
  and memory management for bulk operations.
  Trigger with phrases like "notion scale", "notion bulk operations",
  "notion high volume", "notion worker queue", "notion incremental sync".
allowed-tools: Read, Write, Bash(node:*), Bash(npx:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Load & Scale

## Overview

Patterns for high-volume Notion API usage within the 3 requests/second rate
limit. Covers parallel request orchestration with `p-queue`, worker queue
architecture for background processing, full database pagination at scale
(100K+ records), incremental sync using `last_edited_time` filters to avoid
re-fetching unchanged data, and memory management for bulk operations via
streaming and chunked processing.

Full runnable TypeScript + Python implementations for all three steps live in
[references/implementation.md](references/implementation.md); planning utilities
live in [references/examples.md](references/examples.md).

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- `p-queue` for rate-limited concurrency (`npm install p-queue`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` set (each token gets its own 3 req/s limit)
- Test database in Notion (dedicated for load testing)

## Authentication

All operations authenticate with a Notion internal integration token in the
`NOTION_TOKEN` environment variable; the SDKs send it as a `Bearer` token
automatically. **Each token has an independent 3 req/s limit** — the key lever
for horizontal scaling. Full auth notes, including raw `curl` headers, are in
[references/implementation.md](references/implementation.md).

## Instructions

The three patterns compose: rate-limited calls (Step 1) are the primitive the
worker queue (Step 2) and the streaming paginator (Step 3) both build on. Read
the lean summary here, then open
[references/implementation.md](references/implementation.md) for the complete
code.

### Step 1: Parallel Requests Within Rate Limits

Notion enforces 3 requests/second per integration token. Drive every call
through a single `p-queue` tuned to `interval: 340` / `intervalCap: 1` (~3/s
with a safety margin) rather than relying on concurrency alone, and wrap each
call so a `rate_limited` (429) response honors `retry-after` and retries once.

```typescript
import PQueue from 'p-queue';

const apiQueue = new PQueue({ concurrency: 1, interval: 340, intervalCap: 1 });

// Every Notion call goes through this queue; add 429 retry inside (see refs).
const results = await Promise.all(
  dbIds.map(id => apiQueue.add(() =>
    notion.databases.query({ database_id: id, page_size: 100 })
  ))
);
```

Full wrapper (metrics, `retry-after` handling, Python token-bucket variant) is
in Step 1 of [references/implementation.md](references/implementation.md).

### Step 2: Worker Queue Architecture for Background Processing

For sustained high-volume writes, decouple API calls from user requests with a
job queue. A `NotionWorkerQueue` wraps the same rate-limited `p-queue`, dispatches
by job type (`create`/`update`/`query`/`append`), retries `rate_limited` jobs with
exponential backoff, and routes jobs past `maxRetries` to a dead-letter list. See Step 2 of
[references/implementation.md](references/implementation.md) for the full class
plus a 500-page bulk-create example (~170s at 3/s).

### Step 3: Pagination at Scale, Incremental Sync, Memory Management

For 100K+ record databases, stream pages through an async generator so results
are processed a batch at a time instead of loading everything into memory. Layer
incremental sync on top: filter by `last_edited_time` `on_or_after` your last
run and persist the server-returned timestamp between runs — cutting subsequent
API calls by 90%+.

```typescript
async function* paginateDatabase(databaseId: string, filter?: any) {
  let cursor: string | undefined;
  do {
    const res = await notion.databases.query({
      database_id: databaseId, filter, page_size: 100, start_cursor: cursor,
    });
    yield res.results;                       // process a batch, then release it
    cursor = res.has_more ? res.next_cursor ?? undefined : undefined;
  } while (cursor);
}
```

Full streaming processor, incremental-sync driver with persisted state, and the
Python generator + multi-token scaling helper are in Step 3 of
[references/implementation.md](references/implementation.md).

## Output

- Rate-limited parallel requests maximizing 3 req/s throughput
- Worker queue with priority, retries, and dead letter handling
- Streaming pagination for 100K+ record databases
- Incremental sync reducing API calls by 90%+ on subsequent runs
- Memory-efficient processing via async generators

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Sustained 429 errors | Exceeding 3 req/s | Reduce `intervalCap` or increase `interval` |
| Memory growing during bulk read | Loading all results into array | Use async generator streaming |
| Stale incremental sync | Clock skew between systems | Use server-returned timestamps |
| Queue growing unbounded | Write rate exceeds 3/s sustained | Add more integration tokens (each gets own limit) |
| Timeout on large queries | Notion API response time | Reduce `page_size`, add retry logic |
| Duplicate records in sync | Concurrent modifications | Deduplicate by page ID after collection |

## Examples

- **Capacity Calculator** — estimate whether a planned read/write mix fits your
  token budget before a bulk run (accounts for cache hit rate + multi-token
  scaling).
- **Quick Throughput Benchmark** — time 10 sequential calls to measure baseline
  per-call latency without tripping the rate limit.

Both utilities, with full code, are in
[references/examples.md](references/examples.md).

## Resources

- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [Notion Pagination](https://developers.notion.com/reference/pagination)
- [p-queue - Promise Queue with Concurrency Control](https://github.com/sindresorhus/p-queue)
- [Notion Database Query Filter](https://developers.notion.com/reference/post-database-query-filter)

## Next Steps

For reliability patterns, see `notion-reliability-patterns`.
For architecture decisions at scale, see `notion-architecture-variants`.
