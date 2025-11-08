---
name: monitoring-database-transactions
description: |
  This skill enables Claude to monitor database transactions for performance and lock issues using the database-transaction-monitor plugin. It is triggered when the user requests transaction monitoring, lock detection, or rollback rate analysis for databases. Use this skill when the user mentions "monitor database transactions," "detect long-running transactions," "identify lock contention," "track rollback rates," or asks about "transaction anomalies." The skill leverages the `/txn-monitor` command to provide real-time alerts and insights into database health.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to proactively monitor database transactions, identify performance bottlenecks like long-running queries and lock contention, and alert on anomalies such as high rollback rates. It provides insights into database health and helps prevent performance degradation.

## How It Works

1. **Activation**: The user's request triggers the `database-transaction-monitor` plugin.
2. **Transaction Monitoring**: The plugin executes the `/txn-monitor` command to initiate transaction monitoring.
3. **Alerting**: The plugin analyzes transaction data and generates alerts based on predefined thresholds for long-running transactions, lock wait times, and rollback rates.

## When to Use This Skill

This skill activates when you need to:
- Detect and kill long-running transactions blocking other queries.
- Monitor lock wait times and identify deadlock patterns.
- Track transaction rollback rates for error analysis.

## Examples

### Example 1: Detecting Long-Running Transactions

User request: "Find any long-running database transactions."

The skill will:
1. Activate the `database-transaction-monitor` plugin.
2. Execute the `/txn-monitor` command to identify transactions exceeding a predefined duration threshold.

### Example 2: Analyzing Lock Contention

User request: "Analyze database lock contention."

The skill will:
1. Activate the `database-transaction-monitor` plugin.
2. Execute the `/txn-monitor` command to monitor lock wait times and identify deadlock patterns.

## Best Practices

- **Threshold Configuration**: Configure appropriate thresholds for long-running transactions and lock wait times to minimize false positives.
- **Alerting Integration**: Integrate transaction alerts with existing monitoring systems for timely notification and response.
- **Regular Review**: Regularly review transaction monitoring data to identify trends and proactively address potential performance issues.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide a comprehensive view of database health. It complements tools for query optimization and database schema design.