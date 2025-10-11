---
description: Monitor database health and performance metrics
---

# Database Health Monitor

Track database health metrics and alert on issues.

## Key Metrics

1. **Connection Pool**: Active/idle connections
2. **Query Performance**: Slow query log
3. **Disk Usage**: Table and index sizes
4. **Replication Lag**: Replica delay
5. **Lock Contention**: Blocking queries

## Health Check Script (PostgreSQL)

```sql
-- Connection count
SELECT count(*) as connections FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Replication lag
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()));
```

## When Invoked

Generate health monitoring queries and alerting logic.
