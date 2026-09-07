-- Current role assignments and direct object grants for one validated user.
SHOW GRANTS TO USER __USER_IDENTIFIER__ LIMIT 10000
->>
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'execution_context',
  'observed_at', CURRENT_TIMESTAMP(),
  'session_id', CURRENT_SESSION(),
  'account_locator', CURRENT_ACCOUNT(),
  'current_user_name', CURRENT_USER(),
  'primary_role', CURRENT_ROLE(),
  'primary_role_type', CURRENT_ROLE_TYPE(),
  'secondary_roles', TRY_PARSE_JSON(CURRENT_SECONDARY_ROLES())
) AS EVIDENCE
UNION ALL
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'rows',
  'created_on', src."created_on",
  'privilege', src."privilege",
  'granted_on', src."granted_on",
  'name', src."name",
  'role', src."role",
  'granted_to', src."granted_to",
  'grantee_name', src."grantee_name",
  'grant_option', src."grant_option",
  'granted_by', src."granted_by"
) AS EVIDENCE
FROM $1 AS src;
