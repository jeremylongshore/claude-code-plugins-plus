-- Provider-side installed-instance cohorts. Consumer identities and provider
-- failure text are never emitted; rows are grouped by finite upgrade state.
WITH selected_context AS (
  SELECT CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__')), 256) AS selected_package_key_sha256
), source_rows AS (
  SELECT * FROM SNOWFLAKE.DATA_SHARING_USAGE.APPLICATION_STATE
  WHERE UPPER(PACKAGE_NAME) = '__APPLICATION_PACKAGE_IDENTIFIER__'
), grouped AS (
  SELECT CURRENT_VERSION, CURRENT_PATCH, PREVIOUS_VERSION_STATE, PREVIOUS_VERSION, PREVIOUS_PATCH,
    UPGRADE_STATE, TARGET_UPGRADE_VERSION, TARGET_UPGRADE_PATCH,
    COUNT(*) AS instance_count, MAX(UPGRADE_STATE_UPDATED_ON) AS latest_state_updated_on,
    MAX(UPGRADE_ATTEMPTED_ON) AS latest_upgrade_attempted_on, MAX(UPGRADE_ATTEMPT) AS maximum_upgrade_attempt
  FROM source_rows
  GROUP BY CURRENT_VERSION, CURRENT_PATCH, PREVIOUS_VERSION_STATE, PREVIOUS_VERSION, PREVIOUS_PATCH,
    UPGRADE_STATE, TARGET_UPGRADE_VERSION, TARGET_UPGRADE_PATCH
), upgrade_cohorts AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'upgrade_cohorts', 'package_key_sha256', c.selected_package_key_sha256,
    'cohort_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__', g.CURRENT_VERSION, g.CURRENT_PATCH, g.UPGRADE_STATE, g.TARGET_UPGRADE_VERSION, g.TARGET_UPGRADE_PATCH)), 256),
    'current_version', TO_VARCHAR(g.CURRENT_VERSION), 'current_patch', TRY_TO_NUMBER(g.CURRENT_PATCH),
    'previous_version_state', CASE WHEN UPPER(g.PREVIOUS_VERSION_STATE) IN ('COMPLETE', 'FINALIZING') THEN UPPER(g.PREVIOUS_VERSION_STATE) WHEN g.PREVIOUS_VERSION_STATE IS NULL THEN NULL ELSE 'PROVIDER_OTHER' END,
    'previous_version', TO_VARCHAR(g.PREVIOUS_VERSION), 'previous_patch', TRY_TO_NUMBER(g.PREVIOUS_PATCH),
    'upgrade_state', CASE WHEN UPPER(g.UPGRADE_STATE) IN ('INSTALLING', 'INSTALL_FAILED', 'COMPLETE', 'QUEUED', 'UPGRADING', 'FAILED', 'QUEUED_DELAYED', 'QUEUED_RETRY', 'DISABLED') THEN UPPER(g.UPGRADE_STATE) ELSE 'PROVIDER_OTHER' END,
    'target_version', TO_VARCHAR(g.TARGET_UPGRADE_VERSION), 'target_patch', TRY_TO_NUMBER(g.TARGET_UPGRADE_PATCH),
    'instance_count', g.instance_count,
    'latest_state_updated_on', IFF(g.latest_state_updated_on IS NULL, NULL, CONVERT_TIMEZONE('UTC', g.latest_state_updated_on)),
    'latest_upgrade_attempted_on', IFF(g.latest_upgrade_attempted_on IS NULL, NULL, CONVERT_TIMEZONE('UTC', g.latest_upgrade_attempted_on)),
    'maximum_upgrade_attempt', TRY_TO_NUMBER(g.maximum_upgrade_attempt)
  ) AS evidence, 1 AS dataset_order,
  COALESCE(TO_VARCHAR(g.CURRENT_VERSION), '') || '|' || COALESCE(TO_VARCHAR(g.CURRENT_PATCH), '') || '|' || COALESCE(g.UPGRADE_STATE, '') AS sort_key
  FROM grouped AS g CROSS JOIN selected_context AS c ORDER BY sort_key LIMIT 5000
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
    'truncation_possible', (SELECT COUNT(*) FROM grouped) >= 5000,
    'provider_latency_documented', TRUE, 'provider_latency_seconds', 600,
    'provider_latency_semantics', 'APPROXIMATE_CURRENT_SNAPSHOT_NOT_SETTLEMENT'
  ) AS evidence, 0 AS dataset_order, '' AS sort_key FROM selected_context AS c
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM upgrade_cohorts
) ORDER BY dataset_order, sort_key;
