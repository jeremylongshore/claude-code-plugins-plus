-- Bounded refresh-progress rows for secondary groups in the current account.
WITH collection_context AS (
  SELECT CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    TO_TIMESTAMP_TZ('__WINDOW_START_UTC__') AS window_start_utc,
    TO_TIMESTAMP_TZ('__WINDOW_END_UTC__') AS window_end_utc,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256
), source_rows AS (
  SELECT p.* FROM TABLE(INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL(
    DATE_RANGE_START => TO_TIMESTAMP_TZ('__WINDOW_START_UTC__'),
    DATE_RANGE_END => TO_TIMESTAMP_TZ('__WINDOW_END_UTC__')
  )) AS p
  WHERE p.START_TIME >= TO_TIMESTAMP_TZ('__WINDOW_START_UTC__')
    AND p.START_TIME < TO_TIMESTAMP_TZ('__WINDOW_END_UTC__')
), replication_progress AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'replication_progress',
    'group_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), p.GROUP_NAME)), 256),
    'group_type', CASE WHEN UPPER(p.GROUP_TYPE) IN ('FAILOVER', 'REPLICATION') THEN UPPER(p.GROUP_TYPE) ELSE 'PROVIDER_OTHER' END,
    'phase_name', CASE WHEN UPPER(p.PHASE_NAME) IN (
      'SECONDARY_SYNCHRONIZING_MEMBERSHIP', 'SECONDARY_UPLOADING_INVENTORY',
      'PRIMARY_UPLOADING_METADATA', 'PRIMARY_UPLOADING_DATA',
      'SECONDARY_DOWNLOADING_METADATA', 'SECONDARY_DOWNLOADING_DATA',
      'SECONDARY_COMMITTING', 'COMPLETED', 'FAILED', 'CANCELED'
    ) THEN UPPER(p.PHASE_NAME) ELSE 'PROVIDER_OTHER' END,
    'start_time', p.START_TIME, 'end_time', p.END_TIME, 'progress', p.PROGRESS,
    'primary_snapshot_epoch', p.DETAILS:primarySnapshotTimestamp::NUMBER,
    'error_code', p.DETAILS:errorCode::STRING
  ) AS evidence, 1 AS dataset_order,
  CONCAT_WS('|', COALESCE(TO_VARCHAR(p.START_TIME), ''), COALESCE(p.PHASE_NAME, '')) AS sort_key
  FROM source_rows AS p ORDER BY sort_key LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', c.observed_at,
    'organization_name_sha256', c.organization_name_sha256,
    'account_identifier_sha256', c.account_identifier_sha256,
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC', 'window_start_utc', c.window_start_utc,
    'window_end_utc', c.window_end_utc, 'window_semantics', 'HALF_OPEN_UTC',
    'source_row_count', (SELECT COUNT(*) FROM source_rows), 'source_row_limit', 5000,
    'truncation_possible', (SELECT COUNT(*) FROM source_rows) >= 5000,
    'provider_retention_days', 14
  ) AS evidence, 0 AS dataset_order, '' AS sort_key FROM collection_context AS c
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM replication_progress
) ORDER BY dataset_order, sort_key;
