-- Account Usage is historical and can lag; live promotion decisions need Information Schema evidence too.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'replication_refresh_history',
  'replication_group_name', REPLICATION_GROUP_NAME,
  'replication_group_id', REPLICATION_GROUP_ID,
  'phase_name', PHASE_NAME,
  'start_time', START_TIME,
  'end_time', END_TIME,
  'job_uuid', JOB_UUID,
  'total_bytes', TOTAL_BYTES,
  'object_count', OBJECT_COUNT,
  'primary_snapshot_timestamp', PRIMARY_SNAPSHOT_TIMESTAMP,
  'error_code', ERROR:errorCode::STRING
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_GROUP_REFRESH_HISTORY
WHERE START_TIME >= DATEADD('day', -14, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC
LIMIT 1000;
