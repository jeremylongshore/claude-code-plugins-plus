# Monitoring, Health Checks & Verification Queries

## Metrics to monitor

```sql
-- Key metrics to monitor
-- 1. Query latency (p50/p95/p99)
-- 2. Active parts per table (alert > 300)
-- 3. Merge queue depth
-- 4. Memory usage
-- 5. Disk space free
-- 6. Replication lag (if clustered)

-- Health check query (use for load balancer probes)
SELECT 1;

-- More thorough health check
SELECT
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT sum(value) FROM system.metrics WHERE metric = 'MemoryTracking') AS memory_bytes,
    (SELECT count() FROM system.merges) AS active_merges;
```

## Monitoring checklist

- [ ] Prometheus endpoint configured (`/metrics` via ClickHouse Exporter or Cloud endpoint)
- [ ] Grafana dashboard with key panels (QPS, latency, memory, parts, merges)
- [ ] Alerts on: error rate > 5%, p95 latency > 5s, parts > 300, disk < 20%
- [ ] Query log monitoring for slow/failed queries

## Application health check endpoint

```typescript
// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const { success } = await client.ping();
    res.json({ status: success ? 'healthy' : 'degraded', clickhouse: success });
  } catch {
    res.status(503).json({ status: 'unhealthy', clickhouse: false });
  }
});
```

## Go-live verification queries

Run these against the target instance immediately before flipping traffic.

```sql
-- Verify table sizes and part health
SELECT database, table, count() AS parts, sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts WHERE active
GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC;

-- Verify no pending mutations
SELECT * FROM system.mutations WHERE NOT is_done;

-- Verify no replication lag
SELECT database, table, queue_size, inserts_in_queue
FROM system.replicas WHERE queue_size > 0;
```

**Expected clean-launch results:** every table below its active-parts alert
threshold, zero rows from the mutations query, and zero rows from the replicas
query. Any non-empty result from the last two is a launch blocker until resolved.
