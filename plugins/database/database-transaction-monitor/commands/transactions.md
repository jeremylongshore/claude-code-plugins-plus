---
description: Monitor and manage database transactions
---

# Database Transaction Monitor

Track transaction performance and identify issues.

## Transaction Monitoring

1. **Long-Running Transactions**: Identify blocking queries
2. **Lock Contention**: Detect deadlocks
3. **Transaction Rollback Rate**: Error tracking
4. **Isolation Level Issues**: Detect anomalies

## Monitor Query (PostgreSQL)

```sql
-- Active transactions
SELECT pid, usename, state, query_start, state_change, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Blocking queries
SELECT blocked.pid, blocked.query, blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

## When Invoked

Set up transaction monitoring and alerting.
