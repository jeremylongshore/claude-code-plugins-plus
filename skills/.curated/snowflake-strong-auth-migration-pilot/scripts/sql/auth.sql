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
LIMIT 10000
;

-- LOGIN_HISTORY is historical and can lag by up to two hours. Never export
-- user names, IP addresses, or credential IDs; method names and outcomes are
-- sufficient for migration evidence.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'login_history',
  'event_id', EVENT_ID,
  'event_timestamp', EVENT_TIMESTAMP,
  'user_name_sha256', IFF(USER_NAME IS NULL, NULL, SHA2(TO_VARCHAR(USER_NAME), 256)),
  'event_type', EVENT_TYPE,
  'reported_client_type', REPORTED_CLIENT_TYPE,
  'reported_client_version', REPORTED_CLIENT_VERSION,
  'first_authentication_factor', FIRST_AUTHENTICATION_FACTOR,
  'second_authentication_factor', SECOND_AUTHENTICATION_FACTOR,
  'is_success', IS_SUCCESS,
  'error_code', ERROR_CODE,
  'connection_present', CONNECTION IS NOT NULL,
  'private_link_present', CLIENT_PRIVATE_LINK_ID IS NOT NULL
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE EVENT_TIMESTAMP >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 10000;
