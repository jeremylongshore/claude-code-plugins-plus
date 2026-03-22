---
name: clickhouse-enterprise-rbac
description: |
  Configure ClickHouse enterprise RBAC — SQL-based users, roles, row policies,
  column-level grants, and quota management.
  Use when setting up multi-user access control, implementing tenant isolation,
  or configuring enterprise security for ClickHouse.
  Trigger: "clickhouse RBAC", "clickhouse roles", "clickhouse permissions",
  "clickhouse row policy", "clickhouse enterprise access", "clickhouse GRANT".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Enterprise RBAC

## Overview

Implement enterprise-grade role-based access control in ClickHouse using SQL-based
user management, hierarchical roles, row-level policies, and quotas.

## Prerequisites

- ClickHouse with `access_management = 1` enabled (default in Cloud)
- Admin user with `GRANT OPTION`

## Instructions

### Step 1: Create Users with Authentication

```sql
-- SHA256 password (standard)
CREATE USER app_backend
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics
    HOST IP '10.0.0.0/8'           -- Restrict to VPC
    SETTINGS max_memory_usage = 10000000000,   -- 10GB per query
             max_execution_time = 60;          -- 60s timeout

-- Double SHA1 (MySQL wire protocol compatible)
CREATE USER legacy_app
    IDENTIFIED WITH double_sha1_password BY 'password'
    DEFAULT DATABASE analytics;

-- bcrypt (strongest, slowest — use for admin accounts)
CREATE USER admin_user
    IDENTIFIED WITH bcrypt_password BY 'admin-password';

-- Verify user was created
SHOW CREATE USER app_backend;
SELECT name, host_ip, default_database FROM system.users;
```

### Step 2: Create Role Hierarchy

```sql
-- Base roles (leaf-level permissions)
CREATE ROLE data_reader;
GRANT SELECT ON analytics.* TO data_reader;

CREATE ROLE data_writer;
GRANT INSERT ON analytics.* TO data_writer;

CREATE ROLE schema_manager;
GRANT CREATE TABLE, ALTER TABLE, DROP TABLE ON analytics.* TO schema_manager;

-- Composite roles (inherit from base roles)
CREATE ROLE analyst;
GRANT data_reader TO analyst;
-- Analysts can also create temporary tables for ad-hoc work
GRANT CREATE TEMPORARY TABLE ON *.* TO analyst;

CREATE ROLE developer;
GRANT data_reader, data_writer TO developer;

CREATE ROLE platform_admin;
GRANT data_reader, data_writer, schema_manager TO platform_admin;
GRANT SYSTEM RELOAD, SYSTEM FLUSH LOGS ON *.* TO platform_admin;

-- Assign roles to users
GRANT analyst TO app_backend;         -- Read-only
GRANT developer TO app_backend;       -- Read + write
GRANT platform_admin TO admin_user;   -- Full access

-- Set default role (active when user connects)
SET DEFAULT ROLE developer TO app_backend;

-- Verify the full permission chain
SHOW GRANTS FOR app_backend;
SHOW ACCESS;  -- All users, roles, policies
```

### Step 3: Row-Level Security

```sql
-- Multi-tenant isolation: each user sees only their tenant's data
CREATE USER tenant_acme
    IDENTIFIED WITH sha256_password BY 'pass'
    DEFAULT DATABASE analytics;

CREATE USER tenant_globex
    IDENTIFIED WITH sha256_password BY 'pass'
    DEFAULT DATABASE analytics;

-- Row policy: restrict by tenant_id
CREATE ROW POLICY acme_isolation ON analytics.events
    FOR SELECT
    USING tenant_id = 1
    TO tenant_acme;

CREATE ROW POLICY globex_isolation ON analytics.events
    FOR SELECT
    USING tenant_id = 2
    TO tenant_globex;

-- Admin sees all rows (permissive policy)
CREATE ROW POLICY admin_all ON analytics.events
    FOR SELECT
    USING 1 = 1                     -- No filter
    TO platform_admin;

-- Verify: this user only sees tenant_id = 1
-- (connect as tenant_acme)
SELECT tenant_id, count() FROM analytics.events GROUP BY tenant_id;
-- Returns only rows where tenant_id = 1

-- List all row policies
SELECT * FROM system.row_policies;
```

### Step 4: Column-Level Grants

```sql
-- Grant SELECT on specific columns only (hide PII)
GRANT SELECT(event_id, event_type, created_at) ON analytics.events TO analyst;
-- Analyst cannot SELECT email, user_id, ip_address

-- Grant INSERT on specific columns (prevent metadata injection)
GRANT INSERT(event_type, user_id, properties) ON analytics.events TO data_writer;

-- Verify column-level grants
SHOW GRANTS FOR analyst;
```

