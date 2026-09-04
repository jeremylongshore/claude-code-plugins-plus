-- Provider-visible application-package versions. Raw package labels and comments
-- are excluded; the strict selector is hashed in Snowflake in the same statement.
SHOW VERSIONS IN APPLICATION PACKAGE __APPLICATION_PACKAGE_IDENTIFIER__
->> WITH shown AS (SELECT * FROM $1), source_rows AS (SELECT * FROM shown),
selected_context AS (
  SELECT
    CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP()) AS observed_at,
    SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__')), 256) AS selected_package_key_sha256
), versions AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'versions',
    'package_key_sha256', c.selected_package_key_sha256,
    'version_key_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), '__APPLICATION_PACKAGE_IDENTIFIER__', s."version", s."patch")), 256),
    'version', TO_VARCHAR(s."version"),
    'patch', TRY_TO_NUMBER(s."patch"),
    'state', CASE WHEN UPPER(s."state") IN ('READY', 'DROPPED') THEN UPPER(s."state") ELSE 'PROVIDER_OTHER' END,
    'review_status', CASE WHEN UPPER(s."review_status") IN ('NOT_REVIEWED', 'IN_PROGRESS', 'APPROVED', 'REJECTED') THEN UPPER(s."review_status") ELSE 'PROVIDER_OTHER' END,
    'created_on', CONVERT_TIMEZONE('UTC', s."created_on"),
    'dropped_on', IFF(s."dropped_on" IS NULL, NULL, CONVERT_TIMEZONE('UTC', s."dropped_on"))
  ) AS evidence, 1 AS dataset_order,
  COALESCE(TO_VARCHAR(s."version"), '') || '|' || LPAD(COALESCE(TO_VARCHAR(s."patch"), ''), 10, '0') AS sort_key
  FROM source_rows AS s CROSS JOIN selected_context AS c
  ORDER BY sort_key LIMIT 5000
), execution_context AS (
  SELECT OBJECT_CONSTRUCT_KEEP_NULL(
    '_dataset', 'execution_context', 'observed_at', c.observed_at,
    'organization_name_sha256', SHA2(TO_VARCHAR(CURRENT_ORGANIZATION_NAME()), 256),
    'account_identifier_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME())), 256),
    'collector_user_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER())), 256),
    'primary_role_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_ROLE())), 256),
    'primary_role_type', CURRENT_ROLE_TYPE(),
    'secondary_roles_sha256', SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_SECONDARY_ROLES())), 256),
    'timezone', 'UTC', 'selected_package_key_sha256', c.selected_package_key_sha256,
    'source_row_count', (SELECT COUNT(*) FROM source_rows), 'source_row_limit', 5000,
    'truncation_possible', (SELECT COUNT(*) FROM source_rows) >= 5000,
    'provider_latency_documented', FALSE
  ) AS evidence, 0 AS dataset_order, '' AS sort_key FROM selected_context AS c
)
SELECT evidence FROM (
  SELECT evidence, dataset_order, sort_key FROM execution_context
  UNION ALL SELECT evidence, dataset_order, sort_key FROM versions
) ORDER BY dataset_order, sort_key;
