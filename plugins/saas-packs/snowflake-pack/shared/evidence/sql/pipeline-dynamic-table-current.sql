-- Current dynamic-table scheduling metadata. Query text, predicates, free-text
-- reasons, warehouses, owners, and execute-as users are omitted.
SHOW DYNAMIC TABLES IN ACCOUNT LIMIT 10000
->>
WITH execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context',
    'observed_at', CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()),
    'organization_name_sha256', SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256),
    'account_identifier_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())),
      256
    ),
    'collector_user_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER()
      )),
      256
    ),
    'primary_role_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE()
      )),
      256
    ),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES()
      )),
      256
    ),
    'timezone', 'UTC',
    'source_row_count', COUNT(*),
    'source_row_limit', 10000,
    'truncation_possible', COUNT(*) = 10000
  ) AS evidence
  FROM $1
), projected_rows AS (
  SELECT
    SHA2(
      TO_JSON(ARRAY_CONSTRUCT(
        CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
        src."database_name", src."schema_name", src."name"
      )),
      256
    ) AS sort_key,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'current_dynamic_tables',
      'object_key_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          src."database_name", src."schema_name", src."name"
        )),
        256
      ),
      'created_on', TRY_TO_TIMESTAMP_LTZ(TO_VARCHAR(src."created_on")),
      'rows', TRY_TO_NUMBER(TO_VARCHAR(src."rows")),
      'bytes', TRY_TO_NUMBER(TO_VARCHAR(src."bytes")),
      'scheduler', src."scheduler",
      'refresh_mode', src."refresh_mode",
      'automatic_clustering', TRY_TO_BOOLEAN(TO_VARCHAR(src."automatic_clustering")),
      'scheduling_state', src."scheduling_state",
      'last_suspended_on', TRY_TO_TIMESTAMP_LTZ(TO_VARCHAR(src."last_suspended_on")),
      'is_clone', TRY_TO_BOOLEAN(TO_VARCHAR(src."is_clone")),
      'is_replica', TRY_TO_BOOLEAN(TO_VARCHAR(src."is_replica")),
      'is_iceberg', TRY_TO_BOOLEAN(TO_VARCHAR(src."is_iceberg")),
      'data_timestamp', TRY_TO_TIMESTAMP_LTZ(TO_VARCHAR(src."data_timestamp"))
    ) AS evidence
  FROM $1 AS src
)
SELECT evidence AS EVIDENCE
FROM (
  SELECT 0 AS sort_group, '' AS sort_key, evidence FROM execution_context
  UNION ALL
  SELECT 1, sort_key, evidence FROM projected_rows
)
ORDER BY sort_group, sort_key;
