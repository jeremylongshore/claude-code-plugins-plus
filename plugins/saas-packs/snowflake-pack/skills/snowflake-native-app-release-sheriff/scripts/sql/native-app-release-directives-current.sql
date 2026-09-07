-- Provider-visible release directives. Account targets and region lists are
-- represented only by scoped hashes or omitted.
SHOW RELEASE DIRECTIVES IN APPLICATION PACKAGE __APPLICATION_PACKAGE_IDENTIFIER__
->> WITH shown AS (SELECT * FROM $1), source_rows AS (SELECT * FROM shown),
selected_context AS (
  SELECT CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__')), 256) AS selected_package_key_sha256
), release_directives AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'release_directives', 'package_key_sha256', c.selected_package_key_sha256,
    'directive_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__', s."name", s."target_type", COALESCE(s."target_name", ''))), 256),
    'target_type', CASE WHEN UPPER(s."target_type") IN ('DEFAULT', 'ACCOUNT') THEN UPPER(s."target_type") ELSE 'PROVIDER_OTHER' END,
    'target_key_sha256', IFF(s."target_name" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), s."target_name")), 256)),
    'version', TO_VARCHAR(s."version"), 'patch', TRY_TO_NUMBER(s."patch"),
    'release_status', CASE WHEN UPPER(s."release_status") IN ('IN_PROGRESS', 'IN PROGRESS') THEN 'IN_PROGRESS' WHEN UPPER(s."release_status") IN ('HOLDING', 'DEPLOYED') THEN UPPER(s."release_status") ELSE 'PROVIDER_OTHER' END,
    'release_channel', CASE WHEN UPPER(s."release_channel") IN ('QA', 'ALPHA', 'DEFAULT') THEN UPPER(s."release_channel") ELSE 'PROVIDER_OTHER' END,
    'upgrade_in_maintenance_window', TRY_TO_BOOLEAN(s."upgrade_in_maintenance_window"),
    'upgrade_deadline', IFF(s."upgrade_deadline" IS NULL, NULL, CONVERT_TIMEZONE('UTC', s."upgrade_deadline")),
    'modified_on', CONVERT_TIMEZONE('UTC', s."modified_on")
  ) AS evidence, 1 AS dataset_order,
  COALESCE(TO_VARCHAR(s."version"), '') || '|' || COALESCE(TO_VARCHAR(s."patch"), '') || '|' || COALESCE(s."name", '') AS sort_key
  FROM source_rows AS s CROSS JOIN selected_context AS c ORDER BY sort_key LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', c.observed_at,
    'organization_name_sha256', SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256),
    'account_identifier_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256),
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC', 'selected_package_key_sha256', c.selected_package_key_sha256,
    'source_row_count', (SELECT COUNT(*) FROM source_rows), 'source_row_limit', 5000,
    'truncation_possible', (SELECT COUNT(*) FROM source_rows) >= 5000,
    'provider_latency_documented', FALSE
  ) AS evidence, 0 AS dataset_order, '' AS sort_key FROM selected_context AS c
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM release_directives
) ORDER BY dataset_order, sort_key;
