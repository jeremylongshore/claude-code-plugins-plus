---
name: audit-log
description: Implement database audit logging
---
# Database Audit Logger

Track database changes for compliance and debugging.

## Audit Strategies

1. **Trigger-Based**: Database triggers on INSERT/UPDATE/DELETE
2. **Application-Level**: Log in application code
3. **CDC (Change Data Capture)**: Stream changes
4. **Database Logs**: Parse database transaction logs

## Audit Table Template

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  table_name VARCHAR(100) NOT NULL,
  operation VARCHAR(10) NOT NULL,
  old_data JSONB,
  new_data JSONB,
  user_id INTEGER,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger example
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (table_name, operation, old_data, new_data)
  VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## When Invoked

Generate audit logging implementation for compliance tracking.
