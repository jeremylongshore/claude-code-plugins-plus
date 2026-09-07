# ClickHouse Performance Tuning — Worked Examples

Concrete before/after scenarios and the measurement queries that prove a change
worked.

## Example 1: Measure a query's cost

Every tuning decision should be backed by a measurement. Run the query, then read
its row from `system.query_log` to see exactly how much data it touched.

```sql
-- Measure bytes read and time for a specific query
SELECT
    query_duration_ms,
    read_rows,
    formatReadableSize(read_bytes) AS read_size,
    result_rows,
    formatReadableSize(memory_usage) AS memory
FROM system.query_log
WHERE query_id = currentQueryId()
  AND type = 'QueryFinish';
```

## Example 2: Full table scan → ORDER BY fix

**Symptom:** a dashboard query on `analytics.events` reads every row.

```sql
-- Before: read_rows equals the full table size
EXPLAIN indexes = 1
SELECT event_type, count()
FROM analytics.events
WHERE tenant_id = 1 AND event_type = 'purchase'
GROUP BY event_type;
```

The table was `ORDER BY (created_at)`, so the `tenant_id`/`event_type` filter
could not skip granules. Recreating it with `ORDER BY (tenant_id, event_type,
toDate(created_at))` (see [implementation.md](implementation.md) Step 2) lets the
same query skip every granule outside `tenant_id = 1`, cutting `read_rows` by
orders of magnitude.

## Example 3: Slow GROUP BY → projection

**Symptom:** an hourly rollup scans the whole table on every load.

Add the `events_by_hour` projection (Step 4). After
`MATERIALIZE PROJECTION`, re-run the query and confirm the projection is used —
`read_bytes` should drop sharply because the query now reads the small
pre-aggregated part instead of the base table.

## Example 4: Confirm a data skipping index fires

```sql
-- After ADD INDEX + MATERIALIZE INDEX, the plan should show the index
EXPLAIN indexes = 1
SELECT * FROM analytics.events WHERE session_id = 'abc-123';
-- Look for the idx_session_id entry with a reduced granule count.
```
