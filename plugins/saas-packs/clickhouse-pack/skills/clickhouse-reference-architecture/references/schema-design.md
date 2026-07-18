# Schema Design — 3-Layer Pattern

The reference architecture uses three schema layers: raw events (append-only, full
fidelity), auto-populated aggregation via materialized views, and daily rollups the
dashboards read from. Query the aggregate tables, never the raw table.

```sql
-- Layer 1: Raw events (append-only, full fidelity)
CREATE TABLE analytics.events_raw (
    event_id    UUID DEFAULT generateUUIDv4(),
    tenant_id   UInt32,
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at), user_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 90 DAY;

-- Layer 2: Hourly aggregation (auto-populated via materialized view)
CREATE TABLE analytics.events_hourly (
    hour        DateTime,
    tenant_id   UInt32,
    event_type  LowCardinality(String),
    cnt         UInt64,
    users       AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, hour);

CREATE MATERIALIZED VIEW analytics.events_hourly_mv TO analytics.events_hourly AS
SELECT toStartOfHour(created_at) AS hour, tenant_id, event_type,
       count() AS cnt, uniqState(user_id) AS users
FROM analytics.events_raw GROUP BY hour, tenant_id, event_type;

-- Layer 3: Daily rollup for dashboards
CREATE TABLE analytics.events_daily (
    date        Date,
    tenant_id   UInt32,
    total       UInt64,
    users       AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, date);

CREATE MATERIALIZED VIEW analytics.events_daily_mv TO analytics.events_daily AS
SELECT toDate(created_at) AS date, tenant_id,
       count() AS total, uniqState(user_id) AS users
FROM analytics.events_raw GROUP BY date, tenant_id;
```

## Why this layout

- **Raw layer** keeps full-fidelity events for reprocessing and ad-hoc drill-down; a
  90-day TTL bounds storage while `ZSTD(3)` on the `properties` blob gives 10-20x
  compression.
- **Materialized views** aggregate on INSERT, so rollups are zero-lag — no cron, no
  reconciliation window.
- **`AggregateFunction`/`uniqState`** stores partial aggregation state; dashboards call
  `uniqMerge` at read time to finalize distinct counts across the rolled-up rows.
