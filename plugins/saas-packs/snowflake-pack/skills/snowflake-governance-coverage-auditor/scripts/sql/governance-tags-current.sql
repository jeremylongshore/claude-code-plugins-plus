-- Selector-scoped current tag associations. Tag values and raw names remain in
-- Snowflake; only organization/account-scoped hashes are returned.
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
raw_tags AS (
  SELECT
    r.TAG_DATABASE, r.TAG_SCHEMA, r.TAG_NAME, r.TAG_VALUE, r.APPLY_METHOD,
    r.OBJECT_DATABASE, r.OBJECT_SCHEMA, r.OBJECT_NAME,
    NULL::VARCHAR AS COLUMN_NAME_OVERRIDE
  FROM TABLE(__GOVERNANCE_OBJECT_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.TAG_REFERENCES(
    '__GOVERNANCE_OBJECT_IDENTIFIER__', 'TABLE'
  )) AS r
  UNION ALL
  SELECT
    r.TAG_DATABASE, r.TAG_SCHEMA, r.TAG_NAME, r.TAG_VALUE, r.APPLY_METHOD,
    r.OBJECT_DATABASE, r.OBJECT_SCHEMA, r.OBJECT_NAME,
    r.COLUMN_NAME AS COLUMN_NAME_OVERRIDE
  FROM TABLE(__GOVERNANCE_OBJECT_DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
    '__GOVERNANCE_OBJECT_IDENTIFIER__', 'TABLE'
  )) AS r
),
tag_references AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'tag_references',
    'object_key_sha256', c.selected_object_key_sha256,
    'asset_key_sha256', IFF(
      r.COLUMN_NAME_OVERRIDE IS NULL,
      c.selected_object_key_sha256,
      SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.OBJECT_DATABASE, r.OBJECT_SCHEMA, r.OBJECT_NAME, r.COLUMN_NAME_OVERRIDE)), 256)
    ),
    'asset_domain', IFF(r.COLUMN_NAME_OVERRIDE IS NULL, c.selected_object_domain, 'COLUMN'),
    'tag_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.TAG_DATABASE, r.TAG_SCHEMA, r.TAG_NAME)), 256),
    'tag_binding_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), r.TAG_DATABASE, r.TAG_SCHEMA, r.TAG_NAME, r.TAG_VALUE)), 256),
    'apply_method', CASE
      WHEN UPPER(r.APPLY_METHOD) IN ('CLASSIFIED', 'INHERITED', 'MANUAL', 'PROPAGATED') THEN UPPER(r.APPLY_METHOD)
      WHEN r.APPLY_METHOD IS NULL OR UPPER(r.APPLY_METHOD) IN ('NULL', 'NONE') THEN 'LEGACY_UNKNOWN'
      ELSE 'PROVIDER_OTHER'
    END
  ) AS evidence,
  1 AS dataset_order,
  CONCAT_WS('|', COALESCE(r.COLUMN_NAME_OVERRIDE, ''), COALESCE(r.TAG_DATABASE, ''), COALESCE(r.TAG_SCHEMA, ''), COALESCE(r.TAG_NAME, ''), COALESCE(r.TAG_VALUE, '')) AS sort_key
  FROM raw_tags AS r
  CROSS JOIN selected_context AS c
  ORDER BY sort_key
  LIMIT 5000
),
source_counts AS (
  SELECT COUNT(*) AS source_row_count FROM raw_tags
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
  SELECT evidence, dataset_order, sort_key FROM tag_references
)
ORDER BY dataset_order, sort_key;
