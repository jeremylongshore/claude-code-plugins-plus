# ClickHouse Security — Full Implementation Walkthrough

Deep, copy-pasteable detail for every hardening step. The SKILL.md body carries
the lean workflow; this file carries the complete SQL, XML, and connection code.

## Step 1: Create Restricted Users (SQL-Based RBAC)

```sql
-- Create a read-only analyst user
CREATE USER analyst
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics
    SETTINGS
        readonly = 1,                -- Read-only mode
        max_memory_usage = 5000000000,  -- 5GB per query
        max_execution_time = 60;     -- 60s timeout

GRANT SELECT ON analytics.* TO analyst;

-- Create an application user with insert permissions
CREATE USER app_writer
    IDENTIFIED WITH sha256_password BY 'another-strong-password'
    DEFAULT DATABASE analytics;

GRANT SELECT, INSERT ON analytics.* TO app_writer;
-- Explicitly deny destructive operations
REVOKE DROP, ALTER, CREATE ON *.* FROM app_writer;

-- Create an admin user
CREATE USER ch_admin
    IDENTIFIED WITH sha256_password BY 'admin-password'
    SETTINGS PROFILE 'default';

GRANT ALL ON *.* TO ch_admin WITH GRANT OPTION;
```

## Step 2: Use Roles for Permission Groups

```sql
-- Create reusable roles
CREATE ROLE data_reader;
GRANT SELECT ON analytics.* TO data_reader;

CREATE ROLE data_writer;
GRANT SELECT, INSERT ON analytics.* TO data_writer;

CREATE ROLE schema_admin;
GRANT CREATE TABLE, ALTER TABLE, DROP TABLE ON analytics.* TO schema_admin;

-- Assign roles to users
GRANT data_reader TO analyst;
GRANT data_writer TO app_writer;
GRANT schema_admin, data_writer TO ch_admin;

-- Verify grants
SHOW GRANTS FOR analyst;
SHOW GRANTS FOR app_writer;
```

## Step 3: Row-Level Security

```sql
-- Create a row policy: tenant users only see their own data
CREATE ROW POLICY tenant_isolation ON analytics.events
    FOR SELECT
    USING tenant_id = currentUser()  -- or a mapped value
    TO data_reader;

-- More practical: map users to tenant IDs via settings
CREATE USER tenant_42
    IDENTIFIED WITH sha256_password BY 'pass'
    SETTINGS custom_tenant_id = 42;

CREATE ROW POLICY tenant_filter ON analytics.events
    FOR SELECT
    USING tenant_id = getSetting('custom_tenant_id')
    TO tenant_42;
```

## Step 4: Network Security

```xml
<!-- config.xml — restrict listen addresses -->
<listen_host>0.0.0.0</listen_host>  <!-- or specific IP -->

<!-- IP allowlist per user -->
<users>
    <app_writer>
        <networks>
            <ip>10.0.0.0/8</ip>          <!-- VPC only -->
            <ip>172.16.0.0/12</ip>
        </networks>
    </app_writer>
</users>
```

```sql
-- SQL-based network restriction (ClickHouse 22.6+)
CREATE USER app_writer
    IDENTIFIED WITH sha256_password BY 'pass'
    HOST IP '10.0.0.0/8', IP '172.16.0.0/12';
```

**ClickHouse Cloud:** Use the Cloud console IP Access List to restrict connections
to specific IPs or CIDR ranges.

## Step 5: TLS Configuration

```xml
<!-- config.xml — enable TLS for HTTPS (port 8443) -->
<https_port>8443</https_port>
<openSSL>
    <server>
        <certificateFile>/etc/clickhouse-server/server.crt</certificateFile>
        <privateKeyFile>/etc/clickhouse-server/server.key</privateKeyFile>
        <caConfig>/etc/clickhouse-server/ca.crt</caConfig>
        <verificationMode>strict</verificationMode>
    </server>
</openSSL>
```

## Step 6: Audit Logging

```sql
-- Enable query logging (on by default)
-- All queries are logged to system.query_log

-- Check who ran what queries
SELECT
    event_time,
    user,
    client_hostname,
    query_kind,
    substring(query, 1, 200) AS query_preview,
    exception_code
FROM system.query_log
WHERE event_time >= now() - INTERVAL 1 HOUR
  AND user NOT IN ('default')  -- skip system queries
ORDER BY event_time DESC
LIMIT 50;

-- Track failed login attempts
SELECT
    event_time, user, client_hostname, exception
FROM system.query_log
WHERE exception_code = 516  -- AUTHENTICATION_FAILED
ORDER BY event_time DESC;
```

## Step 7: Application Connection Security

```typescript
import { createClient } from '@clickhouse/client';

// Production: always use TLS, minimal-privilege user
const client = createClient({
  url: 'https://your-host:8443',        // HTTPS, not HTTP
  username: 'app_writer',                // Not 'default'
  password: process.env.CH_PASSWORD!,    // From secret manager
  database: 'analytics',                 // Explicit database
  clickhouse_settings: {
    readonly: 0,                          // Matches user's permission level
  },
});
```

## Security Checklist

- [ ] Default password changed or `default` user disabled
- [ ] Application users created with minimal privileges
- [ ] Roles used for permission groups
- [ ] TLS enabled for all connections (port 8443)
- [ ] IP allowlists configured (Cloud: console; self-hosted: config)
- [ ] Query logging enabled (`system.query_log`)
- [ ] Row policies for multi-tenant isolation (if needed)
- [ ] Secrets stored in environment variables or secret manager
- [ ] `.env` files in `.gitignore`
