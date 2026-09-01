# Query history and evidence collection

Use the narrowest read-only history surface that fits the incident. Record the source,
query ID, collection time, maximum returned timestamp, role, account, and timezone.

Primary sources:

- [QUERY_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
- [Using Query Insights](https://docs.snowflake.com/en/user-guide/query-insights)

## Surface selection

### Information Schema `QUERY_HISTORY` table function

Use for recent client-generated query discovery when its documented seven-day window
and result behavior are sufficient. This surface is useful during an active incident
when Account Usage latency would hide the relevant execution.

Always bound the function by time and, where possible, user, warehouse, session, query
ID, or query tag. Do not use broad history access to collect unrelated users' SQL.

### `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`

Use for historical comparisons and the longer documented retention window. The view can
lag by up to 45 minutes. Record the maximum `END_TIME` returned and do not claim a recent
query is absent until the surface can reasonably contain it.

Relevant fields include:

- query ID, hashes, tag, user, role, warehouse, and execution status;
- start/end time and total elapsed time;
- compilation, execution, queue, provisioning, repair, and transaction-blocked timing;
- bytes and partitions scanned;
- local/remote spill fields when present;
- error code/message, sanitized before sharing.

`QUERY_TEXT` can be truncated and can contain literals or sensitive data. Do not export
it by default. Do not export raw `USER_NAME` or `QUERY_TAG`; use Snowflake-side
SHA-256 pseudonyms when grouping is necessary.

## Bounded discovery shape

```sql
SELECT
  query_id,
  query_hash,
  query_parameterized_hash,
  user_name_sha256,
  query_tag_sha256,
  query_tag_present,
  role_name,
  warehouse_name,
  warehouse_size,
  execution_status,
  error_code,
  error_message,
  start_time,
  end_time,
  total_elapsed_time,
  compilation_time,
  execution_time,
  queued_overload_time,
  queued_provisioning_time,
  queued_repair_time,
  transaction_blocked_time,
  bytes_scanned,
  partitions_scanned,
  partitions_total,
  bytes_spilled_to_local_storage,
  bytes_spilled_to_remote_storage
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= :window_start
  AND start_time < :window_end
  AND warehouse_name = :warehouse_name
ORDER BY start_time DESC;
```

Adapt column names only after checking the current official view. Select explicit
columns; do not use `SELECT *` in an operational bundle.

## Exact query lookup

```sql
SELECT
  query_id,
  execution_status,
  warehouse_name,
  warehouse_size,
  query_hash,
  query_parameterized_hash,
  start_time,
  end_time,
  total_elapsed_time,
  compilation_time,
  execution_time,
  queued_overload_time,
  queued_provisioning_time,
  queued_repair_time,
  transaction_blocked_time,
  bytes_scanned,
  partitions_scanned,
  partitions_total,
  bytes_spilled_to_local_storage,
  bytes_spilled_to_remote_storage
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_id = :query_id;
```

If the query is too recent for Account Usage, use the Information Schema function and
label that source explicitly.

## Comparison discipline

A before/after comparison is defensible only after documenting:

- query hash and parameterized hash;
- parameters or approved redacted predicate differences;
- data time window and approximate volume;
- warehouse and cluster behavior;
- cache/result-reuse state;
- session parameters relevant to the execution;
- concurrency and queue conditions;
- source freshness.

If these cannot be aligned, call the comparison directional or inconclusive rather than
causal.

## Collector reconciliation

The bundled `query` receipt is historical and includes `QUERY_HISTORY` plus
`WAREHOUSE_LOAD_HISTORY`; preserve source views, SQL hash, row cap, truncation flag,
and receipt integrity hash. Query History may lag by up to 45 minutes. Collect
operator evidence separately with `--surface query-operator-stats --query-id
<opaque-id>` only for a completed query; Snowflake documents a 14-day retrieval
window and warehouse visibility is required. Collect Query Insights with
`--surface query-insights --query-id <opaque-id>`; its documented latency can be up
to 90 minutes. The analyzer blocks completeness when a supplied sub-surface receipt
is errored, mismatched, stale, or truncated.

## Redaction

Default evidence excludes query text. Preserve query ID and hashes. Before sharing:

- remove literals from errors or operator attributes;
- pseudonymize user names if identity is not needed;
- retain object names only when the report audience is authorized;
- never capture credentials, client configuration, or environment variables;
- store any query-text mapping separately under the operator's access controls.

## Missing evidence

- No history row can mean source latency, wrong account/role, wrong window, retention,
  or insufficient visibility.
- NULL timing does not mean zero unless the view defines it that way.
- No operator rows can mean the query is running, too old, inaccessible, or unsupported.
- No Query Insight can be caused by a documented exclusion.

Represent every case as unknown or unavailable until resolved.
