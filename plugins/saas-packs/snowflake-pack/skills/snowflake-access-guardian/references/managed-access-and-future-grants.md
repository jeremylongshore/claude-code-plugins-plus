# Managed access, ownership, and future grants

Load this reference when a finding involves a managed access schema, ownership,
or an existing/future-grant conflict.

## Managed access schemas

In a managed access schema, the schema owner or a role with `MANAGE GRANTS`
controls object grants. Object owners do not independently grant access as they
would in a regular schema. Confirm the schema's current owner, the grantor role,
and the policy for delegated administration before suggesting a change. A missing
grantor in a sanitized export is an evidence gap, not proof of an invalid grant.

## Ownership is control

`OWNERSHIP` can change who can alter or grant on an object and can affect tasks,
pipes, policy ownership, and dependent objects. Inventory outbound grants,
dependents, future grants, and the intended reversal before preparing a transfer.
Never convert ownership findings into automatic `GRANT OWNERSHIP` SQL.

## Future grant precedence

Future grants seed privileges on objects created later; they do not repair an
existing object's current grants. Snowflake documents schema-level future grants
as taking precedence over database-level future grants for the same object type
in a schema. Therefore a database future grant and a schema future grant can make
the effective policy differ from what an operator expects. Compare scope,
object type, grantee, privilege, and grantor, then test creation in a disposable
schema if approved.

## Sources

- [Managed access schemas](https://docs.snowflake.com/en/user-guide/security-access-control-configure#label-managed-access-schemas)
- [Future grants](https://docs.snowflake.com/en/user-guide/security-access-control-configure#label-future-grants)
- [`GRANT OWNERSHIP`](https://docs.snowflake.com/en/sql-reference/sql/grant-ownership)
