---
name: managing-database-partitions
description: |
  Process use when you need to work with database partitioning.
  This skill provides table partitioning strategies with comprehensive guidance and automation.
  Trigger with phrases like "partition tables", "implement partitioning",
  or "optimize large tables".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Partition Manager

## Overview

Implement and manage table partitioning for PostgreSQL and MySQL to improve query performance and simplify data lifecycle management on large tables. This skill covers range partitioning (by date or ID), list partitioning (by category or region), hash partitioning (for even distribution), and composite partitioning.

## Prerequisites

- PostgreSQL 10+ (declarative partitioning) or MySQL 5.7+ (native partitioning)
- Database admin credentials with CREATE TABLE and ALTER TABLE permissions
- `psql` or `mysql` CLI for executing partition DDL
- Table size metrics: `SELECT pg_size_pretty(pg_total_relation_size('table_name'))` or `SELECT data_length FROM information_schema.TABLES`
- Query patterns on the target table (especially WHERE clause columns used for filtering)
- Maintenance window availability for initial partition migration on existing tables

## Instructions

1. Identify partitioning candidates by finding tables that exceed 10GB or 100M rows, have time-based query patterns, or require periodic data purging. Query `pg_stat_user_tables` to find tables with high sequential scan counts on large row sets.

2. Select the partition key based on the most common query filter column. For time-series data, use the timestamp column. For multi-tenant data, use tenant_id. The partition key must appear in most WHERE clauses to enable partition pruning.

3. Choose the partitioning strategy:
   - **Range**: Best for time-series data. Create monthly or daily partitions. Queries filtering by date range scan only relevant partitions.
   - **List**: Best for categorical data. Create one partition per category, region, or status value.
   - **Hash**: Best for even distribution when no natural range exists. Distribute rows across N partitions using hash of the partition key.
   - **Composite**: Combine range + list for multi-dimensional partitioning (e.g., range by date, then list by region).

4. For PostgreSQL, create the partitioned parent table: `CREATE TABLE orders (id bigint, created_at timestamptz, ...) PARTITION BY RANGE (created_at)`. Then create child partitions: `CREATE TABLE orders_2024_01 PARTITION OF orders FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')`.

5. For MySQL, define partitions inline: `ALTER TABLE orders PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (PARTITION p202401 VALUES LESS THAN (202402), ...)`.

6. Migrate data from an existing unpartitioned table to a partitioned table:
   - Create the new partitioned table with identical schema
   - Copy data in batches: `INSERT INTO orders_partitioned SELECT * FROM orders_old WHERE created_at BETWEEN ... AND ...`
   - Verify row counts match between old and new tables
   - Rename tables atomically: `ALTER TABLE orders RENAME TO orders_old; ALTER TABLE orders_partitioned RENAME TO orders;`

7. Create indexes on each partition. In PostgreSQL, indexes on the parent table automatically propagate to child partitions. Create the primary key and any secondary indexes on the partitioned table.

8. Automate future partition creation with a scheduled script or cron job. For monthly range partitions, create the next 3 months of partitions in advance to prevent INSERT failures when a new month begins.

9. Implement partition maintenance: drop or detach old partitions for data retention (`ALTER TABLE orders DETACH PARTITION orders_2022_01`), then archive or delete the detached partition. This is vastly faster than `DELETE FROM orders WHERE created_at < '2023-01-01'`.

10. Verify partition pruning works by running `EXPLAIN` on typical queries and confirming only relevant partitions are scanned. Look for "Partitions: 1/24" in the plan output indicating effective pruning.

## Output

- **Partition DDL scripts** for creating partitioned tables and child partitions
- **Data migration scripts** for moving data from unpartitioned to partitioned tables
- **Partition maintenance scripts** for automated creation, detachment, and archival
- **Partition pruning verification queries** confirming optimizer uses partition elimination
- **Cron job configurations** for scheduled partition creation and cleanup

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `no partition of relation "table" found for row` | INSERT targets a range with no matching partition | Create the missing partition; implement automated partition pre-creation for future ranges |
| Partition pruning not occurring | Query filter does not use the partition key, or uses a function on the key column | Rewrite query to filter directly on the partition key column; avoid wrapping partition key in functions |
| Slow data migration from unpartitioned table | Single large INSERT/SELECT locks the table and fills WAL | Migrate in batches by partition range; use `pg_repack` for online migration; increase `maintenance_work_mem` and `max_wal_size` |
| Foreign key references prevent partitioning | PostgreSQL does not support foreign keys referencing partitioned tables (pre-v12) | Upgrade to PostgreSQL 12+; or remove FK constraints and enforce referential integrity at application level |
| Too many partitions causing planner slowdown | Hundreds or thousands of child partitions degrade query planning time | Use wider partition ranges (monthly instead of daily); enable `enable_partition_pruning`; consider sub-partitioning instead of flat partitioning |

## Examples

**Monthly range partitioning for an events table**: A 500GB events table with 2B rows partitioned by `created_at` into monthly partitions. Queries filtering by date range (last 7 days, last month) now scan only 1-2 partitions instead of the full table. Partition drop replaces a 4-hour DELETE operation with a sub-second DDL command for monthly data purges.

**Hash partitioning for a sessions table**: A sessions table with random UUID primary keys and no natural range column. Hash partition by `session_id` across 16 partitions to distribute I/O evenly. Parallel sequential scans across partitions improve full-table analytic queries by 8x on an 8-core server.

**Composite partitioning for multi-region SaaS**: Orders table partitioned first by range on `created_at` (monthly), then by list on `region` (us-east, us-west, eu, asia). Queries for "all US orders this month" prune to just 2 of 48 total partitions, reducing scan volume by 96%.

## Resources

- PostgreSQL table partitioning: https://www.postgresql.org/docs/current/ddl-partitioning.html
- MySQL partitioning: https://dev.mysql.com/doc/refman/8.0/en/partitioning.html
- pg_partman extension (automated partition management): https://github.com/pgpartman/pg_partman
- Partition pruning internals: https://www.postgresql.org/docs/current/ddl-partitioning.html#DDL-PARTITION-PRUNING