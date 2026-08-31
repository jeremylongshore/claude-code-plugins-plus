# Verification and rollback packet

The guardian is an audit and planning tool. It must not execute `GRANT`,
`REVOKE`, `GRANT OWNERSHIP`, `ALTER USER`, or `ALTER ... ENABLE/DISABLE`.

## Positive checks

- Under the real workload primary role, prove one intended action on one named
  object.
- If secondary roles are part of the design, repeat with the exact
  `USE SECONDARY ROLES` mode and record the active roles.
- Confirm required database/schema container privileges and policy behavior.
- For a managed schema, record the grantor and the role holding `MANAGE GRANTS`.

## Negative checks

- Prove one representative prohibited action remains denied.
- Re-test a path that was direct-to-user, PUBLIC, or inherited through a role
  scheduled for removal; do not treat a failed historical query as proof.
- Verify a future object receives the intended privilege and not a conflicting
  database-level or schema-level grant.

## Receipt binding

Every positive and negative receipt must record `observed_at`, `account`,
`principal`, `object`, `privilege`, `primary_role`, `secondary_roles_mode`, and
the exact `secondary_roles` array. The timestamp must fall inside the declared
observation window and no later than collection. A receipt from another account,
principal, object, privilege, or role context is `NOT_PROVEN`, even if its status
is `PASS` or `DENIED`.

## Change and rollback packet

For every proposed change include the exact principal, privilege, object, current
evidence timestamp, owner/approver, executor, precondition, positive test,
negative test, and reversal. Treat ownership and lockout-capable authentication
changes as separate phases. Keep the previous role graph and grant export so an
authorized operator can restore the old edge without guessing.

## Source

- [Access control considerations](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)
