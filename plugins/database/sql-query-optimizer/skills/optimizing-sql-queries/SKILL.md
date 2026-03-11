---
name: optimizing-sql-queries
description: |
  Execute use when you need to work with query optimization.
  This skill provides query performance analysis with comprehensive guidance and automation.
  Trigger with phrases like "optimize queries", "analyze performance",
  or "improve query speed".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# SQL Query Optimizer

## Overview

Rewrite SQL queries for maximum performance by eliminating anti-patterns, restructuring JOINs, leveraging window functions, and applying database-specific optimizations for PostgreSQL and MySQL. This skill takes a slow query and its execution plan as input and produces an optimized version with measurable improvement, along with any supporting index changes needed.

## Prerequisites

- The slow SQL query text and its current execution time
- `EXPLAIN ANALYZE` output (PostgreSQL) or `EXPLAIN FORMAT=JSON` output (MySQL) for the query
- Table row counts and approximate data distribution for involved tables
- `psql` or `mysql` CLI for testing rewrites
- Knowledge of the application's acceptable result ordering and NULL handling requirements

## Instructions

1. Examine the original query structure and identify common anti-patterns:
   - `SELECT *` instead of specific columns (forces unnecessary I/O)
   - `WHERE column IN (SELECT ...)` that can be rewritten as `JOIN` or `EXISTS`
   - `DISTINCT` used to mask duplicate rows from incorrect JOINs
   - Functions applied to indexed columns in WHERE clauses (`WHERE UPPER(name) = 'FOO'`)
   - `OR` conditions that prevent index usage
   - `NOT IN` with nullable columns (produces wrong results and poor plans)

2. Analyze the execution plan to identify the most expensive operation nodes. Focus optimization effort on the node consuming the most time or processing the most rows.

3. Rewrite subqueries as JOINs where possible. Convert correlated subqueries to lateral joins (PostgreSQL) or derived tables. Replace `IN (SELECT ...)` with `EXISTS (SELECT 1 ...)` for existence checks since EXISTS short-circuits after the first match.

4. Optimize JOIN ordering for the query planner: place the most selective table (fewest matching rows after WHERE filters) as the driving table. Use `JOIN` hints only as a last resort since the optimizer usually picks the correct order with accurate statistics.

5. Replace multiple OR conditions on the same column with `IN (...)`: change `WHERE status = 'active' OR status = 'pending'` to `WHERE status IN ('active', 'pending')`. For OR across different columns, consider UNION ALL of two simpler queries.

6. Apply window functions to replace self-joins or correlated subqueries. Use `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` for top-N-per-group queries instead of `GROUP BY` with subqueries.

7. Leverage CTEs (Common Table Expressions) for readability but be aware that PostgreSQL versions before 12 materialize all CTEs. For performance-critical queries on older PostgreSQL, inline the CTE as a subquery.

8. Optimize aggregation queries by filtering before grouping (`WHERE` is more efficient than `HAVING` for non-aggregate conditions), using partial indexes for filtered aggregates, and considering materialized views for expensive recurring aggregations.

9. Test the rewritten query with `EXPLAIN ANALYZE` and compare execution time, row estimates vs. actuals, and buffer usage against the original. The optimized version should show fewer rows processed, index scans replacing sequential scans, and lower total execution time.

10. Document each change made, the reason for the change, and the measured impact so the development team understands and can apply similar patterns to future queries.

## Output

- **Optimized SQL query** with comments explaining each structural change
- **Before/after execution plans** showing performance improvement
- **Index recommendations** (CREATE INDEX statements) needed to support the optimized query
- **Anti-pattern report** listing issues found in the original query with explanations
- **Performance metrics comparison** (execution time, rows scanned, buffer hits)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Rewritten query returns different results | JOIN type change (INNER vs LEFT) or NULL handling difference | Verify result sets match with `EXCEPT` query; preserve original JOIN types; handle NULLs explicitly with `COALESCE` |
| Optimized query slower than original | Statistics outdated causing planner to choose wrong plan | Run `ANALYZE` on involved tables; compare `estimated rows` vs `actual rows` in EXPLAIN; consider `SET enable_seqscan = off` to test alternative plans |
| CTE materialization hurting performance | PostgreSQL <12 materializes CTEs preventing predicate pushdown | Inline the CTE as a subquery; upgrade PostgreSQL; add `AS NOT MATERIALIZED` hint in PostgreSQL 12+ |
| Window function query uses excessive memory | Large partition sizes with ORDER BY in window specification | Add `LIMIT` to outer query; use index matching the PARTITION BY and ORDER BY columns; increase `work_mem` for the session |
| UNION ALL produces duplicates | Overlapping conditions in constituent queries | Add mutually exclusive WHERE conditions to each branch; or use UNION (with dedup cost) if overlap is unavoidable |

## Examples

**Converting correlated subquery to JOIN**: Original: `SELECT * FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE region = 'US')` taking 8 seconds with sequential scan on orders. Rewrite: `SELECT o.* FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.region = 'US'` using index on `orders.customer_id` reduces to 120ms.

**Top-N per group with window function**: Original uses self-join to find the 3 most recent orders per customer (15 seconds). Rewrite: `SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn FROM orders) sub WHERE rn <= 3` with index on `(customer_id, created_at DESC)` completes in 400ms.

**Eliminating DISTINCT from incorrect JOIN**: `SELECT DISTINCT o.* FROM orders o JOIN line_items li ON o.id = li.order_id WHERE li.amount > 100` scans all line items. Rewrite: `SELECT o.* FROM orders o WHERE EXISTS (SELECT 1 FROM line_items li WHERE li.order_id = o.id AND li.amount > 100)` eliminates the deduplication step and halves execution time.

## Resources

- PostgreSQL query planning: https://www.postgresql.org/docs/current/planner-optimizer.html
- MySQL query optimization: https://dev.mysql.com/doc/refman/8.0/en/optimization.html
- SQL anti-patterns reference: https://use-the-index-luke.com/sql/where-clause
- Window functions tutorial: https://www.postgresql.org/docs/current/tutorial-window.html
- Modern SQL features: https://modern-sql.com/
