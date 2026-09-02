-- Recent query metadata only; QUERY_TEXT and raw identity/tag values are excluded.
WITH evidence AS (
SELECT
  'query_history' AS dataset,
  COALESCE(TO_VARCHAR(QUERY_ID), '') AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'query_history',
  'query_id', QUERY_ID,
  'query_hash', QUERY_HASH,
  'query_parameterized_hash', QUERY_PARAMETERIZED_HASH,
  'warehouse_name', WAREHOUSE_NAME,
  'warehouse_size', WAREHOUSE_SIZE,
  'user_name_sha256', IFF(USER_NAME IS NULL, NULL, SHA2(TO_VARCHAR(USER_NAME), 256)),
  'role_name', ROLE_NAME,
  'query_tag_sha256', IFF(QUERY_TAG IS NULL OR QUERY_TAG = '', NULL, SHA2(TO_VARCHAR(QUERY_TAG), 256)),
  'query_tag_present', QUERY_TAG IS NOT NULL AND QUERY_TAG <> '',
  'execution_status', EXECUTION_STATUS,
  'start_time', START_TIME,
  'end_time', END_TIME,
  'total_elapsed_time_ms', TOTAL_ELAPSED_TIME,
  'compilation_time_ms', COMPILATION_TIME,
  'execution_time_ms', EXECUTION_TIME,
  'queued_overload_time_ms', QUEUED_OVERLOAD_TIME,
  'queued_provisioning_time_ms', QUEUED_PROVISIONING_TIME,
  'queued_repair_time_ms', QUEUED_REPAIR_TIME,
  'transaction_blocked_time_ms', TRANSACTION_BLOCKED_TIME,
  'bytes_scanned', BYTES_SCANNED,
  'bytes_spilled_to_local_storage', BYTES_SPILLED_TO_LOCAL_STORAGE,
  'bytes_spilled_to_remote_storage', BYTES_SPILLED_TO_REMOTE_STORAGE,
  'bytes_written', BYTES_WRITTEN,
  'rows_produced', ROWS_PRODUCED,
  'partitions_scanned', PARTITIONS_SCANNED,
  'partitions_total', PARTITIONS_TOTAL
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
UNION ALL
SELECT
  'warehouse_load' AS dataset,
  CONCAT(COALESCE(WAREHOUSE_NAME, ''), '|', TO_VARCHAR(START_TIME)) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'warehouse_load',
  'warehouse_name', WAREHOUSE_NAME,
  'start_time', START_TIME,
  'end_time', END_TIME,
  'avg_running', AVG_RUNNING,
  'avg_queued_load', AVG_QUEUED_LOAD,
  'avg_queued_provisioning', AVG_QUEUED_PROVISIONING,
  'avg_blocked', AVG_BLOCKED
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY
WHERE START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
)
SELECT evidence AS EVIDENCE
FROM evidence
ORDER BY dataset, sort_key
LIMIT 1000;
