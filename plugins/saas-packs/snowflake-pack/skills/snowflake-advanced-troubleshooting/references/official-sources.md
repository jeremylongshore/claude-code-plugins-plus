# Snowflake Advanced Troubleshooting: Primary Sources

Use this map to verify time-sensitive behavior before acting. Snowflake documentation
is authoritative; an incident-specific account policy can be more restrictive.

## Query and operator evidence

- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
  documents that the function accepts completed queries from the previous 14 days,
  requires `OPERATE` or `MONITOR` on the warehouse, and returns nested operator
  statistics for pruning, spilling, input/output rows, and other operator details.
- [Query History view](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
  documents the Account Usage columns and latency of up to 45 minutes.
- [Query Profile common problems](https://docs.snowflake.com/en/user-guide/ui-query-profile)
  describes exploding joins, remote spilling, and ineffective pruning.
- [Queries too large for warehouse memory](https://docs.snowflake.com/en/user-guide/performance-query-warehouse-memory)
  recommends identifying the spilling operator and considering a larger warehouse or
  smaller batches. It also notes that Query Acceleration Service can write a small
  amount to remote storage for eligible queries.

## Transactions and control actions

- [Transactions](https://docs.snowflake.com/en/sql-reference/transactions) documents
  `SHOW LOCKS`, `SHOW TRANSACTIONS`, `LOCK_WAIT_HISTORY`, and transaction-abort
  behavior.
- [SHOW LOCKS](https://docs.snowflake.com/en/sql-reference/sql/show-locks) documents
  `HOLDING` and `WAITING` state, visibility rules, and the `IN ACCOUNT` restriction.
- [SYSTEM$CANCEL_QUERY](https://docs.snowflake.com/en/sql-reference/functions/system_cancel_query)
  documents query cancellation and the privileges needed to cancel another user's or
  a task's running operation.

## Pruning, clustering, and usage

- [Micro-partitions and clustering](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions)
  explains pruning and clustering depth as overlapping micro-partitions.
- [Clustering keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys)
  describes workload and cardinality considerations; it does not define a universal
  `average_depth` threshold that mandates a clustering key.
- [SYSTEM$CLUSTERING_INFORMATION](https://docs.snowflake.com/en/sql-reference/functions/system_clustering_information)
  defines the returned clustering information and histogram.
- [WAREHOUSE_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history)
  defines hourly warehouse usage and its latency. It is not query-level attribution.

## Connectivity and client diagnostics

- [Snowflake troubleshooting tools](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/snowflake-tools)
  recommends Snowflake CLI connection testing or Python connector diagnostics.
- [SYSTEM$ALLOWLIST](https://docs.snowflake.com/en/sql-reference/functions/system_allowlist)
  returns the account-specific service, stage, telemetry, OCSP, and related hosts and
  ports. Private connectivity uses the documented PrivateLink variant.
- [Connectivity issues](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/common-issues)
  explains TLS inspection, proxy, DNS, stage access, and OCSP-related failures.
- [Node.js driver logging](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-logs)
  defines supported log levels and `snowflake.configure` options.
- [Python connector diagnostics](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#running-connectivity-tests-and-diagnostics)
  defines `enable_connection_diag`, `connection_diag_log_path`, the optional allowlist
  input, and the connector version requirement.
