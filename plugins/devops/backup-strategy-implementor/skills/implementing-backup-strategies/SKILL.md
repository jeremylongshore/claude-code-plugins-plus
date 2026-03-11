---
name: implementing-backup-strategies
description: |
  Execute use when you need to work with backup and recovery.
  This skill provides backup automation and disaster recovery with comprehensive guidance and automation.
  Trigger with phrases like "create backups", "automate backups",
  or "implement disaster recovery".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(tar:*), Bash(rsync:*), Bash(aws:s3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Implementing Backup Strategies

## Overview

Design and implement backup strategies for databases, file systems, and cloud resources using tools like `tar`, `rsync`, `pg_dump`, `mysqldump`, AWS S3, and cloud-native snapshot APIs. Covers full, incremental, and differential backup schemes with retention policies, encryption, and automated verification.

## Prerequisites

- `tar`, `rsync`, or `restic` installed for file-level backups
- Database client tools (`pg_dump`, `mysqldump`, `mongodump`) for database backups
- AWS CLI configured with S3 write permissions (or equivalent GCP/Azure storage access)
- Sufficient storage capacity at backup destination (local, NFS, or object storage)
- Cron or systemd timer access for scheduling automated backups
- GPG or OpenSSL for backup encryption at rest

## Instructions

1. Inventory all data sources requiring backup: databases, application data directories, configuration files, secrets/certificates
2. Classify data by RPO (Recovery Point Objective) and RTO (Recovery Time Objective) requirements
3. Select backup strategy per data class: full daily + incremental hourly for databases, snapshot-based for block storage, rsync for file systems
4. Generate backup scripts using appropriate tools (`pg_dump --format=custom`, `tar czf`, `rsync -avz --delete`)
5. Configure retention policy: daily backups kept 7 days, weekly kept 4 weeks, monthly kept 12 months
6. Add encryption for backups containing sensitive data (`gpg --encrypt` or S3 server-side encryption with KMS)
7. Set up automated scheduling via cron jobs or systemd timers with proper logging
8. Implement backup verification: restore to a test environment on a weekly schedule and validate data integrity
9. Configure alerting for backup failures via email, Slack, or PagerDuty

## Output

- Backup shell scripts with logging, error handling, and lock files to prevent concurrent runs
- Cron entries or systemd timer/service unit files
- Retention policy configuration (lifecycle rules for S3, cleanup scripts for local)
- Restore runbook with step-by-step recovery procedures
- Monitoring configuration for backup success/failure alerts

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `No space left on device` | Backup destination full | Verify retention cleanup is running; increase storage or reduce retention window |
| `pg_dump: connection refused` | Database not accepting connections or wrong credentials | Check `pg_hba.conf`, verify connection string, and test with `psql` first |
| `rsync: connection unexpectedly closed` | Network interruption or SSH timeout | Add `--timeout=300` and `--partial` flags; use persistent SSH tunnel |
| `S3 upload failed: Access Denied` | IAM policy missing `s3:PutObject` permission | Attach proper IAM policy; verify bucket policy allows writes from the backup source |
| `Backup file corrupted on restore` | Incomplete write or disk error during backup | Add checksum verification (`sha256sum`) after backup; test restores regularly |

## Examples

- "Create a backup strategy for a PostgreSQL database: full dump nightly to S3, WAL archiving for point-in-time recovery, 30-day retention."
- "Generate rsync scripts to mirror `/var/www` to a remote NAS with incremental daily backups and weekly full backups."
- "Implement encrypted backups for a MongoDB replica set with automated restore testing every Sunday."

## Resources

- PostgreSQL backup guide: https://www.postgresql.org/docs/current/backup.html
- AWS S3 lifecycle policies: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
- Restic backup tool: https://restic.readthedocs.io/
- Backup best practices (3-2-1 rule): https://www.veeam.com/blog/321-backup-rule.html
