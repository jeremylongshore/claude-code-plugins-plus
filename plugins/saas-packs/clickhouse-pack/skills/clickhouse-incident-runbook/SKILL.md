---
name: clickhouse-incident-runbook
description: |
  ClickHouse incident response — triage, diagnose, and remediate server issues
  using system tables, kill stuck queries, and execute recovery procedures.
  Use when ClickHouse is slow, unresponsive, or producing errors in production.
  Trigger: "clickhouse incident", "clickhouse outage", "clickhouse down",
  "clickhouse emergency", "clickhouse on-call", "clickhouse broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Incident Runbook

## Overview

Step-by-step procedures for triaging and resolving ClickHouse incidents
using built-in system tables and SQL commands.

## Severity Levels

| Level | Definition | Response | Examples |
|-------|------------|----------|----------|
| P1 | ClickHouse unreachable / all queries failing | < 15 min | Server down, OOM, disk full |
| P2 | Degraded performance / partial failures | < 1 hour | Slow queries, merge backlog |
| P3 | Minor impact / non-critical errors | < 4 hours | Single table issue, warnings |
| P4 | No user impact | Next business day | Monitoring gaps, optimization |

## Quick Triage (Run First)

```bash
# 1. Is ClickHouse alive?
curl -sf 'http://localhost:8123/ping' && echo "UP" || echo "DOWN"

# 2. Can it answer a query?
curl -sf 'http://localhost:8123/?query=SELECT+1' && echo "OK" || echo "QUERY FAILED"

# 3. Check ClickHouse Cloud status
curl -sf 'https://status.clickhouse.cloud' | head -5
```

```sql
-- 4. Server health snapshot (run if server responds)
SELECT
    version()                         AS version,
    formatReadableTimeDelta(uptime())  AS uptime,
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking')
        AS memory_bytes,
    (SELECT count() FROM system.merges) AS active_merges;

-- 5. Recent errors
SELECT event_time, exception_code, exception, substring(query, 1, 200) AS q
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND event_time >= now() - INTERVAL 10 MINUTE
ORDER BY event_time DESC
LIMIT 10;
```

## Decision Tree

```
Server responds to ping?
├─ NO → Check process/container status, disk space, OOM killer logs
│       └─ Container/process dead → Restart, check logs
│       └─ Disk full → Emergency: drop old partitions, expand disk
│       └─ OOM killed → Reduce max_memory_usage, add RAM
└─ YES → Queries succeeding?
    ├─ NO → Check error codes below
    │   └─ Auth errors (516) → Verify credentials, check user exists
    │   └─ Too many queries (202) → Kill stuck queries, reduce concurrency
    │   └─ Memory exceeded (241) → Kill large queries, reduce max_threads
    └─ YES but slow → Performance triage below
```

## Remediation Procedures

### P1: Server Down / OOM

```bash
# Check if process was OOM-killed
dmesg | grep -i "out of memory" | tail -5
journalctl -u clickhouse-server --since "10 minutes ago" | tail -20

# Restart
sudo systemctl restart clickhouse-server
# or for Docker:
docker restart clickhouse

# Verify recovery
curl 'http://localhost:8123/?query=SELECT+version()'
```

### P1: Disk Full

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

### P2: Stuck / Long-Running Queries

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

### P2: Too Many Parts (Merge Backlog)

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

### P2: Memory Pressure

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

### P3: Replication Lag (Clustered/Cloud)

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

## Post-Incident Evidence Collection

```sql
-- Export error window from query log
SELECT *
FROM system.query_log
WHERE event_time BETWEEN '2025-01-15 14:00:00' AND '2025-01-15 15:00:00'
  AND (type = 'ExceptionWhileProcessing' OR query_duration_ms > 10000)
FORMAT JSONEachRow
INTO OUTFILE '/tmp/incident-queries.json';

-- Metrics snapshot during incident window
SELECT metric, value
FROM system.metrics
FORMAT TabSeparatedWithNames
INTO OUTFILE '/tmp/incident-metrics.tsv';
```

## Communication Templates

**Internal (Slack):**
```
[P1] INCIDENT: ClickHouse [Issue Type]
Status: INVESTIGATING / MITIGATING / RESOLVED
Impact: [What users see]
Root cause: [If known]
Actions taken: [What you did]
Next update: [Time]
Commander: @[name]
```

**Postmortem Template:**
```markdown
## ClickHouse Incident: [Title]
- Date: YYYY-MM-DD
- Duration: X hours Y minutes
- Severity: P[1-4]

### Timeline
- HH:MM — [Event/action]

### Root Cause
[Technical explanation]

### Resolution
[What fixed it]

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```

## Error Handling

| Symptom | Likely Cause | First Action |
|---------|-------------|--------------|
| All queries fail | Server down | Check process, restart |
| Inserts fail | Too many parts | `KILL QUERY` long merges, raise limit |
| Selects slow | Memory pressure | Kill large queries, add filters |
| Disk alerts | No TTL / no cleanup | Drop old partitions |
| Replication lag | Network / merge backlog | Check `system.replicas` |

## Resources

- [ClickHouse Cloud Status](https://status.clickhouse.cloud)
- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [KILL QUERY](https://clickhouse.com/docs/sql-reference/statements/kill)

## Next Steps

For data compliance, see `clickhouse-data-handling`.
