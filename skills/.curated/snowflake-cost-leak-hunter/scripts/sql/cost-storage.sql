-- Daily operational storage snapshots for one half-open UTC window. The
-- current session must be UTC; these values use different semantics from billing.
WITH usage_rows AS (
  SELECT
    TO_VARCHAR(USAGE_DATE) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'storage_usage',
      'start_time', TO_TIMESTAMP_LTZ(USAGE_DATE),
      'end_time', DATEADD('day', 1, TO_TIMESTAMP_LTZ(USAGE_DATE)),
      'storage_bytes', STORAGE_BYTES,
      'stage_bytes', STAGE_BYTES,
      'failsafe_bytes', FAILSAFE_BYTES,
      'hybrid_table_storage_bytes', HYBRID_TABLE_STORAGE_BYTES,
      'archive_storage_cool_bytes', ARCHIVE_STORAGE_COOL_BYTES,
      'archive_storage_cold_bytes', ARCHIVE_STORAGE_COLD_BYTES,
      'archive_storage_retrieval_temp_bytes', ARCHIVE_STORAGE_RETRIEVAL_TEMP_BYTES,
      'invoice_reconciliation', 'not_reconciled'
    ) AS EVIDENCE
  FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
  WHERE TO_TIMESTAMP_LTZ(USAGE_DATE) < TO_TIMESTAMP_TZ('__WINDOW_END_UTC__')
    AND DATEADD('day', 1, TO_TIMESTAMP_LTZ(USAGE_DATE)) > TO_TIMESTAMP_TZ('__WINDOW_START_UTC__')
  ORDER BY USAGE_DATE
  LIMIT 1000
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
