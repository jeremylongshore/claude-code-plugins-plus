---
name: Archiving Databases
description: |
  This skill automates database archival processes. It helps reduce primary database size by moving historical records to archive tables or cold storage solutions like S3, Azure Blob, or GCS. The plugin supports PostgreSQL and MySQL, implementing automated retention policies, compression, compliance tracking, and zero-downtime migration. Use this when the user mentions "database archival", "archive old database records", "retention policies", "cold storage", or "reduce database size." It is particularly useful for handling requests related to data lifecycle management and compliance requirements in database systems.
---

## Overview

This skill provides a streamlined way to archive database records, freeing up space on the primary database and ensuring compliance with data retention policies. It automates the process of moving historical data to more cost-effective storage solutions while maintaining query access.

## How It Works

1. **Identify Archival Candidates**: The skill identifies database records that meet the specified archival criteria based on age, size, or other relevant factors.
2. **Data Migration**: It migrates the identified records to archive tables within the same database or to cold storage solutions like S3, Azure Blob, or GCS.
3. **Policy Enforcement**: The skill enforces automated retention policies, ensuring that data is archived or deleted according to pre-defined rules.
4. **Verification and Reporting**: After the archival process, the skill verifies the successful migration of data and generates reports for compliance tracking.

## When to Use This Skill

This skill activates when you need to:
- Reduce the size of a primary database.
- Implement data retention policies for compliance.
- Move historical data to cost-effective storage solutions.

## Examples

### Example 1: Archiving Old Order Data

User request: "I need to archive order data older than one year from my PostgreSQL database to S3 to reduce database size and comply with retention policies."

The skill will:
1. Identify order records older than one year in the PostgreSQL database.
2. Migrate these records to an S3 bucket, compressing the data for storage efficiency.

### Example 2: Setting Up Automated Retention Policies

User request: "Set up automated retention policies for my MySQL database to archive user activity logs older than 90 days to a separate archive table."

The skill will:
1. Configure automated retention policies to identify user activity logs older than 90 days.
2. Create an archive table within the MySQL database and migrate the identified logs to it.

## Best Practices

- **Data Validation**: Always validate the archived data to ensure data integrity.
- **Compression**: Utilize compression techniques to minimize storage costs in cold storage solutions.
- **Monitoring**: Implement monitoring to track the performance and success of archival processes.

## Integration

This skill integrates well with other database management tools and cloud storage services. It can be used in conjunction with monitoring tools to track database performance and storage utilization after archival.