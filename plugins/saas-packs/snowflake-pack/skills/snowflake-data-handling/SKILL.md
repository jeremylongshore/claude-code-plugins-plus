---
name: snowflake-data-handling
description: |
  Implement Snowflake data governance with masking policies, row access policies,
  tagging, and GDPR/CCPA compliance patterns.
  Use when handling PII, implementing column masking, configuring data classification,
  or ensuring compliance with privacy regulations in Snowflake.
  Trigger with phrases like "snowflake data governance", "snowflake masking",
  "snowflake PII", "snowflake GDPR", "snowflake row access policy", "snowflake tags".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Data Handling

## Overview

Implement data governance in Snowflake using column-level masking policies, row access policies, object tagging, and data classification for GDPR/CCPA compliance.

## Prerequisites

- Enterprise Edition or higher (for masking and row access policies)
- SECURITYADMIN or ACCOUNTADMIN role
- Understanding of GDPR/CCPA data subject rights

## Instructions

### Step 1: Data Classification with Tags

```sql
-- Create tag taxonomy
CREATE TAG IF NOT EXISTS pii_type
  ALLOWED_VALUES 'email', 'phone', 'ssn', 'name', 'address';

CREATE TAG IF NOT EXISTS data_sensitivity
  ALLOWED_VALUES 'public', 'internal', 'confidential', 'restricted';

-- Apply tags to columns
ALTER TABLE users MODIFY COLUMN email SET TAG pii_type = 'email';
ALTER TABLE users MODIFY COLUMN phone SET TAG pii_type = 'phone';
ALTER TABLE users MODIFY COLUMN name SET TAG pii_type = 'name';
ALTER TABLE users MODIFY COLUMN email SET TAG data_sensitivity = 'confidential';

-- Find all tagged columns
SELECT * FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES(
  'users', 'TABLE'
));

-- Discover PII with Snowflake's automatic classification (Enterprise+)
SELECT *
FROM TABLE(
  INFORMATION_SCHEMA.EXTRACT_SEMANTIC_CATEGORIES('users')
);
```

### Step 2: Column-Level Masking Policies

```sql
-- Dynamic masking — shows real data to privileged roles, masked to others
CREATE OR REPLACE MASKING POLICY email_mask AS (val STRING)
  RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('DATA_ENGINEER', 'SYSADMIN') THEN val
    WHEN CURRENT_ROLE() = 'DATA_ANALYST' THEN
      REGEXP_REPLACE(val, '.+@', '***@')  -- Show domain only
    ELSE '***MASKED***'
  END;

CREATE OR REPLACE MASKING POLICY phone_mask AS (val STRING)
  RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('DATA_ENGINEER', 'SYSADMIN') THEN val
    ELSE CONCAT('***-***-', RIGHT(val, 4))  -- Show last 4 digits
  END;

CREATE OR REPLACE MASKING POLICY ssn_mask AS (val STRING)
  RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('SYSADMIN') THEN val
    ELSE '***-**-' || RIGHT(val, 4)
  END;

-- Apply masking policies to columns
ALTER TABLE users MODIFY COLUMN email SET MASKING POLICY email_mask;
ALTER TABLE users MODIFY COLUMN phone SET MASKING POLICY phone_mask;

-- Tag-based masking (apply policy to all columns with a tag)
ALTER TAG pii_type SET MASKING POLICY email_mask;
-- Now ALL columns tagged pii_type='email' are automatically masked
```

### Step 3: Row Access Policies

```sql
-- Row-level security — users only see their own department's data
CREATE OR REPLACE ROW ACCESS POLICY department_access AS (department_col VARCHAR)
  RETURNS BOOLEAN ->
  CURRENT_ROLE() = 'SYSADMIN'
  OR department_col = CURRENT_ROLE()  -- Role name matches department
  OR EXISTS (
    SELECT 1 FROM access_grants
    WHERE user_name = CURRENT_USER()
      AND department = department_col
  );

-- Apply to table
ALTER TABLE employees ADD ROW ACCESS POLICY department_access ON (department);

-- Verify: analyst role only sees their department
USE ROLE ANALYST_ROLE;
SELECT * FROM employees;  -- Only rows matching their department
```

