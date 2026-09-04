-- Selector-scoped live data-metric associations. The selected object's raw
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
current_associations AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'current_associations',
    'object_key_sha256', c.selected_object_key_sha256,
    'association_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.REF_ID)), 256),
    'metric_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.METRIC_DATABASE_NAME, r.METRIC_SCHEMA_NAME, r.METRIC_NAME)), 256),
    'object_domain', CASE
      WHEN UPPER(r.REF_ENTITY_DOMAIN) IN ('TABLE', 'VIEW') THEN UPPER(r.REF_ENTITY_DOMAIN)
      ELSE 'PROVIDER_OTHER'
    END,
    'schedule_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.REF_ID, r.SCHEDULE)), 256),
    'schedule_status', CASE
      WHEN UPPER(r.SCHEDULE_STATUS) IN (
        'STARTED', 'STARTED_AND_PENDING_SCHEDULE_UPDATE', 'SUSPENDED',
        'SUSPENDED_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED',
        'SUSPENDED_DATA_METRIC_FUNCTION_DOES_NOT_EXIST_OR_NOT_AUTHORIZED',
        'SUSPENDED_TABLE_COLUMN_DOES_NOT_EXIST_OR_NOT_AUTHORIZED',
        'SUSPENDED_INSUFFICIENT_PRIVILEGE_TO_EXECUTE_DATA_METRIC_FUNCTION',
        'SUSPENDED_ACTIVE_EVENT_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED'
      ) THEN UPPER(r.SCHEDULE_STATUS)
      ELSE 'PROVIDER_OTHER'
    END,
    'execution_role_sha256', IFF(r.USE_ROLE IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.USE_ROLE)), 256)),
    'association_level', CASE
      WHEN UPPER(r.LEVEL) IN ('TABLE', 'SCHEMA') THEN UPPER(r.LEVEL)
      ELSE 'PROVIDER_OTHER'
    END,
    'filter_sha256', IFF(NULLIF(TO_VARCHAR(r.PROPERTIES:filter), 'null') IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.PROPERTIES:filter)), 256)),
    'group_definition_sha256', IFF(NULLIF(TO_VARCHAR(r.PROPERTIES:within_group), 'null') IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.PROPERTIES:within_group)), 256)),
    'group_limit', CASE
      WHEN NULLIF(TO_VARCHAR(r.PROPERTIES:group_limit), 'null') IS NULL THEN NULL
      WHEN TRY_TO_DECIMAL(TO_VARCHAR(r.PROPERTIES:group_limit), 38, 9) BETWEEN 1 AND 1000
        AND TRY_TO_DECIMAL(TO_VARCHAR(r.PROPERTIES:group_limit), 38, 9) = TRUNC(TRY_TO_DECIMAL(TO_VARCHAR(r.PROPERTIES:group_limit), 38, 9))
        THEN TO_NUMBER(TRY_TO_DECIMAL(TO_VARCHAR(r.PROPERTIES:group_limit), 38, 9))
      ELSE 0
    END,
    'anomaly_status', CASE
      WHEN NULLIF(UPPER(TO_VARCHAR(r.PROPERTIES:anomaly_detection_status)), 'NULL') IS NULL THEN 'NOT_CONFIGURED'
      WHEN UPPER(TO_VARCHAR(r.PROPERTIES:anomaly_detection_status)) = 'TRAINING_IN_PROGRESS' THEN 'TRAINING_IN_PROGRESS'
      ELSE 'PROVIDER_OTHER'
    END,
    'anomaly_sensitivity', CASE
      WHEN NULLIF(UPPER(TO_VARCHAR(r.PROPERTIES:anomaly_detection_sensitivity_level)), 'NULL') IS NULL THEN 'NOT_CONFIGURED'
      WHEN UPPER(TO_VARCHAR(r.PROPERTIES:anomaly_detection_sensitivity_level)) IN ('LOW', 'MEDIUM', 'HIGH') THEN UPPER(TO_VARCHAR(r.PROPERTIES:anomaly_detection_sensitivity_level))
      ELSE 'PROVIDER_OTHER'
    END
  ) AS evidence,
  1 AS dataset_order,
  TO_VARCHAR(r.REF_ID) AS sort_key
  FROM TABLE(__DATA_QUALITY_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    REF_ENTITY_NAME => '__DATA_QUALITY_OBJECT_IDENTIFIER__',
    REF_ENTITY_DOMAIN => '__DATA_QUALITY_DOMAIN__'
  )) AS r
  CROSS JOIN selected_context AS c
  ORDER BY sort_key
  LIMIT 5000
),
source_counts AS (
  SELECT COUNT(*) AS source_row_count
  FROM TABLE(__DATA_QUALITY_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
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
  SELECT evidence, dataset_order, sort_key FROM current_associations
)
ORDER BY dataset_order, sort_key;
