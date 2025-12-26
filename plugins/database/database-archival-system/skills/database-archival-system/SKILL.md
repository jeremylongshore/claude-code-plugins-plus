---
name: archiving-databases
description: |
  Use when you need to archive historical database records to reduce primary database size.
  This skill automates moving old data to archive tables or cold storage (S3, Azure Blob, GCS).
  Trigger with phrases like "archive old database records", "implement data retention policy",
  "move historical data to cold storage", or "reduce database size with archival".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*, mysql:*, aws:s3:*), az:storage:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Database credentials with SELECT and DELETE permissions on source tables
- Access to destination storage (archive table or cloud storage credentials)
- Network connectivity to cloud storage services if using S3/Azure/GCS
- Backup of database before first archival run
- Understanding of data retention requirements and compliance policies
- Monitoring tools configured to track archival job success

## Instructions

### Step 1: Define Archival Criteria
1. Identify tables containing historical data for archival
2. Define age threshold for archival (e.g., records older than 1 year)
3. Determine additional criteria (status flags, record size, access frequency)
4. Calculate expected data volume to be archived
5. Document business requirements and compliance policies

### Step 2: Choose Archival Destination
1. Evaluate options: archive table in same database, separate archive database, or cold storage
2. For cloud storage: select S3, Azure Blob, or GCS based on infrastructure
3. Configure destination storage with appropriate security and access controls
4. Set up compression settings for storage efficiency
5. Define data format for archived records (CSV, Parquet, JSON)

### Step 3: Create Archive Schema
1. Design archive table schema matching source table structure
2. Add metadata columns (archived_at, source_table, archive_reason)
3. Create indexes on commonly queried archive columns
4. For cloud storage: define bucket structure and naming conventions
5. Test archive schema with sample data

### Step 4: Implement Archival Logic
1. Write SQL query to identify records meeting archival criteria
2. Create extraction script to export records from source tables
3. Implement transformation logic if archive format differs from source
4. Build verification queries to confirm data integrity after archival
5. Add transaction handling to ensure atomicity (delete only if archive succeeds)

### Step 5: Execute Archival Process
1. Run archival in staging environment first with subset of data
2. Verify archived data integrity and completeness
3. Execute archival in production during low-traffic window
4. Monitor database performance during archival operation
5. Generate archival report with record counts and storage savings

### Step 6: Automate Retention Policy
1. Schedule periodic archival jobs (weekly, monthly)
2. Configure automated monitoring and alerting for job failures
3. Implement cleanup of successfully archived records from source tables
4. Set up expiration policies on archived data per compliance requirements
5. Document archival schedule and retention periods

## Output

This skill produces:

**Archival Scripts**: SQL and shell scripts to extract, transform, and load data to archive destination

**Archive Tables/Files**: Structured storage containing historical records with metadata and timestamps

**Verification Reports**: Row counts, data checksums, and integrity checks confirming successful archival

**Storage Metrics**: Database size reduction, archive storage utilization, and cost savings estimates

**Archival Logs**: Detailed logs of each archival run with timestamps, record counts, and any errors

## Error Handling

**Insufficient Storage Space**:
- Check available disk space on archive destination before execution
- Implement storage monitoring and alerting
- Use compression to reduce archive size
- Clean up old archives per retention policy before new archival

**Data Integrity Issues**:
- Run checksums on source data before and after archival
- Implement row count verification between source and archive
- Keep source data until archive verification completes
- Rollback archive transaction if verification fails

**Permission Denied Errors**:
- Verify database user has SELECT on source tables and INSERT on archive tables
- Confirm cloud storage credentials have write permissions
- Check network security groups allow connections to cloud storage
- Document required permissions for archival automation

**Timeout During Large Archival**:
- Split archival into smaller batches by date ranges
- Run archival incrementally over multiple days
- Increase database timeout settings for archival sessions
- Schedule archival during maintenance windows with extended timeouts

## Resources

**Archival Configuration Templates**:
- PostgreSQL archival: `{baseDir}/templates/postgresql-archive-config.yaml`
- MySQL archival: `{baseDir}/templates/mysql-archive-config.yaml`
- S3 cold storage: `{baseDir}/templates/s3-archive-config.yaml`
- Azure Blob storage: `{baseDir}/templates/azure-archive-config.yaml`

**Retention Policy Definitions**: `{baseDir}/policies/retention-policies.yaml`

**Archival Scripts Library**: `{baseDir}/scripts/archival/`
- Extract to CSV script
- Extract to Parquet script
- S3 upload with compression
- Archive verification queries

**Monitoring Dashboards**: `{baseDir}/monitoring/archival-dashboard.json`
**Cost Analysis Tools**: `{baseDir}/tools/storage-cost-calculator.py`

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.