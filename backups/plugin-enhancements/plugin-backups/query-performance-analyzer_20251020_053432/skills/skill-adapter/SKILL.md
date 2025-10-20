---
name: Analyzing Query Performance
description: |
  This skill enables Claude to analyze and optimize database query performance. It activates when the user discusses query performance issues, provides an EXPLAIN plan, or asks for optimization recommendations. The skill leverages the query-performance-analyzer plugin to interpret EXPLAIN plans, identify performance bottlenecks (e.g., slow queries, missing indexes), and suggest specific optimization strategies. It is useful for improving database query execution speed and resource utilization.
---

## Overview

This skill empowers Claude to act as a database performance expert. By analyzing EXPLAIN plans and query metrics, Claude can pinpoint inefficiencies and recommend targeted improvements to database queries.

## How It Works

1. **Receive Input**: The user provides an EXPLAIN plan, a slow query, or a description of a performance problem.
2. **Analyze Performance**: The query-performance-analyzer plugin analyzes the provided information, identifying potential bottlenecks, such as full table scans, missing indexes, or inefficient join operations.
3. **Provide Recommendations**: The plugin generates specific optimization recommendations, including suggesting new indexes, rewriting queries, or adjusting database configuration parameters.

## When to Use This Skill

This skill activates when you need to:
- Analyze the EXPLAIN plan of a slow-running query.
- Identify performance bottlenecks in a database query.
- Obtain recommendations for optimizing database query performance.

## Examples

### Example 1: Analyzing a Slow Query

User request: "Here's the EXPLAIN plan for my slow query. Can you help me optimize it? ```EXPLAIN SELECT * FROM orders WHERE customer_id = 123 AND order_date > '2023-01-01';```"

The skill will:
1. Analyze the provided EXPLAIN plan using the query-performance-analyzer plugin.
2. Identify potential issues, such as a missing index on `customer_id` or `order_date`, and suggest creating appropriate indexes.

### Example 2: Identifying a Bottleneck

User request: "My query is taking a long time. It's a simple SELECT statement, but it's still slow. What could be the problem?"

The skill will:
1. Prompt the user to provide the EXPLAIN plan for the query.
2. Analyze the EXPLAIN plan and identify potential bottlenecks, such as a full table scan or an inefficient join. It might suggest creating an index or rewriting the query to use a more efficient join algorithm.

## Best Practices

- **Provide Complete Information**: Include the full EXPLAIN plan and the query itself for the most accurate analysis.
- **Describe the Problem**: Clearly articulate the performance issue you're experiencing (e.g., slow query, high CPU usage).
- **Test Recommendations**: After implementing the suggested optimizations, re-run the EXPLAIN plan to verify the improvements.

## Integration

This skill integrates well with other database tools and plugins within the Claude Code ecosystem. For example, it can be used in conjunction with a database schema explorer to identify potential indexing opportunities or with a query builder to rewrite inefficient queries.