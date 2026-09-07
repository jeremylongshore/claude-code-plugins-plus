# Read-only inventory queries

Use the narrowest role that can produce the required evidence. These examples
are intentionally read-only. The bundled collector accepts only supported
unquoted one-part or two-part identifiers and writes rendered SQL to a temporary
file; never pass free-form SQL as an identifier.

```sql
SHOW ROLES;
SHOW GRANTS TO ROLE <role_name>;
SHOW GRANTS OF ROLE <role_name>;
SHOW GRANTS TO USER <user_name>;
SHOW FUTURE GRANTS IN DATABASE <database_name>;
SHOW FUTURE GRANTS IN SCHEMA <database_name>.<schema_name>;
```

`SHOW GRANTS ON ACCOUNT` lists account-level privileges; it is not an inventory
of all object grants. `SHOW GRANTS TO ROLE` and `SHOW GRANTS OF ROLE` answer
different questions and both are needed to reconstruct a scoped role path.
Current `SHOW` visibility depends on the executing primary role. Full visibility
requires `MANAGE GRANTS`, which can administer grants and must not be described
as read-only or added automatically.

For a repeatable account-wide baseline, use `SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES`,
`GRANTS_TO_USERS`, and `ROLES` through `SNOWFLAKE.SECURITY_VIEWER`. These views can
lag by up to 120 minutes and omit documented shared/imported role cases. A grant
view is not the full authorization engine: check ownership, database roles,
secondary roles, object policies, shares, and the role that executed each query.

The analyzer accepts sanitized JSON rather than credentials or a live connection.
Recommended minimum shape:

```json
{
  "roles": [{"name": "ANALYST", "inherits": ["READER"]}],
  "users": [{"name": "ALICE", "primary_role": "ANALYST", "roles": ["ANALYST"]}],
  "managed_access_schemas": ["DB.SCHEMA"],
  "grants": [{"grantee": "READER", "privilege": "SELECT", "object": "DB.SCHEMA.TABLE"}],
  "future_grants": [{"grantee": "READER", "privilege": "SELECT", "scope": "DB.SCHEMA", "scope_type": "SCHEMA", "object_type": "TABLE"}]
}
```

## Sources

- [`SHOW GRANTS`](https://docs.snowflake.com/en/sql-reference/sql/show-grants)
- [`SHOW FUTURE GRANTS`](https://docs.snowflake.com/en/sql-reference/sql/show-future-grants)
- [Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage)
- [`GRANTS_TO_ROLES`](https://docs.snowflake.com/en/sql-reference/account-usage/grants_to_roles)
- [`GRANTS_TO_USERS`](https://docs.snowflake.com/en/sql-reference/account-usage/grants_to_users)
- [`ROLES`](https://docs.snowflake.com/en/sql-reference/account-usage/roles)
