---
name: analyzing-database-indexes
description: |
  Process use when you need to work with database indexing.
  This skill provides index design and optimization with comprehensive guidance and automation.
  Trigger with phrases like "create indexes", "optimize indexes",
  or "improve query performance".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Index Advisor

## Overview

Analyze database index usage, identify missing indexes causing sequential scans, detect redundant or unused indexes wasting write performance, and recommend optimal index configurations for PostgreSQL and MySQL.

## Prerequisites

- Database credentials with access to `pg_stat_user_indexes`, `pg_stat_user_tables`, and `pg_stat_statements` (PostgreSQL) or `performance_schema` and `sys` schema (MySQL)
- `pg_stat_statements` extension enabled for PostgreSQL query statistics
- `psql` or `mysql` CLI for executing analysis queries
- Representative workload running (analysis during off-peak hours may miss important query patterns)
- At least 24 hours of statistics accumulation since the last `pg_stat_reset()`

## Instructions

1. Identify tables with high sequential scan activity (candidates for missing indexes):
   - PostgreSQL: `SELECT relname, seq_scan, seq_tup_read, idx_scan, n_live_tup FROM pg_stat_user_tables WHERE seq_scan > 100 AND n_live_tup > 10000 ORDER BY seq_tup_read DESC LIMIT 20`
   - A table with high `seq_scan` count and high `seq_tup_read` relative to `n_live_tup` is scanning most of the table repeatedly

2. Find the queries causing sequential scans by correlating with `pg_stat_statements`:
   - `SELECT query, calls, mean_exec_time, rows FROM pg_stat_statements WHERE query ILIKE '%table_name%' ORDER BY mean_exec_time DESC LIMIT 10`
   - Run `EXPLAIN (ANALYZE, BUFFERS)` on the top queries to confirm sequential scan usage

3. Analyze query WHERE clauses and JOIN conditions to determine which columns need indexes. Extract the filtering columns and their selectivity:
   - `SELECT column_name, n_distinct, correlation FROM pg_stats WHERE tablename = 'target_table'`
   - High `n_distinct` (close to row count) indicates good index selectivity
   - `correlation` close to 1.0 or -1.0 suggests the column benefits from a B-tree index

4. Recommend composite indexes for multi-column queries. Follow the equality-first, range-second ordering:
   - Place columns used with `=` operators first in the index
   - Place columns used with `>`, `<`, `BETWEEN`, or `LIKE 'prefix%'` last
   - Example: `WHERE status = 'active' AND created_at > '2024-01-01'` -> `CREATE INDEX ON orders (status, created_at)`

5. Identify unused indexes wasting write performance:
   - PostgreSQL: `SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS index_size FROM pg_stat_user_indexes WHERE idx_scan = 0 AND indexrelname NOT LIKE '%pkey' ORDER BY pg_relation_size(indexrelid) DESC`
   - Indexes with zero scans over a representative period are candidates for removal (verify they are not used by foreign key constraints or unique enforcement)

6. Detect redundant indexes where one index is a prefix of another:
   - A single-column index on `(customer_id)` is redundant if a composite index on `(customer_id, created_at)` exists, because the composite index serves both single-column and multi-column queries
   - Generate DROP INDEX recommendations for the redundant subset indexes

7. Evaluate partial indexes for filtered queries. If a query always filters `WHERE status = 'active'`:
   - `CREATE INDEX idx_orders_active ON orders (created_at) WHERE status = 'active'`
   - Partial indexes are smaller and faster than full indexes when the filter eliminates most rows

8. Consider covering indexes (INCLUDE clause in PostgreSQL 11+) for index-only scans:
   - `CREATE INDEX idx_orders_covering ON orders (customer_id, created_at) INCLUDE (total_amount, status)`
   - The INCLUDE columns are stored in the index leaf pages, enabling index-only scans without heap access

9. Estimate the impact of each recommendation:
   - Index size: `SELECT pg_size_pretty(pg_relation_size('index_name'))` for existing similar indexes
   - Write overhead: each additional index adds approximately 5-15% write latency per INSERT/UPDATE
   - Read improvement: compare EXPLAIN plans with and without the proposed index

10. Generate a prioritized recommendations report with CREATE INDEX and DROP INDEX statements, estimated storage impact, expected query improvement, and write overhead trade-off analysis.

## Output

- **Missing index recommendations** as ready-to-execute CREATE INDEX statements with CONCURRENTLY option
- **Unused index report** with DROP INDEX candidates and their storage savings
- **Redundant index report** identifying prefix-overlapping indexes
- **Index usage statistics** showing scan counts, tuple reads, and sizes for all indexes
- **Impact analysis** estimating read improvement vs. write overhead for each recommendation

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `pg_stat_statements` not available | Extension not installed | `CREATE EXTENSION pg_stat_statements` and add to `shared_preload_libraries` |
| Index creation blocks writes | `CREATE INDEX` acquires exclusive lock on the table | Use `CREATE INDEX CONCURRENTLY` which does not block writes (takes longer but safe for production) |
| Index not used after creation | Statistics not updated or query planner choosing sequential scan | Run `ANALYZE table_name`; check `random_page_cost` setting (reduce to 1.1 for SSD); verify query uses indexed columns without functions |
| Statistics reset unexpectedly | `pg_stat_reset()` called or database restart cleared stats | Wait 24-48 hours for statistics to accumulate; set up periodic stats collection to a metrics table |
| Too many indexes on write-heavy table | Each INSERT/UPDATE must update all indexes | Target 5-7 indexes per table maximum; use composite indexes to replace multiple single-column indexes; remove unused indexes |

## Examples

**Identifying a missing composite index for an API endpoint**: The `/orders?customer_id=123&status=active` endpoint takes 2 seconds. Analysis shows the orders table (5M rows) has indexes on `(id)` and `(customer_id)` but not `(customer_id, status)`. The query filters on both columns. Adding `CREATE INDEX CONCURRENTLY idx_orders_customer_status ON orders (customer_id, status)` reduces the query to 5ms.

**Cleaning up 8 unused indexes saving 12GB**: Index usage analysis reveals 8 indexes with zero scans over 30 days, totaling 12GB of storage. After confirming none are used for FK enforcement or unique constraints, dropping them reduces write latency by 18% and frees disk space. Command: `DROP INDEX CONCURRENTLY idx_name`.

**Replacing 3 single-column indexes with 1 composite covering index**: Table has separate indexes on `(user_id)`, `(created_at)`, and `(status)`. Most queries filter on all three. A single composite index `(user_id, status, created_at) INCLUDE (amount)` replaces all three, reduces total index storage by 40%, and enables index-only scans for the dashboard query.

## Resources

- PostgreSQL index types: https://www.postgresql.org/docs/current/indexes.html
- Use The Index, Luke: https://use-the-index-luke.com/
- pg_stat_user_indexes: https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ALL-INDEXES-VIEW
- MySQL index optimization: https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html
- Dexter (automatic PostgreSQL index advisor): https://github.com/ankane/dexter