-- Current-role-visible custom budget instance metadata only. This does not
-- prove root-budget activation, limits, linked resources, actions, or alerts.
SHOW SNOWFLAKE.CORE.BUDGET INSTANCES IN ACCOUNT LIMIT 10000
->>
WITH budget_rows AS (
  SELECT
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "database_name", "schema_name", "name")), 256) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'budgets',
      'name_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "name")), 256),
      'database_name_sha256', IFF("database_name" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "database_name")), 256)),
      'schema_name_sha256', IFF("schema_name" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "schema_name")), 256)),
      'current_version', "current_version",
      'owner_sha256', IFF("owner" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "owner")), 256)),
      'owner_role_type', "owner_role_type"
    ) AS EVIDENCE
  FROM $1
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', CURRENT_TIMESTAMP(),
    'account_identifier_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256),
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'session_timezone', IFF(TO_CHAR(CURRENT_TIMESTAMP(), 'TZH:TZM') = '+00:00', 'UTC', TO_CHAR(CURRENT_TIMESTAMP(), 'TZH:TZM'))
  ) AS EVIDENCE
)
SELECT EVIDENCE FROM (
  SELECT 0 AS SORT_GROUP, '' AS SORT_KEY, EVIDENCE FROM execution_context
  UNION ALL SELECT 1, SORT_KEY, EVIDENCE FROM budget_rows
)
ORDER BY SORT_GROUP, SORT_KEY;
