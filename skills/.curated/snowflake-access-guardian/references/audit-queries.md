# Read-only inventory queries

Use the narrowest role that can produce the required evidence. These examples
are intentionally read-only. Substitute identifiers only after validating them
against the account's identifier rules; never interpolate untrusted user text
into a mutation.

```sql
SHOW ROLES;
SHOW GRANTS TO ROLE <role_name>;
SHOW GRANTS OF ROLE <role_name>;
SHOW GRANTS TO USER <user_name>;
SHOW FUTURE GRANTS IN DATABASE <database_name>;
SHOW FUTURE GRANTS IN SCHEMA <database_name>.<schema_name>;
```

For a repeatable export, use the relevant `SNOWFLAKE.ACCOUNT_USAGE` grant views
and `INFORMATION_SCHEMA` views, but record their retention and latency. A grant
view is not the full authorization engine: check ownership, database roles,
secondary roles, object policies, shares, and the role that executed the query.

Pair historical grant and role evidence with current operator-scoped collection:
`access-current` (`SHOW GRANTS ON ACCOUNT`) and `access-future --database
<validated-identifier>`. Reconcile current and historical sets by grantee,
privilege, scope, object type, and object. The collector cap and
`truncation_possible` receipt field must be clear before making an absence or
complete-graph claim; Account Usage views may lag, so preserve collection
timestamps and source views.

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
