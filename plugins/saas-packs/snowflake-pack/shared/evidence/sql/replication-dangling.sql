-- Selector-scoped dangling-reference evidence. Entity and group identifiers are
-- hashed inside Snowflake; the selected group name is never emitted.
WITH collection_context AS (
  SELECT CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256) AS organization_name_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256) AS account_identifier_sha256,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__REPLICATION_GROUP_IDENTIFIER__')), 256) AS selected_group_key_sha256
), source_rows AS (
  SELECT d.* FROM TABLE(INFORMATION_SCHEMA.REPLICATION_GROUP_DANGLING_REFERENCES('__REPLICATION_GROUP_IDENTIFIER__')) AS d
), dangling_references AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'dangling_references', 'selected_group_key_sha256', c.selected_group_key_sha256,
    'referenced_entity_domain', UPPER(d.REFERENCED_ENTITY_DOMAIN),
    'referenced_entity_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), d.REFERENCED_ENTITY_DOMAIN, d.REFERENCED_ENTITY_NAME)), 256),
    'referencing_entity_domain', UPPER(d.REFERENCING_ENTITY_DOMAIN),
    'referencing_entity_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), d.REFERENCING_ENTITY_DOMAIN, d.REFERENCING_ENTITY_NAME)), 256),
    'referencing_entity_groups_sha256', IFF(d.REFERENCING_ENTITY_GROUPS IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), d.REFERENCING_ENTITY_GROUPS)), 256)),
    'is_blocking_refresh', d.IS_BLOCKING_REFRESH
  ) AS evidence, 1 AS dataset_order,
  SHA2(TO_JSON(ARRAY_CONSTRUCT(d.REFERENCED_ENTITY_DOMAIN, d.REFERENCED_ENTITY_NAME, d.REFERENCING_ENTITY_DOMAIN, d.REFERENCING_ENTITY_NAME)), 256) AS sort_key
  FROM source_rows AS d CROSS JOIN collection_context AS c ORDER BY sort_key LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', c.observed_at,
    'organization_name_sha256', c.organization_name_sha256,
    'account_identifier_sha256', c.account_identifier_sha256,
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC', 'source_row_count', (SELECT COUNT(*) FROM source_rows),
    'source_row_limit', 5000, 'truncation_possible', (SELECT COUNT(*) FROM source_rows) >= 5000,
    'selected_group_key_sha256', c.selected_group_key_sha256, 'evaluation_scope', 'CALLING_ACCOUNT_ONLY'
  ) AS evidence, 0 AS dataset_order, '' AS sort_key FROM collection_context AS c
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM dangling_references
) ORDER BY dataset_order, sort_key;
