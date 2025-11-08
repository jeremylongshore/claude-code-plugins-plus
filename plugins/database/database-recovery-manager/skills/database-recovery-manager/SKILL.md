---
name: managing-database-recovery
description: |
  This skill manages database recovery operations using the database-recovery-manager plugin. It enables disaster recovery, point-in-time recovery (PITR), and automated failover strategies for production database systems. Use this skill when the user requests help with "database recovery", "disaster recovery", "point-in-time recovery", "PITR", "backup validation", "recovery testing", or "multi-region failover" for databases. It automates backup verification and recovery testing.
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill empowers Claude to orchestrate comprehensive database recovery strategies, including disaster recovery setup, point-in-time recovery implementation, and automated failover configuration. It leverages the database-recovery-manager plugin to ensure database resilience and minimize downtime.

## How It Works

1. **Initiate Recovery Manager**: The skill invokes the `/recovery` command to start the database-recovery-manager plugin.
2. **Analyze User Request**: The plugin analyzes the user's request to determine the specific recovery task (e.g., disaster recovery setup, PITR configuration).
3. **Execute Recovery Steps**: The plugin executes the necessary steps to implement the requested recovery strategy, including configuring backups, setting up replication, and automating failover procedures.

## When to Use This Skill

This skill activates when you need to:
- Implement a disaster recovery plan for a production database.
- Configure point-in-time recovery (PITR) for a database.
- Automate backup validation and recovery testing.

## Examples

### Example 1: Setting up Disaster Recovery

User request: "Set up disaster recovery for my production PostgreSQL database."

The skill will:
1. Invoke the `/recovery` command.
2. Configure a disaster recovery plan, including setting up replication to a secondary region and automating failover procedures.

### Example 2: Implementing Point-in-Time Recovery

User request: "Implement point-in-time recovery for my MySQL database."

The skill will:
1. Invoke the `/recovery` command.
2. Configure point-in-time recovery, including setting up regular backups and enabling transaction log archiving.

## Best Practices

- **Backup Frequency**: Ensure backups are performed frequently enough to meet your recovery point objective (RPO).
- **Recovery Testing**: Regularly test your recovery procedures to ensure they are effective and efficient.
- **Documentation**: Document your recovery procedures thoroughly to ensure they can be followed by anyone on your team.

## Integration

This skill can be integrated with other plugins for database management, monitoring, and alerting to provide a comprehensive database operations solution. For example, it could work with a monitoring plugin to automatically trigger failover in the event of a database outage.