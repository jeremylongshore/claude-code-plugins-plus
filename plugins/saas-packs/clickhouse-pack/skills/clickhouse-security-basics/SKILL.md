---
name: clickhouse-security-basics
description: |
  Secure ClickHouse with user management, network restrictions, TLS, and
  audit logging. Use when hardening a ClickHouse deployment, creating restricted
  users, enforcing multi-tenant row isolation, or configuring network-level
  access controls. Trigger with "clickhouse security", "clickhouse user
  management", "secure clickhouse", "clickhouse TLS", "clickhouse access
  control", "clickhouse firewall".
allowed-tools: Read
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
# ClickHouse Security Basics

## Overview

Secure a ClickHouse deployment with SQL-based user management, network restrictions,
TLS encryption, and query audit logging. This skill walks the seven core hardening
steps at a high level; the full copy-pasteable SQL, XML, and connection code lives in
[references/implementation.md](references/implementation.md).

## Prerequisites

- ClickHouse admin access
- `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` for SQL-based user management
- For self-hosted: access to server config files (`config.xml`, `users.xml`)

## Instructions

Work through the seven steps in order. Each summary below gives the essential
first move; drill into [references/implementation.md](references/implementation.md)
for the complete, copy-ready code for every step.

### Step 1: Create restricted users (SQL-based RBAC)

Create least-privilege users and `REVOKE` destructive verbs from application users.

```sql
CREATE USER analyst
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics
    SETTINGS readonly = 1, max_execution_time = 60;
GRANT SELECT ON analytics.* TO analyst;
```

### Step 2: Use roles for permission groups

Define `data_reader` / `data_writer` / `schema_admin` roles once, then grant roles
to users instead of hand-managing per-user grants. Verify with `SHOW GRANTS`.

### Step 3: Row-level security

Isolate multi-tenant data with `CREATE ROW POLICY`, mapping each user to a tenant
via a custom setting (`getSetting('custom_tenant_id')`).

### Step 4: Network security

Restrict connection sources — SQL `HOST IP '10.0.0.0/8'` (22.6+), `users.xml`
per-user network allowlists for self-hosted, or the ClickHouse Cloud IP Access List.

### Step 5: TLS configuration

Enable the HTTPS port (8443) in `config.xml` with a server cert, private key, and
strict verification mode.

### Step 6: Audit logging

Query `system.query_log` (on by default) to see who ran what, and filter
`exception_code = 516` to hunt failed logins.

### Step 7: Application connection security

Connect over `https://…:8443` with a minimal-privilege user (never `default`) and a
password sourced from a secret manager — see the client snippet in
[references/examples.md](references/examples.md).

Run through the Security Checklist in
[references/implementation.md](references/implementation.md) before declaring a
deployment hardened.

## Output

Applying this skill produces:

- **Restricted user and role definitions** — least-privilege `CREATE USER` /
  `CREATE ROLE` / `GRANT` / `REVOKE` statements ready to run against your cluster.
- **Row policies** for multi-tenant isolation.
- **`config.xml` / `users.xml` fragments** for network allowlists and TLS.
- **Audit queries** against `system.query_log` for access review and failed-login detection.
- A completed **security checklist** confirming default credentials, TLS, IP
  allowlists, logging, and secret handling are all in place.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication failed (516)` | Wrong password or user | Verify credentials |
| `ACCESS_DENIED (497)` | Missing GRANT | `SHOW GRANTS FOR user` to diagnose |
| `READONLY (164)` | User in readonly mode | Grant write if needed |
| `Not enough privileges` | Row policy blocking | Check `SHOW ROW POLICIES` |

## Examples

Four worked, end-to-end scenarios live in
[references/examples.md](references/examples.md):

1. **Stand up a least-privilege analyst** — read-only BI user capped on memory and time.
2. **Multi-tenant isolation with a row policy** — each tenant sees only its own rows.
3. **Lock the app user to the VPC and require TLS** — SQL `HOST IP` + TLS client.
4. **Audit the last hour and hunt failed logins** — `system.query_log` queries.

Minimal first example — a read-only analyst:

```sql
CREATE USER analyst
    IDENTIFIED WITH sha256_password BY 'strong-password-here'
    DEFAULT DATABASE analytics SETTINGS readonly = 1;
GRANT SELECT ON analytics.* TO analyst;
```

## Resources

- [Access Control & Account Management](https://clickhouse.com/docs/operations/access-rights)
- [GRANT Statement](https://clickhouse.com/docs/sql-reference/statements/grant)
- [Row Policies](https://clickhouse.com/docs/knowledgebase/row-column-policy)
- [ClickHouse Cloud Access Management](https://clickhouse.com/docs/cloud/security/cloud-access-management/overview)

## Next Steps

For production deployment, harden the wider cluster with the
`clickhouse-prod-checklist` skill, which covers backups, replication, resource
quotas, and monitoring beyond the security surface covered here.
