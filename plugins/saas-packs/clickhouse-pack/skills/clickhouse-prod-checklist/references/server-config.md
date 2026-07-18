# Server Configuration (Self-Hosted)

Key production settings for `config.xml` / `users.xml`. On ClickHouse Cloud these
are managed for you — this section applies only to self-hosted deployments.

```xml
<!-- Key production settings in config.xml / users.xml -->

<!-- Memory: set to ~80% of available RAM -->
<max_server_memory_usage_to_ram_ratio>0.8</max_server_memory_usage_to_ram_ratio>

<!-- Query limits -->
<max_concurrent_queries>150</max_concurrent_queries>
<max_memory_usage>10000000000</max_memory_usage>  <!-- 10GB per query -->
<max_execution_time>300</max_execution_time>       <!-- 5 min timeout: cap runaway analytical scans -->

<!-- Merge settings -->
<background_pool_size>16</background_pool_size>
<background_schedule_pool_size>16</background_schedule_pool_size>

<!-- Logging -->
<query_log>
    <database>system</database>
    <table>query_log</table>
    <flush_interval_milliseconds>7500</flush_interval_milliseconds>
</query_log>
```

## Tuning notes

- **`max_server_memory_usage_to_ram_ratio`** — 0.8 leaves headroom for the OS
  page cache and merge buffers. Lower it to 0.6–0.7 on hosts that also run other
  services.
- **`max_concurrent_queries`** — 150 is a safe default for a single node; raise
  only after confirming CPU and memory headroom under load test.
- **`max_memory_usage`** — the per-query cap (10 GB here). Set below
  `max_server_memory_usage` divided by expected concurrency to avoid OOM.
- **`max_execution_time`** — 300 s bounds runaway analytical scans so one query
  cannot monopolize the pool.
- **`background_pool_size`** — controls merge parallelism. Match it roughly to
  the core count; too low starves merges and grows the active-parts count.
