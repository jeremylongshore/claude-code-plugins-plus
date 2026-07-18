# Table Recreation: ORDER BY & Engine Changes

ClickHouse cannot alter the sorting key or engine in place. Both changes require
creating a new table, copying data, and atomically swapping via `RENAME TABLE`.

## Change ORDER BY (Requires Table Recreation)

ClickHouse does **not** support `ALTER TABLE ... MODIFY ORDER BY`. You must
create a new table and migrate data.

```sql
-- Step 1: Create new table with desired ORDER BY
CREATE TABLE analytics.events_v2 AS analytics.events
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at))  -- New key
PARTITION BY toYYYYMM(created_at);

-- Step 2: Copy data
INSERT INTO analytics.events_v2 SELECT * FROM analytics.events;

-- Step 3: Atomic swap (zero-downtime if app handles reconnect)
RENAME TABLE
    analytics.events TO analytics.events_old,
    analytics.events_v2 TO analytics.events;

-- Step 4: Verify and drop old table
SELECT count() FROM analytics.events;
SELECT count() FROM analytics.events_old;
-- When satisfied:
DROP TABLE analytics.events_old;
```

## Change Engine (MergeTree to ReplacingMergeTree)

```sql
-- Create new table with ReplacingMergeTree
CREATE TABLE analytics.users_v2 (
    user_id    UInt64,
    email      String,
    plan       LowCardinality(String),
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY user_id;

-- Migrate data
INSERT INTO analytics.users_v2 SELECT * FROM analytics.users;

-- Atomic swap
RENAME TABLE
    analytics.users TO analytics.users_old,
    analytics.users_v2 TO analytics.users;

DROP TABLE analytics.users_old;
```
