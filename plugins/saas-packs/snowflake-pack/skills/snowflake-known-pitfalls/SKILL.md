---
name: snowflake-known-pitfalls
description: 'Identify and avoid Snowflake anti-patterns and common mistakes in SQL,

  warehouse management, data loading, and access control.

  Use when reviewing Snowflake configurations, onboarding new users,

  or auditing existing Snowflake deployments for best practices.

  Trigger with phrases like "snowflake mistakes", "snowflake anti-patterns",

  "snowflake pitfalls", "snowflake what not to do", "snowflake code review".

  '
allowed-tools: Read, Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- data-warehouse
- analytics
- snowflake
compatibility: Designed for Claude Code
---
# Snowflake Known Pitfalls

## Overview

Audit Snowflake designs and SQL for correctness, cost controls, recoverability, and
least privilege. Treat sizes, retention periods, and credit quotas as account policy,
not universal constants, and convert credits to currency only with the customer's
contract rate rather than a hard-coded public price.

## Prerequisites

- Read-only access to the relevant Snowflake configuration, SQL, and deployment files.
- A Snowflake role allowed to inspect the objects under review. Account Usage views can
  require imported privileges and can have reporting latency.
- The account edition, retention policy, workload baseline, and approved cost limits.
- For connection reviews, the driver and identity-provider configuration. Do not request,
  print, or copy passwords, private keys, tokens, or connection profiles.

Use `Read` for the exact configuration under review and `Grep` for risky constructs such
as `AUTO_SUSPEND = 0`, `DEFAULT_ROLE = 'ACCOUNTADMIN'`, `SELECT *`, transient production
tables, and password fields. Redact identifiers if the report will leave the operator's
trusted environment.

## Instructions

1. Establish scope and evidence. Record account, database, schema, warehouse, and time
   window without collecting customer row data or credentials.
2. Inspect the relevant object metadata with the least-privileged role. Prefer documented
   `SHOW` commands or Account Usage views over assumed `INFORMATION_SCHEMA` objects.
3. Compare behavior against the workload's measured baseline and account policy. Do not
   invent dollar costs, table-size thresholds, or credit quotas.
4. Classify each finding as confirmed, needs runtime evidence, or not applicable. Include
   the exact object and the evidence query used.
5. Propose one bounded change at a time. State validation, rollback, and the approval
   required before changing production objects.

## Pitfall 1: Warehouses That Never Suspend

Warehouses are billed per second, with a 60-second minimum each time one starts. An idle
warehouse with auto-suspend disabled can consume credits without doing useful work.

```sql
-- Inspect first; SHOW WAREHOUSES is the documented account-level interface.
SHOW WAREHOUSES
  ->> SELECT "name", "size", "state", "auto_suspend", "auto_resume"
      FROM $1
      WHERE "auto_suspend" = 0 OR "auto_suspend" IS NULL;
```

Set a workload-specific timeout only after measuring queueing and resume behavior:

```sql
ALTER WAREHOUSE ETL_WH SET AUTO_SUSPEND = 120 AUTO_RESUME = TRUE;
```

Validate representative jobs after the change and restore the previous properties if
resume latency or job behavior violates the approved service objective.

## Pitfall 2: Routine Use of ACCOUNTADMIN

Do not make `ACCOUNTADMIN` the default role for analysts or applications. The correct
number of administrators is an organization-specific governance decision; the invariant
is least privilege and separately controlled elevation.

```sql
SELECT grantee_name, role, granted_by
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE role = 'ACCOUNTADMIN' AND deleted_on IS NULL;
```

Review grants with the security owner, then move routine work to scoped functional roles.
Never revoke the last controlled administrative path during remediation.

## Pitfall 3: Unnecessary `SELECT *`

Column pruning reduces scanned data on wide columnar tables, but bytes scanned alone does
not prove a regression. Compare equivalent queries over the same data and warehouse.

```sql
SELECT event_id, event_type, event_timestamp
FROM analytics.events
WHERE event_timestamp >= DATEADD(day, -1, CURRENT_TIMESTAMP());

SELECT query_id, bytes_scanned, total_elapsed_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_SESSION(RESULT_LIMIT => 20))
ORDER BY start_time DESC;
```

Preserve `SELECT *` only where the consumer intentionally needs the complete schema and
can tolerate schema expansion.

## Pitfall 4: Clustering Without Evidence

Clustering keys are not required for every table. Snowflake recommends considering them
for very large tables with selective or sorting queries and a high query-to-DML ratio;
automatic maintenance consumes credits. There is no universal byte threshold.

```sql
SELECT SYSTEM$CLUSTERING_INFORMATION(
  'ANALYTICS.EVENTS',
  '(EVENT_DATE, CUSTOMER_ID)'
);
```

Test a candidate on representative queries, compare query profile and clustering depth,
and include maintenance credit consumption. Remove the key if the measured benefit does
not meet the operator's acceptance criteria.

## Pitfall 5: Assuming `MERGE` Is Automatically Idempotent

`MERGE` can be nondeterministic when multiple source rows match one target row, and
duplicate source rows can produce duplicate inserts when no target row matches. Deduplicate
on a stable business key before merging and make the selected row deterministic.

```sql
MERGE INTO dim_orders AS target
USING (
  SELECT order_id, amount, source_updated_at
  FROM staging_orders
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY source_updated_at DESC, ingest_sequence DESC
  ) = 1
) AS source
ON target.order_id = source.order_id
WHEN MATCHED AND source.source_updated_at >= target.source_updated_at THEN
  UPDATE SET amount = source.amount,
             source_updated_at = source.source_updated_at
WHEN NOT MATCHED THEN
  INSERT (order_id, amount, source_updated_at)
  VALUES (source.order_id, source.amount, source.source_updated_at);
```

