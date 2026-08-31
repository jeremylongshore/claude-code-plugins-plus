-- Expectation status and usage metadata; raw failed rows are intentionally excluded.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'expectation_status',
  'scheduled_time', SCHEDULED_TIME,
  'change_commit_time', CHANGE_COMMIT_TIME,
  'measurement_time', MEASUREMENT_TIME,
  'table_id', TABLE_ID,
  'table_name', TABLE_NAME,
  'table_schema', TABLE_SCHEMA,
  'table_database', TABLE_DATABASE,
  'metric_id', METRIC_ID,
  'metric_name', METRIC_NAME,
  'metric_schema', METRIC_SCHEMA,
  'metric_database', METRIC_DATABASE,
  'reference_id', REFERENCE_ID,
  'expectation_name', EXPECTATION_NAME,
  'expectation_id', EXPECTATION_ID,
  'expectation_violated', EXPECTATION_VIOLATED
) AS EVIDENCE
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
WHERE MEASUREMENT_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'data_quality_usage',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'table_id', TABLE_ID,
  'table_name', TABLE_NAME,
  'schema_id', SCHEMA_ID,
  'schema_name', SCHEMA_NAME,
  'database_id', DATABASE_ID,
  'database_name', DATABASE_NAME,
  'credits_used', CREDITS_USED
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
LIMIT 5000;
