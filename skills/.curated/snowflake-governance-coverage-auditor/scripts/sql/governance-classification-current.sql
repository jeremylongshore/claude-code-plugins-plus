-- Bounded Account Usage classification snapshot for one validated database.
-- Raw object names, classification RESULT, and ERROR_MESSAGE are never emitted.
WITH collection_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__GOVERNANCE_DATABASE_IDENTIFIER__')), 256) AS selected_database_key_sha256
),
classification_latest AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'classification_latest',
    'database_key_sha256', c.selected_database_key_sha256,
    'object_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), q.DATABASE_NAME, q.SCHEMA_NAME, q.TABLE_NAME)), 256),
    'classification_status', CASE
      WHEN UPPER(q.STATUS) IN ('CLASSIFIED', 'REVIEWED') THEN UPPER(q.STATUS)
      ELSE 'PROVIDER_OTHER'
    END,
    'trigger_type', CASE
      WHEN UPPER(q.TRIGGER_TYPE) IN ('MANUAL', 'AUTO CLASSIFICATION') THEN UPPER(q.TRIGGER_TYPE)
      ELSE 'PROVIDER_OTHER'
    END,
    'last_classified_on', q.LAST_CLASSIFIED_ON,
    'last_attempt_on', q.LAST_CLASSIFICATION_ATTEMPT,
    'error_present', q.ERROR_MESSAGE IS NOT NULL
  ) AS evidence,
  1 AS dataset_order,
  CONCAT_WS('|', COALESCE(TO_VARCHAR(q.SCHEMA_ID), ''), COALESCE(TO_VARCHAR(q.TABLE_ID), '')) AS sort_key
  FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST AS q
  CROSS JOIN collection_context AS c
  WHERE UPPER(q.DATABASE_NAME) = '__GOVERNANCE_DATABASE_IDENTIFIER__'
  ORDER BY sort_key
  LIMIT 5000
),
source_counts AS (
  SELECT COUNT(*) AS source_row_count
  FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
  WHERE UPPER(DATABASE_NAME) = '__GOVERNANCE_DATABASE_IDENTIFIER__'
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
    'source_row_count', s.source_row_count,
    'source_row_limit', 5000,
    'truncation_possible', s.source_row_count >= 5000,
    'provider_latency_seconds', 10800,
    'selected_database_key_sha256', c.selected_database_key_sha256
  ) AS evidence,
  0 AS dataset_order,
  '' AS sort_key
  FROM collection_context AS c
  CROSS JOIN source_counts AS s
)
SELECT evidence
FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL
  SELECT evidence, dataset_order, sort_key FROM classification_latest
)
ORDER BY dataset_order, sort_key;
