-- Bounded expectation history. Snowflake documents no latency SLA for this
-- SNOWFLAKE.LOCAL surface, so this evidence makes no settlement claim.
WITH collection_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    TO_TIMESTAMP_TZ('__WINDOW_START_UTC__') AS window_start_utc,
    TO_TIMESTAMP_TZ('__WINDOW_END_UTC__') AS window_end_utc,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256
),
expectation_history AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'expectation_history',
    'object_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), h.TABLE_DATABASE, h.TABLE_SCHEMA, h.TABLE_NAME)), 256),
    'association_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), h.REFERENCE_ID)), 256),
    'metric_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), h.METRIC_DATABASE, h.METRIC_SCHEMA, h.METRIC_NAME)), 256),
    'expectation_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), h.REFERENCE_ID, h.EXPECTATION_ID, h.EXPECTATION_NAME)), 256),
    'definition_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), h.REFERENCE_ID, h.EXPECTATION_ID, h.EXPECTATION_NAME, h.EXPECTATION_EXPRESSION)), 256),
    'scheduled_time', h.SCHEDULED_TIME,
    'change_commit_time', h.CHANGE_COMMIT_TIME,
    'measurement_time', h.MEASUREMENT_TIME,
    'expectation_violated', h.EXPECTATION_VIOLATED
  ) AS evidence,
  1 AS dataset_order,
  CONCAT_WS('|', COALESCE(TO_VARCHAR(h.MEASUREMENT_TIME), ''), COALESCE(TO_VARCHAR(h.REFERENCE_ID), ''), COALESCE(TO_VARCHAR(h.EXPECTATION_ID), '')) AS sort_key
  FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS AS h
  CROSS JOIN collection_context AS c
  WHERE h.MEASUREMENT_TIME >= c.window_start_utc
    AND h.MEASUREMENT_TIME < c.window_end_utc
  ORDER BY sort_key
  LIMIT 5000
),
execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context',
    'observed_at', c.observed_at,
    'organization_name_sha256', c.organization_name_sha256,
    'account_identifier_sha256', c.account_identifier_sha256,
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC',
    'window_start_utc', c.window_start_utc,
    'window_end_utc', c.window_end_utc,
    'window_semantics', 'HALF_OPEN_UTC',
    'per_dataset_row_limit', 5000,
    'provider_latency_documented', FALSE,
    'settlement_policy_status', 'NOT_DECLARED'
  ) AS evidence,
  0 AS dataset_order,
  '' AS sort_key
  FROM collection_context AS c
)
SELECT evidence
FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL
  SELECT evidence, dataset_order, sort_key FROM expectation_history
)
ORDER BY dataset_order, sort_key;
