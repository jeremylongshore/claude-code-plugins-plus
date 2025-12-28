---
name: automating-database-backups
description: |
  Use when you need to automate database backup processes with scheduling and encryption.
  This skill creates backup scripts for PostgreSQL, MySQL, MongoDB, and SQLite with compression.
  Trigger with phrases like "automate database backups", "schedule database dumps",
  "create backup scripts", or "implement disaster recovery for database".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(pg_dump:*), Bash(mysqldump:*), Bash(mongodump:*), Bash(cron:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Database Backup Automator

This skill provides automated assistance for database backup automator tasks.

## Prerequisites

Before using this skill, ensure:
- Database credentials with backup permissions (SELECT on all tables)
- Sufficient disk space for backup files (estimate 2-3x database size with compression)
- Cron or task scheduler access for automated scheduling
- Backup destination storage (local disk, NFS, S3, GCS, Azure Blob)
- Encryption tools installed (gpg, openssl) for secure backups
- Test database available for restore validation

## Instructions

### Step 1: Assess Backup Requirements
1. Identify database type (PostgreSQL, MySQL, MongoDB, SQLite)
2. Determine backup frequency (hourly, daily, weekly, monthly)
3. Define retention policy (how long to keep backups)
4. Calculate expected backup size and storage needs
5. Document RTO (Recovery Time Objective) and RPO (Recovery Point Objective)

### Step 2: Design Backup Strategy
1. Choose backup type: full, incremental, or differential
2. Select backup destination (local, network storage, cloud)
3. Plan backup scheduling to avoid peak usage times
4. Define backup naming convention with timestamps
5. Determine compression and encryption requirements

### Step 3: Generate Backup Scripts
1. Create database-specific backup command (pg_dump, mysqldump, mongodump)
2. Add compression using gzip or zstd for storage efficiency
3. Implement encryption using gpg or openssl for security
4. Add error handling and logging to backup script
5. Include backup verification (checksum, test restore)

### Step 4: Configure Backup Schedule
1. Create cron job entry for automated execution
2. Set appropriate schedule based on backup frequency
3. Configure environment variables for credentials
4. Set up log rotation for backup logs
5. Test manual execution before enabling automation

### Step 5: Implement Retention Policy
1. Create cleanup script to remove old backups
2. Implement tiered retention (daily 7 days, weekly 4 weeks, monthly 12 months)
3. Schedule retention cleanup after backup completion
4. Add safeguards to prevent accidental deletion of recent backups
5. Log all backup deletions for audit trail

### Step 6: Create Restore Procedures
1. Document step-by-step restore process
2. Create restore scripts for each database type
3. Include procedures for point-in-time recovery
4. Test restore process on non-production environment
5. Document restore time estimates and validation steps

## Output

This skill produces:

**Backup Scripts**: Shell scripts for database dumps with compression and encryption

**Cron Configurations**: Crontab entries for automated backup scheduling

**Retention Scripts**: Automated cleanup scripts implementing retention policies

**Restore Procedures**: Step-by-step documentation and scripts for database restoration

**Monitoring Configuration**: Log file locations and success/failure notification setup

## Error Handling

**Backup Failures**:
- Check database connectivity and credentials
- Verify sufficient disk space for backup files
- Review database logs for lock or permission issues
- Implement retry logic with exponential backoff
- Send alerts on backup failures

**Insufficient Disk Space**:
- Monitor disk usage before backup execution
- Implement pre-backup cleanup of old backups
- Use incremental backups to reduce space requirements
- Compress backups more aggressively
- Move backups to remote storage immediately after creation

**Encryption Errors**:
- Verify encryption tools (gpg, openssl) are installed
- Check encryption key availability and permissions
- Test encryption/decryption process manually
- Document key management procedures
- Store encryption keys securely separate from backups

**Schedule Conflicts**:
- Ensure only one backup runs at a time (use lock files)
- Adjust backup schedule to avoid peak database usage
- Implement backup queuing for multiple databases
- Monitor backup duration and adjust schedule if needed
- Alert if backup duration exceeds acceptable window

## Resources

**Backup Script Templates**:
- PostgreSQL: `{baseDir}/templates/backup-scripts/postgresql-backup.sh`
- MySQL: `{baseDir}/templates/backup-scripts/mysql-backup.sh`
- MongoDB: `{baseDir}/templates/backup-scripts/mongodb-backup.sh`
- SQLite: `{baseDir}/templates/backup-scripts/sqlite-backup.sh`

**Restore Procedures**: `{baseDir}/docs/restore-procedures/`
- Point-in-time recovery
- Full database restore
- Selective table restore
- Cross-server migration

**Retention Policy Templates**: `{baseDir}/templates/retention-policies.yaml`
**Cron Job Examples**: `{baseDir}/examples/crontab-entries.txt`
**Monitoring Scripts**: `{baseDir}/scripts/backup-monitoring.sh`

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.