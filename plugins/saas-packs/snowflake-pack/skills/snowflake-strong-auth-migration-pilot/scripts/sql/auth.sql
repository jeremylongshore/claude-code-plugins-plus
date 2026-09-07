-- Historical user posture only. Identity values are pseudonymized; no credentials,
-- role names, profile data, or credential material leave Snowflake.
WITH projected_users AS (
  SELECT
    SHA2(TO_VARCHAR(NAME), 256) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'historical_users',
      'user_name_sha256', SHA2(TO_VARCHAR(NAME), 256),
      'created_on', CREATED_ON,
      'disabled', DISABLED,
      'type', COALESCE(UPPER(TYPE), 'PERSON'),
      'principal_scope', IFF(
        UPPER(TYPE) = 'SNOWFLAKE_SERVICE',
        'SNOWFLAKE_MANAGED_EXCLUDED',
        'OPERATOR_OWNED'
      ),
      'has_password', HAS_PASSWORD,
      'has_rsa_public_key', HAS_RSA_PUBLIC_KEY,
      'has_mfa', HAS_MFA,
      'has_pat', HAS_PAT,
      'has_workload_identity', HAS_WORKLOAD_IDENTITY
    ) AS EVIDENCE
  FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
  WHERE DELETED_ON IS NULL
  ORDER BY NAME
  LIMIT 10000
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
