-- External/cross-region transfer volume. The view reports bytes, not invoice price.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'data_transfer_usage',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'source_cloud', SOURCE_CLOUD,
  'source_region', SOURCE_REGION,
  'target_cloud', TARGET_CLOUD,
  'target_region', TARGET_REGION,
  'transfer_type', TRANSFER_TYPE,
  'bytes_transferred', BYTES_TRANSFERRED
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME, TRANSFER_TYPE
LIMIT 5000;
