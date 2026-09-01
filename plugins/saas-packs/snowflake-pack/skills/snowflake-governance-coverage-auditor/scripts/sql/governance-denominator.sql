-- Read-only bounded candidate-object inventory. The operator must decide which
-- opaque keys belong in the sensitive-asset denominator; never derive the
-- denominator only from already-tagged objects.
WITH candidate_assets AS (
  SELECT IFF(TABLE_TYPE ILIKE '%VIEW', 'VIEW', 'TABLE') AS domain,
    TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, NULL AS COLUMN_NAME, NULL AS DATA_TYPE
  FROM SNOWFLAKE.ACCOUNT_USAGE.TABLES
  WHERE DELETED IS NULL AND TABLE_CATALOG = '__DATABASE_LITERAL__'

  UNION ALL

  SELECT 'COLUMN' AS domain, TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
  FROM SNOWFLAKE.ACCOUNT_USAGE.COLUMNS
  WHERE DELETED IS NULL AND TABLE_CATALOG = '__DATABASE_LITERAL__'
)
SELECT
  'asset_' || LOWER(SHA2(UPPER(CONCAT_WS('|', domain, TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COALESCE(COLUMN_NAME, ''))), 256)) AS asset_key,
  domain,
  DATA_TYPE
FROM candidate_assets
ORDER BY asset_key
LIMIT __ROW_LIMIT_PLUS_ONE__;
