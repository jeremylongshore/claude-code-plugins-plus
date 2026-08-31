# Snowflake Incident Diagnostics

Use these patterns only through an approved, least-privileged diagnostic role.
Replace example identifiers with reviewed object names. Keep all time windows and
result counts bounded, and store results in the restricted incident record.

## Contents

1. Connection and platform evidence
2. Current query failures
3. Historical query and login evidence
4. Task history
5. Streams and Snowpipe
6. Warehouses and resource monitors
7. Safe table recovery
8. Task-graph recovery
9. Evidence checklist

## 1. Connection and platform evidence

Record the affected region and component from <https://status.snowflake.com>, then
test from the affected execution environment with an existing named connection:

```bash
snow connection test --connection incident-readonly
```

The command proves only that this client and named configuration can connect at
that moment. It does not prove that a workload identity, task, pipe, storage
integration, warehouse, or downstream consumer is healthy. Never replace the
named connection with password, token, or private-key values on the command line.

## 2. Current query failures

Information Schema query-history table functions cover recent activity and are
appropriate for current triage. Their arguments are applied before the outer
`WHERE`, so bound the time range and `RESULT_LIMIT` inside the function call:

```sql
SELECT
  query_id,
  execution_status,
  error_code,
  error_message,
  start_time,
  end_time,
  total_elapsed_time,
  role_name,
  database_name,
  schema_name,
  warehouse_name
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  END_TIME_RANGE_START => DATEADD('minute', -30, CURRENT_TIMESTAMP()),
  END_TIME_RANGE_END => CURRENT_TIMESTAMP(),
  RESULT_LIMIT => 1000
))
WHERE error_code IS NOT NULL
ORDER BY start_time DESC;
```

Do not select `query_text` or `bind_values` into broadly visible output by
default. Query-history functions are limited to recent history and the visibility
of the active role.

## 3. Historical query and login evidence

`SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` provides longer history but can lag by up
to 45 minutes. `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY` can lag by up to 120
minutes. Always bound their timestamp columns and row counts. Do not interpret a
missing fresh record as proof that an event did not occur; use current client
errors, connection diagnostics, and login-failure UUIDs for live investigation.

For key-pair failure `390144`, an authorized administrator can pass the failure
UUID—not a key or token—to `SYSTEM$GET_LOGIN_FAILURE_DETAILS`. Compare the
reported account and user claims with the expected account identifier and the
user's `LOGIN_NAME`, then verify clock, algorithm, and registered public-key
fingerprint. Redact the function output before sharing it.

## 4. Task history

Use bounded task history and retain the query ID that connects a task run to query
history:

```sql
SELECT
  name,
  state,
  query_id,
  error_code,
  error_message,
  scheduled_time,
  query_start_time,
  completed_time
FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.TASK_HISTORY(
  SCHEDULED_TIME_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP()),
  SCHEDULED_TIME_RANGE_END => CURRENT_TIMESTAMP(),
  RESULT_LIMIT => 1000
))
WHERE query_id IS NOT NULL
ORDER BY scheduled_time DESC;
```

The function's arguments are applied before the outer filter. The active role
must have the documented task privileges; do not silently elevate roles to fill a
visibility gap.

## 5. Streams and Snowpipe

Inspect stream state without changing it:

```sql
SHOW STREAMS IN ACCOUNT;
```

From the result, record the exact stream identity, `stale`, `stale_after`, source,
and owner. `stale_after` is predictive: after it passes, the stream can become
stale at any time. Once stale, its historical and unconsumed change records are
not recoverable through that stream. Do not drop or replace it until the backfill
source, replay boundary, deduplication key, and reconciliation check are approved.

Inspect a named pipe and the destination table's bounded load history:

```sql
SELECT SYSTEM$PIPE_STATUS('DB.SCHEMA.PIPE');

SELECT
  file_name,
  status,
  row_count,
  first_error_message,
  last_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'DB.SCHEMA.TARGET_TABLE',
  START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
))
ORDER BY last_load_time DESC;
```

Correlate status, file identity, load state, row count, and first error before
considering replay. Do not issue a blanket pipe refresh or resubmit files without
proving the exact missing set and idempotent destination behavior.

## 6. Warehouses and resource monitors

```sql
SHOW WAREHOUSES LIKE 'TARGET_WH';
SHOW RESOURCE MONITORS;
```

Record suspension reason, running/queued workload, size, and assigned monitor.
Resource monitors act on configured thresholds for supported warehouses; they do
not cover every serverless or AI cost surface and are not precise per-credit
meters. Keep all quota, assignment, resizing, and resume actions behind the
organization's cost/change approval boundary.

## 7. Safe table recovery

When retained Time Travel history covers the approved point, clone to a new
recovery object instead of replacing production:

```sql
CREATE TABLE INCIDENT_RECOVERY.USERS_BEFORE_BAD_DML
  CLONE PROD.SILVER.USERS
  BEFORE (STATEMENT => 'REPLACE_WITH_APPROVED_QUERY_ID');
```

Validate keys, row counts, constraints, policies, grants, and downstream behavior
against the expected state. Do not use `SELECT *` when sensitive columns are not
needed. Production repair or swap requires explicit data-owner approval and a
proven reversal.

Before `UNDROP`, inspect retained dropped-object history and name conflicts:

```sql
SHOW TABLES HISTORY LIKE 'TARGET_TABLE' IN SCHEMA PROD.SILVER;
```

If history is outside retention or the intended object cannot be identified,
stop. Do not drop a current same-named object merely to make `UNDROP` succeed.

## 8. Task-graph recovery

Preserve the graph definition and the affected run receipts. Resume child tasks
before the root, or use documented `SYSTEM$TASK_DEPENDENTS_ENABLE` from the root
when that is the approved method. Execute one controlled run, then reconcile every
destination side effect before restoring the schedule. If the workload is not
idempotent, keep it contained until duplicate risk is resolved.

## 9. Evidence checklist

| Evidence | Minimum receipt |
|---|---|
| Platform | status component, region, timestamp |
| Connection | client/environment, named profile, timestamp, sanitized result |
| Query | query ID, status/error, timing, role/database/schema/warehouse |
| Task | task identity, scheduled time, state, query ID |
| Stream | fully qualified name, source, `stale`, `stale_after` |
| Pipe/load | pipe, file, status, row count, first error, load time |
| Change | approver, exact target, before/after state, reversal |
| Recovery | recovery object/run ID, boundary, reconciliation result |

## Official references

- [Snowflake CLI connection test](https://docs.snowflake.com/en/developer-guide/snowflake-cli/command-reference/connection-commands/test-connection)
- [Information Schema QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/query_history)
- [Account Usage QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [Account Usage LOGIN_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/login_history)
- [Key-pair authentication troubleshooting](https://docs.snowflake.com/en/user-guide/key-pair-auth-troubleshooting)
- [TASK_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/task_history)
- [Streams](https://docs.snowflake.com/en/user-guide/streams-intro)
- [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)
- [Resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [CREATE CLONE](https://docs.snowflake.com/en/sql-reference/sql/create-clone)
- [UNDROP TABLE](https://docs.snowflake.com/en/sql-reference/sql/undrop-table)
- [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
