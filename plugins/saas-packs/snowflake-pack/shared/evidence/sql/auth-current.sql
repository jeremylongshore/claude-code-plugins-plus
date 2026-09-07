-- Near-current SHOW USERS posture. SHOW metadata can be privilege-filtered, so
-- metadata_visible is evidence and NULL never means false.
SHOW USERS LIMIT 10000
->>
WITH show_rows AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(*) AS SHOW_ROW
  FROM $1
), normalized_show_rows AS (
  SELECT
    SHOW_ROW,
    COALESCE(
      UPPER(IFF(
        COALESCE(IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'type')), TRUE),
        NULL,
        TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'type'))
      )),
      'PERSON'
    ) AS USER_TYPE,
    IFF(
      COALESCE(NOT IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'created_on')), FALSE)
      AND COALESCE(NOT IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'disabled')), FALSE),
      TRUE,
      FALSE
    ) AS METADATA_VISIBLE
  FROM show_rows
), projected_users AS (
  SELECT
    SHA2(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'name')), 256) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'current_users',
      'user_name_sha256', SHA2(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'name')), 256),
      'created_on', TRY_TO_TIMESTAMP_LTZ(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'created_on'))),
      'disabled', TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'disabled'))),
      'type', USER_TYPE,
      'principal_scope', IFF(
        USER_TYPE = 'SNOWFLAKE_SERVICE',
        'SNOWFLAKE_MANAGED_EXCLUDED',
        'OPERATOR_OWNED'
      ),
      'has_password', TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_password'))),
      'has_rsa_public_key', TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_rsa_public_key'))),
      'has_mfa', TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_mfa'))),
      'has_pat', TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_pat'))),
      'has_workload_identity', COALESCE(
        TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_workload_identity'))),
        TRY_TO_BOOLEAN(TO_VARCHAR(GET_IGNORE_CASE(SHOW_ROW, 'has_federated_workload_authentication')))
      ),
      'metadata_visible', METADATA_VISIBLE
    ) AS EVIDENCE
  FROM normalized_show_rows
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context',
    'observed_at', CURRENT_TIMESTAMP(),
    'account_identifier_sha256', SHA2(
      TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())),
      256
    ),
    'collector_user_sha256', SHA2(TO_VARCHAR(CURRENT_USER()), 256),
    'primary_role_sha256', SHA2(TO_VARCHAR(CURRENT_ROLE()), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_VARCHAR(CURRENT_SECONDARY_ROLES()), 256)
  ) AS EVIDENCE
)
SELECT EVIDENCE
FROM (
  SELECT 0 AS SORT_GROUP, '' AS SORT_KEY, EVIDENCE FROM execution_context
  UNION ALL
  SELECT 1 AS SORT_GROUP, SORT_KEY, EVIDENCE FROM projected_users
)
ORDER BY SORT_GROUP, SORT_KEY;
