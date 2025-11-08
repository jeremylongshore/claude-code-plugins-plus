---
name: managing-database-partitions
description: |
  This skill enables Claude to design, implement, and manage table partitioning strategies for large databases. It is triggered when the user needs to optimize query performance, manage time-series data, or reduce maintenance windows for tables exceeding 100GB. Use this skill when asked to "create database partitions", "optimize database queries with partitioning", "manage large database tables", or when the user mentions "partitioning strategy", "data archival", or uses the command `/partition`. The skill helps automate partition maintenance and data lifecycle management. It focuses on database best practices and production-ready implementations.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the design, implementation, and management of database table partitioning strategies. It helps optimize query performance, manage time-series data, and reduce maintenance windows for massive datasets.

## How It Works

1. **Analyze Requirements**: Claude analyzes the user's request to understand the specific partitioning needs, including data size, query patterns, and maintenance requirements.
2. **Design Partitioning Strategy**: Based on the analysis, Claude designs an appropriate partitioning strategy (e.g., range, list, hash) and determines the optimal partition key.
3. **Implement Partitioning**: Claude generates the necessary SQL scripts or configuration files to implement the partitioning strategy on the target database.
4. **Optimize Queries**: Claude provides guidance on optimizing queries to take advantage of the partitioning scheme, including suggestions for partition pruning and index creation.

## When to Use This Skill

This skill activates when you need to:
- Manage tables exceeding 100GB with slow query performance.
- Implement time-series data archival strategies (IoT, logs, metrics).
- Optimize queries that filter by date ranges or specific values.
- Reduce database maintenance windows.

## Examples

### Example 1: Optimizing Time-Series Data

User request: "Create database partitions for my IoT sensor data to improve query performance."

The skill will:
1. Analyze the data schema and query patterns for the IoT sensor data.
2. Design a range-based partitioning strategy using the timestamp column as the partition key.
3. Generate SQL scripts to create partitioned tables and indexes.

### Example 2: Managing Large Order History Table

User request: "Implement table partitioning for my order history table to reduce maintenance window."

The skill will:
1. Analyze the size and growth rate of the order history table.
2. Design a list-based partitioning strategy based on order status or region.
3. Generate SQL scripts to create partitioned tables and migrate existing data.

## Best Practices

- **Partition Key Selection**: Choose a partition key that is frequently used in queries and evenly distributes data across partitions.
- **Partition Size**: Determine the optimal partition size based on query patterns and storage capacity.
- **Maintenance**: Implement automated partition maintenance tasks, such as creating new partitions and archiving old partitions.

## Integration

This skill can be integrated with other database management tools for monitoring partition performance and managing data lifecycle. It can also work with data migration tools to efficiently move data between partitions.