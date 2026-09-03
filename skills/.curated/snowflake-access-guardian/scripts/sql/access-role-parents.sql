-- Current account roles and users that receive one validated account role.
SHOW GRANTS OF ROLE __ROLE_IDENTIFIER__ LIMIT 10000
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
  'role', src."role",
  'granted_to', src."granted_to",
  'grantee_name', src."grantee_name",
  'granted_by', src."granted_by"
) AS EVIDENCE
FROM $1 AS src;
