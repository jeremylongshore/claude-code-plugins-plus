# Authentication cutover and recovery

The pilot produces a plan, not an account mutation. An authorized operator
owns the exact SQL/API changes, maintenance window, and approval record.

## Preconditions

- workload and identity owner, security approver, executor, recovery identity;
- current auth evidence with no secret values;
- target runtime/driver/integration compatibility and least-privilege role;
- tested canary environment or bounded production slice; and
- explicit rollback association and observation window.

## Receipt matrix

| Test | Expected evidence |
|---|---|
| Positive workload login | selected WIF/key-pair/OAuth/PAT path succeeds; session identity and role are recorded without token material |
| Positive least-privilege action | one named approved operation succeeds |
| Negative old path | password/basic path is rejected only after replacement and recovery are proven |
| Negative scope | unauthorized role/object or MCP role outside scope is denied |
| Recovery | independent recovery identity can restore the prior association |

Do not set a universal date or disable all legacy identities in one operation.
Unbound and unknown services remain quarantined for ownership discovery. If a
canary cannot authenticate, preserve the old path, restore the documented
association, and record the failure rather than widening scope.

## Sources

- [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Network policies](https://docs.snowflake.com/en/user-guide/network-policies)
- [Key-pair rotation guidance](https://docs.snowflake.com/en/user-guide/key-pair-auth)
