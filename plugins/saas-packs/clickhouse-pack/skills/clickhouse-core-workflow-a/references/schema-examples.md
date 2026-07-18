# ClickHouse Schema Examples

Full, copy-pasteable DDL for the three canonical table shapes referenced from
the core workflow. Each shows engine selection, ORDER BY design, partitioning,
codecs, and TTL working together.

## Event Analytics Table

Append-only clickstream/IoT events. `MergeTree` with a tenant-first sort key,
monthly partitions, and a 1-year retention TTL.

```sql
CREATE TABLE analytics.events (
    event_id     UUID DEFAULT generateUUIDv4(),
    tenant_id    UInt32,
    event_type   LowCardinality(String),
    user_id      UInt64,
    session_id   String,
    properties   String CODEC(ZSTD(3)),  -- JSON blob, compress well
    url          String CODEC(ZSTD(1)),
    ip_address   IPv4,
    country      LowCardinality(FixedString(2)),
    created_at   DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at), user_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;
```

## User Profile Table (Upserts)

Mutable rows keyed by `user_id`. `ReplacingMergeTree` keeps the latest row per
ORDER BY key on merge; query with `FINAL` for deduplicated reads.

```sql
CREATE TABLE analytics.users (
    user_id      UInt64,
    email        String,
    plan         LowCardinality(String),
    mrr_cents    UInt32,
    properties   String CODEC(ZSTD(3)),
    updated_at   DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)   -- keeps latest row per ORDER BY key
ORDER BY user_id;

-- Query with FINAL to get deduplicated results
SELECT * FROM analytics.users FINAL WHERE user_id = 42;
```

## Daily Aggregation Table

Materialized-view target holding pre-aggregated state. `AggregatingMergeTree`
merges `AggregateFunction` states on background merges.

```sql
CREATE TABLE analytics.daily_stats (
    date         Date,
    tenant_id    UInt32,
    event_type   LowCardinality(String),
    event_count  UInt64,
    unique_users AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, date);
```

## Codecs and Compression

Column-level codecs picked to match the data shape. Chain a specialized codec
(`Delta`, `DoubleDelta`, `Gorilla`) with a general compressor (`ZSTD`).

```sql
-- Column-level compression codecs
column1  UInt64 CODEC(Delta, ZSTD(3)),      -- Time series / sequential IDs
column2  Float64 CODEC(Gorilla, ZSTD(1)),   -- Floating point (similar values)
column3  String CODEC(ZSTD(3)),              -- General text / JSON
column4  DateTime CODEC(DoubleDelta, ZSTD),  -- Timestamps (near-sequential)
```
