-- Current-role-visible resource-monitor inventory. Assignment, quota, and
-- actions are distinct; notification recipients are intentionally excluded.
SHOW RESOURCE MONITORS
->>
WITH monitor_rows AS (
  SELECT
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "name")), 256) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'resource_monitors',
      'name_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "name")), 256),
      'owner_sha256', IFF("owner" IS NULL, NULL, SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), "owner")), 256)),
      'level', "level",
      'frequency', "frequency",
      'credit_quota', "credit_quota",
      'used_credits', "used_credits",
      'remaining_credits', "remaining_credits",
      'notify', "notify",
      'suspend', "suspend",
      'suspend_immediate', "suspend_immediate"
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
  UNION ALL SELECT 1, SORT_KEY, EVIDENCE FROM monitor_rows
)
ORDER BY SORT_GROUP, SORT_KEY;
