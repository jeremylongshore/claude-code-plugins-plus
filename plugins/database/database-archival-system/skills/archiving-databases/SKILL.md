---
name: archiving-databases
description: |
  Process use when you need to archive historical database records to reduce primary database size.
  This skill automates moving old data to archive tables or cold storage (S3, Azure Blob, GCS).
  Trigger with phrases like "archive old database records", "implement data retention policy",
  "move historical data to cold storage", or "reduce database size with archival".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(aws:s3:*), Bash(az:storage:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Archival System

## Overview

Implement automated data archival pipelines that move historical records from primary database tables to archive storage (archive tables, S3, Azure Blob, or GCS) based on age, status, or access frequency criteria.

## Prerequisites

- Database credentials with SELECT, INSERT, and DELETE permissions on source and archive tables
- Cloud storage credentials (AWS S3, Azure Blob, or GCS) if archiving to cold storage
- `psql` or `mysql` CLI for executing archival queries
- `aws s3`, `az storage`, or `gsutil` CLI for cloud storage uploads
- Understanding of data retention requirements and compliance policies (GDPR, HIPAA, SOX)
- Current table sizes: `SELECT pg_size_pretty(pg_total_relation_size('table_name'))` to identify archival candidates

## Instructions

1. Identify archival candidates by finding large tables with time-based data:
   - `SELECT relname, n_live_tup, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10`
   - Focus on tables where historical data is rarely queried: logs, audit trails, events, old orders, expired sessions

2. Define archival criteria for each table:
   - **Age-based**: Records older than N days/months (`WHERE created_at < NOW() - INTERVAL '1 year'`)
   - **Status-based**: Records in terminal state (`WHERE status IN ('completed', 'cancelled', 'expired')`)
   - **Combined**: Old AND terminal (`WHERE created_at < NOW() - INTERVAL '6 months' AND status = 'completed'`)
   - Calculate the expected volume: `SELECT COUNT(*), pg_size_pretty(pg_column_size(t.*)) FROM table_name t WHERE <criteria>`

3. Handle referential integrity by archiving in dependency order:
   - Archive child records first (order_items before orders)
   - For tables with active foreign key references, verify no active records reference the candidates: `SELECT COUNT(*) FROM active_child WHERE parent_id IN (SELECT id FROM parent WHERE <archive_criteria>)`
   - Option: cascade archive by archiving parent and all descendants together

4. Create archive destination tables matching the source schema plus metadata columns:
   - `CREATE TABLE orders_archive (LIKE orders INCLUDING ALL)`
   - `ALTER TABLE orders_archive ADD COLUMN archived_at TIMESTAMPTZ DEFAULT NOW()`
   - `ALTER TABLE orders_archive ADD COLUMN archive_batch_id UUID`
   - Remove foreign key constraints on archive tables (archived data is self-contained)

5. Implement the archival operation as an atomic batch:
   - Generate a batch ID: `SELECT gen_random_uuid() AS batch_id`
   - Insert into archive: `INSERT INTO orders_archive SELECT *, NOW(), batch_id FROM orders WHERE <criteria>`
   - Verify row counts match: `SELECT COUNT(*) FROM orders_archive WHERE archive_batch_id = batch_id`
   - Delete from source only after verification: `DELETE FROM orders WHERE id IN (SELECT id FROM orders_archive WHERE archive_batch_id = batch_id)`
   - Wrap in a transaction for atomicity

6. For cloud storage archival, export data to files before upload:
   - PostgreSQL: `COPY (SELECT * FROM orders WHERE <criteria>) TO '/tmp/archive_orders_2023.csv' WITH CSV HEADER`
   - Compress: `gzip /tmp/archive_orders_2023.csv`
   - Upload: `aws s3 cp /tmp/archive_orders_2023.csv.gz s3://archive-bucket/orders/2023/ --sse aws:kms`
   - Store manifest: record file path, row count, checksum, and date range in an archive_manifest table

7. Process archival in batches to avoid long-running transactions and excessive lock time:
   - Archive 10,000-50,000 rows per batch
   - Add a short delay between batches (100-500ms) to allow other transactions to proceed
   - Log progress after each batch for monitoring and restart capability

8. Run `VACUUM ANALYZE` on source tables after archival to reclaim disk space and update statistics. For large archival operations (>30% of table), consider `VACUUM FULL` during a maintenance window (requires exclusive lock).

9. Implement data retrieval procedures for archived data:
   - For archive tables: direct SQL queries with `UNION ALL` between active and archive tables
   - For cloud storage: import script that restores specific date ranges from S3/GCS to temporary tables
   - Document retrieval procedures for support and compliance teams

10. Schedule recurring archival with a cron job or database scheduler. Run weekly or monthly. Include monitoring that alerts on: archival job failure, unexpected archive volume (too many or too few records), and source table size not decreasing after archival.

## Output

- **Archive table DDL** with matching schema plus metadata columns
- **Archival scripts** (SQL and shell) for batch extraction, verification, and deletion
- **Cloud storage upload scripts** with compression and encryption
- **Archive manifest table** tracking all archival batches with metadata
- **Retrieval scripts** for restoring archived data when needed
- **Cron job configuration** for scheduled recurring archival

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Foreign key violation during DELETE | Active child records still reference archived parent | Archive child records first; verify no active references exist before deleting parent records |
| Disk space not reclaimed after archival | PostgreSQL marks deleted rows as dead tuples but does not release space | Run `VACUUM FULL table_name` during maintenance window; or use `pg_repack` for online space reclamation |
| Archive batch interrupted mid-transaction | Network failure, timeout, or crash during archival | Transaction rollback ensures atomicity; restart from the last completed batch using batch_id tracking |
| Cloud storage upload fails | Network timeout, credential expiration, or bucket permissions | Implement retry with exponential backoff; verify credentials before starting; use multipart upload for files >100MB |
| Archived data needed for audit | Compliance request requires access to archived records | Query archive tables directly; or restore from cloud storage using the archive manifest to locate the correct files |

## Examples

**Archiving 2 years of completed orders to reduce database size by 60%**: An orders table with 50M rows (120GB) contains 30M completed orders older than 1 year. Archival moves these to `orders_archive` in batches of 50,000 rows over 3 hours during off-peak. Source table drops to 20M rows (48GB). VACUUM reclaims 72GB. Query performance on active orders improves by 40%.

**Tiered archival to S3 with Parquet format**: Orders 6-12 months old move to archive tables (warm tier, queryable via SQL). Orders older than 12 months export to S3 as Parquet files (cold tier, retrievable on request). Parquet format reduces storage costs by 80% compared to CSV. Archive manifest tracks 156 Parquet files across 36 monthly partitions.

**GDPR-compliant data retention with automatic purging**: Archival script moves user data older than 3 years to archive tables. A separate purge job permanently deletes archive records older than 7 years. Both jobs log actions to an immutable audit trail. Monthly compliance report shows record counts by age tier and confirms purge completion.

## Resources

- PostgreSQL COPY command: https://www.postgresql.org/docs/current/sql-copy.html
- AWS S3 CLI: https://docs.aws.amazon.com/cli/latest/reference/s3/
- pg_repack (online table rewrite): https://reorg.github.io/pg_repack/
- Data retention best practices: https://www.postgresql.org/docs/current/routine-vacuuming.html
- Parquet format: https://parquet.apache.org/documentation/latest/