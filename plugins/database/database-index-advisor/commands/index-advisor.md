---
description: Analyze and recommend database indexes
---

# Database Index Advisor

Analyze query patterns and recommend optimal indexes.

## Index Analysis

1. **Identify Missing Indexes**: WHERE, JOIN, ORDER BY columns
2. **Find Unused Indexes**: Remove overhead
3. **Composite Index Opportunities**: Multi-column indexes
4. **Covering Indexes**: Include query columns

## Example Recommendation

```sql
-- Query analysis
SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';

-- Recommended index
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Impact: Sequential scan → Index scan (100x faster)
```

## When Invoked

Provide index recommendations based on query patterns and EXPLAIN output.
