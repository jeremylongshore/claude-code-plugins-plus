# ClickHouse Enterprise RBAC — Worked Examples & Audit Queries

Two worked scenarios plus the audit queries that verify an RBAC deployment is
behaving as designed.

## Example 1: Multi-tenant SaaS isolation

Goal: `tenant_acme` and `tenant_globex` share the `analytics.events` table but
each may only read its own rows; the platform admin reads everything.

```sql
-- 1. Users
CREATE USER tenant_acme   IDENTIFIED WITH sha256_password BY 'pass' DEFAULT DATABASE analytics;
CREATE USER tenant_globex IDENTIFIED WITH sha256_password BY 'pass' DEFAULT DATABASE analytics;

-- 2. Read grant (row policy narrows the visible rows)
GRANT SELECT ON analytics.events TO tenant_acme, tenant_globex;

-- 3. Row policies pin each tenant to its own tenant_id
CREATE ROW POLICY acme_isolation   ON analytics.events FOR SELECT USING tenant_id = 1 TO tenant_acme;
CREATE ROW POLICY globex_isolation ON analytics.events FOR SELECT USING tenant_id = 2 TO tenant_globex;
CREATE ROW POLICY admin_all        ON analytics.events FOR SELECT USING 1 = 1        TO platform_admin;

-- 4. Verify (connected as tenant_acme):
SELECT tenant_id, count() FROM analytics.events GROUP BY tenant_id;
-- Returns ONLY tenant_id = 1 — globex rows are invisible, not just filtered.
```

## Example 2: PII-safe analyst role

Goal: analysts can query event telemetry but never see `email`, `user_id`, or
`ip_address`, and are capped to read-only with a 2-minute query ceiling.

```sql
CREATE ROLE analyst;
GRANT SELECT(event_id, event_type, created_at) ON analytics.events TO analyst;

CREATE SETTINGS PROFILE analyst_profile
    SETTINGS readonly = 1, max_execution_time = 120, max_result_rows = 1000000
    TO analyst;

-- Verify the analyst cannot reach PII columns:
SHOW GRANTS FOR analyst;
-- Any SELECT email FROM analytics.events → error 497 ACCESS_DENIED
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