Retry safety depends on stable source data and deterministic match/update logic. Test a
replay in a disposable table and verify row counts and key uniqueness.

## Pitfall 6: Letting Streams Become Stale

Inspect streams with `SHOW STREAMS` or `DESCRIBE STREAM` and consume change records before
`STALE_AFTER`. A stale stream can lose its unconsumed change records and must be recreated.

```sql
SHOW STREAMS IN ACCOUNT
  ->> SELECT "database_name", "schema_name", "name", "stale", "stale_after"
      FROM $1
      ORDER BY "stale_after";
```

`SYSTEM$STREAM_HAS_DATA` can prevent staleness when it returns `FALSE` for an empty stream;
when it returns `TRUE`, consume the stream in a transaction. Do not blindly raise table
retention: retention support depends on table type, edition, and account policy.

## Pitfall 7: Excessive Small Load Files

Snowflake recommends roughly 100-250 MB compressed files for efficient parallel bulk and
Snowpipe loading. This is guidance, not proof that each file becomes a micro-partition.

```sql
SELECT file_name, file_size, row_count, status
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'RAW.EVENTS',
  START_TIME => DATEADD(hour, -24, CURRENT_TIMESTAMP())
))
ORDER BY file_size;
```

Compare queueing time, load duration, and end-to-end freshness before and after changing
producer batching. Do not expose staged object names outside the approved report.

## Pitfall 8: Treating Resource Monitors as Complete Cost Control

Resource monitors govern warehouse credit usage; they do not govern serverless features
or Snowflake AI features. Use budgets where supported for serverless resources and retain
independent usage monitoring. Threshold actions can occur after the exact quota, so use
an approved buffer.

```sql
SHOW WAREHOUSES
  ->> SELECT "name", "size", "resource_monitor"
      FROM $1
      WHERE "resource_monitor" = 'null';
```

That query does not account for an account-level monitor. Verify account and warehouse
assignments separately. Choose quota and actions from the organization's credit budget;
do not paste a fixed quota into production.

## Pitfall 9: Transient Tables for Data That Needs Recovery

Transient tables have no Fail-safe and support at most one day of Time Travel. Use them
only when that recovery boundary is explicitly acceptable. Permanent-table retention
depends on edition and policy, so do not prescribe an unsupported fixed duration.

```sql
SHOW TABLES IN SCHEMA PROD.CURATED
  ->> SELECT "name", "kind", "retention_time"
      FROM $1
      WHERE "kind" = 'TRANSIENT';
```

Changing table type or rebuilding data is a production migration. Require an owner,
backup/replay plan, validation query, and rollback path.

## Pitfall 10: Incorrect Account Identifiers or Weak Authentication

Drivers expect an account identifier, not the full `snowflakecomputing.com` hostname.
Prefer the organization-name and account-name form documented for the driver; account
locators remain supported where required by existing configuration.

```typescript
const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT_IDENTIFIER,
  authenticator: 'SNOWFLAKE_JWT',
  privateKeyPath: process.env.SNOWFLAKE_PRIVATE_KEY_PATH,
});
```

The example assumes an administrator-approved key-pair setup and protected private-key
file. OAuth, external-browser SSO, workload identity federation, and other documented
methods may be more appropriate. Never put passwords, tokens, or private keys in source.

## Error Handling

| Condition | Response |
|---|---|
| Metadata query is denied | Record the required privilege; do not elevate or switch roles silently. |
| Account Usage and `SHOW` disagree | Note Account Usage latency and use the live object metadata for the immediate decision. |
| `MERGE` source is not unique | Stop the load; quarantine duplicate keys and define deterministic precedence. |
| Stream is stale | Stop downstream assumptions, quantify the missing interval, recreate the stream, and replay from an authoritative source if available. |
| Cost or performance evidence is incomplete | Mark the finding unconfirmed and request an approved measurement window. |
| Remediation changes production behavior | Obtain owner approval, capture previous object settings, test, and roll back on the stated criterion. |

## Output

Return an audit report containing:

- scope, role, time window, and evidence sources;
- one row per finding with severity, object, evidence, documented invariant, and confidence;
- a bounded remediation with owner, approval boundary, validation query, and rollback;
- credit quantities without currency conversion unless the customer's contract rate was
  explicitly supplied; and
- redactions for credentials, customer data, account locators, and sensitive object names.

Do not claim an account is safe when relevant metadata was inaccessible.

## Examples

**Warehouse review:** `SHOW WAREHOUSES` finds `AUTO_SUSPEND = 0` on `ETL_WH`.
Report a confirmed idle-credit risk, recommend a measured timeout, preserve the previous
setting, and validate two representative ETL runs before accepting the change.

**Load review:** a `MERGE` source contains three rows for one `order_id`. Report the load
as non-idempotent, stop automatic retry, define a deterministic source ordering, replay
into a disposable target, and accept only when key uniqueness and result totals match.

**Cost review:** warehouses have monitors but a serverless feature is consuming credits.
Report warehouse controls as present but incomplete, route supported serverless resources
to budgets, and retain usage alerts; do not assign a dollar value without the account rate.

## References

Read [the official-source matrix](references/official-sources.md) when validating a
platform claim, query surface, edition-dependent boundary, or authentication option. It
maps every pitfall to its current Snowflake primary documentation and states what must be
verified in the operator's account rather than inferred from this skill.
