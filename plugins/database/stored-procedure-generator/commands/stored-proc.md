---
description: Generate stored procedures and functions
---

# Stored Procedure Generator

Create database stored procedures for business logic.

## Use Cases

1. **Complex Calculations**: Multi-step computations
2. **Data Validation**: Enforce business rules
3. **Batch Operations**: Process multiple rows
4. **Triggers**: Automated actions on changes

## Example (PostgreSQL Function)

```sql
CREATE OR REPLACE FUNCTION calculate_order_total(order_id INTEGER)
RETURNS DECIMAL(10,2) AS $$
DECLARE
  total DECIMAL(10,2);
BEGIN
  SELECT SUM(quantity * price)
  INTO total
  FROM order_items
  WHERE order_id = order_id;

  RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql;
```

## When Invoked

Generate stored procedures based on business logic requirements.
