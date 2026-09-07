-- Near-live failover-group inventory. SHOW output is piped through a privacy
-- projection so raw account, group, owner, and comment values never leave the session.
SHOW FAILOVER GROUPS
->> WITH shown AS (SELECT * FROM $1), source_rows AS (
  SELECT * FROM shown WHERE UPPER("account_name") = UPPER(CURRENT_ACCOUNT_NAME())
), current_groups AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'current_groups',
    'local_account_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), "account_name")), 256),
    'local_group_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), "account_name", "name")), 256),
    'lineage_group_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(COALESCE("primary", CONCAT_WS('.', CURRENT_ORGANIZATION_NAME(), "account_name", "name")))), 256),
    'group_type', CASE WHEN UPPER("type") = 'FAILOVER' THEN 'FAILOVER' ELSE 'PROVIDER_OTHER' END,
    'is_primary', "is_primary",
    'object_types_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), COALESCE("object_types", ''))), 256),
    'allowed_accounts_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), COALESCE("allowed_accounts", ''))), 256),
    'allowed_integration_types_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), COALESCE("allowed_integration_types", ''))), 256),
    'replication_schedule_sha256', IFF("replication_schedule" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), "replication_schedule")), 256)),
    'schedule_status', CASE WHEN "replication_schedule" IS NULL THEN 'NOT_CONFIGURED'
      WHEN LOWER("secondary_state") = 'started' THEN 'STARTED'
      WHEN LOWER("secondary_state") = 'suspended' THEN 'SUSPENDED' ELSE 'PROVIDER_OTHER' END,
    'next_scheduled_refresh', "next_scheduled_refresh"
  ) AS evidence, 1 AS dataset_order,
  COALESCE("account_name", '') || '|' || COALESCE("name", '') AS sort_key
  FROM source_rows ORDER BY sort_key LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()),
    'organization_name_sha256', SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256),
    'account_identifier_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256),
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC', 'source_row_count', (SELECT COUNT(*) FROM source_rows),
    'source_row_limit', 5000, 'truncation_possible', (SELECT COUNT(*) FROM source_rows) >= 5000
  ) AS evidence, 0 AS dataset_order, '' AS sort_key
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM current_groups
) ORDER BY dataset_order, sort_key;
