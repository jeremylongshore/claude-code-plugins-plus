-- Bounded Account Usage observation. Factor labels are observations, not proof
-- of workload attribution or policy enforcement. Client telemetry is excluded
-- because Snowflake documents REPORTED_CLIENT_TYPE as unauthenticated input.
WITH projected_events AS (
  SELECT
    TO_VARCHAR(EVENT_TIMESTAMP) || ':' || SHA2(TO_VARCHAR(EVENT_ID), 256) AS SORT_KEY,
    OBJECT_CONSTRUCT_KEEP_NULL(
      '_dataset', 'login_history',
      'auth_event_sha256', SHA2(TO_VARCHAR(EVENT_ID), 256),
      'user_name_sha256', SHA2(TO_VARCHAR(USER_NAME), 256),
      'event_timestamp', EVENT_TIMESTAMP,
      'event_type', UPPER(TO_VARCHAR(EVENT_TYPE)),
      'first_authentication_factor', UPPER(TO_VARCHAR(FIRST_AUTHENTICATION_FACTOR)),
      'second_authentication_factor', UPPER(TO_VARCHAR(SECOND_AUTHENTICATION_FACTOR)),
      'is_success', TRY_TO_BOOLEAN(TO_VARCHAR(IS_SUCCESS)),
      'error_code', ERROR_CODE
    ) AS EVIDENCE
  FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
  WHERE EVENT_TIMESTAMP >= DATEADD('DAY', -7, CURRENT_TIMESTAMP())
    AND EVENT_TIMESTAMP < DATEADD('SECOND', -7200, CURRENT_TIMESTAMP())
    AND EVENT_TYPE = 'LOGIN'
  ORDER BY EVENT_TIMESTAMP, EVENT_ID
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
  SELECT 1 AS SORT_GROUP, SORT_KEY, EVIDENCE FROM projected_events
)
ORDER BY SORT_GROUP, SORT_KEY;
