---
name: analyzing-query-performance
description: |
  Execute use when you need to work with query optimization.
  This skill provides query performance analysis with comprehensive guidance and automation.
  Trigger with phrases like "optimize queries", "analyze performance",
  or "improve query speed".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Query Performance Analyzer

## Overview

Analyze slow database queries using execution plans, wait statistics, and I/O metrics across PostgreSQL, MySQL, and MongoDB. This skill captures EXPLAIN output, identifies sequential scans on large tables, detects missing indexes, measures buffer cache hit ratios, and produces actionable optimization recommendations ranked by expected performance impact.

## Prerequisites

- Database credentials with permissions to run `EXPLAIN ANALYZE` (PostgreSQL), `EXPLAIN FORMAT=JSON` (MySQL), or `explain()` (MongoDB)
- `pg_stat_statements` extension enabled for PostgreSQL (provides aggregated query statistics)
- Access to slow query logs or performance_schema (MySQL)
- Baseline query execution times for comparison
- `psql`, `mysql`, or `mongosh` CLI tools installed

## Instructions

1. Identify the slowest queries by examining `pg_stat_statements` (PostgreSQL): `SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20`. For MySQL, enable and query the slow query log or `performance_schema.events_statements_summary_by_digest`.

2. Run `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` on each slow query in PostgreSQL, or `EXPLAIN ANALYZE FORMAT=JSON` in MySQL. Capture the full execution plan including actual row counts, loop iterations, and buffer usage.

3. Analyze the execution plan for these red flags:
   - **Sequential scans** on tables with >10,000 rows (indicates missing index)
   - **Nested loop joins** with high outer row counts (consider hash join or merge join)
   - **Sort operations** without index support (adding a covering index eliminates the sort)
   - **High `rows_removed_by_filter`** relative to `rows` (predicate not selective enough)
   - **Bitmap heap scans** with high recheck rate (index selectivity too low)

4. Check buffer cache performance: `SELECT heap_blks_read, heap_blks_hit, heap_blks_hit::float / (heap_blks_hit + heap_blks_read) AS cache_hit_ratio FROM pg_statio_user_tables WHERE relname = 'table_name'`. A ratio below 0.95 suggests the working set exceeds available shared_buffers.

5. Evaluate index usage with `SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch FROM pg_stat_user_indexes WHERE schemaname = 'public' ORDER BY idx_scan ASC`. Indexes with zero scans are unused and waste write performance.

6. Check for table bloat using `SELECT relname, n_live_tup, n_dead_tup, n_dead_tup::float / GREATEST(n_live_tup, 1) AS dead_ratio FROM pg_stat_user_tables WHERE n_dead_tup > 1000 ORDER BY dead_ratio DESC`. A dead tuple ratio above 0.2 indicates the table needs VACUUM.

7. For each identified issue, generate a specific recommendation: CREATE INDEX statement with the exact columns, query rewrite suggestions, or configuration parameter adjustments.

8. Estimate the performance impact of each recommendation by comparing the EXPLAIN plan before and after applying the change on a staging database or by analyzing the expected row reduction from new indexes.

9. Prioritize recommendations by impact-to-effort ratio: index additions (high impact, low effort) before query rewrites (medium impact, medium effort) before schema changes (high impact, high effort).

10. Generate a performance analysis report with before/after execution plans, estimated improvements, and implementation priority ranking.

## Output

- **Slow query inventory** with execution frequency, mean/P95 duration, and total time consumed
- **Annotated execution plans** highlighting sequential scans, sort bottlenecks, and join inefficiencies
- **Index recommendations** as ready-to-execute CREATE INDEX statements with expected impact
- **Query rewrite suggestions** with original and optimized SQL side by side
- **Buffer cache analysis** with shared_buffers sizing recommendations
- **Performance report** ranking all findings by severity and implementation priority

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `EXPLAIN ANALYZE` takes too long on production | Query modifies data or runs for minutes | Use `EXPLAIN` without `ANALYZE` for estimated plans; run `EXPLAIN ANALYZE` on staging with representative data |
| `pg_stat_statements` not available | Extension not installed or not in shared_preload_libraries | Run `CREATE EXTENSION pg_stat_statements`; add to `shared_preload_libraries` in postgresql.conf and restart |
| Execution plan differs between staging and production | Different data distribution, statistics, or configuration | Run `ANALYZE` on staging tables to update statistics; match `work_mem`, `random_page_cost`, and `effective_cache_size` settings |
| Index recommendation causes slow writes | Too many indexes on a write-heavy table | Limit indexes to 5-7 per table; use partial indexes to reduce scope; consider covering indexes to replace multiple single-column indexes |
| Query plan uses wrong index | Stale statistics or cost model miscalculation | Run `ANALYZE table_name` to refresh statistics; adjust `random_page_cost` for SSD storage; use `SET enable_seqscan = off` to test index plans |

## Examples

**Optimizing a dashboard aggregate query**: A query computing daily revenue with `GROUP BY date` and `JOIN` across orders and line_items takes 12 seconds. EXPLAIN reveals a sequential scan on line_items (5M rows). Adding a composite index on `(order_id, created_at)` with `INCLUDE (amount)` reduces execution to 200ms by enabling an index-only scan.

**Diagnosing N+1 query pattern**: Application loads a list page showing 50 products, each with a separate query for category name. `pg_stat_statements` reveals `SELECT name FROM categories WHERE id = $1` called 50 times per page load. Resolution: rewrite as a single JOIN query or implement eager loading in the ORM.

**Identifying bloated table causing cache misses**: Buffer cache hit ratio drops to 0.78 on the sessions table. Investigation reveals 80% dead tuples due to aggressive INSERT/DELETE cycling without autovacuum tuning. Setting `autovacuum_vacuum_scale_factor = 0.01` and running `VACUUM FULL` restores cache hit ratio to 0.99.

## Resources

- PostgreSQL EXPLAIN documentation: https://www.postgresql.org/docs/current/using-explain.html
- pg_stat_statements reference: https://www.postgresql.org/docs/current/pgstatstatements.html
- MySQL EXPLAIN output format: https://dev.mysql.com/doc/refman/8.0/en/explain-output.html
- Use The Index, Luke (SQL indexing guide): https://use-the-index-luke.com/
- pgMustard EXPLAIN visualizer: https://www.pgmustard.com/
