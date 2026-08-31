-- Effective-access inputs; principal names are metadata and must be handled as sensitive.
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'grants_to_roles',
  'created_on', CREATED_ON,
  'privilege', PRIVILEGE,
  'granted_on', GRANTED_ON,
  'name', NAME,
  'grantee_name', GRANTEE_NAME,
  'grant_option', GRANT_OPTION,
  'granted_by', GRANTED_BY,
  'deleted_on', DELETED_ON
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE DELETED_ON IS NULL
UNION ALL
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'grants_to_users',
  'created_on', CREATED_ON,
  'role', ROLE,
  'grantee_name', GRANTEE_NAME,
  'granted_by', GRANTED_BY,
  'deleted_on', DELETED_ON
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE DELETED_ON IS NULL
UNION ALL
SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'roles',
  'role_id', ROLE_ID,
  'created_on', CREATED_ON,
  'name', NAME,
  'owner', OWNER,
  'role_type', ROLE_TYPE,
  'role_database_name', ROLE_DATABASE_NAME,
  'owner_role_type', OWNER_ROLE_TYPE,
  'deleted_on', DELETED_ON
) AS EVIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES
WHERE DELETED_ON IS NULL
LIMIT 10000;
