---
name: snowflake-policy-guardrails
description: |
  Implement Snowflake governance guardrails with network rules, session policies,
  authentication policies, and automated compliance checks.
  Use when enforcing security policies, implementing data governance,
  or configuring automated compliance for Snowflake.
  Trigger with phrases like "snowflake policy", "snowflake guardrails",
  "snowflake governance", "snowflake compliance", "snowflake enforce".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Policy & Guardrails

## Overview

Automated policy enforcement and governance guardrails using Snowflake-native features: network rules, authentication policies, session policies, and object-level governance.

## Instructions

### Step 1: Network Rules and Policies

```sql
-- Network rules (more granular than legacy network policies)
CREATE OR REPLACE NETWORK RULE corp_vpn_rule
  TYPE = IPV4
  MODE = INGRESS
  VALUE_LIST = ('203.0.113.0/24', '198.51.100.0/24');

CREATE OR REPLACE NETWORK RULE cloud_services_rule
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('api.company.com:443', 'events.company.com:443');

-- Create network policy using rules
CREATE OR REPLACE NETWORK POLICY prod_network_policy
  ALLOWED_NETWORK_RULE_LIST = (corp_vpn_rule)
  BLOCKED_NETWORK_RULE_LIST = ();

-- Apply at account level
ALTER ACCOUNT SET NETWORK_POLICY = prod_network_policy;

-- Or per-user (service accounts can have different rules)
ALTER USER svc_etl SET NETWORK_POLICY = prod_network_policy;
```

### Step 2: Authentication Policies

```sql
-- Require MFA for interactive users
CREATE OR REPLACE AUTHENTICATION POLICY interactive_auth
  MFA_AUTHENTICATION_METHODS = ('TOTP')
  CLIENT_TYPES = ('SNOWFLAKE_UI', 'SNOWSQL')
  SECURITY_INTEGRATIONS = ('saml_sso');

-- Service accounts: key pair only, no password
CREATE OR REPLACE AUTHENTICATION POLICY service_auth
  AUTHENTICATION_METHODS = ('KEYPAIR')
  CLIENT_TYPES = ('SNOWFLAKE_DRIVER')
  MFA_AUTHENTICATION_METHODS = ();

-- Apply policies
ALTER USER analyst_user SET AUTHENTICATION POLICY = interactive_auth;
ALTER USER svc_etl SET AUTHENTICATION POLICY = service_auth;
```

### Step 3: Session Policies

```sql
-- Enforce session timeout and idle limits
CREATE OR REPLACE SESSION POLICY prod_session_policy
  SESSION_IDLE_TIMEOUT_MINS = 30
  SESSION_UI_IDLE_TIMEOUT_MINS = 15;

-- Apply to account
ALTER ACCOUNT SET SESSION POLICY = prod_session_policy;
```

### Step 4: Statement-Level Guardrails

```sql
-- Prevent runaway queries
ALTER WAREHOUSE PROD_WH SET
  STATEMENT_TIMEOUT_IN_SECONDS = 3600,          -- 1 hour max
  STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = 600;     -- 10 min max queue

-- Prevent accidental full table operations
-- Use row access policies + stored procedures instead of raw access

-- Example: Safe delete procedure with audit
CREATE OR REPLACE PROCEDURE safe_delete(
  table_name VARCHAR, where_clause VARCHAR, max_rows INTEGER DEFAULT 10000
)
  RETURNS VARCHAR
  LANGUAGE SQL
AS
$$
BEGIN
  -- Count affected rows first
  LET count_sql VARCHAR := 'SELECT COUNT(*) FROM ' || :table_name || ' WHERE ' || :where_clause;
  LET affected_rows INTEGER;
  EXECUTE IMMEDIATE :count_sql INTO :affected_rows;

  IF (:affected_rows > :max_rows) THEN
    RETURN 'BLOCKED: Would delete ' || :affected_rows || ' rows (max: ' || :max_rows || ')';
  END IF;

  -- Audit log
  INSERT INTO audit.delete_log (table_name, where_clause, row_count, executed_by, executed_at)
  VALUES (:table_name, :where_clause, :affected_rows, CURRENT_USER(), CURRENT_TIMESTAMP());

  -- Execute delete
  EXECUTE IMMEDIATE 'DELETE FROM ' || :table_name || ' WHERE ' || :where_clause;
  RETURN 'Deleted ' || :affected_rows || ' rows from ' || :table_name;
END;
$$;

-- Usage: CALL safe_delete('orders', 'order_date < ''2024-01-01''', 50000);
```

### Step 5: Data Governance Tags and Policies

