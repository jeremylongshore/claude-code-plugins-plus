---
name: Monitoring Database Health
description: |
  This skill enables Claude to monitor database health using real-time metrics, predictive alerts, and automated remediation. It's designed for production-grade database health monitoring for PostgreSQL and MySQL, detecting performance degradation, resource exhaustion, and replication issues. Use this skill when the user requests to monitor database health, check database performance, receive database alerts, or automate database remediation. The skill is triggered by phrases like "check database health", "monitor database performance", "database health check", or "/health-check".
---

## Overview

This skill empowers Claude to proactively monitor the health of your databases. It provides real-time metrics, predictive alerts, and automated remediation capabilities to ensure optimal performance and uptime.

## How It Works

1. **Initiate Health Check**: The user requests a database health check via natural language or the `/health-check` command.
2. **Collect Metrics**: The plugin gathers real-time metrics from the specified database (PostgreSQL or MySQL), including connection counts, query performance, resource utilization, and replication status.
3. **Analyze and Alert**: The collected metrics are analyzed against predefined thresholds and historical data to identify potential issues. Predictive alerts are generated for anomalies.
4. **Provide Report**: A comprehensive health report is provided, detailing the current status, potential issues, and recommended remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Check the current health status of a database.
- Monitor database performance for potential bottlenecks.
- Receive alerts about potential database issues before they impact production.

## Examples

### Example 1: Checking Database Performance

User request: "Check the health of my PostgreSQL database."

The skill will:
1. Connect to the PostgreSQL database.
2. Collect metrics on CPU usage, memory consumption, disk I/O, connection counts, and query execution times.
3. Analyze the collected data and generate a report highlighting any performance bottlenecks or potential issues.

### Example 2: Setting Up Monitoring for a MySQL Database

User request: "Monitor the health of my MySQL database and alert me if CPU usage exceeds 80%."

The skill will:
1. Connect to the MySQL database.
2. Configure monitoring to track CPU usage, memory consumption, disk I/O, and connection counts.
3. Set up an alert that triggers if CPU usage exceeds 80%.

## Best Practices

- **Database Credentials**: Ensure that the plugin has the necessary credentials to access the database.
- **Alert Thresholds**: Customize alert thresholds to match the specific needs of your application and infrastructure.
- **Regular Monitoring**: Schedule regular health checks to proactively identify and address potential issues.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide a comprehensive view of your infrastructure's health.