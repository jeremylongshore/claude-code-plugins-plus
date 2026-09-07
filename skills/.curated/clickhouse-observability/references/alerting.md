# Prometheus Alert Rules

Load these into your AlertManager / Prometheus rule files. Thresholds are
production defaults — tune `expr` values and `for` windows to your workload.

```yaml
# clickhouse-alerts.yml
groups:
  - name: clickhouse
    rules:
      - alert: ClickHouseHighErrorRate
        expr: |
          rate(clickhouse_query_errors_total[5m]) /
          rate(clickhouse_query_duration_seconds_count[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ClickHouse error rate > 5%"

      - alert: ClickHouseHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(clickhouse_query_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ClickHouse P95 latency > 5 seconds"

      - alert: ClickHouseTooManyParts
        expr: clickhouse_table_parts > 300
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Table has > 300 active parts — merges falling behind"

      - alert: ClickHouseMemoryHigh
        expr: clickhouse_server_memory_usage / clickhouse_server_memory_limit > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "ClickHouse memory usage > 90%"

      - alert: ClickHouseDiskLow
        expr: clickhouse_disk_free_bytes / clickhouse_disk_total_bytes < 0.15
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "ClickHouse disk space < 15% free"
```

## Alert Tuning Notes

| Alert | Why the threshold | When to raise/lower |
|-------|-------------------|---------------------|
| `ClickHouseHighErrorRate` | 5% sustained errors signals a real problem, not transient | Lower to 1% for critical pipelines |
| `ClickHouseTooManyParts` | >300 active parts means merges can't keep up with inserts | Lower if you batch inserts aggressively |
| `ClickHouseMemoryHigh` | >90% risks OOM query kills | Keep at 90%; below that is noisy |
| `ClickHouseDiskLow` | <15% free leaves no room for merges (need 2x largest part) | Raise to 25% on write-heavy clusters |
