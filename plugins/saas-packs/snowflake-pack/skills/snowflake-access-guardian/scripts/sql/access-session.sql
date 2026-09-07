-- Capture the current authorization context without changing primary or
-- secondary roles. The JSON-returning functions describe direct activation;
-- inherited lower roles require separate role-graph traversal.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'session_context',
  'observed_at', CURRENT_TIMESTAMP(),
  'session_id', CURRENT_SESSION(),
  'account_locator', CURRENT_ACCOUNT(),
  'account_name', CURRENT_ACCOUNT_NAME(),
  'organization_name', CURRENT_ORGANIZATION_NAME(),
  'current_user_name', CURRENT_USER(),
  'primary_role', CURRENT_ROLE(),
  'primary_role_type', CURRENT_ROLE_TYPE(),
  'secondary_roles', TRY_PARSE_JSON(CURRENT_SECONDARY_ROLES()),
  'available_account_roles', TRY_PARSE_JSON(CURRENT_AVAILABLE_ROLES())
) AS EVIDENCE;
