---
name: snowflake-advanced-troubleshooting
description: 'Apply advanced Snowflake debugging with query profiling, spill analysis,

  lock contention, and performance deep-dives using ACCOUNT_USAGE views.

  Use when standard troubleshooting fails, investigating slow queries,

  or diagnosing warehouse performance issues.

  Trigger with phrases like "snowflake hard bug", "snowflake slow query debug",

  "snowflake query profile", "snowflake spilling", "snowflake deep debug".

  '
allowed-tools: Read, Grep, Bash(snowsql:*), Bash(curl:*)
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
# Snowflake Advanced Troubleshooting

## Overview

Diagnose difficult Snowflake incidents with evidence from query profiles, operator
statistics, transaction state, historical usage views, and supported client
diagnostics. Separate live state from delayed history, collect a baseline before
changing anything, and treat cancellation, transaction aborts, warehouse resizing,
and clustering changes as explicitly authorized operator actions.

## Prerequisites

- Start with a query ID, UTC incident window, warehouse, user or service identity,
  active role, and a concise symptom. Do not paste unredacted SQL, bind values,
  credentials, or customer data into tickets or chat.
- Use an approved SnowSQL connection profile. Keep passwords, OAuth tokens, private
  keys, and passphrases out of command arguments and diagnostic artifacts.
- Confirm visibility before interpreting an empty result. Account Usage access and
  object visibility depend on the active role. `GET_QUERY_OPERATOR_STATS` requires
  `MONITOR` or `OPERATE` on the warehouse that ran the completed query.
- Distinguish live and historical sources. `SHOW LOCKS` and `SHOW TRANSACTIONS`
  describe current state; `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` can lag by up to
  45 minutes and is for retrospective analysis.
- Establish an evidence destination with restricted access and a retention period.
  Query text, driver logs, diagnostic reports, and account-specific hostnames can
  disclose sensitive operational details.

## Authentication and safety boundaries

- Reuse the repository or operator's configured SnowSQL authentication method. Do
  not request credentials, invent account identifiers, downgrade TLS validation, or
  switch authentication methods just to troubleshoot.
- Use `Read` and `Grep` only on files the operator identifies as in scope. Redact
  secrets, SQL literals, session identifiers, and customer payloads before sharing.
- Use `curl` only for an unauthenticated DNS/TCP/TLS reachability probe to an exact
  hostname returned by the existing client configuration and corroborated by
  `SYSTEM$ALLOWLIST()` or `SYSTEM$ALLOWLIST_PRIVATELINK()`. Never attach credentials,
  cookies, query text, request bodies, or `--insecure`.
- Prefer read-only evidence collection. Never cancel a query, abort a transaction,
  resize a warehouse, change a clustering key, or alter network policy without
  explicit authorization and a recorded rollback or recovery path.
- A successful HTTP response or connection test proves reachability only. It does
  not prove authentication, authorization, query correctness, or stage access.

## Instructions

### Step 1: Classify the delay before tuning

Record compilation, warehouse queue, transaction blocking, and execution time
separately. Do not resize a warehouse for a lock wait or rewrite SQL for a network
failure. For retrospective query evidence:

```sql
SELECT query_id,
       warehouse_name,
       warehouse_size,
       execution_status,
       compilation_time,
       queued_overload_time,
       queued_provisioning_time,
       transaction_blocked_time,
       execution_time,
       total_elapsed_time,
       bytes_scanned,
       bytes_spilled_to_local_storage,
       bytes_spilled_to_remote_storage
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_id = '<query_id>';
```

Treat a missing row inside the latency window as inconclusive. Use Snowsight Query
History or the Information Schema query-history table function when fresher query
history is required and the operator has suitable visibility.

### Step 2: Inspect completed-query operators

`GET_QUERY_OPERATOR_STATS` accepts a completed query from the prior 14 days. Its
statistics and attributes are `VARIANT` objects, so inspect the documented nested
keys rather than assuming they are top-level columns.

```sql
SELECT query_id,
       step_id,
       operator_id,
       operator_type,
       operator_statistics:input_rows::NUMBER AS input_rows,
       operator_statistics:output_rows::NUMBER AS output_rows,
       operator_statistics:spilling:bytes_spilled_local_storage::NUMBER
         AS local_spill_bytes,
       operator_statistics:spilling:bytes_spilled_remote_storage::NUMBER
         AS remote_spill_bytes,
       operator_statistics:pruning:partitions_scanned::NUMBER
         AS partitions_scanned,
       operator_statistics:pruning:partitions_total::NUMBER
         AS partitions_total,
       execution_time_breakdown,
       operator_attributes
FROM TABLE(GET_QUERY_OPERATOR_STATS('<completed_query_id>'))
ORDER BY COALESCE(remote_spill_bytes, 0) DESC,
         COALESCE(local_spill_bytes, 0) DESC;
```

Investigate join operators whose output is unexpectedly larger than their inputs,
operators dominated by execution time, and table scans with ineffective pruning.
Corroborate every suspected operator in Snowsight Query Profile before changing SQL.

### Step 3: Find spill patterns without overdiagnosing

