-- Identity posture only; no credentials, keys, tokens, or policy bodies.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'users',
  'name', NAME,
  'disabled', DISABLED,
  'default_role', DEFAULT_ROLE,
  'default_secondary_role', DEFAULT_SECONDARY_ROLE,
  'type', TYPE,
  'has_password', HAS_PASSWORD,
  'has_rsa_public_key', HAS_RSA_PUBLIC_KEY,
  'has_pat', HAS_PAT,
  'has_workload_identity', HAS_WORKLOAD_IDENTITY,
  'last_success_login', LAST_SUCCESS_LOGIN,
  'created_on', CREATED_ON,
  'deleted_on', DELETED_ON
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
WHERE DELETED_ON IS NULL
ORDER BY NAME
LIMIT 10000;
