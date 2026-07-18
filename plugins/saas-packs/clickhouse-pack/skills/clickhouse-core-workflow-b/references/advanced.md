# Advanced ClickHouse: Materialized Views, Window Functions & Function Reference

Pre-aggregation, analytical windowing, and the day-to-day function toolbox.
These are the deep patterns extracted from the core workflow — reach for them
once basic inserts and queries are working.

## Materialized Views (pre-aggregation)

A materialized view aggregates rows automatically on every INSERT into the
source table, so dashboard reads hit small pre-rolled tables instead of scanning
raw events. Pair the view with an `AggregatingMergeTree` target and merge the
partial aggregation states at read time.

```sql
-- Source table receives raw events
-- Materialized view aggregates automatically on INSERT

CREATE MATERIALIZED VIEW analytics.hourly_stats_mv
TO analytics.hourly_stats  -- target table
AS
SELECT
    toStartOfHour(created_at) AS hour,
    tenant_id,
    event_type,
    count()                   AS event_count,
    uniqState(user_id)        AS unique_users_state
FROM analytics.events
GROUP BY hour, tenant_id, event_type;

-- Target table uses AggregatingMergeTree
CREATE TABLE analytics.hourly_stats (
    hour              DateTime,
    tenant_id         UInt32,
    event_type        LowCardinality(String),
    event_count       UInt64,
    unique_users_state AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, hour);

-- Query the materialized view (merge aggregation states)
SELECT
    hour,
    sum(event_count)           AS events,
    uniqMerge(unique_users_state) AS unique_users
FROM analytics.hourly_stats
WHERE tenant_id = 1
GROUP BY hour
ORDER BY hour;
```

**Key rule:** columns stored with a `*State` function (`uniqState`) must be read
back with the matching `*Merge` function (`uniqMerge`) to produce a final value.

## Window Functions

```sql
-- Running total and rank within each tenant
SELECT
    tenant_id,
    event_type,
    count()   AS cnt,
    sum(count()) OVER (PARTITION BY tenant_id ORDER BY count() DESC) AS running_total,
    row_number() OVER (PARTITION BY tenant_id ORDER BY count() DESC) AS rank
FROM analytics.events
WHERE created_at >= today() - 7
GROUP BY tenant_id, event_type
ORDER BY tenant_id, rank;
```

## Common ClickHouse Functions

| Function | Description | Example |
|----------|-------------|---------|
| `count()` | Row count | `count()` |
| `uniq(col)` | Approximate distinct count (HyperLogLog) | `uniq(user_id)` |
| `uniqExact(col)` | Exact distinct count | `uniqExact(user_id)` |
| `quantile(0.95)(col)` | Percentile | `quantile(0.95)(latency_ms)` |
| `arrayJoin(arr)` | Unnest array to rows | `arrayJoin(tags)` |
| `JSONExtractString(col, key)` | Extract from JSON string | `JSONExtractString(properties, 'plan')` |
| `toStartOfHour(dt)` | Truncate to hour | `toStartOfHour(created_at)` |
| `formatReadableSize(n)` | Human-readable bytes | `formatReadableSize(bytes)` |
| `if(cond, then, else)` | Conditional | `if(cnt > 0, cnt, NULL)` |
| `multiIf(...)` | Multi-branch conditional | `multiIf(x>10, 'high', x>5, 'med', 'low')` |