### Step 5: Quotas (Resource Limits per User)

```sql
-- Limit query resources per time interval
CREATE QUOTA analyst_quota
    FOR INTERVAL 1 HOUR
        MAX queries = 1000,
        MAX result_rows = 10000000,        -- 10M result rows
        MAX read_rows = 1000000000,        -- 1B rows read
        MAX execution_time = 1800          -- 30 minutes total
    FOR INTERVAL 1 DAY
        MAX queries = 10000,
        MAX read_rows = 10000000000
    TO analyst;

-- Check quota usage
SELECT
    quota_name, quota_key,
    interval_duration,
    queries, max_queries,
    result_rows, max_result_rows,
    round(queries / max_queries * 100, 1) AS usage_pct
FROM system.quota_usage;

-- Override quota for specific user
CREATE QUOTA power_user_quota
    FOR INTERVAL 1 HOUR MAX queries = 10000
    TO developer;
```

### Step 6: Settings Profiles

```sql
-- Create a restrictive profile for external analysts
CREATE SETTINGS PROFILE analyst_profile
    SETTINGS
        readonly = 1,                            -- Read-only mode
        max_memory_usage = 5000000000 MIN 0 MAX 10000000000,  -- 5GB, can request up to 10GB
        max_execution_time = 120,                -- 2 min timeout
        max_threads = 4,                         -- 4 threads per query
        max_result_rows = 1000000,               -- 1M result rows
        max_concurrent_queries_for_user = 5,     -- 5 parallel queries
        use_uncompressed_cache = 0               -- Don't pollute cache
    TO analyst;

-- Create a profile for ETL / ingestion users
CREATE SETTINGS PROFILE writer_profile
    SETTINGS
        max_memory_usage = 10000000000,
        max_execution_time = 300,
        max_insert_block_size = 1000000,
        async_insert = 1,
        async_insert_busy_timeout_ms = 5000
    TO developer;
```

### Step 7: Application-Level RBAC Wrapper

```typescript
import { createClient } from '@clickhouse/client';

// Create per-role clients
function createRoleClient(role: 'reader' | 'writer' | 'admin') {
  const credentials = {
    reader: { user: 'app_reader', pass: process.env.CH_READER_PASS! },
    writer: { user: 'app_writer', pass: process.env.CH_WRITER_PASS! },
    admin:  { user: 'app_admin',  pass: process.env.CH_ADMIN_PASS! },
  };

  const cred = credentials[role];
  return createClient({
    url: process.env.CLICKHOUSE_HOST!,
    username: cred.user,
    password: cred.pass,
  });
}

// Use the appropriate client for each operation
const readerClient = createRoleClient('reader');
const writerClient = createRoleClient('writer');

// Read operations use the reader client
async function queryEvents() {
  return readerClient.query({ query: 'SELECT * FROM events LIMIT 100', format: 'JSONEachRow' });
}

// Write operations use the writer client
async function insertEvents(events: Record<string, unknown>[]) {
  return writerClient.insert({ table: 'events', values: events, format: 'JSONEachRow' });
}
```

## Access Control Audit

```sql
-- Who has access to what?
SELECT
    user_name, role_name, granted_role_name,
    access_type, database, table, column
FROM system.grants
ORDER BY user_name, role_name;

-- Track authentication failures
SELECT event_time, user, client_hostname, exception
FROM system.query_log
WHERE exception_code = 516  -- AUTHENTICATION_FAILED
ORDER BY event_time DESC
LIMIT 20;

-- Track privilege denials
SELECT event_time, user, exception, substring(query, 1, 200)
FROM system.query_log
WHERE exception_code = 497  -- ACCESS_DENIED
ORDER BY event_time DESC
LIMIT 20;
```

## Error Handling

| Error Code | Name | Solution |
|------------|------|----------|
| 497 | ACCESS_DENIED | `SHOW GRANTS FOR user`, add missing GRANT |
| 516 | AUTHENTICATION_FAILED | Verify password, check HOST restriction |
| 164 | READONLY | User has `readonly=1`, grant write if needed |
| 497 | Not enough privileges to execute GRANT | Use admin user with GRANT OPTION |

## Resources

- [Access Control Docs](https://clickhouse.com/docs/operations/access-rights)
- [CREATE USER](https://clickhouse.com/docs/sql-reference/statements/create/user)
- [GRANT Statement](https://clickhouse.com/docs/sql-reference/statements/grant)
- [Row Policies](https://clickhouse.com/docs/knowledgebase/row-column-policy)
- [Quotas](https://clickhouse.com/docs/operations/quotas)

## Next Steps

For schema migrations, see `clickhouse-migration-deep-dive`.
