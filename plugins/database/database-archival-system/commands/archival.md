---
description: Archive old database records
---

# Database Archival System

Move old data to archive tables or storage.

## Archival Strategies

1. **Archive Tables**: Move to separate tables
2. **Cold Storage**: Move to S3/blob storage
3. **Data Retention**: Automated cleanup
4. **Compliance**: Meet retention requirements

## Archival Script Example

```sql
-- Create archive table
CREATE TABLE orders_archive (LIKE orders INCLUDING ALL);

-- Move old records
INSERT INTO orders_archive
SELECT * FROM orders
WHERE created_at < CURRENT_DATE - INTERVAL '2 years';

-- Delete archived records
DELETE FROM orders
WHERE created_at < CURRENT_DATE - INTERVAL '2 years';
```

## When Invoked

Implement data archival and retention policies.
