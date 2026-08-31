# Snowflake identity inventory

Read this reference before classifying users. A label is an observed inventory
fact, not a migration verdict.

## Principal classes

- **PERSON** — an interactive human account. Prefer the organization's SSO/IdP
  path or an approved OAuth flow. Do not disable password or alter a policy until
  the person has a tested recovery path and an owner approves the change.
- **SERVICE** — an intentionally non-human principal with a named workload,
  owner, runtime, role, and rotation/revocation process.
- **LEGACY_SERVICE** — a non-human principal whose ownership, workload, or
  authentication path is not yet governed. Inventory and bind it before
  attempting retirement; an unknown service must never be disabled by cleanup.

Capture user name/type, disabled state, default/primary role, observed method
names, workload identity binding, integration, runtime/driver, role scope, and
last-evidence timestamp. Never capture a password, token, private key, or secret
value. `ACCOUNT_USAGE.USERS` and `SHOW USERS` have different freshness and
visibility; record which supplied each field.

## No universal deadline

Snowflake feature support varies by cloud, connector, runtime, account edition,
and authentication integration. The pilot deliberately does not claim a single
retirement date. Use current Snowflake documentation and an approved internal
change window for each workload.

## Sources

- [User types and management](https://docs.snowflake.com/en/user-guide/admin-user-management)
- [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Account Usage USERS view](https://docs.snowflake.com/en/sql-reference/account-usage/users)
