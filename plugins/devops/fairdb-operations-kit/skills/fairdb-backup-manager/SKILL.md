---
name: fairdb-backup-manager
description: |
  Manage use when you need to work with backup and recovery.
  This skill provides backup automation and disaster recovery with comprehensive guidance and automation.
  Trigger with phrases like "create backups", "automate backups",
  or "implement disaster recovery".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(tar:*), Bash(rsync:*), Bash(aws:s3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# FairDB Backup Manager

## Overview

Automate backup and recovery operations for FairDB database instances. Generate backup scripts, configure retention policies, schedule automated backups to local storage or S3, and produce tested restore procedures with integrity verification.

## Prerequisites

- FairDB instance running and accessible with admin credentials
- `tar` and `rsync` installed for file-level backups
- AWS CLI configured with `s3:PutObject` and `s3:GetObject` permissions (if using S3 as backup target)
- Sufficient storage at backup destination (2-3x database size for rotation)
- Cron or systemd timer access for scheduling
- Test environment available for restore verification

## Instructions

1. Assess the FairDB instance: identify data directory location, database size, and write throughput
2. Select backup method: logical dump for portability, filesystem snapshot for speed, or continuous archiving for minimal RPO
3. Generate backup script with lock acquisition, data export, compression (`tar czf`), and checksum generation
4. Configure S3 upload with server-side encryption (`aws s3 cp --sse aws:kms`) for off-site copies
5. Set up retention policy: keep hourly backups for 24 hours, daily for 7 days, weekly for 4 weeks, monthly for 12 months
6. Create cleanup script to purge expired backups according to retention schedule
7. Schedule backups via cron with proper logging to `/var/log/fairdb-backup.log`
8. Generate restore procedure: download from S3, verify checksum, decompress, and import with validation query
9. Test restore procedure in a staging environment and document the time-to-recovery

## Output

- Backup shell script with logging, locking, compression, and S3 upload
- Restore shell script with checksum verification and data validation
- Cron schedule entries or systemd timer units
- Retention cleanup script
- S3 lifecycle policy configuration for long-term archive tiering

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Backup lock acquisition failed` | Another backup or maintenance process is running | Check for stale lock files; implement timeout-based lock with `flock` |
| `tar: Cannot open: No space left on device` | Local backup destination full | Run retention cleanup; check disk usage with `df -h`; increase volume size |
| `aws s3 cp: upload failed` | Network issue or expired AWS credentials | Retry with `--retry 3`; refresh credentials; check S3 bucket permissions |
| `Restore failed: checksum mismatch` | Backup file corrupted during transfer or storage | Re-download from S3; verify S3 object integrity; use a different backup copy |
| `Database inconsistent after restore` | Backup taken during active write without lock | Ensure backup script acquires a consistent snapshot lock before export |

## Examples

- "Create an automated nightly backup for the FairDB production instance, compressed and uploaded to S3 with KMS encryption and 30-day retention."
- "Generate a restore runbook that pulls the latest backup from S3, verifies integrity, and restores to a staging instance for validation."
- "Set up backup monitoring that alerts via Slack if a backup job fails or if no successful backup exists within the last 25 hours."

## Resources

- AWS S3 CLI: https://docs.aws.amazon.com/cli/latest/reference/s3/
- rsync documentation: https://rsync.samba.org/documentation.html
- Backup automation patterns: https://www.veeam.com/blog/321-backup-rule.html
- Linux cron scheduling: https://crontab.guru/