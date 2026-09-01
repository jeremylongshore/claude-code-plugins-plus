-- Render once per validated object in the restricted object manifest. The
-- emitted object/tag/policy identities remain opaque.
SELECT
  '__ASSET_KEY_LITERAL__' AS asset_key,
  'policy_' || LOWER(SHA2(UPPER(CONCAT_WS('|', POLICY_DB, POLICY_SCHEMA, POLICY_NAME)), 256)) AS policy_key,
  POLICY_KIND,
  IFF(TAG_NAME IS NULL, 'DIRECT', 'TAG') AS assignment,
  POLICY_STATUS,
  IFF(
    POLICY_KIND = 'AGGREGATION_POLICY' AND REF_ARG_COLUMN_NAMES IS NOT NULL,
    'sha256:' || LOWER(SHA2(UPPER(REF_ARG_COLUMN_NAMES), 256)),
    NULL
  ) AS entity_key_hash
FROM TABLE(__DATABASE_IDENTIFIER__.INFORMATION_SCHEMA.POLICY_REFERENCES(
  REF_ENTITY_NAME => '__OBJECT_LITERAL__',
  REF_ENTITY_DOMAIN => '__DOMAIN_LITERAL__'
))
ORDER BY POLICY_KIND, policy_key
LIMIT __ROW_LIMIT_PLUS_ONE__;
