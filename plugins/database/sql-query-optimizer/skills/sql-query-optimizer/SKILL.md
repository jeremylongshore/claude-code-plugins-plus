---
name: optimizing-sql-queries
description: |
  This skill analyzes and optimizes SQL queries for improved performance. It identifies potential bottlenecks, suggests optimal indexes, and proposes query rewrites. Use this when the user mentions "optimize SQL query", "improve SQL performance", "SQL query optimization", "slow SQL query", or asks for help with "SQL indexing". The skill helps enhance database efficiency by analyzing query structure, recommending indexes, and reviewing execution plans.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to analyze SQL queries, identify performance bottlenecks, and suggest optimizations such as index creation or query rewriting. It leverages the sql-query-optimizer plugin to provide actionable recommendations for improving database performance.

## How It Works

1. **Query Input**: The user provides an SQL query to be optimized.
2. **Analysis**: The plugin analyzes the query structure, potential indexing issues, and execution plan (if available).
3. **Recommendations**: The plugin generates optimization suggestions, including index recommendations and query rewrites.

## When to Use This Skill

This skill activates when you need to:
- Optimize a slow-running SQL query.
- Identify missing or unused indexes in a database.
- Improve the performance of a database application.

## Examples

### Example 1: Optimizing a Slow Query

User request: "Optimize this SQL query: SELECT * FROM orders WHERE customer_id = 123 AND order_date < '2023-01-01';"

The skill will:
1. Analyze the provided SQL query.
2. Suggest creating an index on customer_id and order_date columns to improve query performance.

### Example 2: Finding Indexing Opportunities

User request: "I need help optimizing a query that filters on product_category and price.  Can you suggest any indexes?"

The skill will:
1. Analyze a hypothetical query based on the user's description.
2. Recommend a composite index on (product_category, price) to speed up filtering.

## Best Practices

- **Provide Full Queries**: Include the complete SQL query for accurate analysis.
- **Include EXPLAIN Output**: Providing the output of `EXPLAIN` can help the optimizer identify bottlenecks more effectively.
- **Test Recommendations**: Always test the suggested optimizations in a staging environment before applying them to production.

## Integration

This skill can be used in conjunction with other database management plugins to automate index creation and query rewriting based on the optimizer's suggestions.