# Partitioning and Applying Schema

Detailed partitioning guidance plus the Node.js path for applying DDL
programmatically with `@clickhouse/client`.

## Partitioning Guidelines

| Partition Expression | Typical Use | Parts Per Partition |
|---------------------|-------------|---------------------|
| `toYYYYMM(date)` | Most common — monthly | Target 10-1000 |
| `toMonday(date)` | Weekly rollups | More parts, finer drops |
| `toYYYYMMDD(date)` | Daily TTL drops | Many parts — use carefully |
| None | Small tables (<1M rows) | Fine |

**Warning:** Each partition creates separate parts on disk. Over-partitioning
(e.g., by `user_id`) creates millions of tiny parts and kills performance.

## Applying Schema via Node.js

Run DDL from application code so schema lives in version control alongside your
service. `command()` is the right call for DDL (no result set is returned).

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

async function applySchema() {
  await client.command({ query: 'CREATE DATABASE IF NOT EXISTS analytics' });

  await client.command({
    query: `
      CREATE TABLE IF NOT EXISTS analytics.events (
        event_id   UUID DEFAULT generateUUIDv4(),
        tenant_id  UInt32,
        event_type LowCardinality(String),
        user_id    UInt64,
        payload    String CODEC(ZSTD(3)),
        created_at DateTime DEFAULT now()
      )
      ENGINE = MergeTree()
      ORDER BY (tenant_id, event_type, created_at)
      PARTITION BY toYYYYMM(created_at)
    `,
  });

  console.log('Schema applied.');
}
```
