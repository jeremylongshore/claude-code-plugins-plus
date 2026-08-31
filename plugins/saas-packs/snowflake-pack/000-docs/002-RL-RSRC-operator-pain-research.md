# Snowflake Operator Pain Research

**Status:** accepted research input for the v2 rebuild
**Date:** 2026-08-30
**Beads:** `claude-zhc5.1`

## Method

Community discussions and Stack Overflow were used to discover recurring jobs and
failure signatures. Product behavior was accepted only when it could be verified
against current Snowflake documentation or a Snowflake-maintained repository.
Semantic Scholar was planned as a discovery channel for general diagnostic methods,
but the public Graph API returned HTTP 429 and no Semantic Scholar MCP server was
exposed in the active tool environment. No paper result was accepted into this
record. Product claims below come from current Snowflake documentation or a
Snowflake-maintained repository; community channels were discovery inputs only.

## Evidence-backed pain clusters

### 1. Cost attribution and waste

Operators need to reconcile metered credits with query-attributed work, identify idle
warehouse time, distinguish serverless/storage/transfer/AI charges, and assign owners.
Snowflake documents both the available attribution surfaces and their limits:

- [Cost attribution](https://docs.snowflake.com/en/user-guide/cost-attributing)
- [`QUERY_ATTRIBUTION_HISTORY`](https://docs.snowflake.com/en/sql-reference/organization-usage/query_attribution_history)
- [Resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)

The important product constraint is that query attribution is not invoice truth. It
can lag, excludes idle time and several non-warehouse categories, and cannot justify
automatic resizing or suspension by itself.

### 2. Query and warehouse root-cause analysis

Slow queries are routinely misdiagnosed because queueing, blocking, exploding joins,
remote spill, poor pruning, client fetch time, and cache effects require different
remedies. The supported evidence surfaces include:

- [`GET_QUERY_OPERATOR_STATS`](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
- [Query Insights](https://docs.snowflake.com/en/user-guide/query-insights)
- [Query Profile](https://docs.snowflake.com/en/user-guide/ui-snowsight-activity)
- [Performance Explorer](https://docs.snowflake.com/en/user-guide/performance-explorer)

Recommendations must be hypotheses tied to observed operators and workload context.
Storage optimization, clustering, materialized views, Query Acceleration, and larger
warehouses all add cost and are never universal first moves.

### 3. Effective access and grant drift

Security teams need to answer why a principal can or cannot access an object and then
produce a reviewable least-privilege change packet. Role inheritance, primary and
secondary role aggregation, managed-access schemas, ownership, future grants, shares,
database roles, and service roles make a flat grant list insufficient.

- [Access-control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Access-control considerations](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)
- [Access-control configuration](https://docs.snowflake.com/en/user-guide/security-access-control-configure)
- [Terraform provider roadmap](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/ROADMAP.md)

The workflow must never auto-revoke or transfer ownership. Account Usage latency and
incomplete privileges are explicit confidence limits.

### 4. Task, stream, dynamic-table, and Snowpipe failures

Pipeline failures propagate through DAGs and often surface far from the causal node.
The operator job is to traverse upstream, find the first supported cause, and produce
an ordered recovery plan with post-fix invariants.

- [Task troubleshooting](https://docs.snowflake.com/en/user-guide/tasks-ts)
- [Dynamic-table troubleshooting](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshooting)
- [Dynamic-table monitoring](https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-monitor)
- [`COPY_HISTORY`](https://docs.snowflake.com/en/sql-reference/functions/copy_history)
- [`VALIDATE`](https://docs.snowflake.com/en/sql-reference/functions/validate)

The workflow must distinguish suspension, upstream failure, schema/change-tracking
breakage, stale streams, refresh lag, rejected files, duplicate replay risk, and
platform incidents. It must not blindly resume objects or replay files.

### 5. Terraform and migration safety

Provider grant redesign, imports, preview resources, state migrations, schemachange
checksums, repeatable scripts, driver upgrades, and behavior-change bundles can turn a
routine deployment into destructive plan churn.

- [Official Terraform provider](https://github.com/snowflakedb/terraform-provider-snowflake)
- [Provider roadmap](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/ROADMAP.md)
- [Migration script behavior](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/pkg/scripts/migration_script/README.md)
- [Behavior-change policy](https://docs.snowflake.com/en/release-notes/behavior-changes)

The safe product is a plan and verification medic, not an apply bot. It must back up
state, classify destroy/recreate/security impact, target a zero-change migration plan,
and re-check current upstream guidance each run.

### 6. Strong authentication and AI-client role scoping

Workload identities and AI clients need a dependency-ordered path away from legacy
password access. The correct method depends on user type, client capability, account
policy, and whether a client requests secondary roles.

- [Workload identity federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation)
- [Managed MCP server security](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [Agent Identity](https://docs.snowflake.com/en/user-guide/agent-identity)
- [MFA and strong-auth rollout](https://docs.snowflake.com/en/user-guide/security-mfa-rollout)

The workflow must inventory dependencies and emit a cutover packet. It must not store,
rotate, or print credentials, grant broad secondary-role access, or assume that a
published rollout window applies identically to every account.

## Secondary candidates

Semi-structured VARIANT/schema-evolution analysis and post-SnowConvert verification
are legitimate jobs, but the current evidence is narrower and they overlap with the
six core workflows. They remain research candidates rather than v2 launch slots.

## Portfolio implication

The evidence supports six operator products: cost leak hunting, query forensics,
pipeline guardianship, deployment migration safety, strong-auth migration, and access
governance. It does not support a fixed taxonomy of tutorials, hello-world examples,
generic architecture pages, static limit tables, or stand-alone error catalogs.
