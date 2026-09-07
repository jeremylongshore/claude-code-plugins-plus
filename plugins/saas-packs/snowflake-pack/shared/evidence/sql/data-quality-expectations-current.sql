-- Selector-scoped live data-metric expectations. The selected object's raw
-- identifier is never emitted; execution_context persists at zero rows.
WITH collection_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256
),
selected_context AS (
  SELECT
    c.*,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), SPLIT_PART('__DATA_QUALITY_OBJECT_IDENTIFIER__', '.', 1), SPLIT_PART('__DATA_QUALITY_OBJECT_IDENTIFIER__', '.', 2), SPLIT_PART('__DATA_QUALITY_OBJECT_IDENTIFIER__', '.', 3))), 256) AS selected_object_key_sha256,
    '__DATA_QUALITY_DOMAIN__' AS selected_object_domain
  FROM collection_context AS c
),
current_expectations AS (
  SELECT OBJECT_CONSTRUCT(
    '_dataset', 'current_expectations',
    'object_key_sha256', c.selected_object_key_sha256,
    'association_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), e.REF_ID)), 256),
    'metric_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), e.METRIC_DATABASE_NAME, e.METRIC_SCHEMA_NAME, e.METRIC_NAME)), 256),
    'expectation_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), e.REF_ID, e.EXPECTATION_ID, e.EXPECTATION_NAME)), 256),
    'definition_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), e.REF_ID, e.EXPECTATION_ID, e.EXPECTATION_NAME, e.EXPECTATION_EXPRESSION)), 256)
  ) AS evidence,
  1 AS dataset_order,
  CONCAT_WS('|', COALESCE(TO_VARCHAR(e.REF_ID), ''), COALESCE(TO_VARCHAR(e.EXPECTATION_ID), '')) AS sort_key
  FROM TABLE(__DATA_QUALITY_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_EXPECTATIONS(
    REF_ENTITY_NAME => '__DATA_QUALITY_OBJECT_IDENTIFIER__',
    REF_ENTITY_DOMAIN => '__DATA_QUALITY_DOMAIN__'
  )) AS e
  CROSS JOIN selected_context AS c
  ORDER BY sort_key
  LIMIT 5000
),
source_counts AS (
  SELECT COUNT(*) AS source_row_count
  FROM TABLE(__DATA_QUALITY_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_EXPECTATIONS(
    REF_ENTITY_NAME => '__DATA_QUALITY_OBJECT_IDENTIFIER__',
    REF_ENTITY_DOMAIN => '__DATA_QUALITY_DOMAIN__'
  ))
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
    'selected_object_key_sha256', c.selected_object_key_sha256,
    'selected_object_domain', c.selected_object_domain
  ) AS evidence,
  0 AS dataset_order,
  '' AS sort_key
  FROM selected_context AS c
  CROSS JOIN source_counts AS s
)
SELECT evidence
FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL
  SELECT evidence, dataset_order, sort_key FROM current_expectations
)
ORDER BY dataset_order, sort_key;
