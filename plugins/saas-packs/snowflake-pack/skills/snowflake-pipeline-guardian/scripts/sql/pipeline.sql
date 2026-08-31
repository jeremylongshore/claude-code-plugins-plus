-- Recent pipeline control-plane evidence; no COPY payload or SQL text is collected.
WITH evidence AS (
SELECT
  'task_history' AS dataset,
  CONCAT(COALESCE(DATABASE_NAME, ''), '.', COALESCE(SCHEMA_NAME, ''), '.', COALESCE(NAME, ''), '|', TO_VARCHAR(SCHEDULED_TIME), '|', COALESCE(TO_VARCHAR(RUN_ID), '')) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'task_history',
  'name', NAME,
  'database_name', DATABASE_NAME,
  'schema_name', SCHEMA_NAME,
  'state', STATE,
  'scheduled_time', SCHEDULED_TIME,
  'completed_time', COMPLETED_TIME,
  'query_start_time', QUERY_START_TIME,
  'root_task_id', ROOT_TASK_ID,
  'run_id', RUN_ID,
  'graph_run_group_id', GRAPH_RUN_GROUP_ID,
  'attempt_number', ATTEMPT_NUMBER,
  'scheduled_from', SCHEDULED_FROM,
  'query_id', QUERY_ID,
  'error_code', ERROR_CODE
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE SCHEDULED_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT
  'dynamic_table_refresh_history' AS dataset,
  CONCAT(COALESCE(DATABASE_NAME, ''), '.', COALESCE(SCHEMA_NAME, ''), '.', COALESCE(NAME, ''), '|', TO_VARCHAR(REFRESH_START_TIME), '|', COALESCE(TO_VARCHAR(QUERY_ID), '')) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'dynamic_table_refresh_history',
  'name', NAME,
  'database_name', DATABASE_NAME,
  'schema_name', SCHEMA_NAME,
  'state', STATE,
  'state_code', STATE_CODE,
  'refresh_start_time', REFRESH_START_TIME,
  'refresh_end_time', REFRESH_END_TIME,
  'data_timestamp', DATA_TIMESTAMP,
  'query_id', QUERY_ID
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.DYNAMIC_TABLE_REFRESH_HISTORY
WHERE REFRESH_START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT
  'copy_history' AS dataset,
  CONCAT(COALESCE(TABLE_NAME, ''), '|', TO_VARCHAR(LAST_LOAD_TIME), '|', SHA2(FILE_NAME, 256)) AS sort_key,
  OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'copy_history',
  'file_name_sha256', SHA2(FILE_NAME, 256),
  'stage_location_sha256', SHA2(STAGE_LOCATION, 256),
  'table_name', TABLE_NAME,
  'last_load_time', LAST_LOAD_TIME,
  'status', STATUS,
  'row_count', ROW_COUNT,
  'row_parsed', ROW_PARSED
) AS evidence
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE LAST_LOAD_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
)
SELECT evidence AS EVIDENCE
FROM evidence
ORDER BY dataset, sort_key
LIMIT 5000;
