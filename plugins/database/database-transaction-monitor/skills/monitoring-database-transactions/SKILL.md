---
name: monitoring-database-transactions
description: |
  Monitor use when you need to work with monitoring and observability.
  This skill provides health monitoring and alerting with comprehensive guidance and automation.
  Trigger with phrases like "monitor system health", "set up alerts",
  or "track metrics".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Transaction Monitor

## Overview

Monitor active database transactions in real time to detect long-running queries, lock contention, uncommitted transactions, and transaction throughput anomalies across PostgreSQL, MySQL, and MongoDB. This skill instruments transaction lifecycle tracking, identifies transactions holding locks beyond acceptable thresholds, and generates alerts before stalled transactions cascade into application-wide failures.

## Prerequisites

- Database credentials with access to system catalogs (`pg_stat_activity`, `information_schema.PROCESSLIST`, or MongoDB `currentOp`)
- `psql`, `mysql`, or `mongosh` CLI installed
- Permissions to view other sessions' transactions (PostgreSQL: `pg_monitor` role; MySQL: `PROCESS` privilege)
- Baseline metrics for normal transaction duration and throughput
- Alerting infrastructure (email, Slack webhook, or PagerDuty) for notifications

## Instructions

1. Query the active transaction view to establish a baseline. For PostgreSQL: `SELECT pid, state, query_start, now() - query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC`. For MySQL: `SELECT id, user, host, db, command, time, state, info FROM information_schema.PROCESSLIST WHERE command != 'Sleep'`.

2. Identify long-running transactions by filtering for duration exceeding the application's expected transaction time. Set initial thresholds at 30 seconds for OLTP workloads or 5 minutes for batch/reporting workloads.

3. Detect idle-in-transaction sessions that hold locks without executing queries. For PostgreSQL: `SELECT pid, state, query_start, now() - state_change AS idle_duration FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - state_change > interval '5 minutes'`.

4. Monitor lock contention by querying the lock manager. For PostgreSQL: `SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid, blocked_activity.query AS blocked_query FROM pg_catalog.pg_locks blocked_locks JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype`. For MySQL: `SELECT * FROM information_schema.INNODB_LOCK_WAITS`.

5. Track transaction throughput by sampling `pg_stat_database` (xact_commit, xact_rollback) or MySQL `Com_commit` / `Com_rollback` status variables at regular intervals. Calculate commits/second and rollback ratio.

6. Create monitoring scripts that run on a cron schedule (every 30-60 seconds) to capture transaction metrics and write to a time-series store or log file.

7. Configure alerting thresholds: transactions exceeding 60 seconds, idle-in-transaction sessions exceeding 5 minutes, lock wait queues exceeding 10 waiters, and rollback ratio exceeding 5%.

8. Build a transaction summary dashboard query that shows: active transaction count, average duration, longest running transaction, lock wait count, and commits-per-second over the last hour.

9. Implement automatic remediation for known-safe scenarios: terminate idle-in-transaction sessions older than 30 minutes using `SELECT pg_terminate_backend(pid)` (PostgreSQL) or `KILL connection_id` (MySQL), with logging of terminated sessions.

10. Generate weekly transaction health reports summarizing peak transaction counts, P95/P99 duration percentiles, deadlock occurrences, and long-running transaction incidents.

## Output

- **Transaction monitoring queries** tailored to the specific database engine in use
- **Monitoring scripts** (shell or Python) for scheduled transaction health checks
- **Alert configuration** with threshold definitions and notification channel setup
- **Dashboard queries** showing transaction throughput, duration distribution, and lock metrics
- **Weekly health report template** with transaction performance trends and anomaly highlights

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `pg_stat_activity` returns no rows for other sessions | Missing `pg_monitor` role or `track_activities` disabled | Grant `pg_monitor` role; set `track_activities = on` in postgresql.conf |
| Lock monitoring query times out | Massive lock table during contention storm | Query `pg_locks` with a statement_timeout; reduce monitoring frequency during incidents |
| False positive alerts for long-running transactions | Batch jobs or maintenance operations trigger duration alerts | Create an exclusion list for known batch job PIDs or application users; use separate thresholds for batch vs OLTP |
| Transaction throughput drops to zero | Connection pool exhaustion or database crash | Check `max_connections` usage; verify database process is running; check for full disk or OOM conditions |
| Monitoring queries add overhead | High-frequency polling of system catalogs | Reduce polling interval to every 60 seconds; use `pg_stat_statements` for aggregated stats instead of per-query monitoring |

## Examples

**Detecting a connection leak in a web application**: Transaction count steadily increases over hours while commit rate remains flat. Monitoring reveals hundreds of `idle in transaction` sessions from the application server. Root cause: missing `connection.close()` in error handling paths. Resolution: terminate stale sessions and fix application connection management.

**Identifying lock contention during peak hours**: Dashboard shows lock wait count spiking from 0 to 50+ between 2-4 PM daily. Lock analysis reveals a nightly reporting query overlapping with high-volume order processing. Resolution: reschedule reporting queries to off-peak hours and add `NOWAIT` hints to critical transaction paths.

**Tracking transaction rollback ratio spike**: Rollback ratio jumps from 1% to 15% after a deployment. Transaction monitor logs show serialization failures on a frequently updated inventory table. Resolution: reduce transaction isolation level from SERIALIZABLE to READ COMMITTED for non-critical paths and add retry logic for serialization failures.

## Resources

- PostgreSQL monitoring views: https://www.postgresql.org/docs/current/monitoring-stats.html
- MySQL performance schema: https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html
- MongoDB currentOp: https://www.mongodb.com/docs/manual/reference/method/db.currentOp/
- pg_stat_statements extension: https://www.postgresql.org/docs/current/pgstatstatements.html
- Lock monitoring best practices: https://wiki.postgresql.org/wiki/Lock_Monitoring
