---
name: monitoring-database-health
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
# Database Health Monitor

## Overview

Monitor database server health across PostgreSQL, MySQL, and MongoDB by tracking key performance indicators including connection utilization, query throughput, replication lag, disk usage, cache hit ratios, vacuum activity, and lock contention.

## Prerequisites

- Database credentials with access to system statistics views (`pg_stat_*`, `performance_schema`, `serverStatus`)
- `psql`, `mysql`, or `mongosh` CLI tools for running health check queries
- Permissions: `pg_monitor` role (PostgreSQL), `PROCESS` privilege (MySQL)
- Baseline metrics from a period of normal operation for threshold calibration
- Alerting channel configured (email, Slack webhook, PagerDuty)

## Instructions

1. Check connection utilization:
   - PostgreSQL: `SELECT count(*) AS active_connections, (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections, round(count(*)::numeric / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') * 100, 1) AS utilization_pct FROM pg_stat_activity`
   - MySQL: `SELECT VARIABLE_VALUE AS connections FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected'`
   - Alert threshold: utilization above 80%

2. Monitor query throughput and error rate:
   - PostgreSQL: `SELECT datname, xact_commit AS commits_total, xact_rollback AS rollbacks_total, xact_rollback::float / GREATEST(xact_commit, 1) AS rollback_ratio FROM pg_stat_database WHERE datname = current_database()`
   - MySQL: `SHOW GLOBAL STATUS LIKE 'Com_commit'` and `SHOW GLOBAL STATUS LIKE 'Com_rollback'`
   - Alert threshold: rollback ratio above 5% or throughput drops more than 50% from baseline

3. Check disk usage and growth:
   - PostgreSQL: `SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size` and `SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::text)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(tablename::text) DESC LIMIT 10`
   - Alert threshold: disk usage above 80% or growth rate projecting full disk within 7 days

4. Monitor cache hit ratio:
   - PostgreSQL: `SELECT sum(heap_blks_hit)::float / GREATEST(sum(heap_blks_hit) + sum(heap_blks_read), 1) AS cache_hit_ratio FROM pg_statio_user_tables`
   - MySQL: `SELECT (1 - (VARIABLE_VALUE / (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'))) AS hit_ratio FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'`
   - Alert threshold: cache hit ratio below 95% indicates shared_buffers or innodb_buffer_pool_size needs increasing

5. Check vacuum and autovacuum health (PostgreSQL):
   - `SELECT relname, last_vacuum, last_autovacuum, n_dead_tup, n_live_tup, round(n_dead_tup::numeric / GREATEST(n_live_tup, 1) * 100, 1) AS dead_pct FROM pg_stat_user_tables WHERE n_dead_tup > 1000 ORDER BY n_dead_tup DESC LIMIT 10`
   - Alert threshold: dead tuple percentage above 20% or autovacuum not running for more than 24 hours on active tables

6. Monitor replication lag (if replicas exist):
   - PostgreSQL: `SELECT client_addr, state, pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes FROM pg_stat_replication`
   - MySQL: `SHOW REPLICA STATUS\G` - check `Seconds_Behind_Source`
   - Alert threshold: lag above 30 seconds or replication stopped

7. Check for long-running queries:
   - PostgreSQL: `SELECT pid, now() - query_start AS duration, state, query FROM pg_stat_activity WHERE state != 'idle' AND now() - query_start > interval '5 minutes' ORDER BY duration DESC`
   - Alert threshold: any query running longer than 10 minutes (OLTP) or 1 hour (analytics)

8. Monitor lock contention:
   - PostgreSQL: `SELECT count(*) AS waiting_queries FROM pg_stat_activity WHERE wait_event_type = 'Lock'`
   - Alert threshold: more than 10 queries waiting for locks simultaneously

9. Compile all health checks into a single monitoring script that runs via cron every 60 seconds, outputs metrics in a structured format (JSON), and triggers alerts when thresholds are breached.

10. Create a health summary dashboard query that returns a single-row result with RAG (Red/Amber/Green) status for each health dimension: connections, throughput, disk, cache, vacuum, replication, queries, and locks.

## Output

- **Health check queries** tailored to the specific database engine
- **Monitoring script** (shell or Python) for scheduled health checks with alerting
- **Threshold configuration** with default values and tuning guidance
- **Dashboard summary query** providing RAG status across all health dimensions
- **Alert notification templates** for Slack, email, or PagerDuty integration

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `pg_stat_activity` returns incomplete data | `track_activities = off` in postgresql.conf | Enable `track_activities = on` and `track_counts = on`; reload configuration |
| Health check query itself times out | Database under heavy load or lock contention | Set `statement_timeout = '5s'` for monitoring queries; use a dedicated monitoring connection |
| False alerts during maintenance windows | Planned maintenance triggers threshold breaches | Implement alert suppression windows; add maintenance mode flag to monitoring script |
| Disk usage alert but no obvious growth | WAL files, temporary files, or pg_stat_tmp consuming space | Check `pg_wal` directory size; check for orphaned temporary files; verify `wal_keep_size` setting |
| Cache hit ratio drops after restart | Buffer pool/shared_buffers cold after database restart | Implement cache warming script that runs key queries after restart; alert will self-resolve as cache warms |

## Examples

**PostgreSQL health dashboard for a production SaaS application**: A single cron-based script checks 8 health dimensions every 60 seconds, writing results to a metrics table. A dashboard query shows: connections 45/200 (GREEN), cache hit 98.5% (GREEN), dead tuples 2.1% (GREEN), disk 62% (GREEN), replication lag 0.5s (GREEN), long queries 0 (GREEN), lock waiters 1 (GREEN), rollback ratio 0.3% (GREEN).

**Detecting impending disk full condition**: Health monitor tracks daily disk growth rate. Current usage: 72%, daily growth: 1.2GB, remaining: 280GB. Projected full date: 233 days. Alert triggers at 80% with recommendation to archive old data or add storage. A second alert at 90% escalates to PagerDuty.

**Identifying autovacuum falling behind**: Health check shows the `events` table with 15M dead tuples (45% dead ratio) and last autovacuum 3 days ago. Root cause: `autovacuum_vacuum_cost_delay` too conservative for a high-write table. Fix: set per-table `autovacuum_vacuum_cost_delay = 2` and `autovacuum_vacuum_scale_factor = 0.01`.

## Resources

- PostgreSQL monitoring statistics: https://www.postgresql.org/docs/current/monitoring-stats.html
- MySQL performance_schema: https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html
- MongoDB serverStatus: https://www.mongodb.com/docs/manual/reference/command/serverStatus/
- PostgreSQL autovacuum tuning: https://www.postgresql.org/docs/current/runtime-config-autovacuum.html
- check_postgres monitoring tool: https://bucardo.org/check_postgres/