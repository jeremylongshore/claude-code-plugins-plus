---
name: clickhouse-webhooks-events
description: |
  Ingest data into ClickHouse from webhooks, Kafka, and streaming sources
  with batching, dedup, and exactly-once patterns.
  Use when building data ingestion pipelines, consuming webhook payloads,
  or integrating Kafka topics into ClickHouse.
  Trigger: "clickhouse ingestion", "clickhouse webhook", "clickhouse Kafka",
  "stream data to clickhouse", "clickhouse data pipeline".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Data Ingestion

## Overview

Build data ingestion pipelines into ClickHouse from HTTP webhooks, Kafka,
and streaming sources with proper batching, deduplication, and error handling.

## Prerequisites

- ClickHouse table with appropriate engine (see `clickhouse-core-workflow-a`)
- `@clickhouse/client` connected

## Instructions

### Step 1: Webhook Receiver with Batched Inserts

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

### Step 2: Kafka Table Engine (Server-Side Ingestion)

```sql
-- Create a Kafka engine table (consumes messages automatically)
CREATE TABLE analytics.events_kafka (
    event_type  String,
    user_id     UInt64,
    properties  String,
    timestamp   DateTime
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'events',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 2,
    kafka_max_block_size = 65536;

-- Materialized view pipes Kafka → MergeTree automatically
CREATE MATERIALIZED VIEW analytics.events_kafka_mv
TO analytics.events
AS SELECT
    event_type,
    user_id,
    properties,
    timestamp AS created_at
FROM analytics.events_kafka;

-- ClickHouse now consumes from Kafka continuously!
-- Check lag:
SELECT * FROM system.kafka_consumers;
```

### Step 3: ClickPipes (ClickHouse Cloud Managed Ingestion)

ClickHouse Cloud offers **ClickPipes** — a managed ingestion service that
connects to Kafka, Confluent, Amazon MSK, S3, and GCS without code.

```
ClickPipes Configuration (Cloud Console):
1. Source: Amazon MSK / Confluent Cloud / Apache Kafka
2. Topic: events
3. Format: JSONEachRow
4. Target: analytics.events
5. Scaling: 2 consumers (auto-scales)
```

### Step 4: HTTP Interface Bulk Insert

```bash
# Insert from CSV file via HTTP (no client needed)
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+CSVWithNames' \
  --data-binary @events.csv

# Insert from NDJSON file
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+JSONEachRow' \
  --data-binary @events.ndjson

# Insert from Parquet file
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+Parquet' \
  --data-binary @events.parquet

# Insert from remote URL (ClickHouse fetches it)
INSERT INTO analytics.events
SELECT * FROM url('https://data.example.com/events.csv', CSVWithNames);

# Insert from S3
INSERT INTO analytics.events
SELECT * FROM s3(
    'https://my-bucket.s3.amazonaws.com/events/*.parquet',
    'ACCESS_KEY', 'SECRET_KEY',
    'Parquet'
);
```

### Step 5: Deduplication with ReplacingMergeTree

```sql
-- For idempotent ingestion (webhook retries, Kafka reprocessing)
CREATE TABLE analytics.events_dedup (
    event_id    String,           -- Unique event identifier
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String,
    created_at  DateTime,
    _version    UInt64 DEFAULT toUnixTimestamp(now())
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY event_id;               -- Dedup key

-- Insert duplicate-safe: same event_id keeps latest _version
-- Query with FINAL for deduplicated results
SELECT * FROM analytics.events_dedup FINAL
WHERE created_at >= today() - 7;
```

### Step 6: Insert Monitoring

```sql
-- Track insert throughput
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS inserts,
    sum(written_rows) AS rows_inserted,
    formatReadableSize(sum(written_bytes)) AS bytes_inserted
FROM system.query_log
WHERE type = 'QueryFinish'
  AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute
ORDER BY minute;

-- Check for insert errors
SELECT event_time, exception, substring(query, 1, 200)
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
ORDER BY event_time DESC;
```

## Insert Best Practices

| Practice | Why |
|----------|-----|
| Batch 10K-100K rows per INSERT | Fewer parts, faster merges |
| Buffer 1-5 seconds for real-time | Balances latency vs throughput |
| Use `JSONEachRow` format | Client handles serialization |
| Compress with `ZSTD` on wire | Reduces network transfer |
| Use `ReplacingMergeTree` for retries | Handles duplicate delivery |
| Use `async_insert=1` for small batches | Server-side batching |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Too many parts` | Single-row inserts | Batch inserts (10K+ rows) |
| `Cannot parse input` | Wrong format | Match format to data structure |
| `TIMEOUT` on large insert | Slow network | Enable compression, split batch |
| Duplicate events | Webhook retries | Use ReplacingMergeTree + event_id |

## Resources

- [Kafka Integration](https://clickhouse.com/docs/integrations/kafka)
- [ClickPipes](https://clickhouse.com/cloud/clickpipes)
- [HTTP Interface](https://clickhouse.com/docs/interfaces/http)
- [S3 Table Function](https://clickhouse.com/docs/sql-reference/table-functions/s3)

## Next Steps

For query and server performance, see `clickhouse-performance-tuning`.
