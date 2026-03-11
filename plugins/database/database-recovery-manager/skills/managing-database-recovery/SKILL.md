---
name: managing-database-recovery
description: |
  Process use when you need to work with database operations.
  This skill provides database management and optimization with comprehensive guidance and automation.
  Trigger with phrases like "manage database", "optimize database",
  or "configure database".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(tar:*), Bash(rsync:*), Bash(aws:s3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Recovery Manager

## Overview

Plan and execute database backup and recovery procedures for PostgreSQL and MySQL, including point-in-time recovery (PITR), logical and physical backups, WAL archiving, and disaster recovery testing. This skill covers the full backup lifecycle from configuration through automated verification, ensuring Recovery Point Objective (RPO) and Recovery Time Objective (RTO) targets are met.

## Prerequisites

- Database superuser or replication-role credentials
- Backup storage destination (local disk, NFS mount, S3, GCS, or Azure Blob)
- `pg_basebackup`, `pg_dump`, `pg_restore` (PostgreSQL) or `mysqldump`, `xtrabackup` (MySQL)
- `tar`, `rsync`, or `aws s3` CLI for backup transfer and storage
- WAL archiving configured for PITR (PostgreSQL: `archive_mode = on`, `archive_command`)
- Sufficient storage for backup retention (estimate 2-3x database size for full + incremental)

## Instructions

1. Assess the current backup situation by checking existing backup configurations. For PostgreSQL: verify `archive_mode`, `archive_command`, and `wal_level` in `postgresql.conf`. For MySQL: check if binary logging is enabled with `SHOW VARIABLES LIKE 'log_bin'`.

2. Define RPO and RTO targets based on business requirements:
   - RPO (acceptable data loss): determines backup frequency and WAL archiving interval
   - RTO (acceptable downtime): determines backup type and recovery procedure complexity
   - Typical targets: RPO < 1 hour (WAL archiving), RTO < 30 minutes (physical backup restore)

3. Configure WAL archiving for PostgreSQL PITR:
   - Set `wal_level = replica` and `archive_mode = on`
   - Configure `archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'` (or use pgBackRest/WAL-G for S3)
   - Verify archiving works: `SELECT * FROM pg_stat_archiver`
   - For MySQL, enable binary logging: `log_bin = mysql-bin`, `binlog_format = ROW`

4. Create a full physical backup using `pg_basebackup -D /backups/base -Ft -z -P` (PostgreSQL) or `xtrabackup --backup --target-dir=/backups/full` (MySQL). Physical backups are faster to restore than logical backups for databases larger than 10GB.

5. Create logical backups for portability and selective restoration: `pg_dump -Fc -f database.dump dbname` (PostgreSQL) or `mysqldump --single-transaction --routines --triggers dbname > database.sql` (MySQL).

6. Upload backups to remote storage for disaster recovery: `aws s3 cp /backups/base.tar.gz s3://backup-bucket/postgres/$(date +%Y%m%d)/` with server-side encryption enabled. Implement a retention policy (e.g., daily backups for 30 days, weekly for 90 days, monthly for 1 year).

7. Test recovery by restoring to a separate server or container:
   - Restore physical backup: `pg_restore -d testdb database.dump` or untar base backup and start PostgreSQL
   - For PITR: restore base backup, copy WAL files to `pg_wal`, create `recovery.signal` with `recovery_target_time = '2024-01-15 14:30:00'`
   - Verify data integrity by running application test suite against restored database
   - Measure actual recovery time to validate RTO target

8. Automate backup verification with a daily cron job that: takes backup, restores to a test instance, runs integrity checks (`pg_catalog.pg_class` row counts, checksum verification), and sends a success/failure notification.

9. Document the recovery runbook with exact commands for each recovery scenario: full database restore, PITR to a specific timestamp, single table restore, and cross-region failover.

10. Schedule monthly disaster recovery drills to verify the runbook works and the team can execute recovery within RTO targets.

## Output

- **Backup configuration files** for PostgreSQL (postgresql.conf changes, archive_command) or MySQL (my.cnf changes)
- **Backup scripts** (shell) for automated full and incremental backups with S3/GCS upload
- **Recovery runbook** with step-by-step commands for each recovery scenario
- **Backup verification scripts** that automate restore-and-check procedures
- **Retention policy configuration** with automated cleanup of old backups

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| WAL segment not found during PITR | Gap in WAL archiving due to archive_command failure | Check `pg_stat_archiver` for `last_failed_wal`; fix archive_command; consider WAL-G or pgBackRest for reliable archiving |
| `pg_basebackup` fails with "replication connection" error | Missing replication permissions or `max_wal_senders` exhausted | Grant REPLICATION role; increase `max_wal_senders`; add entry to `pg_hba.conf` for replication connections |
| Backup storage full | Retention policy not enforced or backup size grew unexpectedly | Implement automated cleanup script; compress backups with `gzip` or `zstd`; monitor storage usage with alerts at 80% |
| Recovery takes longer than RTO target | Database grew since RTO was last validated, or restore is I/O-bound | Use physical backups instead of logical; restore to SSD storage; parallelize restore with `pg_restore -j 4`; consider standby replica for faster failover |
| Restored database has corruption | Backup taken during crash or disk error | Enable `data_checksums` in PostgreSQL; verify backups with `pg_verifybackup`; run `ANALYZE` and `REINDEX` after restore |

## Examples

**Point-in-time recovery after accidental table drop**: At 14:30 a developer runs `DROP TABLE orders` on production. Recovery: restore the most recent physical backup (taken at 02:00), replay WAL files up to 14:29:59 using `recovery_target_time`, verify orders table is intact, then swap the recovered database into production. Total recovery time: 25 minutes for a 200GB database.

**Automated daily backup to S3 with verification**: A cron job runs at 02:00 UTC: takes `pg_basebackup`, compresses with `zstd`, uploads to S3 with server-side encryption, restores to a Docker container, runs row count checks against production, and sends a Slack notification with backup size and verification status.

**Cross-region disaster recovery drill**: Monthly exercise: restore the latest S3 backup to a different AWS region, replay WAL files to catch up, run the application test suite, measure total failover time, and document results. Target: full recovery in a different region within 1 hour.

## Resources

- PostgreSQL backup and recovery: https://www.postgresql.org/docs/current/backup.html
- pgBackRest (production backup tool): https://pgbackrest.org/
- WAL-G (WAL archiving to cloud storage): https://github.com/wal-g/wal-g
- Percona XtraBackup: https://docs.percona.com/percona-xtrabackup/
- MySQL point-in-time recovery: https://dev.mysql.com/doc/refman/8.0/en/point-in-time-recovery.html