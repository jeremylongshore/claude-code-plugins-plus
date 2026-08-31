-- Bounded cost metadata; Account Usage can be delayed and is not invoice truth.
-- Raw user and query-tag values are excluded; hashes preserve stable grouping without
-- exporting operator-controlled identity or tenant metadata.
WITH evidence AS (
SELECT
  'warehouse_metering' AS dataset,
  CONCAT(COALESCE(WAREHOUSE_NAME, ''), '|', TO_VARCHAR(START_TIME)) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'warehouse_metering',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'warehouse_id', WAREHOUSE_ID,
  'warehouse_name', WAREHOUSE_NAME,
  'credits_used_compute', CREDITS_USED_COMPUTE,
  'credits_used_cloud_services', CREDITS_USED_CLOUD_SERVICES,
  'credits_attributed_compute_queries', CREDITS_ATTRIBUTED_COMPUTE_QUERIES
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT
  'query_attribution' AS dataset,
  CONCAT(COALESCE(TO_VARCHAR(qa.QUERY_ID), ''), '|', TO_VARCHAR(qa.START_TIME)) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'query_attribution',
  'query_id', qa.QUERY_ID,
  'query_hash', qa.QUERY_HASH,
  'query_parameterized_hash', qa.QUERY_PARAMETERIZED_HASH,
  'warehouse_name', qa.WAREHOUSE_NAME,
  'user_name_sha256', IFF(qa.USER_NAME IS NULL, NULL, SHA2(TO_VARCHAR(qa.USER_NAME), 256)),
  'query_tag_sha256', IFF(qa.QUERY_TAG IS NULL OR qa.QUERY_TAG = '', NULL, SHA2(TO_VARCHAR(qa.QUERY_TAG), 256)),
  'query_tag_present', qa.QUERY_TAG IS NOT NULL AND qa.QUERY_TAG <> '',
  'start_time', qa.START_TIME,
  'end_time', qa.END_TIME,
  'total_elapsed_time_ms', qh.TOTAL_ELAPSED_TIME,
  'execution_status', qh.EXECUTION_STATUS,
  'warehouse_size', qh.WAREHOUSE_SIZE,
  'credits_attributed_compute', qa.CREDITS_ATTRIBUTED_COMPUTE,
  'credits_used_query_acceleration', qa.CREDITS_USED_QUERY_ACCELERATION
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY qa
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh ON qh.QUERY_ID = qa.QUERY_ID
WHERE qa.START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
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
  'avg_queued_provisioning', AVG_QUEUED_PROVISIONING
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT
  'serverless_usage' AS dataset,
  CONCAT(COALESCE(SERVICE_TYPE, ''), '|', TO_VARCHAR(START_TIME)) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'serverless_usage',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'service_type', SERVICE_TYPE,
  'credits_used', CREDITS_USED
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
)
SELECT evidence AS EVIDENCE
FROM evidence
ORDER BY dataset, sort_key
LIMIT 5000;
