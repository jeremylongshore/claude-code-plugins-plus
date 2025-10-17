---
name: Analyzing Database Indexes
description: |
  This skill uses the database-index-advisor plugin to analyze query patterns and recommend optimal database indexes. It identifies missing indexes to improve query performance and unused indexes that can be removed to save storage and improve write performance. Use this skill when the user asks to "analyze database indexes", "optimize slow queries", "find missing indexes", "remove unused indexes", or requests help with "database index optimization". The plugin analyzes database workloads, detects potential indexing issues, and provides actionable recommendations for indexing strategies.
---

## Overview

This skill empowers Claude to analyze database workloads, identify suboptimal or missing indexes, and suggest improvements to enhance database performance. It leverages the database-index-advisor plugin to provide concrete recommendations for indexing strategies, including identifying unused indexes for removal.

## How It Works

1. **Initiate Analysis**: The skill activates the database-index-advisor plugin.
2. **Workload Analysis**: The plugin analyzes the database's query workload and existing index configurations.
3. **Recommendation Generation**: The plugin identifies missing index opportunities and unused indexes, generating a report with suggested actions.

## When to Use This Skill

This skill activates when you need to:
- Optimize slow-running database queries.
- Identify potential performance bottlenecks related to missing indexes.
- Reclaim storage space by identifying and removing unused indexes.

## Examples

### Example 1: Optimizing a Slow Query

User request: "My orders table query is running slowly. Can you help optimize it?"

The skill will:
1. Activate the database-index-advisor plugin.
2. Analyze the query patterns against the orders table.
3. Recommend creating a specific index on the orders table to improve query performance.

### Example 2: Identifying Unused Indexes

User request: "Can you help me identify and remove any unused indexes in my database?"

The skill will:
1. Activate the database-index-advisor plugin.
2. Analyze the existing indexes and their usage patterns.
3. Generate a report listing unused indexes that can be safely removed.

## Best Practices

- **Database Connection**: Ensure the database connection is properly configured for the plugin to access the database.
- **Permissions**: Grant the plugin the necessary permissions to analyze query patterns and retrieve index information.
- **Impact Assessment**: Review the recommended index changes and assess their potential impact on other queries before applying them.

## Integration

This skill can be used in conjunction with other database management plugins to automate index creation and removal based on the advisor's recommendations. It also integrates with monitoring tools to track the performance impact of the applied index changes.