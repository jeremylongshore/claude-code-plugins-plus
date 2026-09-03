-- Current pipe inventory. SHOW PIPES has a fixed 10,000-row ceiling and no
-- pagination, so treat a 10,000-row account result as incomplete.
SHOW PIPES IN ACCOUNT
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
      '_dataset', 'current_pipes',
      'object_key_sha256', SHA2(
        TO_JSON(ARRAY_CONSTRUCT(
          CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(),
          src."database_name", src."schema_name", src."name"
        )),
        256
      ),
      'created_on', TRY_TO_TIMESTAMP_LTZ(TO_VARCHAR(src."created_on")),
      'kind', src."kind"
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
