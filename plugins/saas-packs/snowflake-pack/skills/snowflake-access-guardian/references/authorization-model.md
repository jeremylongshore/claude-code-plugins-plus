# Snowflake authorization model

Read this reference when tracing why a principal can or cannot use an object.
It is a decision aid, not a replacement for the live account's `SHOW GRANTS`,
`INFORMATION_SCHEMA`, or policy checks.

## Evidence layers

Use a current export of:

1. account roles and role-to-role grants;
2. users, default roles, and the secondary-role session mode;
3. account-role edges; database-role edges are a separate live-verification
   boundary in v2.0;
4. object grants, ownership, grantor, and grant options; and
5. database/schema `USAGE`, object privileges, future grants, and the object
   type's container rules.

`ACCOUNT_USAGE.GRANTS_TO_ROLES` and related views are useful historical evidence
and may lag. `SHOW GRANTS` is closer to current state, but the result is still
scoped by the role running it. Record the extraction time, role, and omitted
object classes in the packet.

## Effective path notation

Represent every proven path as:

```text
USER -> ACCOUNT_ROLE -> PARENT_ROLE -> object privilege
```

The bundled analyzer does not ingest or traverse database-role edges in v2.0.
Do not certify an answer that depends on one: capture it separately, add
`-> DATABASE_ROLE` to the manual evidence path, and verify it against live
Snowflake metadata. Mark `PUBLIC`, direct-user grants, and ownership as separate
paths rather than silently normalizing them into a role.
For a workload, capture the primary role and whether `USE SECONDARY ROLES ALL`
or an explicit secondary-role list was active. A path that only works with a
secondary role is not evidence that a default-role session works.

For a read, the packet normally needs `USAGE` on the database, `USAGE` on the
schema, and the object privilege. The exact chain varies by object type. Do not
claim denial merely because one historical view lacks a row: row access policies,
masking policies, network policies, shares, and managed-account boundaries can
also change the result.

## Sources

- [Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Access control privileges](https://docs.snowflake.com/en/user-guide/security-access-control-privileges)
- [Understanding secondary roles](https://docs.snowflake.com/en/user-guide/security-access-control-configure#label-secondary-roles)