```sql
-- Create governance taxonomy
CREATE TAG IF NOT EXISTS data_domain ALLOWED_VALUES 'finance', 'marketing', 'engineering', 'hr';
CREATE TAG IF NOT EXISTS data_owner;
CREATE TAG IF NOT EXISTS retention_days;

-- Apply tags to databases/schemas
ALTER DATABASE PROD_DW SET TAG data_domain = 'finance';
ALTER SCHEMA PROD_DW.GOLD SET TAG data_owner = 'analytics-team@company.com';
ALTER TABLE PROD_DW.GOLD.REVENUE SET TAG retention_days = '2555';  -- 7 years

-- Automated compliance report
SELECT
  tag_name, tag_value, object_database, object_schema, object_name, column_name
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
  'PROD_DW.GOLD.REVENUE', 'TABLE'
));

-- Find untagged tables (governance gap)
SELECT t.table_catalog, t.table_schema, t.table_name, t.row_count
FROM INFORMATION_SCHEMA.TABLES t
LEFT JOIN TABLE(INFORMATION_SCHEMA.TAG_REFERENCES(
  t.table_catalog || '.' || t.table_schema || '.' || t.table_name, 'TABLE'
)) tr ON TRUE
WHERE tr.tag_name IS NULL
  AND t.table_schema NOT IN ('INFORMATION_SCHEMA')
ORDER BY t.row_count DESC NULLS LAST;
```

### Step 6: CI/CD Policy Checks

```yaml
# .github/workflows/snowflake-governance.yml
name: Snowflake Governance Check

on:
  pull_request:
    paths: ['sql/**', 'migrations/**']

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for dangerous SQL patterns
        run: |
          # No DROP DATABASE/SCHEMA without IF EXISTS
          if grep -rn "DROP DATABASE\|DROP SCHEMA" sql/ | grep -v "IF EXISTS"; then
            echo "ERROR: DROP without IF EXISTS detected"
            exit 1
          fi

          # No GRANT ... TO PUBLIC
          if grep -rn "TO ROLE PUBLIC\|TO PUBLIC" sql/; then
            echo "ERROR: Granting to PUBLIC role is not allowed"
            exit 1
          fi

          # No hardcoded passwords
          if grep -rn "PASSWORD = " sql/ | grep -v "PASSWORD = \$"; then
            echo "ERROR: Hardcoded password detected"
            exit 1
          fi

          # All tables must have DATA_RETENTION_TIME_IN_DAYS
          for f in $(grep -rl "CREATE TABLE\|CREATE OR REPLACE TABLE" sql/); do
            if ! grep -q "DATA_RETENTION_TIME_IN_DAYS" "$f"; then
              echo "WARNING: $f missing explicit retention policy"
            fi
          done

          echo "All governance checks passed"

      - name: Validate SchemaChange naming
        run: |
          # Ensure migration files follow V{version}__{description}.sql
          for f in migrations/V*.sql; do
            if ! echo "$f" | grep -qE 'V[0-9]+\.[0-9]+\.[0-9]+__[a-z_]+\.sql'; then
              echo "ERROR: Invalid migration filename: $f"
              echo "Expected: V{major}.{minor}.{patch}__{description}.sql"
              exit 1
            fi
          done
```

### Step 7: Automated Compliance Audit

```sql
-- Weekly compliance audit stored procedure
CREATE OR REPLACE PROCEDURE run_compliance_audit()
  RETURNS TABLE (check_name VARCHAR, status VARCHAR, details VARCHAR)
  LANGUAGE SQL
AS
$$
  -- Check 1: No users with ACCOUNTADMIN default role
  SELECT 'accountadmin_check' AS check_name,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
    COUNT(*) || ' users with ACCOUNTADMIN default' AS details
  FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
  WHERE default_role = 'ACCOUNTADMIN' AND disabled = 'false'

  UNION ALL

  -- Check 2: Network policy active
  SELECT 'network_policy_check',
    CASE WHEN value != '' THEN 'PASS' ELSE 'FAIL' END,
    'Account network policy: ' || COALESCE(value, 'NONE')
  FROM TABLE(FLATTEN(INPUT => PARSE_JSON(
    SYSTEM$GET_SNOWFLAKE_PLATFORM_INFO()
  )))
  WHERE key = 'network_policy'

  UNION ALL

  -- Check 3: MFA adoption
  SELECT 'mfa_check',
    CASE WHEN COUNT_IF(has_mfa = 'true') * 100 / COUNT(*) >= 90 THEN 'PASS' ELSE 'WARN' END,
    COUNT_IF(has_mfa = 'true') || '/' || COUNT(*) || ' users have MFA'
  FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
  WHERE disabled = 'false';
$$;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Network policy blocks legitimate user | IP not in allowlist | Add IP range to network rule |
| Auth policy prevents login | Wrong client type in policy | Adjust CLIENT_TYPES |
| Session timeout too aggressive | Short idle timeout | Increase SESSION_IDLE_TIMEOUT_MINS |
| CI check false positive | SQL pattern too broad | Refine regex pattern |

## Resources

- [Network Policies](https://docs.snowflake.com/en/user-guide/network-policies)
- [Authentication Policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Data Governance](https://docs.snowflake.com/en/guides-overview-govern)
- [Object Tagging](https://docs.snowflake.com/en/user-guide/object-tagging)

## Next Steps

For architecture blueprints, see `snowflake-architecture-variants`.
