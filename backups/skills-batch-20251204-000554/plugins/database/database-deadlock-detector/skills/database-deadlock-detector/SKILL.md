---
name: detecting-database-deadlocks
description: |
  This skill uses the database-deadlock-detector plugin to detect, analyze, and prevent database deadlocks. It monitors database lock contention, analyzes transaction patterns, and suggests resolution strategies. Use this skill when the user asks to "detect database deadlocks", "analyze deadlock causes", "monitor database locks", or any requests related to database deadlock prevention and resolution. This skill is particularly useful for production database systems experiencing recurring deadlock issues. The plugin's command `/deadlock` is triggered by these requests.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill enables Claude to automatically detect, analyze, and prevent database deadlocks in database systems. It provides insights into transaction patterns, lock contention, and suggests optimization strategies to minimize deadlock occurrences.

## How It Works

1. **Initiate Deadlock Detection**: Claude recognizes the user's request related to database deadlocks and activates the database-deadlock-detector plugin.
2. **Execute Deadlock Analysis**: The plugin executes the `/deadlock` command to analyze the database for current and potential deadlocks.
3. **Report Findings**: The plugin generates a report summarizing detected deadlocks, their causes, and potential resolution strategies.

## When to Use This Skill

This skill activates when you need to:
- Investigate recurring deadlock issues in production.
- Implement proactive deadlock detection and alerting.
- Analyze transaction patterns causing deadlocks.

## Examples

### Example 1: Investigating Production Deadlocks

User request: "Investigate recent deadlocks in the production database."

The skill will:
1. Activate the database-deadlock-detector plugin and run the `/deadlock` command.
2. Generate a report detailing recent deadlock events, involved transactions, and potential root causes.

### Example 2: Implementing Proactive Deadlock Monitoring

User request: "Set up deadlock monitoring for the database."

The skill will:
1. Activate the database-deadlock-detector plugin and run the `/deadlock` command with monitoring configurations.
2. Configure alerts to notify when deadlocks are detected, including details on the involved transactions.

## Best Practices

- **Database Access**: Ensure the plugin has the necessary database access and permissions to perform deadlock detection.
- **Configuration**: Properly configure the plugin with the correct database connection details.
- **Regular Monitoring**: Schedule regular deadlock detection runs to proactively identify and address potential issues.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide a comprehensive view of database performance and stability. It can also be used in conjunction with database optimization tools to implement recommended resolution strategies.