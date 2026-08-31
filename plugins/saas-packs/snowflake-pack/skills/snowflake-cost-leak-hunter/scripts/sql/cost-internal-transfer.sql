-- Snowpark Container Services internal-transfer volume. Kept separate because this
-- view has a different latency and availability boundary from DATA_TRANSFER_HISTORY.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'internal_transfer_usage',
  'start_time', START_TIME,
  'end_time', END_TIME,
  'transfer_type', TRANSFER_TYPE,
  'compute_pool_name_sha256', IFF(COMPUTE_POOL_NAME IS NULL, NULL, SHA2(TO_VARCHAR(COMPUTE_POOL_NAME), 256)),
  'bytes_transferred', BYTES_TRANSFERRED
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME, TRANSFER_TYPE
LIMIT 5000;
