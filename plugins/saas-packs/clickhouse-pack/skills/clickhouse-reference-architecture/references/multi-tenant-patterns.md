# Multi-Tenant Patterns

Three isolation strategies, from lowest to highest operational overhead. Approach A is
the recommended default and scales to 10K+ tenants; reach for B or C only when a
compliance boundary demands stricter isolation.

## Approach A: Shared table with tenant_id in ORDER BY (recommended)

```sql
-- Tenant_id first in ORDER BY = queries filter on tenant efficiently
ORDER BY (tenant_id, event_type, created_at)

-- Query: only scans data for this tenant
SELECT count() FROM events_raw WHERE tenant_id = 42;
```

Putting `tenant_id` first in the sort key lets ClickHouse skip every granule that
doesn't belong to the tenant, so per-tenant queries stay fast even as the shared table
grows. One schema, one set of DDL changes, one place to operate.

## Approach B: Database per tenant (for strict isolation)

```sql
CREATE DATABASE tenant_42;
CREATE TABLE tenant_42.events (...) ENGINE = MergeTree() ...;

-- Pros: Full isolation, easy to drop tenant
-- Cons: Schema changes need per-tenant DDL, more operational overhead
```

Use when a tenant must be fully separable — e.g. one-command offboarding via
`DROP DATABASE`, or a contractual data-isolation requirement. The cost is fan-out on
every migration.

## Approach C: Row-level security (ClickHouse RBAC)

```sql
CREATE ROW POLICY tenant_isolation ON analytics.events_raw
    FOR SELECT USING tenant_id = getSetting('custom_tenant_id')
    TO app_user;
```

Enforces the tenant filter in the database itself, so an application bug that forgets a
`WHERE tenant_id = …` clause cannot leak cross-tenant rows. Pairs well with Approach A
as defense-in-depth.
