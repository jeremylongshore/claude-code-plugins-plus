# ClickHouse Security — Worked Examples

Concrete end-to-end scenarios that combine the steps in
[implementation.md](implementation.md).

## Example 1: Stand up a least-privilege analyst

Goal: a BI user who can only read the `analytics` database, capped at 5GB/query
and a 60s timeout, with no ability to mutate data.

```sql
CREATE USER analyst
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics
    SETTINGS readonly = 1, max_memory_usage = 5000000000, max_execution_time = 60;

CREATE ROLE data_reader;
GRANT SELECT ON analytics.* TO data_reader;
GRANT data_reader TO analyst;

SHOW GRANTS FOR analyst;
-- Expect: GRANT SELECT ON analytics.* TO analyst (via data_reader)
```

## Example 2: Multi-tenant isolation with a row policy

Goal: every tenant user sees only their own rows in `analytics.events`.

```sql
CREATE USER tenant_42
    IDENTIFIED WITH sha256_password BY 'pass'
    SETTINGS custom_tenant_id = 42;

CREATE ROW POLICY tenant_filter ON analytics.events
    FOR SELECT
    USING tenant_id = getSetting('custom_tenant_id')
    TO tenant_42;

-- Verify the policy is active
SHOW ROW POLICIES;
```

## Example 3: Lock the app user to the VPC and require TLS

```sql
-- Restrict where the app user can connect from (ClickHouse 22.6+)
CREATE USER app_writer
    IDENTIFIED WITH sha256_password BY 'pass'
    HOST IP '10.0.0.0/8', IP '172.16.0.0/12';

GRANT SELECT, INSERT ON analytics.* TO app_writer;
REVOKE DROP, ALTER, CREATE ON *.* FROM app_writer;
```

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: 'https://your-host:8443',        // HTTPS on the TLS port, never :8123 HTTP
  username: 'app_writer',                // minimal-privilege, not 'default'
  password: process.env.CH_PASSWORD!,    // from a secret manager
  database: 'analytics',
});
```

## Example 4: Audit the last hour and hunt failed logins

```sql
-- Who ran what in the last hour (excluding system noise)
SELECT event_time, user, client_hostname, query_kind,
       substring(query, 1, 200) AS query_preview, exception_code
FROM system.query_log
WHERE event_time >= now() - INTERVAL 1 HOUR AND user NOT IN ('default')
ORDER BY event_time DESC
LIMIT 50;

-- Brute-force / bad-credential signal
SELECT event_time, user, client_hostname, exception
FROM system.query_log
WHERE exception_code = 516  -- AUTHENTICATION_FAILED
ORDER BY event_time DESC;
```
