# Query history and evidence collection

Use the narrowest read-only history surface that fits the incident. Record the source,
query ID, collection time, maximum returned timestamp, role, account, and timezone.

Primary sources:

- [QUERY_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
- [QUERY_INSIGHTS Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/query_insights)
- [Using Query Insights](https://docs.snowflake.com/en/user-guide/query-insights)
- [SYSTEM$CANCEL_QUERY query-ID format](https://docs.snowflake.com/en/sql-reference/functions/system_cancel_query)

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

Comparison runs are not anchor evidence. They may use different Snowflake UUID query IDs
when they share the reviewed fingerprint and every comparison-alignment field. Keep
those rows in `query_runs`; never place a comparison run's ID on an anchor history,
operator-statistics, or Query Insights row.

## Freshness and query binding

Treat the query ID as the join key across every anchor diagnostic surface. Snowflake's
primary documentation describes query IDs as UUID text strings. The normalized history
row, each operator-statistics row, and each Query Insights row must repeat the same UUID
as `metadata.query_id`. Reject a malformed or mismatched ID. Exclude an
operator or insight row that lacks the ID rather than attributing it to the anchor by
position or file name. For a running or otherwise nonterminal query, mark evidence
binding incomplete and block all confirmed/completeness claims whether the optional arrays
are populated or empty. A terminal full-evidence packet requires at least one bound
operator row. An empty or missing operator array is a partial packet, never vacuous proof
that evidence binding is complete. Query Insights rows remain optional and their absence
is reported as unknown coverage rather than positive evidence.

Set `metadata.source_max_age_seconds` to a positive incident-specific bound. Snowflake
documents up to 45 minutes of latency for the Account Usage `QUERY_HISTORY` view and up
to 90 minutes for `QUERY_INSIGHTS`; those are platform ceilings, not automatic incident
objectives. `GET_QUERY_OPERATOR_STATS` is limited to completed queries from the past 14
days and requires `OPERATE` or `MONITOR` on the warehouse. Pass the bound to the query
collector. Receipt schema `2` records the maximum timestamp across all receipted
history rows as informational `dataset_max_time`. Normalized input schema `2.0` must
set `metadata.history_source_max_time` from the latest timestamp on the receipt row
whose UUID equals the anchor query ID. The analyzer repeats both derivations; unrelated
fresh rows cannot freshen an old anchor. A mismatch makes freshness `UNVERIFIED` and
blocks completeness rather than accepting caller-edited metadata.

The receipt checksum checks its own contents but does not authenticate the collector.
Record the final normalized bundle digest at a trusted local boundary, preserve it on
an independent channel, and supply it with `--trusted-input-sha256`. Without that
external boundary, confirmed and completeness claims remain blocked. A digest is not a
signature or proof of collector identity, and computing it from the same untrusted
copy creates no trust.

`metadata.history_source` must exactly match the query-history source named by the
receipt. The anchor receipt row must contain `role_name`, and it must exactly match
`metadata.role`. Apply terminal statuses only to their source: Account Usage supports
`success`, `fail`, and `incident`; Information Schema supports `success`,
`failed_with_error`, and `failed_with_incident`. The bundled live collector currently
receipts Account Usage. Information Schema discovery remains partial unless a separately
reviewed receipt proves that surface.

## Redaction

Default evidence excludes query text. Preserve query ID and hashes. Before sharing:

- remove literals from errors or operator attributes;
- pseudonymize user names if identity is not needed;
- retain object names only when the report audience is authorized;
- never capture credentials, client configuration, or environment variables;
- store any query-text mapping separately under the operator's access controls.

The deterministic analyzer also applies a final recursive output redaction pass to every
string in JSON and Markdown. Identifier fields such as operator ID/type and experiment
owner use bounded grammars and reject credential-bearing or raw-SQL-like values before
rendering. Explicit Authorization headers consume their complete folded values for any
valid scheme. Headerless values redact only when a standardized scheme has credential
evidence from token shape/position or a recognized sensitive parameter; parameter names
use the full token grammar, and the registered SCRAM-SHA-1/SHA-256 family shares one
boundary. Known ambiguous capability/status phrases such as `Bearer
support` and `DPoP enabled` remain prose, so this boundary deliberately does not promise
complete detection of arbitrary alphabetic headerless token68. This also preserves
OAuth-flow and non-secret Signature-algorithm prose. Password/token tails
are removed as one unit. Raw SQL is detected after optional labels and empty leading
statements are removed, then quote-aware comments are stripped and lexical statement-family
classification covers comments between keywords, chained diagnostic labels,
positional/named binds, quoted file URIs, arbitrary integration subtypes, modifiers such
as `OR ALTER`, and the shared statement-verb family inside Snowflake scripting blocks.
Expression and sentence continuations distinguish parenthesized SQL from
ordinary Select/Values prose. Sensitive keys are normalized across snake,
kebab, camel, and case
variants. Credential-adjacent presence flags (`hasPassword`, `has_pat`,
`hasRsaPublicKey`, and `has-workload-identity`) bypass redaction only for actual boolean
values. Free-text evidence is preserved when safe and replaced with explicit redaction
markers otherwise.

## Missing evidence

- No history row can mean source latency, wrong account/role, wrong window, retention,
  or insufficient visibility.
- NULL timing does not mean zero unless the view defines it that way.
- No operator rows can mean the query is running, too old, inaccessible, or unsupported.
- No Query Insight can be caused by a documented exclusion.

Represent every case as unknown or unavailable until resolved.
