---
name: Automating Database Backups
description: |
  This skill automates database backups using the database-backup-automator plugin. It creates scripts for scheduled backups, compression, encryption, and restore procedures across PostgreSQL, MySQL, MongoDB, and SQLite. Use this when the user requests database backup automation, disaster recovery planning, setting up backup schedules, or creating restore procedures. The skill is triggered by phrases like "create database backup", "automate database backups", "setup backup schedule", or "generate restore procedure".
---

## Overview

This skill streamlines the creation of database backup solutions. It generates scripts, configures schedules, and provides comprehensive restore procedures, ensuring data safety and efficient recovery.

## How It Works

1. **Analyze Requirements**: Determines the database type (PostgreSQL, MySQL, MongoDB, or SQLite) and backup requirements (frequency, retention).
2. **Generate Scripts**: Creates backup scripts with compression and encryption.
3. **Schedule Backups**: Sets up cron jobs for automated, scheduled backups.
4. **Document Restore**: Generates clear, concise restore procedures.

## When to Use This Skill

This skill activates when you need to:
- Create a backup schedule for a database.
- Automate the database backup process.
- Generate scripts for database restoration.
- Implement a disaster recovery plan for a database.

## Examples

### Example 1: Setting up Daily Backups for PostgreSQL

User request: "Create daily backups for my PostgreSQL database."

The skill will:
1. Generate a `pg_dump` script with compression and encryption.
2. Create a cron job to run the backup script daily.

### Example 2: Automating Weekly Backups for MongoDB

User request: "Automate weekly backups for my MongoDB database."

The skill will:
1. Generate a `mongodump` script with compression and encryption.
2. Create a cron job to run the backup script weekly and implement a retention policy.

## Best Practices

- **Retention Policies**: Implement clear retention policies to manage storage space.
- **Testing Restores**: Regularly test restore procedures to ensure data integrity.
- **Secure Storage**: Store backups in secure, encrypted locations, preferably offsite.

## Integration

This skill can integrate with cloud storage plugins (S3, GCS, Azure) for offsite backup storage and monitoring plugins for backup success/failure alerts.