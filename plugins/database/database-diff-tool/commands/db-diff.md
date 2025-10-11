---
description: Compare database schemas
---

# Database Diff Tool

Compare two database schemas and generate migration scripts.

## Comparison Features

1. **Table Differences**: Added, removed, modified tables
2. **Column Changes**: Type, constraint, default changes
3. **Index Differences**: New or dropped indexes
4. **Constraint Changes**: Foreign keys, unique constraints

## Example Output

```sql
-- Differences found:
-- 1. Table 'users': Column 'phone' added
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 2. Table 'orders': Index 'idx_status' missing
CREATE INDEX idx_orders_status ON orders(status);

-- 3. Table 'products': Column 'price' type changed
ALTER TABLE products ALTER COLUMN price TYPE DECIMAL(12,2);
```

## When Invoked

Generate schema comparison and migration scripts.
