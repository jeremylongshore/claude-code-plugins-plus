---
name: clickhouse-enterprise-rbac
description: |
  Configure ClickHouse enterprise RBAC — SQL-based users, roles, row policies,
  column-level grants, and quota management.
  Use when setting up multi-user access control, implementing tenant isolation,
  or configuring enterprise security for ClickHouse.
  Trigger with "clickhouse RBAC", "clickhouse roles", "clickhouse permissions",
  "clickhouse row policy", "clickhouse enterprise access", "clickhouse GRANT".
allowed-tools: Read, Write
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Enterprise RBAC

## Overview

Implement enterprise-grade role-based access control in ClickHouse using SQL-based
user management, hierarchical roles, row-level policies, column grants, quotas, and
settings profiles. The workflow builds least-privilege access from the ground up:
create authenticated users, compose reusable roles, then narrow visibility with row
and column policies and cap resource use with quotas.

Follow the seven steps below at a high level from this file; drill into
[the full implementation](references/implementation.md) for every SQL statement, and
[worked examples](references/examples.md) for two end-to-end scenarios plus audit queries.

## Prerequisites

- ClickHouse with `access_management = 1` enabled (default in Cloud)
- Admin user with `GRANT OPTION`

## Instructions

The build-out is seven steps. Steps 1–3 (users, roles, row security) carry the core
skeleton here; Steps 4–7 (column grants, quotas, settings profiles, and the
application wrapper) are summarized here and fully specified in
[references/implementation.md](references/implementation.md).

### Step 1: Create Users with Authentication

Pick an authentication method per user: `sha256_password` (standard),
`double_sha1_password` (MySQL wire protocol), or `bcrypt_password` (strongest — use
for admin accounts). Restrict network reach with `HOST IP` and cap per-user resources
inline with `SETTINGS`.

```sql
CREATE USER app_backend
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics
    HOST IP '10.0.0.0/8'           -- Restrict to VPC
    SETTINGS max_memory_usage = 10000000000,   -- 10GB per query
             max_execution_time = 60;          -- 60s timeout

SHOW CREATE USER app_backend;      -- Verify
```

### Step 2: Create Role Hierarchy

Build leaf-level base roles (`data_reader`, `data_writer`, `schema_manager`), then
compose them into job roles (`analyst`, `developer`, `platform_admin`). Grant roles to
users and set a default role that activates on connect.

```sql
CREATE ROLE data_reader;
GRANT SELECT ON analytics.* TO data_reader;

CREATE ROLE analyst;
GRANT data_reader TO analyst;      -- Composite inherits base

GRANT analyst TO app_backend;
SET DEFAULT ROLE analyst TO app_backend;
SHOW GRANTS FOR app_backend;       -- Verify the full chain
```

### Step 3: Row-Level Security

Isolate multi-tenant data with row policies — each user sees only rows matching its
`USING` predicate. A permissive `USING 1 = 1` policy lets an admin role see everything.

```sql
CREATE ROW POLICY acme_isolation ON analytics.events
    FOR SELECT
    USING tenant_id = 1
    TO tenant_acme;

SELECT * FROM system.row_policies;  -- List all policies
```

### Steps 4–7: Column Grants, Quotas, Profiles, App Wrapper

- **Step 4 — Column-level grants:** `GRANT SELECT(col, ...)` to hide PII columns and
  `GRANT INSERT(col, ...)` to prevent metadata injection.
- **Step 5 — Quotas:** cap `queries`, `read_rows`, `result_rows`, and `execution_time`
  per interval so one user cannot exhaust the cluster.
- **Step 6 — Settings profiles:** enforce `readonly`, memory, thread, and concurrency
  ceilings; a separate ETL profile enables `async_insert`.
- **Step 7 — Application wrapper:** a per-role client factory in the app layer so read,
  write, and admin operations use distinct ClickHouse users.

Full SQL and the TypeScript wrapper: [references/implementation.md](references/implementation.md).

## Output

Running this workflow produces, in the target ClickHouse instance:

- **Users** with scoped authentication, network restrictions, and per-user resource caps.
- **A role hierarchy** — base roles composed into job roles, assigned as default roles.
- **Row policies** enforcing tenant/row isolation, visible in `system.row_policies`.
- **Column grants** hiding PII, verifiable via `SHOW GRANTS FOR <role>`.
- **Quotas and settings profiles** bounding resource use per user/role.

Verify the deployment with `SHOW ACCESS`, `SHOW GRANTS FOR <user>`, and the audit
queries in [references/examples.md](references/examples.md).

## Error Handling

| Error Code | Name | Solution |
|------------|------|----------|
| 497 | ACCESS_DENIED | `SHOW GRANTS FOR user`, add missing GRANT |
| 516 | AUTHENTICATION_FAILED | Verify password, check HOST restriction |
| 164 | READONLY | User has `readonly=1`, grant write if needed |
| 497 | Not enough privileges to execute GRANT | Use admin user with GRANT OPTION |

## Examples

Two end-to-end scenarios — a multi-tenant SaaS isolation setup and a PII-safe analyst
role — plus the access-control audit queries live in
[references/examples.md](references/examples.md). The core of Example 1:

```sql
-- Each tenant reads only its own rows from a shared table
CREATE ROW POLICY acme_isolation   ON analytics.events FOR SELECT USING tenant_id = 1 TO tenant_acme;
CREATE ROW POLICY globex_isolation ON analytics.events FOR SELECT USING tenant_id = 2 TO tenant_globex;
-- Connected as tenant_acme, this returns ONLY tenant_id = 1:
SELECT tenant_id, count() FROM analytics.events GROUP BY tenant_id;
```

## Resources

- [Access Control Docs](https://clickhouse.com/docs/operations/access-rights)
- [CREATE USER](https://clickhouse.com/docs/sql-reference/statements/create/user)
- [GRANT Statement](https://clickhouse.com/docs/sql-reference/statements/grant)
- [Row Policies](https://clickhouse.com/docs/knowledgebase/row-column-policy)
- [Quotas](https://clickhouse.com/docs/operations/quotas)

## Next Steps

For schema migrations, see the `clickhouse-migration-deep-dive` skill in this pack.
