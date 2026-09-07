# Remediation Procedures

Deep, copy-paste remediation steps for each incident class, organized by severity.
Run the [Quick Triage](../SKILL.md#instructions) and walk the decision tree first to
pick the right procedure below.

## P1: Server Down / OOM

```bash
# Check if process was OOM-killed
dmesg | grep -i "out of memory" | tail -5
journalctl -u clickhouse-server --since "10 minutes ago" | tail -20

# Restart
sudo systemctl restart clickhouse-server
# or for Docker:
docker restart clickhouse

# Verify recovery (8123 is the default ClickHouse HTTP interface port)
curl 'http://localhost:8123/?query=SELECT+version()'
```

## P1: Disk Full

```sql
-- Find largest tables
SELECT database, table,
       formatReadableSize(sum(bytes_on_disk)) AS size,
       sum(rows) AS rows
FROM system.parts WHERE active
GROUP BY database, table
ORDER BY sum(bytes_on_disk) DESC
LIMIT 10;

-- Emergency: drop old partitions
ALTER TABLE analytics.events DROP PARTITION '202301';
ALTER TABLE analytics.events DROP PARTITION '202302';

-- Check free space
SELECT name, formatReadableSize(free_space) AS free,
       formatReadableSize(total_space) AS total
FROM system.disks;
```

## P2: Stuck / Long-Running Queries

```sql
-- Find stuck queries
SELECT
    query_id,
    user,
    elapsed,
    formatReadableSize(memory_usage) AS memory,
    substring(query, 1, 200) AS query_preview
FROM system.processes
ORDER BY elapsed DESC;

-- Kill a specific query
KILL QUERY WHERE query_id = 'abc-123-def';

-- Kill all queries from a user
KILL QUERY WHERE user = 'runaway_user';

-- Kill all queries running longer than 5 minutes
KILL QUERY WHERE elapsed > 300;
```

## P2: Too Many Parts (Merge Backlog)

```sql
-- Check part counts
SELECT database, table, count() AS parts
FROM system.parts WHERE active
GROUP BY database, table
HAVING parts > 200
ORDER BY parts DESC;

-- Check active merges
SELECT database, table, progress, elapsed,
       formatReadableSize(total_size_bytes_compressed) AS size
FROM system.merges;

-- Temporary: raise the limit to prevent INSERT failures
ALTER TABLE analytics.events MODIFY SETTING parts_to_throw_insert = 1000;

-- Wait for merges to catch up, then lower back
-- Root cause: too many small inserts — batch them
```

## P2: Memory Pressure

```sql
-- Who's using the most memory?
SELECT user, query_id, elapsed,
       formatReadableSize(memory_usage) AS memory,
       substring(query, 1, 200) AS q
FROM system.processes
ORDER BY memory_usage DESC;

-- Kill the largest query
KILL QUERY WHERE query_id = '<largest_query_id>';

-- Reduce per-query memory for all users
ALTER USER app_writer SETTINGS max_memory_usage = 5000000000;  -- 5GB
```

## P3: Replication Lag (Clustered/Cloud)

```sql
-- Check replica status
SELECT
    database, table,
    is_leader,
    total_replicas,
    active_replicas,
    queue_size,
    inserts_in_queue,
    merges_in_queue,
    log_pointer,
    last_queue_update
FROM system.replicas
WHERE active_replicas < total_replicas OR queue_size > 0;
```
