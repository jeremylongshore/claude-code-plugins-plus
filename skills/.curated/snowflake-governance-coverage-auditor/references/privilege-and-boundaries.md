# Privilege and mutation boundaries

Use an existing least-privilege Snowflake CLI profile. Do not place credentials in
arguments, evidence, logs, or files. Information Schema functions expose only
objects visible to the executing role, so row absence is not completeness proof.
The independent scope receipt must be produced by an owner-controlled
reconciliation and bind the same hashed user, primary role type/role, secondary
roles, organization, account, objects, and databases.

The shared collector permits reviewed read-only SQL and rejects `EXECUTE`, DDL,
DML, procedures, network access, and shell execution. `POLICY_CONTEXT` requires
`EXECUTE USING` and is therefore outside that boundary. An operator can run an
approved simulation separately, sanitize it to the exact hash-only schema, and
have its envelope included in the independently trusted evidence digest.

Do not auto-escalate roles or apply tags, policies, grants, feature flags,
classification profiles, failover actions, or edition changes. Remediation is a
dry-run list of fixed action codes and validated hashes; mutation SQL is always
null and separate authorization is always required.
