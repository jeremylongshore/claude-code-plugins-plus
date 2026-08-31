# Load, query-hash, pruning, and SOS evidence

Use this reference after operator statistics and Query Insights are collected.

## Correlate load and latency

`WAREHOUSE_LOAD_HISTORY` is a five-minute, delayed view of running, overloaded
queue, provisioning queue, and blocked load. Align its UTC intervals with
`QUERY_HISTORY` queue components. Positive queue load corroborates contention; it
does not identify a warehouse size or prove that this query caused the load.

## Hash comparisons

Compare `QUERY_PARAMETERIZED_HASH` first, then `QUERY_HASH` as a narrower fallback.
Retain query IDs, warehouse size, data window, cache/result-reuse state, session
context, and concurrency. A hash match alone does not align parameters or input
volume. A hash mismatch is not a rewrite recommendation.

## Pruning and operator stats

Use `GET_QUERY_OPERATOR_STATS` only for a completed query in its documented
retrieval window and with warehouse `OPERATE`/`MONITOR` visibility. Partition
scanned/total is a derived fraction: a full scan may be correct. Join expansion,
spill, and pruning remain hypotheses until the redacted plan and workload context
are corroborated.

## Search Optimization Service (SOS) ROI

Report measured before/after latency or bytes scanned alongside SOS credits or
maintenance cost. A positive latency/scan delta is evidence of benefit, not a
currency return; an absent baseline makes ROI unknown. Do not enable, disable, or
alter SOS and do not substitute a public price for a supplied contract rate.

Primary sources:

- [Warehouse load history](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_load_history)
- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
- [Search Optimization Service](https://docs.snowflake.com/en/user-guide/search-optimization-service)
