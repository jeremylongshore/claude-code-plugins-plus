# ClickHouse DDL & Column Operations

Deep reference for understanding ClickHouse mutation semantics and performing
column-level schema changes. Read this before running any `ALTER TABLE` against
a production table.

## Understanding ClickHouse DDL

ClickHouse ALTER operations are **mutations** — they run asynchronously and
rewrite data parts in the background. This is fundamentally different from
PostgreSQL/MySQL where ALTER is often instant or blocking.

```sql
-- Lightweight operations (instant, metadata only)
ALTER TABLE events ADD COLUMN country LowCardinality(String) DEFAULT '';
ALTER TABLE events RENAME COLUMN old_name TO new_name;
ALTER TABLE events COMMENT COLUMN user_id 'Unique user identifier';

-- Heavyweight operations (mutations — rewrite parts in background)
ALTER TABLE events MODIFY COLUMN properties String CODEC(ZSTD(3));
ALTER TABLE events DROP COLUMN deprecated_field;
ALTER TABLE events DELETE WHERE user_id = 0;
ALTER TABLE events UPDATE email = '' WHERE created_at < '2024-01-01';

-- Check mutation progress
SELECT database, table, mutation_id, command, is_done,
       parts_to_do, create_time
FROM system.mutations
WHERE NOT is_done ORDER BY create_time;
```

## Column Operations

```sql
-- Add a column (instant — no data rewrite)
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS country LowCardinality(String) DEFAULT ''
    AFTER user_id;

-- Add column with materialized default (fills new data, not old)
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS event_date Date
    MATERIALIZED toDate(created_at);

-- Modify column type (mutation — rewrites all parts)
ALTER TABLE analytics.events
    MODIFY COLUMN user_id UInt64;   -- Was UInt32, now UInt64

-- Drop a column
ALTER TABLE analytics.events
    DROP COLUMN IF EXISTS deprecated_field;

-- Change default value
ALTER TABLE analytics.events
    MODIFY COLUMN created_at DateTime DEFAULT now();

-- Add codec to existing column (mutation)
ALTER TABLE analytics.events
    MODIFY COLUMN properties String CODEC(ZSTD(3));
```
