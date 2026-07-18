---
name: clickhouse-webhooks-events
description: |
  Ingest data into ClickHouse from webhooks, Kafka, and streaming sources
  with batching, dedup, and exactly-once patterns.
  Use when building data ingestion pipelines, consuming webhook payloads,
  or integrating Kafka topics into ClickHouse.
  Trigger with "clickhouse ingestion", "clickhouse webhook", "clickhouse Kafka",
  "stream data to clickhouse", "clickhouse data pipeline".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Data Ingestion

## Overview

Build data ingestion pipelines into ClickHouse from HTTP webhooks, Kafka, and
streaming sources with proper batching, deduplication, and error handling.

The core rule: ClickHouse hates one-row-at-a-time inserts — buffer events and
flush them in batches. This skill covers four ingestion paths (application-side
webhook receiver, server-side Kafka engine, managed ClickPipes, and HTTP bulk
loads) plus idempotent dedup and insert monitoring.

## Prerequisites

- A ClickHouse table with an appropriate engine already exists (a `MergeTree`
  variant, e.g. `analytics.events`) — see `clickhouse-core-workflow-a`.
- The `@clickhouse/client` package is installed and connected via
  `CLICKHOUSE_HOST`.
- For the Kafka paths, a reachable Kafka broker and topic.

## Instructions

### Step 1: Webhook Receiver with Batched Inserts

Buffer incoming events in memory, flush on a size threshold or a timer, and
re-queue the batch on failure so no event is lost. This is the application-side
core of the skill:

```typescript
import express from 'express';
import { createClient } from '@clickhouse/client';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });
const app = express();
app.use(express.json());

// Buffer for batching — ClickHouse hates one-row-at-a-time inserts
const buffer: Record<string, unknown>[] = [];
const BATCH_SIZE = 5_000;
const FLUSH_INTERVAL_MS = 5_000;

async function flushBuffer() {
  if (buffer.length === 0) return;
  const batch = buffer.splice(0, buffer.length);

  try {
    await client.insert({
      table: 'analytics.events',
      values: batch,
      format: 'JSONEachRow',
    });
    console.log(`Flushed ${batch.length} events to ClickHouse`);
  } catch (err) {
    console.error('Insert failed, re-queuing:', (err as Error).message);
    buffer.unshift(...batch);  // Put back at front for retry
  }
}

// Flush periodically
setInterval(flushBuffer, FLUSH_INTERVAL_MS);

// Webhook endpoint
app.post('/ingest', async (req, res) => {
  const events = Array.isArray(req.body) ? req.body : [req.body];

  for (const event of events) {
    buffer.push({
      event_type: event.type ?? 'unknown',
      user_id: event.userId ?? 0,
      properties: JSON.stringify(event.properties ?? {}),
      created_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
    });
  }

  if (buffer.length >= BATCH_SIZE) {
    await flushBuffer();
  }

  res.status(202).json({ queued: events.length, buffer_size: buffer.length });
});
```

### Step 2: Choose a Server-Side or Managed Path

For high-volume streams, prefer a path that needs no application consumer:

- **Kafka table engine** — ClickHouse consumes a topic directly and a
  materialized view pipes rows into your MergeTree table. No consumer to run.
- **ClickPipes** — ClickHouse Cloud's managed, code-free ingestion for Kafka,
  Confluent, Amazon MSK, S3, and GCS.
- **HTTP interface** — bulk-load CSV / NDJSON / Parquet from files, remote
  URLs, or S3 with plain `curl`, no client library.

Full DDL and configuration for all three: see
[Ingestion methods](references/ingestion-methods.md).

### Step 3: Make Ingestion Idempotent and Observable

Webhook retries and Kafka reprocessing deliver duplicates. Use a
`ReplacingMergeTree` keyed on a unique `event_id` so re-delivered events collapse
to one row, and query `system.query_log` to watch insert throughput and errors.
Full DDL, monitoring queries, and the batch-tuning matrix:
[Deduplication & monitoring](references/dedup-and-monitoring.md).

## Output

Applying this skill produces:

- A running **webhook receiver** (`POST /ingest`) that buffers events and
  batch-flushes to ClickHouse, returning `202 { queued, buffer_size }`.
- Optionally, a **Kafka engine table + materialized view** (or a ClickPipes
  pipe) that ingests a topic server-side with no application consumer.
- A **`ReplacingMergeTree` dedup table** keyed on `event_id` for idempotent,
  retry-safe ingestion.
- **Monitoring queries** over `system.query_log` reporting inserts/minute,
  rows, bytes, and insert exceptions in the last hour.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Too many parts` | Single-row inserts | Batch inserts (10K+ rows) |
| `Cannot parse input` | Wrong format | Match format to data structure |
| `TIMEOUT` on large insert | Slow network | Enable compression, split batch |
| Duplicate events | Webhook retries | Use ReplacingMergeTree + event_id |

## Examples

**Ingest a webhook batch via the receiver** (Step 1):

```bash
curl -X POST http://localhost:3000/ingest \
  -H 'Content-Type: application/json' \
  -d '[{"type":"signup","userId":42,"properties":{"plan":"pro"}}]'
# → 202 { "queued": 1, "buffer_size": 1 }
```

**Bulk-load a Parquet file with no client** (HTTP interface — see
[Ingestion methods](references/ingestion-methods.md)):

```bash
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+Parquet' \
  --data-binary @events.parquet
```

**Read deduplicated events** (ReplacingMergeTree — see
[Deduplication & monitoring](references/dedup-and-monitoring.md)):

```sql
SELECT * FROM analytics.events_dedup FINAL
WHERE created_at >= today() - 7;
```

## Resources

- [Ingestion methods](references/ingestion-methods.md) — Kafka engine,
  ClickPipes, HTTP bulk insert (full DDL)
- [Deduplication & monitoring](references/dedup-and-monitoring.md) —
  ReplacingMergeTree, `system.query_log` queries, best-practices matrix
- [Kafka Integration](https://clickhouse.com/docs/integrations/kafka)
- [ClickPipes](https://clickhouse.com/cloud/clickpipes)
- [HTTP Interface](https://clickhouse.com/docs/interfaces/http)
- [S3 Table Function](https://clickhouse.com/docs/sql-reference/table-functions/s3)

## Next Steps

For query and server performance after ingestion is flowing, see
`clickhouse-performance-tuning`. For engine and schema choices on the target
table, see `clickhouse-core-workflow-a`.
