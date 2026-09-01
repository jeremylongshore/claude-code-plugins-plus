-- Adaptive Warehouse per-query credits. This surface is region-dependent and is
-- attribution evidence, not an additional WAREHOUSE_METERING_HISTORY total.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'adaptive_usage',
  'start_time', QUERY_METERING_HOUR,
  'end_time', DATEADD('hour', 1, QUERY_METERING_HOUR),
  'query_id', QUERY_ID,
  'warehouse_name', WAREHOUSE_NAME,
  'query_hash', QUERY_HASH,
  'query_parameterized_hash', QUERY_PARAMETERIZED_HASH,
  'query_tag_sha256', IFF(QUERY_TAG IS NULL OR QUERY_TAG = '', NULL, SHA2(TO_VARCHAR(QUERY_TAG), 256)),
  'query_tag_present', QUERY_TAG IS NOT NULL AND QUERY_TAG <> '',
  'user_name_sha256', IFF(USER_NAME IS NULL, NULL, SHA2(TO_VARCHAR(USER_NAME), 256)),
  'credits_used', CREDITS_USED,
  'credits_used_compute', CREDITS_USED_COMPUTE,
  'credits_used_cloud_services', CREDITS_USED_CLOUD_SERVICES,
  'query_start_time', QUERY_START_TIME,
  'query_end_time', QUERY_END_TIME
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY
WHERE QUERY_METERING_HOUR >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY QUERY_METERING_HOUR, QUERY_ID
LIMIT 5000;
