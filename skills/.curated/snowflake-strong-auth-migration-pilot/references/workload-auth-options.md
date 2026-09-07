# Workload authentication decision guide

Read this reference while mapping a service workload to a target method. The
decision is capability- and risk-based; the planner never assumes every driver
supports every method.

## Decision order

1. **WIF** where the cloud workload, Snowflake account/integration, and exact
   driver support it. Verify issuer, audience, subject mapping, role mapping,
   clock skew, and failure/recovery behavior. No long-lived Snowflake secret is
   placed in the workload.
2. **Key pair** when WIF is unavailable and the connector supports it. Verify
   public-key registration, private-key custody outside the report, rotation
   ownership, and a second recovery key/path.
3. **OAuth** when an approved Snowflake OAuth/external OAuth integration maps
   the workload to a bounded role and audience. Verify token acquisition and
   scope without copying token values into logs or artifacts.
4. **PAT** only as an explicitly approved, bounded fallback for clients that
   require it. Record owner, audience, expiration/revocation procedure, and why
   stronger workload identity methods are unavailable. PAT is not a universal
   replacement for service identity design.

Password/basic authentication is a migration finding for non-human workloads,
not an instruction to disable it. Run a parallel canary and keep a tested
recovery path until positive and negative receipts are accepted.

## Sources

- [Workload identity federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation)
- [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [OAuth overview](https://docs.snowflake.com/en/user-guide/oauth-intro)
- [Programmatic access tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