```sql
SELECT query_id, query_text,
       bytes_spilled_to_local_storage / 1e9 AS local_spill_gb,
       bytes_spilled_to_remote_storage / 1e9 AS remote_spill_gb,
       total_elapsed_time / 1000 AS seconds,
       warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE (bytes_spilled_to_local_storage > 0 OR bytes_spilled_to_remote_storage > 0)
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY bytes_spilled_to_remote_storage DESC,
         bytes_spilled_to_local_storage DESC
LIMIT 20;
```

Remote spill can materially slow a query, but nonzero remote-spill bytes are not by
themselves proof that a warehouse resize is required. Query Acceleration Service can
write a small amount to remote storage for an eligible query. Compare repeated runs,
locate the spilling operator, check join cardinality and batch size, then test one
bounded change. Snowflake documents larger warehouses or smaller batches as possible
remedies; choose only after measuring the actual operator.

### Step 4: Diagnose current and historical lock contention

Use current transaction commands first. `SHOW LOCKS IN ACCOUNT` is limited to
`ACCOUNTADMIN`; otherwise use `SHOW LOCKS` and interpret only the state visible to
the current role.

```sql
SHOW LOCKS;
SELECT "resource", "type", "transaction", "transaction_started_on",
       "status", "acquired_on", "query_id"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "transaction_started_on";

SHOW TRANSACTIONS;
```

For retrospective analysis, use measured blocked time and then correlate the query
with `LOCK_WAIT_HISTORY`. Account Usage latency means these queries are not a live
control plane.

```sql
SELECT query_id, start_time, session_id, transaction_id,
       execution_status, transaction_blocked_time, total_elapsed_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND transaction_blocked_time > 0
ORDER BY transaction_blocked_time DESC;

SELECT query_id, object_name, lock_type, transaction_id, blocker_queries
FROM SNOWFLAKE.ACCOUNT_USAGE.LOCK_WAIT_HISTORY
WHERE query_id = '<blocked_query_id>';
```

Do not infer the blocker solely from SQL statement type. Inspect the holding and
waiting transaction IDs and all relevant statements in the blocker transaction.
If cancellation is authorized, verify the exact active query ID immediately before:

```sql
SELECT SYSTEM$CANCEL_QUERY('<verified_active_query_id>');
```

The query owner can cancel their own operation. Canceling another user's operation
requires one of Snowflake's documented ownership, warehouse, task, or account-level
privileges. Aborting a transaction is broader than canceling one query and can roll
back its work; escalate rather than substituting it automatically.

### Step 5: Analyze pruning before proposing clustering

```sql
SELECT query_id,
       SUBSTR(query_text, 1, 200) AS query_preview,
       partitions_scanned,
       partitions_total,
       ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 1) AS scan_pct,
       bytes_scanned / 1e9 AS gb_scanned,
       total_elapsed_time / 1000 AS seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE partitions_total > 100
  AND partitions_scanned > partitions_total * 0.5
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND query_type = 'SELECT'
ORDER BY partitions_scanned DESC
LIMIT 10;

SELECT SYSTEM$CLUSTERING_INFORMATION('my_db.my_schema.orders', '(order_date)');
```

There is no universal `average_depth` cutoff that proves a clustering key will pay
off. Compare representative query profiles, filter selectivity, table size and
change rate, clustering depth trends, and the expected maintenance cost. A `LIMIT`
clause does not guarantee a smaller scan; use a selective predicate over a controlled
data range when testing a reduced workload.

### Step 6: Correlate warehouse and metadata signals carefully

`WAREHOUSE_METERING_HISTORY` is hourly warehouse usage, not query-level attribution.
Cloud-services credit data can also arrive later than the query itself. Use it as a
retrospective correlation signal, not proof that one metadata statement caused a
charge.

```sql
SELECT start_time, warehouse_name,
       credits_used_compute,
       credits_used_cloud_services
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND warehouse_name = '<warehouse_name>'
ORDER BY start_time;
```

Correlate unusual hours with redacted Query History, deployment times, query tags,
and client telemetry. Do not publish raw query text or describe usage-view values as
the final invoice.

### Step 7: Use account-specific connectivity diagnostics

First obtain the supported endpoint set through the approved connection. Use
`SYSTEM$ALLOWLIST_PRIVATELINK()` instead when the account uses private connectivity.

```bash
# Use a named profile; never place credentials on the command line.
snowsql -c "$SNOWSQL_CONNECTION" -q 'SELECT SYSTEM$ALLOWLIST();'

# Set this to the exact configured and allowlisted hostname, not an account-name guess.
case "$SNOWFLAKE_HOST" in
  ''|*[!A-Za-z0-9.-]*) echo "invalid Snowflake hostname" >&2; exit 2 ;;
esac

curl --silent --show-error --output /dev/null \
  --connect-timeout 10 --max-time 20 \
  --write-out 'http=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s total=%{time_total}s\n' \
  "https://${SNOWFLAKE_HOST}/"
```