### Step 4: GDPR Data Subject Rights

```sql
-- Right to Access (DSAR): Export all user data
CREATE OR REPLACE PROCEDURE export_user_data(user_email VARCHAR)
  RETURNS TABLE (source VARCHAR, data VARIANT)
  LANGUAGE SQL
AS
$$
  SELECT 'users' AS source, OBJECT_CONSTRUCT(*) AS data
  FROM users WHERE email = user_email
  UNION ALL
  SELECT 'orders', OBJECT_CONSTRUCT(*)
  FROM orders WHERE customer_email = user_email
  UNION ALL
  SELECT 'events', OBJECT_CONSTRUCT(*)
  FROM events WHERE user_email = user_email
$$;

-- Right to Erasure: Delete all user data
CREATE OR REPLACE PROCEDURE delete_user_data(user_email VARCHAR)
  RETURNS VARCHAR
  LANGUAGE SQL
AS
$$
BEGIN
  -- Delete from all tables containing user data
  DELETE FROM events WHERE user_email = :user_email;
  DELETE FROM orders WHERE customer_email = :user_email;
  DELETE FROM users WHERE email = :user_email;

  -- Audit log (must retain for compliance)
  INSERT INTO gdpr_audit_log (action, subject_email, executed_at, executed_by)
  VALUES ('ERASURE', :user_email, CURRENT_TIMESTAMP(), CURRENT_USER());

  RETURN 'Deletion complete for ' || :user_email;
END;
$$;

-- Right to Rectification
UPDATE users SET name = 'New Name' WHERE email = 'user@example.com';
INSERT INTO gdpr_audit_log (action, subject_email, executed_at, executed_by)
VALUES ('RECTIFICATION', 'user@example.com', CURRENT_TIMESTAMP(), CURRENT_USER());
```

### Step 5: Data Retention and Cleanup

```sql
-- Automated data retention with tasks
CREATE OR REPLACE TASK enforce_retention
  WAREHOUSE = ADMIN_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'  -- 2 AM UTC daily
AS
BEGIN
  -- Delete audit logs older than 7 years
  DELETE FROM audit_logs
  WHERE created_at < DATEADD(years, -7, CURRENT_TIMESTAMP());

  -- Delete session logs older than 90 days
  DELETE FROM session_logs
  WHERE created_at < DATEADD(days, -90, CURRENT_TIMESTAMP());

  -- Anonymize old order data (keep for analytics, remove PII)
  UPDATE orders SET
    customer_email = SHA2(customer_email),
    customer_name = 'ANONYMIZED'
  WHERE order_date < DATEADD(years, -2, CURRENT_DATE())
    AND customer_name != 'ANONYMIZED';
END;

ALTER TASK enforce_retention RESUME;
```

### Step 6: Audit Trail

```sql
-- Query access history — who accessed what
SELECT user_name, query_text, start_time,
       direct_objects_accessed
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE start_time >= DATEADD(days, -7, CURRENT_TIMESTAMP())
  AND ARRAY_CONTAINS('USERS'::VARIANT,
    TRANSFORM(direct_objects_accessed, x -> x:objectName))
ORDER BY start_time DESC;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Masking policy error on query | Policy function error | Test with `SELECT email_mask('test@test.com')` |
| Row access blocks all rows | Policy too restrictive | Check CURRENT_ROLE() logic |
| Tag not found | Wrong scope | Ensure tag is in same or parent schema |
| GDPR deletion incomplete | Foreign key dependencies | Delete child records first |

## Resources

- [Masking Policies](https://docs.snowflake.com/en/user-guide/tag-based-masking-policies)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Data Classification](https://docs.snowflake.com/en/user-guide/governance-classify-concepts)
- [Access History](https://docs.snowflake.com/en/sql-reference/account-usage/access_history)

## Next Steps

For enterprise RBAC, see `snowflake-enterprise-rbac`.
