-- Account Usage transfer volume for one half-open UTC window. The service
-- enumerates evolving transfer types; bytes remain non-price context.
WITH usage_rows AS (
  SELECT
    CONCAT(TO_VARCHAR(START_TIME), '|', COALESCE(TRANSFER_TYPE, ''), '|', COALESCE(TARGET_REGION, '')) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
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
  WHERE START_TIME < TO_TIMESTAMP_TZ('__WINDOW_END_UTC__')
    AND END_TIME > TO_TIMESTAMP_TZ('__WINDOW_START_UTC__')
  ORDER BY START_TIME, TRANSFER_TYPE, TARGET_REGION
  LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', CURRENT_TIMESTAMP(),
    'account_identifier_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256),
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'session_timezone', IFF(TO_CHAR(CURRENT_TIMESTAMP(), 'TZH:TZM') = '+00:00', 'UTC', TO_CHAR(CURRENT_TIMESTAMP(), 'TZH:TZM'))
  ) AS EVIDENCE
)
SELECT EVIDENCE FROM (
  SELECT 0 AS SORT_GROUP, '' AS SORT_KEY, EVIDENCE FROM execution_context
  UNION ALL SELECT 1, SORT_KEY, EVIDENCE FROM usage_rows
)
ORDER BY SORT_GROUP, SORT_KEY;
