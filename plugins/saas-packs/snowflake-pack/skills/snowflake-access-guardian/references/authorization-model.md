# Snowflake authorization model

Read this reference when tracing why a principal can or cannot use an object.
It is a decision aid, not a replacement for the live account's `SHOW GRANTS`,
`INFORMATION_SCHEMA`, or policy checks.

## Evidence layers

Use a current export of:

1. account roles and role-to-role grants;
2. users, default roles, and the secondary-role session mode;
3. account-role and database-role edges, with database roles kept distinct;
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

Database roles are scoped to one database and cannot be activated directly.
Their privileges become effective through a current account-role linkage, and
granting one to an account role implicitly provides database `USAGE`. The
receipted analyzer follows a fully qualified database-role path only when both
the current database-role object grant and current account-role linkage are
receipted. A capability failure or missing linkage blocks the path. Mark
`PUBLIC`, direct-user grants, and
ownership as separate paths rather than silently normalizing them into a role.
For a workload, capture the primary role and whether `USE SECONDARY ROLES ALL`
or an explicit secondary-role list was active. A path that only works with a
secondary role is not evidence that a default-role session works.

Every user also has `PUBLIC`, so a scoped graph must collect it explicitly.
Direct user privileges are a separate user-based access-control path and become
effective only with `USE SECONDARY ROLES ALL`; an explicit secondary-role list
does not activate direct user grants.

For a read, the packet normally needs `USAGE` on the database, `USAGE` on the
schema, and the object privilege. The exact chain varies by object type. Do not
claim denial merely because one historical view lacks a row: row access policies,
masking policies, network policies, shares, and managed-account boundaries can
also change the result.

## Sources

- [Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Access control privileges](https://docs.snowflake.com/en/user-guide/security-access-control-privileges)
- [Understanding secondary roles](https://docs.snowflake.com/en/user-guide/security-access-control-configure#label-secondary-roles)
- [Database roles](https://docs.snowflake.com/en/user-guide/security-access-control-overview#database-roles)
- [`GRANT DATABASE ROLE`](https://docs.snowflake.com/en/sql-reference/sql/grant-database-role)
