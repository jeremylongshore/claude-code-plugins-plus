-- Selector-scoped current policy associations. Policy/tag/object names and
-- policy bodies never leave Snowflake.
WITH collection_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256
),
selected_context AS (
  SELECT
    c.*,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), SPLIT_PART('__GOVERNANCE_OBJECT_IDENTIFIER__', '.', 1), SPLIT_PART('__GOVERNANCE_OBJECT_IDENTIFIER__', '.', 2), SPLIT_PART('__GOVERNANCE_OBJECT_IDENTIFIER__', '.', 3))), 256) AS selected_object_key_sha256,
    '__GOVERNANCE_DOMAIN__' AS selected_object_domain
  FROM collection_context AS c
),
raw_policies AS (
  SELECT *
  FROM TABLE(__GOVERNANCE_OBJECT_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME => '__GOVERNANCE_OBJECT_IDENTIFIER__',
    REF_ENTITY_DOMAIN => '__GOVERNANCE_DOMAIN__'
  ))
  WHERE UPPER(POLICY_KIND) IN (
    'MASKING_POLICY', 'ROW_ACCESS_POLICY', 'PROJECTION_POLICY',
    'JOIN_POLICY', 'AGGREGATION_POLICY', 'PRIVACY_POLICY'
  )
),
policy_references AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'policy_references',
    'object_key_sha256', c.selected_object_key_sha256,
    'asset_key_sha256', IFF(
      p.REF_COLUMN_NAME IS NULL,
      c.selected_object_key_sha256,
      SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), p.REF_DATABASE_NAME, p.REF_SCHEMA_NAME, p.REF_ENTITY_NAME, p.REF_COLUMN_NAME)), 256)
    ),
    'asset_domain', IFF(p.REF_COLUMN_NAME IS NULL, c.selected_object_domain, 'COLUMN'),
    'policy_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), p.POLICY_DB, p.POLICY_SCHEMA, p.POLICY_NAME)), 256),
    'policy_kind', UPPER(p.POLICY_KIND),
    'assignment', IFF(p.TAG_NAME IS NULL, 'DIRECT', 'TAG'),
    'tag_key_sha256', IFF(p.TAG_NAME IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), p.TAG_DATABASE, p.TAG_SCHEMA, p.TAG_NAME)), 256)),
    'policy_status', UPPER(p.POLICY_STATUS),
    'entity_key_set_sha256', IFF(
      UPPER(p.POLICY_KIND) = 'AGGREGATION_POLICY',
      SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), p.REF_ARG_COLUMN_NAMES)), 256),
      NULL
    )
  ) AS evidence,
  1 AS dataset_order,
  CONCAT_WS('|', COALESCE(p.REF_COLUMN_NAME, ''), COALESCE(p.POLICY_KIND, ''), COALESCE(p.POLICY_DB, ''), COALESCE(p.POLICY_SCHEMA, ''), COALESCE(p.POLICY_NAME, '')) AS sort_key
  FROM raw_policies AS p
  CROSS JOIN selected_context AS c
  ORDER BY sort_key
  LIMIT 5000
),
source_counts AS (
  SELECT COUNT(*) AS source_row_count FROM raw_policies
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
  SELECT evidence, dataset_order, sort_key FROM policy_references
)
ORDER BY dataset_order, sort_key;