Do not replace the allowlist with a hardcoded `ocsp.snowflakecomputing.com` probe.
Snowflake's returned endpoint set can include account, stage, telemetry, OCSP cache,
OCSP responder, and other hosts with distinct ports. Prefer Snowflake CLI connection
testing or the Python connector diagnostic report for comprehensive checks.

### Step 8: Enable bounded driver diagnostics

```typescript
import snowflake from 'snowflake-sdk';

snowflake.configure({
  logLevel: 'DEBUG',
  logFilePath: '/restricted/snowflake-debug.log',
  additionalLogToConsole: false,
});
```

```python
diagnostic_options = {
    "enable_connection_diag": True,
    "connection_diag_log_path": "/restricted/snowflake-diag",
}

# Merge these options into the existing approved connector configuration.
# Connector diagnostics require Snowflake Connector for Python 3.9.1 or newer.
conn = snowflake.connector.connect(
    **existing_connection_options,
    **diagnostic_options,
)
```

Keep elevated logging time-bounded, store it with restrictive permissions, and return
to the normal log level after reproducing the incident. Do not monkey-patch execution
methods to log raw SQL. Review and redact diagnostic artifacts before sharing them.

### Step 9: Isolate one variable and verify

```
1. Capture query ID, UTC window, role, warehouse, client and error code.
2. Test approved connectivity without changing TLS or authentication.
3. Verify context with CURRENT_ACCOUNT(), CURRENT_ROLE(), and CURRENT_WAREHOUSE().
4. Separate compilation, queue, transaction-blocked, and execution time.
5. For completed queries, inspect operator statistics and Query Profile.
6. Reproduce on a selective, representative range; do not rely on LIMIT alone.
7. Change one variable and retain the before/after query IDs.
8. Compare the same metrics and confirm the symptom, not just query success.
9. Roll back an ineffective change and record residual risk or escalation owner.
```

Stop when evidence cannot distinguish competing causes. Report what is unknown and
request the missing privilege, client artifact, or Snowflake Support guidance rather
than guessing.

## Output

Produce a redacted incident evidence bundle with:

1. Symptom, UTC window, environment, warehouse, role, client version, and query IDs.
2. Source and freshness for every observation: live command, Information Schema,
   Account Usage, Query Profile, driver log, or connector diagnostic report.
3. Timing classification and the highest-impact operator or lock evidence.
4. Ranked hypotheses, with confirming and disconfirming evidence for each.
5. One authorized change at a time, its expected effect, rollback, and owner.
6. Before/after query IDs and comparable metrics: elapsed, blocked, queued, scanned,
   pruned, local spill, remote spill, input rows, and output rows as applicable.
7. Redactions performed, artifacts retained, remaining unknowns, and escalation path.

Never include credentials, private keys, tokens, raw customer rows, or unredacted SQL
literals in the output.

## Examples

### Example: Remote spill on a completed query

1. Record the completed query ID and confirm it is within the operator-stat window.
2. Compare Query History spill bytes with `GET_QUERY_OPERATOR_STATS` to identify the
   operator that spilled; check join input/output cardinality and pruning evidence.
3. Confirm the same node in Snowsight Query Profile. Note whether Query Acceleration
   Service could explain a small remote-spill value.
4. Test either a selective smaller batch or an authorized warehouse-size change—not
   both—and compare a new query ID against the baseline.
5. Keep the change only if the target symptom and comparable metrics improve.

### Example: A write appears blocked

1. Run `SHOW LOCKS` and `SHOW TRANSACTIONS` using the least-privileged visible scope.
2. Match the waiting query, transaction, and resource to the holding transaction.
3. Use historical `transaction_blocked_time` and `LOCK_WAIT_HISTORY` only after their
   latency window; do not use them as proof of current state.
4. Ask the transaction owner to commit or roll back. If query cancellation is
   explicitly authorized, re-verify the active query ID and required privilege.
5. Confirm the waiter proceeds, capture the final state, and document any rollback.

## Error Handling

| Observation | Do not assume | Next evidence |
|---|---|---|
| Remote spill bytes are nonzero | A resize is always required | Locate the operator, compare repeated runs, QAS state, cardinality, and batch size |
| Query History has no row | The query never ran | Account for view latency and visibility; use a fresher supported source |
| `SHOW LOCKS` is empty | No account-wide locks exist | Confirm role visibility and whether account-wide inspection is authorized |
| Many partitions were scanned | A clustering key is automatically justified | Check filter selectivity, operator pruning, table size, change rate, and cost |
| Curl reaches the account host | Authentication and stage access work | Run the approved connection test and an authenticated `SELECT 1` |
| Driver logs are incomplete | More logging is always safe | Bound the window, verify permissions, reproduce once, then redact and disable |

## Resources

- [Primary-source claim map](references/official-sources.md)
- [Query Profile and common query problems](https://docs.snowflake.com/en/user-guide/ui-query-profile)
- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
- [Transactions and locks](https://docs.snowflake.com/en/sql-reference/transactions)
- [Snowflake connectivity tools](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/snowflake-tools)

## Next Steps

After the incident is stable, convert the evidence bundle into a regression query,
dashboard threshold, or runbook update. Use `snowflake-load-scale` only for an
authorized, bounded workload test in a non-production environment or approved window.
